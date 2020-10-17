import vapoursynth as vs
from vapoursynth import core
import fvsfunc as fvf
import mvsfunc as mvf
import lvsfunc as lvf
import kagefunc as kgf
import havsfunc as hvf
import havsfunc as haf
import muvsfunc as muvf
import vsTAAmbk as taa
import vardefunc as vrdf
import hysteria as hys
import debandshit as dbs
from cooldegrain import CoolDegrain
import vsutil
core.max_cache_size = 32768


#x264 --demuxer y4m --preset veryslow --crf 14.5 --deblock=-1:-1 --bframes 16 --aq-mode 3 --aq-strength 0.85 --qcomp 0.70 --output-depth 10

src = lvf.src(r"E:\projects\Pasta\Crusade\02\[Erai-raws] Kimi to Boku no Saigo no Senjou Arui wa Sekai ga Hajimaru Seisen - 02 [v0][1080p].mkv")
src = fvf.Depth(src, 32)


src = src[624:2782]
#src = src[31739:33897]

y, u, v = kgf.split(src)
height = 810
width = vsutil.get_w(height)

descale_b = core.descale.Debicubic(y, width, height, b=1/3, c=1/3).resize.Bicubic(1920, 1080, filter_param_a=1/3, filter_param_b=1/3)
descale_b = kgf.join([descale_b, u, v])
src = fvf.Depth(descale_b, 10)
src = fvf.Depth(src, 10)


src = fvf.Depth(src, 16)
src = CoolDegrain(src, tr=1, thsad=60, thsadc=48, bits=16, blksize=8, overlap=4, plane=4)

    
src = taa.TAAmbk(src,aatype='Nnedi3')

#src = dbs.f3kbilateral(src, 20, 30, 30)
src =  core.f3kdb.Deband(src, range=17, y=30, cb=30, cr=30, grainy=16, grainc=0, output_depth=16) # OKs

src = hys.Hysteria(src)


src = fvf.Depth(src, 10)

src.set_output()
