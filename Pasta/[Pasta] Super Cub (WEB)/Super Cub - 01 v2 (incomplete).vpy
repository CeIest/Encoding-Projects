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
import havsfunc as hvf
import G41Fun as gf
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

opstart = 0
op_signs = [] \
    if opstart is not None else []
op_range = [] \
    if opstart is not None else []
op_interp = [] \
    if opstart is not None else []    
hs_signs = [    
]    
replace_scenes = [(894, 965),(5729, 5848),(6089, 6160),(9182, 9289),(12825, 12920),(15006, 15113),(25012, 25131),(27636, 27719),(27966, 28037),(28223, 28282),(31425, 34762), ]


#AoD+CR dehardsub luma ;  Waka+AMZ dehardsub chroma = merge
src_cr = lvf.misc.source(r"E:\sc01v2\episodes\CR.mkv")
src_aod = lvf.misc.source(r"E:\sc01v2\episodes\AoD.mkv")
src_amz = lvf.misc.source(r"E:\sc01v2\episodes\AMZ.mkv")
src_wk = lvf.misc.source(r"E:\sc01v2\episodes\WAKA.mp4")
src_fu = lvf.misc.source(r"E:\sc01v2\episodes\Funi.mkv")[240:]

#dehardsub
luma = dehardsub(src_aod, src_cr)
chroma = dehardsub(src_wk, src_amz)

luma = fvf.Depth(luma, 16)
chroma = fvf.Depth(chroma, 16)

#This destroys too much details, plz revise this (6883)
#Luma dering 
dering = hvf.EdgeCleaner(luma, 14, smode=1, hot=True)
dering = gf.MaskedDHA(dering, darkstr=0.05, brightstr=0.75)
luma = dering

#Luma aa (incomplete)
luma = lvf.sraa(luma, rfactor=1.8, rep=13, alpha=0.2, beta=0.8, gamma=500)#.rgvs.RemoveGrain(3)

#merge chromas
src = vdf.merge_chroma(luma, chroma)


#deband
detail_mask = lvf.mask.detail_mask(src, brz_a=0.040, brz_b=0.020)
deband = vdf.dumb3kdb(src, threshold=28)
src = core.std.MaskedMerge(deband, src, detail_mask)


#Checking if I didn't miss any signs
#scomp = lvf.comparison.diff(src, src_cr, thr=127, height=288, return_array=False)
#diff = lvf.comparison.diff(src, src_cr)


final = depth(src, 10)
final.set_output()
