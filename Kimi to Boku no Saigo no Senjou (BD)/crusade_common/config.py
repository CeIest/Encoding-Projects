from typing import List, Union, Any

import vapoursynth as vs
from vardautomation import (JAPANESE, ENGLISH, EztrimCutter, AudioTrack, QAACEncoder,
                            FileInfo, Patch, RunnerConfig, SelfRunner, MatroskaFile, MediaTrack, Eac3toAudioExtracter,
                            VideoTrack, X265, ChaptersTrack)
from vardautomation.tooling import AudioExtracter, mux
from vardefunc.types import Range

core = vs.core


class Encoding:
    runner: SelfRunner
    xml_tag: str = 'xml_tag.xml'


    def __init__(self, file: FileInfo, clip: vs.VideoNode) -> None:
        self.file = file
        self.clip = clip
        assert self.file.a_src

        self.v_encoder = X265('crusade_common/x265_settings')
        self.a_extracters = Eac3toAudioExtracter(self.file, track_in=2, track_out=1, eac3to_args=['-log=NUL'])
        self.a_cutters = [EztrimCutter(self.file, track=1)]
        self.a_encoders = [QAACEncoder(self.file, track=1, xml_tag=self.xml_tag)]


    def run(self) -> None:
        assert self.file.a_src_cut

        tracks = [
            VideoTrack(self.file.name_clip_output, 'Encode by your fav Pasta', JAPANESE),
            AudioTrack(self.file.a_enc_cut.set_track(1), 'AAC 2.0', JAPANESE),
        ]
        mkv = MatroskaFile(self.file.name_file_final, tracks, '--ui-language', 'en')

        config = RunnerConfig(
            self.v_encoder, None,
            self.a_extracters, self.a_cutters, self.a_encoders,
            mkv
        )

        self.runner = SelfRunner(self.clip, self.file, config)
        self.runner.run()

    def do_patch(self, ranges: Union[Range, List[Range]]) -> None:
        p = Patch(self.v_encoder, self.clip, self.file, ranges)
        p.run()
        p.do_cleanup()

    def cleanup(self) -> None:
        files: List[Any] = [self.xml_tag]
        self.runner.work_files.clear()