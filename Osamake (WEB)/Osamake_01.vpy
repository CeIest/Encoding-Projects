import vapoursynth as vs
from vapoursynth import core
import fvsfunc as fvf
import lvsfunc as lvf
import kagefunc as kgf
import havsfunc as haf
import vardefunc as vdf
import vsTAAmbk as taa
import G41Fun as gf
core.max_cache_size = 32768



src = lvf.src(r"Episodes/01.mkv")

#Couldn't really find the native res, so no rescaling
  
#aa
src = fvf.Depth(src, 16)
aa = taa.TAAmbk(src, aatype='Nnedi3')

#deband - I love dis https://slow.pics/c/7bNWMZWL
aa = fvf.Depth(aa, 16) 
detail_mask = lvf.mask.detail_mask(aa, brz_a=0.070, brz_b=0.070)
deband = vdf.deband.dumb3kdb(aa, threshold=56, grain=12)
deband = core.std.MaskedMerge(deband, aa, detail_mask)
deband = kgf.adaptive_grain(deband, 0.2)


#dehalo
dhmask = haf.HQDeringmod(deband, show=True)
dh = gf.MaskedDHA(deband, rx=2.0, ry=2.0, darkstr=0.00, brightstr=0.8, maskpull=25, maskpush=120)
dh = core.std.MaskedMerge(dh, deband, dhmask)

#grain
grain = kgf.adaptive_grain(dh, 0.2)


src = fvf.Depth(grain, 10)
src.set_output()
