import vapoursynth as vs
from lvsfunc.misc import source
from vardautomation import (JAPANESE, AudioCutter,
                            AudioStream, BasicTool, FileInfo, Mux, Patch,
                            PresetWEB, PresetAAC, RunnerConfig, SelfRunner,
                            VideoStream, VPath, X265Encoder)
from vardautomation.types import Range
from typing import List, Union

core = vs.core
core.num_threads = 16


#Source
SRC_FB = FileInfo(r'src/Facebook.mkv',
                idx=lambda x: source(x),
                preset=[PresetWEB, PresetAAC])
SRC_FB.name_file_final = VPath(fr"premux/{SRC_FB.name} (Premux).mkv")
SRC_FB.do_qpfile = True
#Doesn't work very well, whoops...

SRC_AD = FileInfo(r'src/Game_RIP.mkv', preset=[PresetWEB, PresetAAC])
SRC_AD.a_src = VPath(f"{SRC_AD.name}.aac")



#Filtering
def main() -> vs.VideoNode:
    """Vapoursynth filtering"""
    from vsutil import depth, get_y
    from nnedi3_resample import nnedi3_resample
    import vardefunc as vdf
    import kagefunc as kgf
    import havsfunc as hvf
    import lvsfunc as lvf
    import EoEfunc as eoe

    src = SRC_FB.clip_cut
    src = depth(src, 32)


    #Rescale
    src = kgf.inverse_scale(src, height=874, kernel='bicubic', b=0, c=1/2)
    rescale = nnedi3_resample(src).resize.Spline36(1920, 1080, format=vs.YUV420P16)


    #Denoise
    rescale = depth(rescale, 32)
    denoise = eoe.denoise.BM3D(rescale, 1, radius=2)


    #Deblock
    deblock = core.deblock.Deblock(denoise, quant=12)
    deblock = depth(deblock, 16)


    #AA
    luma = get_y(deblock)

    aa = core.sangnom.SangNom(deblock, aa=18).sangnom.SangNom(aa=18)

    aa = vdf.misc.merge_chroma(aa, deblock)
    aa = hvf.FastLineDarkenMOD(aa, strength=36, protection=5, threshold=2, thinning=0)

    #Skipping the AA filter on the early scene
    aaa = lvf.misc.replace_ranges(aa, deblock, [(0, 226),(310, 563)])


    #Deband
    detail_mask = lvf.mask.detail_mask(aaa)
    deband = vdf.deband.dumb3kdb(aaa, threshold=54, grain=12)
    deband = core.std.MaskedMerge(deband, aaa, detail_mask)


    #Graining
    graigasm_args = dict(
        thrs=[x << 8 for x in (32, 80, 128, 176)],
        strengths=[(0.4, 0.2), (0.3, 0.2), (0.2, 0.0), (0.0, 0.0)],
        sizes=(1.25, 1.15, 1, 1),
        sharps=(70, 60, 50, 50),
        grainers=[
            vdf.noise.AddGrain(seed=333, constant=True),
            vdf.noise.AddGrain(seed=333, constant=True),
            vdf.noise.AddGrain(seed=333, constant=True)
        ]
    )
    grain = vdf.noise.Graigasm(**graigasm_args).graining(deband)

    return depth(grain, 10).std.Limiter(16 << 2, [235 << 2, 240 << 2], [0, 1, 2])





class Encoding:
    runner: SelfRunner

    def __init__(self, file: FileInfo, clip: vs.VideoNode) -> None:
        self.file = file
        self.clip = clip
        assert self.file.a_src

        self.v_encoder = X265Encoder('settings/x265_settings_AB')
        self.a_extracters = [
            BasicTool('mkvextract', [self.file.path.to_str(), 'tracks', f'1:{self.file.a_src.format(1).to_str()}'])
        ]
        self.a_cutters = [AudioCutter(self.file, track=1)]


    def run(self) -> None:
        assert self.file.a_src_cut

        muxer = Mux(
            self.file,
            streams=(
                VideoStream(self.file.name_clip_output, 'x265 10Bits WEBrip @ Celest', JAPANESE),
                [AudioStream(self.file.a_src_cut.format(1), 'AAC', JAPANESE)],
                None
            )
        )
        # muxer = Mux(self.file)

        config = RunnerConfig(
            self.v_encoder, None,
            self.a_extracters, self.a_cutters, None,
            muxer
        )

        self.runner = SelfRunner(self.clip, self.file, config)
        self.runner.run()

    def do_patch(self, ranges: Union[Range, List[Range]]) -> None:
        p = Patch(self.v_encoder, self.clip, self.file, ranges)
        p.run()
        p.do_cleanup()

    def cleanup(self) -> None:
        self.runner.do_cleanup()


if __name__ == '__main__':
    print
    filtered = main()
    filtered = filtered
    Encoding(SRC_AD, filtered).run()
else:
    SRC_FB.clip_cut.set_output(0)
    FILTERED = main()
    FILTERED.set_output(1)
