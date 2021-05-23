import vapoursynth as vs
from vapoursynth import core
import fvsfunc as fvf
import mvsfunc as mvf
import lvsfunc as lvf
import kagefunc as kgf
import havsfunc as hvf
import havsfunc as haf
import vardefunc as vdf
import muvsfunc as muvf
import vsTAAmbk as taa
import G41Fun as gf
import hysteria as hys
import debandshit as dbs
from vsutil import get_y, get_w
from cooldegrain import CoolDegrain
import vsutil
core.max_cache_size = 32768


src = lvf.src(r"Osananajimi ga Zettai ni Makenai Love Comedy - 0x (1080p).mkv")

#Couldn't really find the native res, so no descaling

src = fvf.Depth(src, 16)    

#aa
aa = lvf.sraa(src, rfactor=1.8, rep=13, alpha=0.2, beta=0.8, gamma=500)

src = fvf.Depth(src, 32) 

#deband
detail_mask = lvf.mask.detail_mask(aa, brz_a=0.070, brz_b=0.070)
deband = vdf.dumb3kdb(aa, threshold=56, grain=1)
deband = core.std.MaskedMerge(deband, aa, detail_mask)

#dehalo
dhmask = haf.HQDeringmod(deband, show=True)
dh = gf.MaskedDHA(deband, rx=2.0, ry=2.0, darkstr=0.00, brightstr=0.8, maskpull=25, maskpush=120)
dh = core.std.MaskedMerge(dh, deband, dhmask)

src = fvf.Depth(dh, 10)
src.set_output()

#| x264 --demuxer y4m --preset slow --output-depth 10 --crf 16.5 --aq-mode 3 --aq-strength 0.85 --ref 16 --qcomp 0.8
