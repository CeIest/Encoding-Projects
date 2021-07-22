import vapoursynth as vs
from lvsfunc.misc import source
from vardautomation import (JAPANESE, AudioCutter,
                            AudioStream, BasicTool, FileInfo, FlacEncoder, Mux,
                            PresetBD, PresetFLAC, RunnerConfig, SelfRunner,
                            VideoStream, VPath, X265Encoder)


core = vs.core
core.num_threads = 16


#Source
JPBD = FileInfo(r'm2ts/SAO_S3_Alicization_OP2v2.m2ts', 24, -24,
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
    from vsutil import depth
    import havsfunc as hvf
    import vardefunc as vdf
    import kagefunc as kgf
    import lvsfunc as lvf
    from alicizafunc import hybrid_denoise

    src = JPBD.clip_cut
    src = depth(src, 32)


    #Adaptive denoise
    denoise = hybrid_denoise(src, 0.70, 2.0)


    #AA
    aa = lvf.aa.nneedi3_clamp(denoise, strength=1.6)
    aa = depth(aa, 16)


    #Weak dehalo
    dehalo = hvf.FineDehalo(aa, rx=2.4, thmi=91, thma=211, darkstr=0, brightstr=1, contra=1)


    #Edgecleaner
    ec = hvf.EdgeCleaner(dehalo, strength=6, rmode=13, smode=1, hot=True)


    #Deband
    Mask = kgf.retinex_edgemask(ec, sigma=0.1)
    detail_mask = core.std.Binarize(Mask,9820,0)
    deband = vdf.deband.dumb3kdb(ec, threshold=56, grain=14)
    deband = core.std.MaskedMerge(deband, ec, detail_mask.std.BoxBlur(0, 4, 2, 4, 2))


    #Grain
    graigasm_args = dict(
        thrs=[x << 8 for x in (32, 80, 128, 176)],
        strengths=[(0.4, 0.3), (0.3, 0.1), (0.2, 0.1), (0.1, 0.0)],
        sizes=(1.25, 1.15, 1, 1),
        sharps=(80, 70, 60, 50),
        grainers=[
            vdf.noise.AddGrain(seed=333, constant=True),
            vdf.noise.AddGrain(seed=333, constant=True),
            vdf.noise.AddGrain(seed=333, constant=True)
        ]
    )
    grain = vdf.noise.Graigasm(**graigasm_args).graining(deband)  

    return depth(grain, 10)





class Encoding:
    def __init__(self, file: FileInfo, clip: vs.VideoNode) -> None:
        self.file = file
        self.clip = clip

    def run(self) -> None:
        assert self.file.a_src
        assert self.file.a_enc_cut

        v_encoder = X265Encoder('settings/x265_settings_S3_Alicization')

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
                VideoStream(self.file.name_clip_output, 'x265 10Bits BDrip @ Celest', JAPANESE),
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