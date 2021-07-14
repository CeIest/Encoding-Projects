import vapoursynth as vs
from vapoursynth import core
import fvsfunc as fvf
import mvsfunc as mvf
import kagefunc as kgf
import vsTAAmbk as taa
import nnedi3_rpow2
import EoEfunc as eoe
import lvsfunc as lvf
from lvsfunc.mask import BoundingBox, detail_mask
from vsutil import depth, get_y, split
import havsfunc as hvf
from nnedi3_resample import nnedi3_resample
from vardefunc.mask import FDOG, MinMax, SobelStd
import G41Fun as gf
import vardefunc as vdf


core.max_cache_size = 32768

#vspipe --y4m RS.vpy - | x264 --demuxer y4m --preset veryslow --output-depth 10 --ref 16 --qcomp 0.70  -o final.mkv -


src = core.lsmas.LWLibavSource(r"G:\Rising Steel\Facebook.mp4")
src = fvf.Depth(src, 32)



#Rescaling, original seemed 874p bicubic
src = kgf.inverse_scale(src, height=874, kernel='bicubic', b=0, c=1/2)
rescale = nnedi3_resample(src).resize.Spline36(1920, 1080, format=vs.YUV420P16)

rescale = fvf.Depth(rescale, 32)
denoise = eoe.denoise.BM3D(rescale, 1, radius=2)

deblock = core.deblock.Deblock(denoise, quant=8)
deblock = fvf.Depth(deblock, 16)




luma = get_y(deblock)
lineart = kgf.retinex_edgemask(luma)

aa = taa.TAAmbk(luma, aatype='Nnedi3')
aa = core.std.Expr((aa, luma), 'x y min')

aa = core.std.MaskedMerge(luma, aa, lineart)
aa = vdf.misc.merge_chroma(aa, deblock)
#darken = hvf.FastLineDarkenMOD(aa, strength=54, protection=5, threshold=2, thinning=0)
#mask = kgf.retinex_edgemask(aa)
#maskedmerge = core.std.MaskedMerge(aa, darken, mask)

#Skipping the AA filter on the early scene
aaa = lvf.misc.replace_ranges(aa, deblock, [(227, 2399)])



detail_mask = detail_mask(aaa)
deband = vdf.deband.dumb3kdb(aaa, threshold=42, grain=12)
deband = core.std.MaskedMerge(deband, aaa, detail_mask)
deband = kgf.adaptive_grain(deband, 0.5)

final = fvf.Depth(deband, 10)
final.set_output()






