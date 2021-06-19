import vapoursynth as vs
from functools import partial
import os
from vsutil import depth, get_w, get_y, iterate, join, plane, split
import vsutil
import xvs
import kagefunc as kgf
import fvsfunc as fvf
import lvsfunc as lvf
import vsTAAmbk as taa
import vardefunc as vdf
import havsfunc as hvf

core = vs.core



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
#01
replace_scenes = [(894, 965),(5729, 5848),(6089, 6160),(9182, 9289),(12825, 12920),(15006, 15113),(25012, 25131),(27636, 27719),(27966, 28037),(28223, 28282),(31425, 34762), ]



#AoD+CR dehardsub luma ;  Waka+AMZ dehardsub chroma = merge
src_cr = lvf.misc.source(r"E:\Super Cub\Episodes\CR\Super Cub E01 [1080p][AAC][JapDub][GerSub][Web-DL].mkv")
src_aod = lvf.misc.source(r"E:\Super Cub\Episodes\AoD\Super Cub E01 [1080p+][AAC][JapDub][GerSub][Web-DL].mkv")
src_amz = lvf.misc.source(r"E:\Super Cub\Episodes\AMZ\Super Cub - 01 (Amazon dAnime CBR 1080p).mkv")
src_wk = lvf.misc.source(r"E:\Super Cub\Episodes\WKN\SuperCub_01_FR_HD.mp4")


#dehardsub
luma = dehardsub(src_aod, src_cr)
chroma = dehardsub(src_wk, src_amz)


luma = fvf.Depth(luma, 16)
chroma = fvf.Depth(chroma, 16)


#Luma dering
luma = hvf.EdgeCleaner(luma, 10, rmode=1, smode=1)

#Luma AA
lumasraa = lvf.aa.upscaled_sraa(luma, rfactor=1.8, rep=13, alpha=0.2, beta=0.8, gamma=500.3)
LumaNnedi3 = taa.TAAmbk(luma, aatype='Nnedi3')
luma = lvf.aa.clamp_aa(luma, LumaNnedi3, lumasraa, strength=2)


#Chroma denoise
chroma = hvf.SMDegrain(chroma, tr=1, thSAD=80)


#merge chromas
src = vdf.misc.merge_chroma(luma, chroma)

#cwarp
src = xvs.WarpFixChromaBlend(src, thresh=63)


#scenefiltering WIP / Originally tried to smooth the scenes, but it ended up doing some weird interpolation shit. Will leave it commented so my future self will laugh at me.
#QTGMC = hvf.QTGMC(src, Preset="Slower", InputType=1)
#src = lvf.rfs(src, QTGMC,  [(591, 2314), (4558, 5516), (17871, 19392), (27966, 28037)])


#deband
detail_mask = lvf.mask.detail_mask(src, brz_a=0.040, brz_b=0.020)
deband = vdf.deband.dumb3kdb(src, threshold=36, grain=6)
src = core.std.MaskedMerge(deband, src, detail_mask)
src = kgf.adaptive_grain(src, 0.2)


#Checking if I didn't miss any signs
#diff = lvf.comparison.diff(src, src_cr)

#final = depth(diff, 10)
final = depth(src, 10)
final.set_output()
