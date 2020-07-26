from functools import partial
import os
import havsfunc as haf
import kagefunc as kgf
import lvsfunc as lvf
import vsTAAmbk as taa
import mvsfunc as mvf
from descale import Debicubic
from nnedi3_resample import nnedi3_resample
from toolz import functoolz
from vsutil import depth, get_w, get_y, iterate, join, plane, split
import vapoursynth as vs
core = vs.core



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

replace_scenes = [
]




src_wk = lvf.misc.source(r"E:\encode\SAO3_WoU_15_EN_HD.mp4")
src_fu = lvf.misc.source(r"E:\encode\[Erai-raws] Sword Art Online Alicization - War of Underworld 2nd Season - 03 [1080p][Multiple Subtitle].mkv")

#freezing WAKA's first frame to match CR
src_wk = src_wk[0] * 1 + src_wk

src_fu = src_fu[:9445]+src_fu[9446:]


src_fu = src_fu.std.DuplicateFrames([18722]*3)
src_fu = src_fu[:18726]+src_fu[18728:]
src_fu = src_fu.std.DuplicateFrames([33924]*72)

scomp = lvf.comparison.stack_compare(src_wk, src_fu, make_diff=True, warn=True)


src = dehardsub(src_wk, src_fu)
scomp2 = lvf.comparison.stack_compare(src_wk, src_fu, make_diff=True)

src = depth(src, 32)



out = functoolz.compose(
#Filtering defs
)


out = out(src)
#scomp.set_output()
final = depth(out, 10)
final.set_output()
#vspipe --y4m 15.vpy - | x264 --demuxer y4m --preset veryslow --output-depth 10 --crf 15 --threads 18 --tune animation -o output.mkv -
