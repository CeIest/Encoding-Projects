from typing import List, Tuple, cast

import EoEfunc as eoe
import lvsfunc as lvf
import vapoursynth as vs
import vardefunc as vdf
from vardautomation import FileInfo, PresetEAC3, PresetWEB, VPath
from vardefunc.mask import FDOG, MinMax, SobelStd
from vsutil import depth, get_y, split

from tantei_common import Encoding, dehardsub, upscaled_sraa

core = vs.core


# 03
replace_scenes: List[Tuple[int, int]] = [(1008, 3287), (14259, 14491), (28551, 28669), (31769, 34046), ]


# WAKANIM dehardsubbed with Funimation, audio trimmed and taken from Amazon
WEB_FU = FileInfo("Episodes/Funimation/[SubsPlease] Tantei wa Mou, Shindeiru. - 03 (1080p) [A7518BB0].mkv", 240, None, preset=[PresetWEB, PresetEAC3])
WEB_WK = FileInfo("Episodes/Wakanim/The Detective Is Already Dead E03 [1080p][E-AC3][JapDub][GerSub][Web-DL].mkv", preset=[PresetWEB, PresetEAC3])
WEB_BL = FileInfo("Episodes/B-Global/[NC-Raws] 侦探已死 - 03 [B-Global][WEB-DL][1080p][AVC AAC][CHS_CHT_ENG_TH_SRT][MKV].mkv", 1, None, preset=[PresetWEB, PresetEAC3])
WEB_AMZ = FileInfo('Episodes/Amazon/Tantei wa Mou, Shindeiru. - 03 (Amazon dAnime CBR 720p).mkv', None, -1, preset=[PresetWEB, PresetEAC3])
WEB_AMZ.name_clip_output = VPath(WEB_AMZ.name + '.265')


def main() -> vs.VideoNode:
    src_fu = WEB_FU.clip_cut
    src_wk = WEB_WK.clip_cut
    src_bl = WEB_BL.clip_cut

    src_bl = src_bl[:8638] + src_bl[8638] * 2 + src_bl[8639:] #B-Global's video starts 1 frame early but has one frame less than the other sources at 8638
    src_fu, src_wk, src_bl = [depth(x, 16) for x in [src_fu, src_wk, src_bl]]


    dehardsubed = dehardsub(src_wk, src_fu, replace_scenes)


# Denoise
    denoise = eoe.denoise.BM3D(dehardsubed, 1, radius=1)
    denoise = cast(vs.VideoNode, denoise)


# Anti-aliasing
    luma = get_y(denoise)
    lineart = SobelStd().get_mask(luma).std.Maximum().std.Binarize(75 << 8).std.Convolution([1]*9)

    aaa_a = upscaled_sraa(luma, 2160, 3, alpha=0.4, beta=0.5, gamma=40, nrad=3, mdis=20)
    aaa_a = core.std.Expr((aaa_a, luma), 'x y min')

    aa = core.std.MaskedMerge(luma, aaa_a, lineart)
    aa = vdf.misc.merge_chroma(aa, denoise)


# Debanding
    range_mask = MinMax(3, 2).get_mask(aa, 2500, 2500)
    lineart = FDOG().get_mask(aa, 3000, 3000).rgvs.RemoveGrain(3).std.Maximum()
    range_mask, lineart = [core.resize.Bilinear(c, format=vs.YUV444P16) for c in [range_mask, lineart]]
    detail_mask = core.std.Expr((split(range_mask) + split(lineart)), 'x y z a b c max max max max max')
    detail_mask = detail_mask.std.BoxBlur(0, 2, 2, 2, 2)

    deband = vdf.deband.dumb3kdb(aa, 16, threshold=[36, 48], grain=16)
    deband = core.std.MaskedMerge(deband, aa, detail_mask)


# Graining
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
    grain = vdf.noise.Graigasm(**graigasm_args).graining(deband)  # type: ignore
    final = depth(grain, 10)


    # scomp = lvf.comparison.stack_compare(src_fu, src_bl, make_diff=True, warn=True)
    # diff = lvf.comparison.diff(src_fu, src_bl)

    return final


if __name__ == '__main__':
    filtered = main()
    brrrr = Encoding(WEB_AMZ, filtered)
  # brrrr.do_patch([(x, x)]) # For patching
    brrrr.run()
    brrrr.cleanup()
else:
    WEB_FU.clip_cut.set_output(0)
    WEB_WK.clip_cut.set_output(1)
    # WEB_BL.clip_cut.set_output(2)
    # WEB_AMZ.clip_cut.set_output(3)
    filtered = main()
    if not isinstance(filtered, vs.VideoNode):
        for i, clip_filtered in enumerate(filtered):
            clip_filtered.set_output(i+4)
    else:
        filtered.set_output(10)


# main().set_output(0)


# main()[0].set_output(3)
# main()[1].set_output(4)
