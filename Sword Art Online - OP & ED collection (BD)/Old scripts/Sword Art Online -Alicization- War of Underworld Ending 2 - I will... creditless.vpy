from functools import partial
from pathlib import Path
import havsfunc as haf
import kagefunc as kgf
from cooldegrain import CoolDegrain
from vsutil import get_y
import lvsfunc as lvf
import vapoursynth as vs


core = vs.core
core.max_cache_size = 32768


#loading the frames (Thanks Vardë <3)
#Based off ◯PMan's script
def images_to_clip(path: Path) -> vs.VideoNode:
    return core.std.Splice([core.imwri.Read(str(image)) for image in path.glob('*')])
test = images_to_clip(Path(r'frames'))
test = core.resize.Bicubic(test, format=vs.YUV420P8, matrix_s='709').std.AssumeFPS(fpsnum=24000,fpsden=1001)


deband_a_args   = dict(iterations = 2, threshold = 3,  radius = 14)
deband_b_args   = dict(iterations = 2, threshold = 10, radius = 18)
denoise_args    = dict(tr=1, bits=16, blksize=8, overlap=4)


src = lvf.misc.source(r'[BDMV][JP] Sword Art Online - Alicization War of Underworld [Vol.06]\BDMV\STREAM\00006.m2ts')[24:-24]
srccheck = lvf.misc.source(r'[BDMV][JP] Sword Art Online - Alicization War of Underworld [Vol.06]\BDMV\STREAM\00006.m2ts')[24:-24]

#trimming + replaing to manual frames
src = src[:770]+test+src[784:]
src = lvf.util.depth(src, 32)


pre_den     = core.knlm.KNLMeansCL(src, d=1.5, h=2, device_type="GPU")
luma_mask   = lvf.mask.adaptive_mask(pre_den, luma_scaling=8)

denoise_a   = lvf.util.depth(CoolDegrain(src, thsad=48, thsadc=36, **denoise_args), 32)
denoise_b   = lvf.util.depth(CoolDegrain(src, thsad=36, thsadc=24, **denoise_args), 32)
denoise     = core.std.MaskedMerge(denoise_a, denoise_b, luma_mask)

aa = lvf.util.quick_resample(denoise, partial(lvf.aa.nneedi3_clamp, strength=1.5))
dehalo = lvf.util.quick_resample(aa, partial(haf.FineDehalo, rx=2.4, thmi=71, thma=191, darkstr=0))
ec = lvf.util.quick_resample(dehalo, partial(haf.EdgeCleaner, strength=4, rmode=13, smode=1, hot=True))


detail_mask   = lvf.mask.detail_mask(ec, sigma = 2.6, brz_a = 0.06, brz_b = 0.052)
deband_a      = core.placebo.Deband(ec,     planes = 1,   grain = 0, **deband_a_args)
deband_a      = core.placebo.Deband(deband_a, planes = 2|4, grain = 0,  **deband_a_args)
deband_a      = core.std.MaskedMerge(deband_a, ec, detail_mask)

deband_b      = core.placebo.Deband(ec,       planes = 1,   grain = 0, **deband_b_args)
deband_b      = core.placebo.Deband(deband_b, planes = 1,   grain = 8, **deband_b_args)
deband_b      = core.placebo.Deband(deband_b, planes = 2|4, grain = 4,  **deband_b_args)
deband_b      = core.placebo.Deband(deband_b, planes = 2|4, grain = 0,  **deband_b_args)


deband = core.std.MaskedMerge(deband_a, deband_b, detail_mask)


grain = kgf.adaptive_grain(deband, 0.2, luma_scaling=2)


out = grain
final = lvf.util.depth(out, 10)

#checking if the framereplaces are OK
#srccheck = lvf.util.depth(srccheck, 10)
#scomp = lvf.comparison.stack_compare(final, srccheck, make_diff=True, warn=True)

final.set_output()
