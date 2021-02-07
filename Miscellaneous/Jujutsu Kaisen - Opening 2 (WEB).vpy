from functools import partial
import os
import havsfunc as haf
import kagefunc as kgf
import fvsfunc as fvf
import lvsfunc as lvf
import vsTAAmbk as taa
import mvsfunc as mvf
from descale import Debicubic
from nnedi3_resample import nnedi3_resample
from cooldegrain import CoolDegrain
import hysteria as hys
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


#replacing bad dehardsubbed signs.
hs_signs = [(568, 616),(1474, 1508), ]    

replace_scenes = []




src_wk = lvf.misc.source(r"Jujutsu Kaisen - 14 (1080p).mkv")[4891:7047]
src_fu = lvf.misc.source(r"TVアニメ『呪術廻戦』ノンクレジットOPムービー／第2クールOPテーマ：Who-ya Extended「VIVID VICE」.mp4")



scomp = lvf.comparison.stack_compare(src_wk, src_fu, make_diff=True, warn=True)


src = dehardsub(src_wk, src_fu)
scomp2 = lvf.comparison.stack_compare(src_wk, src_fu, make_diff=True)

#filtering
src = fvf.Depth(src, 16)
src = CoolDegrain(src, tr=1, thsad=60, thsadc=48, bits=16, blksize=8, overlap=4, plane=4)    
src = taa.TAAmbk(src,aatype='Nnedi3')
#src = dbs.f3kbilateral(src, 20, 30, 30)
src =  core.f3kdb.Deband(src, range=17, y=30, cb=30, cr=30, grainy=16, grainc=0, output_depth=16) # OKs
src = hys.Hysteria(src)


#scomp.set_output()
final = fvf.Depth(src, 10)
final.set_output()
#| x264 --demuxer y4m --preset placebo --output-depth 10 --crf 10 --deblock=-1:-1
