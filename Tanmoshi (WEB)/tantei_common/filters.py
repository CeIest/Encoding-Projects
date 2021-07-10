from typing import Any, Dict, List, Optional, Tuple

import kagefunc as kgf
import lvsfunc as lvf
import vapoursynth as vs
import vardefunc as vdf

from vsutil.info import get_w

core = vs.core


def dehardsub(clip_hardsub: vs.VideoNode, ref: vs.VideoNode, replace_scenes: Optional[List[Tuple[int, int]]]) -> vs.VideoNode:
    hardsubmask = kgf.hardsubmask(clip_hardsub, ref)
    clip = core.std.MaskedMerge(clip_hardsub, ref, hardsubmask)

    hardsubmask_fade = kgf.hardsubmask_fades(clip, ref=ref, expand_n=15, highpass=800)
    clip_fade = core.std.MaskedMerge(clip, ref, hardsubmask_fade)

    if replace_scenes:
        clip = lvf.misc.replace_ranges(clip, clip_fade, replace_scenes)
    return clip



def sraa_eedi3(clip: vs.VideoNode, rep: Optional[int] = None, **eedi3_args: Any) -> vs.VideoNode:
    """Drop half the field with eedi3+nnedi3 and interpolate them.

    Args:
        clip (vs.VideoNode): Source clip.
        rep (Optional[int], optional): Repair mode. Defaults to None.

    Returns:
        vs.VideoNode: AA'd clip
    """
    nnargs: Dict[str, Any] = dict(nsize=6, nns=2, qual=1)
    eeargs: Dict[str, Any] = dict(alpha=0.2, beta=0.6, gamma=40, nrad=2, mdis=20)
    eeargs.update(eedi3_args)

    eedi3_fun, nnedi3_fun = core.eedi3m.EEDI3CL, core.nnedi3cl.NNEDI3CL

    flt = core.std.Transpose(clip)
    flt = eedi3_fun(flt, 0, False, sclip=nnedi3_fun(flt, 0, False, False, **nnargs), **eeargs)
    flt = core.std.Transpose(flt)
    flt = eedi3_fun(flt, 0, False, sclip=nnedi3_fun(flt, 0, False, False, **nnargs), **eeargs)

    if rep:
        flt = core.rgvs.Repair(flt, clip, rep)

    return flt


def upscaled_sraa(clip: vs.VideoNode, height: int, rep: Optional[int] = None, **eedi3_args: Any) -> vs.VideoNode:
    upscale = vdf.scale.nnedi3_upscale(clip, correct_shift=False) \
        .resize.Bicubic(get_w(height), height, src_left=0.5, src_top=0.5)
    aaa = sraa_eedi3(upscale, rep, **eedi3_args)
    return core.resize.Bicubic(aaa, clip.width, clip.height)
