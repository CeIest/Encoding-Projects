import vapoursynth as vs
from lvsfunc.misc import source
from vardautomation import (JAPANESE, AudioCutter,
                            AudioStream, BasicTool, FileInfo, FlacEncoder, Mux,
                            PresetBD, PresetFLAC, RunnerConfig, SelfRunner,
                            VideoStream, VPath, X265Encoder)


core = vs.core
core.num_threads = 16


#Source
JPBD = FileInfo(r'm2ts/SAO_AGGO_OP1.m2ts', None, -24,
                idx=lambda x: source(x),
                preset=[PresetBD, PresetFLAC])
JPBD.name_file_final = VPath(fr"premux/{JPBD.name} (Premux).mkv")
JPBD.do_qpfile = True
JPBD.a_src = VPath(f"{JPBD.name}.wav")
JPBD.a_src_cut = VPath(f"{JPBD.name}_cut.wav")
JPBD.a_enc_cut = VPath(f"{JPBD.name}_cut.flac")




#Filtering
def main() -> vs.VideoNode:
    """Vapoursynth filtering"""
    from vsutil import depth, get_y
    from nnedi3_resample import nnedi3_resample
    import havsfunc as hvf
    import vardefunc as vdf
    from alicizafunc import hybrid_denoise
    import kagefunc as kgf

    src = JPBD.clip_cut
    src = depth(src, 16)


    #Rescale
    y = get_y(src)
    rescale = kgf.inverse_scale(y, height=720, kernel='bicubic', b=1/3, c=1/3)
    rescale = nnedi3_resample(rescale).resize.Spline36(1920, 1080, format=vs.GRAY16)
    scaled = core.std.ShufflePlanes([rescale, src], planes=[0, 1, 2], colorfamily=vs.YUV)


    #Dehalo
    dehalo = hvf.FineDehalo(scaled, rx=2.2, thmi=91, thma=211, darkstr=0, brightstr=1, contra=1)


    #Denoise
    denoise = hybrid_denoise(dehalo, 0.60, 1.0)


    #Debanding
    Mask = kgf.retinex_edgemask(denoise, sigma=0.1)
    detail_mask = core.std.Binarize(Mask,9828,0)
    deband = vdf.deband.dumb3kdb(denoise, threshold=52, grain=12)
    deband = core.std.MaskedMerge(deband, denoise, detail_mask)


    #Graining
    graigasm_args = dict(
        thrs=[x << 8 for x in (32, 80, 128, 176)],
        strengths=[(0.4, 0.2), (0.3, 0.1), (0.2, 0.0), (0.0, 0.0)],
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
    def __init__(self, file: FileInfo, clip: vs.VideoNode) -> None:
        self.file = file
        self.clip = clip

    def run(self) -> None:
        assert self.file.a_src
        assert self.file.a_enc_cut

        v_encoder = X265Encoder('settings/x265_settings_AGGO')

        a_extracters = [
            BasicTool(
                'eac3to',
                [self.file.path.to_str(),
                 '2:', self.file.a_src.format(1).to_str()]
            )
        ]

        a_cutters = [AudioCutter(self.file, track=1)]
        a_encoders = [FlacEncoder(self.file, track=1)]

        muxer = Mux(
            self.file,
            streams=(
                VideoStream(self.file.name_clip_output, 'Encode by Celest @ SAOfandom', JAPANESE),
                AudioStream(self.file.a_enc_cut.format(1), 'FLAC', JAPANESE),
                None
            )
        )

        config = RunnerConfig(v_encoder, None, a_extracters, a_cutters, a_encoders, muxer)

        runner = SelfRunner(self.clip, self.file, config)
        runner.run()
        runner.do_cleanup()




if __name__ == '__main__':
    print
    filtered = main()
    filtered = filtered
    Encoding(JPBD, filtered).run()
else:
    JPBD.clip_cut.set_output(0)
    FILTERED = main()
    FILTERED.set_output(1)
