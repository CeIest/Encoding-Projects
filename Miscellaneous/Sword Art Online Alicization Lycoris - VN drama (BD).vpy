import vapoursynth as vs
from vapoursynth import core
import fvsfunc as fvf
import mvsfunc as mvf
import kagefunc as kgf
import vsTAAmbk as taa
import nnedi3_rpow2
import lvsfunc as lvf
import havsfunc as hvf
from nnedi3_resample import nnedi3_resample
import G41Fun as gf
import vardefunc as vdf


core.max_cache_size = 32768

#x264 --demuxer y4m --preset veryslow --crf 15.5 --ref 16 --output-depth 10


src = core.lsmas.LWLibavSource(r"00002.m2ts")
src = fvf.Depth(src, 32)


#Rescaling, original seemed 900p bicubic
rescaled = kgf.inverse_scale(src, height=900, kernel='bicubic', b=1/3, c=1/3, mask_detail=True)
rescaled = nnedi3_resample(src).resize.Spline36(1920, 1080)

#Denoising that fucking shitty source
denoise = mvf.BM3D(rescaled, sigma=3.5)

#Dering
denoise = fvf.Depth(denoise, 16)
dering = hvf.EdgeCleaner(denoise, 10, smode=1, hot=True)
dering = gf.MaskedDHA(dering, darkstr=0.05, brightstr=0.75)

##strong aa
line_m = kgf.retinex_edgemask(dering)
aa = taa.TAAmbk(dering, aatype='Eedi3', mclip=line_m)

#weak debanding
detail_mask = lvf.mask.detail_mask(aa, brz_a=0.070, brz_b=0.070)
deband = vdf.deband.dumb3kdb(aa, threshold=32, grain=8) #people I'm encoding for apparently don't like grain, F
deband = core.std.MaskedMerge(deband, aa, detail_mask)
deband = kgf.adaptive_grain(deband, 0.2)


final = fvf.Depth(deband, 10)
final.set_output()
