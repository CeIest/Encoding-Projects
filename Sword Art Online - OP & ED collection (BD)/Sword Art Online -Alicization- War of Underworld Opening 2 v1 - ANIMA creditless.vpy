from functools import partial
import havsfunc as haf
import kagefunc as kgf
from cooldegrain import CoolDegrain
from vsutil import get_y
import lvsfunc as lvf
import vapoursynth as vs

core = vs.core
core.max_cache_size = 1024 * 3

#Based off ◯PMan's script
deband_a_args   = dict(iterations = 2, threshold = 3,  radius = 14)
deband_b_args   = dict(iterations = 2, threshold = 10, radius = 18)
denoise_args    = dict(tr=1, bits=16, blksize=8, overlap=4)

src = lvf.misc.source(r'00005.m2ts')

src = src[24:-24]
src = lvf.util.depth(src, 32)


pre_den     = core.knlm.KNLMeansCL(src, d=1.5, h=2, device_type="GPU")
luma_mask   = lvf.mask.adaptive_mask(pre_den, luma_scaling=8)

denoise_a   = lvf.util.depth(CoolDegrain(src, thsad=72, thsadc=48, **denoise_args), 32)
denoise_b   = lvf.util.depth(CoolDegrain(src, thsad=40, thsadc=48, **denoise_args), 32)
denoise     = core.std.MaskedMerge(denoise_a, denoise_b, luma_mask)

aa = lvf.util.quick_resample(denoise, partial(lvf.aa.nneedi3_clamp, strength=1.5))
dehalo = lvf.util.quick_resample(aa, partial(haf.FineDehalo, rx=2.4, thmi=91, thma=211, darkstr=0, brightstr=1, contra=1))
ec = lvf.util.quick_resample(dehalo, partial(haf.EdgeCleaner, strength=8, rmode=13, smode=1, hot=True))

detail_mask   = lvf.mask.detail_mask(ec, sigma = 2.6, brz_a = 0.06, brz_b = 0.012)
deband_a      = core.placebo.Deband(ec,     planes = 1,   grain = 0, **deband_a_args)
deband_a      = core.placebo.Deband(deband_a, planes = 2|4, grain = 0,  **deband_a_args)
deband_a      = core.std.MaskedMerge(deband_a, ec, detail_mask)

deband_b      = core.placebo.Deband(ec,       planes = 1,   grain = 0, **deband_b_args)
deband_b      = core.placebo.Deband(deband_b, planes = 1,   grain = 12, **deband_b_args)
deband_b      = core.placebo.Deband(deband_b, planes = 2|4, grain = 0,  **deband_b_args)
deband_b      = core.placebo.Deband(deband_b, planes = 2|4, grain = 0,  **deband_b_args)



deband = core.std.MaskedMerge(deband_a, deband_b, detail_mask)

grain = kgf.adaptive_grain(deband, 0.3, luma_scaling=2)


out = grain
final = lvf.util.depth(out, 10)
final.set_output()