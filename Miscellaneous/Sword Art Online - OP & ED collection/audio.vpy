import vapoursynth as vs
core = vs.core
from acsuite import eztrim

file  = r'00005.m2ts'
afile = r'audio.wav'  # pre-extracted

src = core.lsmas.LWLibavSource(file)
eztrim(src, [(24, -24)], afile)

src.set_output(0)

