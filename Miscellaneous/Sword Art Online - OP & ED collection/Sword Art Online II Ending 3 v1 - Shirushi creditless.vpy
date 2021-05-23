from vapoursynth import core
import fvsfunc as fvf
import kagefunc as kgf
import mvsfunc as mvf
import vardefunc as vdf
import insaneAA
import havsfunc as hvf
import lvsfunc as lvf
import cooldegrain



src = lvf.misc.source(r'00005.m2ts')[24:-24]

aa = fvf.Depth(src, 32)
aa = insaneAA.insaneAA(src, nnedi3_mode=insaneAA.NNEDI3Mode.NNEDI3, nnedi3_device=-1, descale_strength=0.28, kernel='bicubic', descale_height=720)
aa = fvf.Depth(aa, 16)

clip_y = mvf.GetPlane(aa, 0)
pf = core.dfttest.DFTTest(clip_y, sigma=2, tbsize=3, opt=1)
den_y = cooldegrain.CoolDegrain(clip_y, tr=1, thsad=24, thsadc=24, bits=16, blksize=8, overlap=4, pf=pf)
dn = core.std.ShufflePlanes([den_y, aa, aa], [0,1,2], colorfamily=aa.format.color_family)

src = fvf.Depth(src, 16)
sharpen = hvf.ContraSharpening(dn, src)

detail_mask = lvf.mask.detail_mask(sharpen, brz_a=0.018, brz_b=0.055)
deband = vdf.deband.dumb3kdb(sharpen, threshold=20, grain=10)
deband = core.std.MaskedMerge(deband, sharpen, detail_mask)


grain = kgf.adaptive_grain(deband, 0.1, luma_scaling=2)


final = fvf.Depth(grain, 10)
final.set_output()
