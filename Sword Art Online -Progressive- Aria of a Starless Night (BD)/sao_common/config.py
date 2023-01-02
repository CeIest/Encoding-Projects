from __future__ import annotations

import inspect
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, ParamSpec, Type, TypeVar

from vapoursynth import VideoNode, core
from vardautomation import (
    FRENCH, JAPANESE, X264, X265, BlurayShow, Chapter, ChaptersTrack, Eac3toAudioExtracter,
    FileInfo, MatroskaFile, MatroskaXMLChapters, MediaTrack, NVEncCLossless, Patch, PresetAAC,
    PresetBD, PresetChapXML, QAACEncoder, RunnerConfig, SelfRunner, SoxCutter, VPath, make_qpfile
)
from vardefunc.types import Range


class Encoding:
    # v_encoder = X265('selection_common/x265_settings')

    def __init__(self, file: FileInfo, clip: VideoNode) -> None:
        self.file = file
        self.clip = clip

    def run(self, add_chapter: bool = True, override_params: Optional[Dict[str, Any]] = None) -> None:
        assert self.file.a_enc_cut
        assert self.file.chapter

        # v_encoder = X265('boogiepop_common/x265_settings', override_params=override_params)
        v_encoder = X264('boogiepop_common/x264_settings')
        # v_encoder.params.extend(['--qpfile', r'G:\Encodages\Boogipop\boogie_04_qpfile.log'])
        v_encoder.resumable = True
        a_extracter = Eac3toAudioExtracter(self.file, track_in=2, track_out=1, eac3to_args=['-log=nul'])
        a_cutter = SoxCutter(self.file, track=1)
        a_encoder = QAACEncoder(self.file, track=1)

        mkv = MatroskaFile(
            self.file.name_file_final,
            [MediaTrack(self.file.name_clip_output, 'AVC BDRip by Vardë@Raws-Maji', JAPANESE),
             MediaTrack(self.file.a_enc_cut.set_track(1), 'AAC 2.0', JAPANESE),
             ChaptersTrack(self.file.chapter, FRENCH)],
            '--ui-language', 'en'
        )

        config = RunnerConfig(
            v_encoder,
            # NVEncCLossless(),
            None,
            a_extracter, a_cutter, a_encoder,
            mkv,
            order=RunnerConfig.Order.AUDIO
        )

        runner = SelfRunner(self.clip, self.file, config)
        runner.inject_qpfile_params(qpfile_clip=self.file.clip_cut)
        runner.run()
        runner.work_files.discard(self.file.name_clip_output)
        runner.work_files.discard(self.file.chapter)
        runner.work_files.clear()

    def do_patch(self, ranges: Range | List[Range]) -> None:
        p = Patch(X264('boogiepop_common/x264_settings'), self.clip, self.file, ranges)
        p.run()
        p.do_cleanup()
