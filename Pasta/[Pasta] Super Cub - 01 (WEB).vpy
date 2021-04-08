from functools import partial
import os
import havsfunc as haf
import kagefunc as kgf
import lvsfunc as lvf
import vsTAAmbk as taa
from nnedi3_resample import nnedi3_resample
from toolz import functoolz
from vsutil import depth, get_w, get_y, iterate, join, plane, split
import vapoursynth as vs
import vsutil
import kagefunc as kgf
import fvsfunc as fvf
import lvsfunc as lvf
from nnedi3_rpow2CL import *
core = vs.core

core.max_cache_size = 32768



#Stolen from LightArrowsEXE.
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



src_wk = lvf.misc.source(r"E:\SuperCub_01_FR_HD.mp4")
src_fu = lvf.misc.source(r"E:\[SubsPlease] Super Cub - 01 (1080p) [5A27D649].mkv")[240:]



#dehardsub
src = dehardsub(src_wk, src_fu)
scomp2 = lvf.comparison.stack_compare(src_wk, src_fu, make_diff=True)


scaled = depth(src, 32)

#descale + rescale
scaled = kgf.inverse_scale(scaled, height=970, kernel='bicubic')
scaled = nnedi3_rpow2CL(scaled).resize.Bicubic(1920, 1080, filter_param_a=0, filter_param_b=0, format=vs.YUV420P10)                
 
scaled = fvf.Depth(scaled, 16)


#filtering
dering = haf.HQDeringmod(scaled)

aa = taa.TAAmbk(dering,aatype='Nnedi3')

deband = core.f3kdb.Deband(aa, output_depth=16, dynamic_grain=True, grainy=16, grainc=16)

dehalo = haf.DeHalo_alpha(deband, rx=1.0, ry=1.0, darkstr=0.4, brightstr=1.0, lowsens=50, highsens=50, ss=1.5)	



final = depth(dehalo, 10)
final.set_output()

#| x264 --demuxer y4m --preset veryslow --output-depth 10 --crf 16.5 --aq-mode 3 --aq-strength 0.85 --ref 16 --qcomp 0.7
