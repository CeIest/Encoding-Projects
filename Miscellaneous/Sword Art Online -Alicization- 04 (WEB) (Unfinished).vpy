from functools import partial
import os
import havsfunc as haf
import kagefunc as kgf
import lvsfunc as lvf
import mvsfunc as mvf
from descale import Debicubic
from nnedi3_resample import nnedi3_resample
from toolz import functoolz
from vsutil import depth, get_w, get_y, iterate, join, plane, split
import vapoursynth as vs
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
    


#scenes
opstart = 1296

op_signs = [(opstart+397, opstart+508)] \
    if opstart is not None else []
op_range = [(opstart, opstart+2157)] \
    if opstart is not None else []
op_interp = [(opstart+594, opstart+628)] \
    if opstart is not None else []    



hs_signs = [    
]    

 
replace_scenes = [
]



#compare
src_wk = lvf.misc.source(r"E:\dehardsub\SAO3_04_EN_HD.mp4")#[9432:16049]
src_fu = lvf.misc.source(r"E:\dehardsub\[HorribleSubs] Sword Art Online - Alicization - 04 [1080p].mkv")#[9447:16064]
src_wk = src_wk[0] * 4 + src_wk
scomp = lvf.comparison.stack_compare(src_wk, src_fu, make_diff=True, warn=True)



src = dehardsub(src_wk, src_fu)
scomp2 = lvf.comparison.stack_compare(src, src_fu, make_diff=True)

src = depth(src, 32)



out = functoolz.compose(
#def dependencies
)


out = out(src)

final = depth(out, 10)
final.set_output()
#vspipe --y4m dehardsub.vpy - | x264 --demuxer y4m --preset veryslow --output-depth 10 --crf 14 --threads 18 --tune animation -o x264output.mkv -



