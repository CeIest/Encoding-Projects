import vapoursynth as vs
from vapoursynth import core
import fvsfunc as fvf
import mvsfunc as mvf
import kagefunc as kgf
import havsfunc as haf
import vsTAAmbk as taa

import debandshit as dbs
from cooldegrain import CoolDegrain
import vsutil

core.max_cache_size = 32768

#x264 --demuxer y4m --preset veryslow --crf 15.5 --deblock=-1:-1 --output-depth 10 -o x264output.h264 -


src = core.lsmas.LWLibavSource(r"Sword Art Online - Alicization Lycoris\SAOAL_SPECIAL_CONTENTS_DISC\BDMV\STREAM\00002.m2ts")
src = fvf.Depth(src, 32)


#Bicubic b 0.33 c 0.33 AR: 1.78 Steps: 1
y, u, v = kgf.split(src)
height = 900
width = vsutil.get_w(height)

descale_b = core.descale.Debicubic(y, width, height, b=1/3, c=1/3).resize.Bicubic(1920, 1080, filter_param_a=1/3, filter_param_b=1/3)
descale_b = kgf.join([descale_b, u, v])

rescaled = fvf.Depth(descale_b, 16)



denoise = mvf.BM3D(rescaled, sigma=5)
dering = haf.HQDeringmod(denoise)		

aa = taa.TAAmbk(dering,aatype='Nnedi3')
deband = core.f3kdb.Deband(aa, output_depth=16, dynamic_grain=True, grainy=16, grainc=16)

dehalo = haf.DeHalo_alpha(deband, rx=1.0, ry=1.0, darkstr=0.4, brightstr=1.0, lowsens=50, highsens=50, ss=1.5)		



final = fvf.Depth(dehalo, 10)
final.set_output()
