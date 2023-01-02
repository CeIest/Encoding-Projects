import vapoursynth as vs
from vardautomation import FileInfo, PresetAAC, PresetBD, VPath
core = vs.core

from cub_common import Encoding


BDMV_PATH = VPath(r'F:\u2\[BDMV][210825][KAXA-9840][スーパーカブ][Blu-ray BOX]\SUPERCUB_1\BDMV\STREAM')

JPBD = FileInfo(BDMV_PATH / r'00010.m2ts', (24, -24), preset=[PresetBD, PresetAAC])


def main() -> vs.VideoNode:
    from vsutil import depth, get_y, split
    import havsfunc as hvf
    import lvsfunc as lvf
    import vardefunc as vdf
    import kagefunc as kgf
    import vsTAAmbk as taa
    import debandshit

    src = JPBD.clip_cut
    src = depth(src, 16)



    src = hvf.SMDegrain(src, tr=1.5, thSAD=150)

    taam = taa.TAAmbk(src, aatype='Nnedi3')
    sraa = lvf.aa.upscaled_sraa(src, rfactor=1.9)
    src = lvf.aa.clamp_aa(src, taam, sraa, strength=1)

    src = hvf.FineDehalo(src, rx=2.1, darkstr=0, brightstr=1, contra=1)
    src = hvf.EdgeCleaner(src, strength=1, rmode=13, smode=1, hot=True)

    Mask = kgf.retinex_edgemask(src, sigma=0.1)
    detail_mask = core.std.Binarize(Mask)
    deband = debandshit.dumb3kdb(src, threshold=26, grain=8)
    deband = core.std.MaskedMerge(deband, src, detail_mask.std.BoxBlur(0, 4, 2, 4, 2))

    graigasm_args = dict(
        thrs=[x << 8 for x in (32, 80, 128, 176)],
        strengths=[(0.6, 0.5), (0.4, 0.3), (0.3, 0.2), (0.2, 0.1)],
        sizes=(1.25, 1.15, 1, 1),
        sharps=(80, 70, 60, 50),
        grainers=[
            vdf.noise.AddGrain(seed=333, constant=True),
            vdf.noise.AddGrain(seed=333, constant=True),
            vdf.noise.AddGrain(seed=333, constant=True)
        ]
    )
    grain = vdf.noise.Graigasm(**graigasm_args).graining(deband)


    final = depth(grain, 10)
    return final



if __name__ == '__main__':
    filtered = main()
    brrrr = Encoding(JPBD, filtered)
    brrrr.run()
    brrrr.cleanup()
else:
    JPBD.clip_cut.set_output(0)
    filtered = main()
    if not isinstance(filtered, vs.VideoNode):
        for i, clip_filtered in enumerate(filtered):
            clip_filtered.set_output(i+4)
    else:
        filtered.set_output(10)