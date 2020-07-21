#very weak script. Sorry!
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

core.max_cache_size = 32768



src = core.lsmas.LWLibavSource(r"E:\projects\Kagerou\BDMV\Kagerou_Daze_In_A_Days_BDMV\BDMV\STREAM\00001.m2ts")


src = mvf.BM3D(src, sigma=1, radius1=1) 
src = core.fft3dfilter.FFT3DFilter(src, sigma=1.5)
src = core.f3kdb.Deband(src)



src.set_output()
#vspipe --y4m red.vpy - | x264 --demuxer y4m --preset veryslow --output-depth 10 --crf 14 --threads 18 --tune animation -o x264output.mkv -
