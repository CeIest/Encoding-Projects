#Dummy script I'll be using for future sped:tm: encode of SAO trailers.
import vapoursynth as vs
from vapoursynth import core
import fvsfunc as fvf
import mvsfunc as mvf
import lvsfunc as lvf
import kagefunc as kgf
import havsfunc as hvf
import muvsfunc as muvf
import vsTAAmbk as taa
import hysteria as hys

core.max_cache_size = 32768

#vspipe --y4m Trailer.vpy - | x264 --demuxer y4m --preset veryslow --output-depth 10 --deblock -1:-1 --aq-mode 3 --aq-strength 1.0 -o owo.mkv -

src = core.ffms2.Source(r"F:\video")
src = fvf.Depth(src, 16)



#src = src.resize.Spline36(1280,720)
#src = src[50:100]



src = src.dfttest.DFTTest(sigma=8,tbsize=1)
src = mvf.BM3D(src, sigma=1, radius1=1)
src = taa.TAAmbk(src,aatype='Nnedi3')
src = core.f3kdb.Deband(src, output_depth=16, dynamic_grain=True, grainy=16, grainc=16)


src = hys.Hysteria(src)




src = fvf.Depth(src, 10)
src.set_output()