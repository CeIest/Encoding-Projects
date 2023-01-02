from typing import List, Union, Any

import vapoursynth as vs
from vardautomation import (JAPANESE, EztrimCutter, AudioStream, QAACEncoder,
                            FileInfo, Mux, Patch, RunnerConfig, SelfRunner,
                            VideoStream, X265Encoder)
from vardautomation.tooling import AudioExtracter
from vardefunc.types import Range

core = vs.core


class Encoding:
    runner: SelfRunner
    xml_tag: str = 'xml_tag.xml'


    def __init__(self, file: FileInfo, clip: vs.VideoNode) -> None:
        self.file = file
        self.clip = clip
        assert self.file.a_src

        self.v_encoder = X265Encoder('cub_common/x265_settings')
        self.a_extracters = [
        AudioExtracter('eac3to', [self.file.path.to_str(), '3:', self.file.a_src.set_track(1).to_str(), '-log=NUL'], self.file)
        ]
        self.a_cutters = [EztrimCutter(self.file, track=1)]
        self.a_encoders = [QAACEncoder(self.file, track=1, xml_tag=self.xml_tag)]


    def run(self) -> None:
        assert self.file.a_src_cut

        muxer = Mux(
            self.file,
            streams=(
                VideoStream(self.file.name_clip_output, '', JAPANESE),
                [AudioStream(self.file.a_enc_cut.set_track(1), '', JAPANESE)],
                None
            )
        )
        # muxer = Mux(self.file)

        config = RunnerConfig(
            self.v_encoder, None,
            self.a_extracters, self.a_cutters, self.a_encoders,
            muxer
        )

        self.runner = SelfRunner(self.clip, self.file, config)
        self.runner.run()

    def do_patch(self, ranges: Union[Range, List[Range]]) -> None:
        p = Patch(self.v_encoder, self.clip, self.file, ranges)
        p.run()
        p.do_cleanup()

    def cleanup(self) -> None:
        files: List[Any] = [self.xml_tag]
        self.runner.do_cleanup()