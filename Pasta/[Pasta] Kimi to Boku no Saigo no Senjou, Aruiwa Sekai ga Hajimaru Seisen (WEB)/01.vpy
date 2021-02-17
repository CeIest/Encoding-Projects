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
core.max_cache_size = 32768
#Thanks Vardë <3

#x264 --demuxer y4m --preset veryslow --crf 14.5 --ref 16 --deblock=-1:-1 --bframes 16 --aq-mode 3 --aq-strength 0.85 --qcomp 0.70 --output-depth 10

src = core.ffms2.Source(r"E:\[-missingNo-] Our Last Crusade or the Rise of a New World - 01 [1080p].mkv")
src = fvf.Depth(src, 16)

src = src[240:]


src = CoolDegrain(src, tr=1, thsad=60, thsadc=48, bits=16, blksize=8, overlap=4, plane=4)             #for possible v2
#denoise = CoolDegrain(src, tr=1, thsad=24, blksize=8, overlap=4, plane=4)
#src = denoise

src = taa.TAAmbk(src,aatype='Nnedi3') 

src =  core.f3kdb.Deband(src, range=17, y=30, cb=30, cr=30, grainy=16, grainc=0, output_depth=16)     #for possible v2
#src = dbs.f3kbilateral(src, range=17, y=30, c=30)

src = hys.Hysteria(src)



src = fvf.Depth(src, 10)
src.set_output()
