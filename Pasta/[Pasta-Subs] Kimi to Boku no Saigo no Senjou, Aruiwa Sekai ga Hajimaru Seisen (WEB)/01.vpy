import vapoursynth as vs
from vapoursynth import core
import fvsfunc as fvf
import mvsfunc as mvf
import lvsfunc as lvf
import kagefunc as kgf
import havsfunc as hvf
import muvsfunc as muvf
import vsTAAmbk as taa
import vardefunc as vrdf
import hysteria as hys
import debandshit as dbs
from cooldegrain import CoolDegrain
core.max_cache_size = 32768

# Vardë <3
#vspipe --y4m 01.vpy - | x264 --demuxer y4m --preset veryslow --crf 14.5 --ref 16 --deblock=-1:-1 --bframes 16 --aq-mode 3 --aq-strength 0.85 --qcomp 0.70 --output-depth 10 -o out.mkv -


src = core.ffms2.Source(r"E:\[-missingNo-] Our Last Crusade or the Rise of a New World - 01 [1080p].mkv") #Recommended for .mkv and .avi

src = fvf.Depth(src, 16)


src = src[240:]


denoise = CoolDegrain(src, tr=1, thsad=24, blksize=8, overlap=4, plane=4)
src = denoise
   
    
src = taa.TAAmbk(src,aatype='Nnedi3') #antialiasing


deband_mask = lvf.denoise.detail_mask(src, brz_a=2000, brz_b=1000)
deband = dbs.f3kpf(src, 17, 30, 30)
deband_b = dbs.f3kpf(src, 17, 84, 84)
deband = lvf.rfs(deband, deband_b, [(2090, 2107)])
deband = core.std.MaskedMerge(deband, src, deband_mask)
src = deband


src = hys.Hysteria(src) #sharpening


src = fvf.Depth(src, 10)

src.set_output()
