import vapoursynth as vs
from functools import partial
import os
import kagefunc as kgf
import lvsfunc as lvf
#import vsTAAmbk as taa
#from nnedi3_resample import nnedi3_resample
#from nnedi3_rpow2CL import *
#from toolz import functoolz
from vsutil import depth, get_w, get_y, iterate, join, plane, split
import vsutil
import kagefunc as kgf
import fvsfunc as fvf
import muvsfunc as muvf
import lvsfunc as lvf
import atomchtools as atf
import vardefunc as vdf
core = vs.core

core.max_cache_size = 32768



#Stolen from LightArrowsEXE
def dehardsub(clip_a: vs.VideoNode, clip_b: vs.VideoNode) -> vs.VideoNode:
    hardsubmask = kgf.hardsubmask(clip_a, clip_b)
    clip = core.std.MaskedMerge(clip_a, clip_b, hardsubmask)

    hardsubmask_fade = lvf.util.quick_resample(
        clip_a, partial(kgf.hardsubmask_fades, ref=clip_b, expand_n=15, highpass=600)
    )
    clip_fade = core.std.MaskedMerge(clip_a, clip_b, hardsubmask_fade)
    clip = lvf.rfs(clip, clip_fade, ranges=op_signs + hs_signs)
    if replace_scenes:
        clip = lvf.rfs(clip, clip_b, ranges=replace_scenes)
    return clip
    


#Scenes replace
opstart = 0

op_signs = [] \
    if opstart is not None else []
op_range = [] \
    if opstart is not None else []
op_interp = [] \
    if opstart is not None else []    

hs_signs = [    
]    

replace_scenes = [(5729, 5849),(6089, 6161),(13344, 13428),(28223, 28283),(31425, 34762), ]

src_wk = lvf.misc.source(r"E:\sc 01\SuperCub_01_FR_HD.mp4")
src_fu = lvf.misc.source(r"E:\sc 01\[SubsPlease] Super Cub - 01 (1080p) [5A27D649].mkv")[240:]


#dehardsub
src = dehardsub(src_wk, src_fu)
scomp2 = lvf.comparison.stack_compare(src_wk, src_fu, make_diff=True)


#descale + rescale ---- V2: this added more artefacts than planned, so dropped
#scaled = depth(src, 32)
#scaled = kgf.inverse_scale(scaled, height=970, kernel='bicubic')
#scaled = nnedi3_rpow2CL(scaled).resize.Bicubic(1920, 1080, filter_param_a=0, filter_param_b=0, format=vs.YUV420P10)                
 


#filtering
scaled = fvf.Depth(src, 16)

#aa ---- V2. figured there was no need to add rgvs / and didn't really want to use Nnedi3
#linemask = muvf.AnimeMask(scaled, mode=-1).rgvs.RemoveGrain(3).rgvs.RemoveGrain(3).rgvs.RemoveGrain(3)
#aa = taa.TAAmbk(scaled, aatype='Nnedi3', mclip=linemask, opencl=True)
aa = lvf.sraa(scaled, rfactor=1.8, rep=13, alpha=0.2, beta=0.8, gamma=500)#.rgvs.RemoveGrain(3)

#deband ---- Note: Thought about debanding only that one annoying dark scene, but there are a lot of other dark scenes in this episode (or I should just learn how to scene-filter)
detail_mask = lvf.mask.detail_mask(aa, brz_a=2000, brz_b=1200)
#detail_mask = atf.retinex_edgemask(aa, draft=True, opencl=True).std.Binarize(5000).rgvs.RemoveGrain(4).std.Inflate()
deband = vdf.dumb3kdb(aa, threshold=28)
deband = core.std.MaskedMerge(deband, aa, detail_mask)


final = depth(deband, 10)
final.set_output()

#| x264 --demuxer y4m --preset veryslow --output-depth 10 --crf 16 --aq-mode 3 --aq-strength 0.85 --ref 16 --qcomp 0.7
