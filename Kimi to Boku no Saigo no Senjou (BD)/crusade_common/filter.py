from __future__ import annotations

from typing import List, NamedTuple, Tuple

import vapoursynth as vs


from vardefunc import Graigasm, Grainer, get_chroma_shift
from vardefunc.noise import AddGrain
from vsmask.edge import FDoGTCanny, ExLaplacian4, MinMax, SobelStd
from vsutil import depth, iterate, join

core = vs.core


graigasm_args = dict(
    thrs=[x << 8 for x in (32, 80, 128, 176)],
    strengths=[(0.3, 0.12), (0.2, 0.08), (0.10, 0.0), (0.0, 0.0)],
    sizes=(1.2, 1.1, 1.0, 1.0),
    sharps=(60, 55, 50, 40),
    grainers=[
        AddGrain(seed=333, constant=False),
        AddGrain(seed=333, constant=False),
        AddGrain(seed=333, constant=True)
    ]
)



class Thr(NamedTuple):
    lo: float
    hi: float


class Mask:
    class ExLaplaDOG(ExLaplacian4):
        def __init__(self, *, ret: bool = False) -> None:
            self.ret = ret
            super().__init__()

        def _compute_mask(self, clip: vs.VideoNode) -> vs.VideoNode:
            assert clip.format
            if self.ret:
                pre = depth(clip, 16).retinex.MSRCP(sigma=[25, 150, 280], upper_thr=9e-4)
                pre = pre.resize.Point(format=clip.format.id)
            else:
                pre = clip

            exlaplacian4 = super()._compute_edge_mask(pre)
            fdog = FDoGTCanny().edgemask(pre)

            mask = core.std.Expr((exlaplacian4, fdog), 'x y max')
            mask = mask.std.Crop(right=2).resize.Point(mask.width, src_width=mask.width)

            return mask

    def lineart_deband_mask(self, clip: vs.VideoNode,
                            brz_rg: float, brz_ed: float, brz_ed_ret: float,
                            ret_thrs: Thr, extra: bool = True) -> vs.VideoNode:
        range_mask = MinMax(6, 0).edgemask(clip).std.Binarize(brz_rg)
        # edgemask = self.ExLaplaDOG().edgemask(clip).std.Binarize(brz_ed)
        edgemask = SobelStd().edgemask(clip).std.Binarize(brz_ed)
        edgemaskret = self.ExLaplaDOG(ret=True).edgemask(clip).std.Binarize(brz_ed_ret)

        # Keep retinex edgemask only under th_lo
        th_lo, th_hi = ret_thrs
        strength = f'{th_hi} x - {th_hi} {th_lo} - /'
        edgemask = core.std.Expr(
            [clip.std.BoxBlur(0, 3, 3, 3, 3), edgemask, edgemaskret],
            f'x {th_lo} > x {th_hi} < and z ' + strength + ' * y 1 ' + strength + f' - * + x {th_lo} <= z y ? ?'
        )

        lmask = core.std.Expr((range_mask, edgemask), 'x y max')

        if extra:
            lmask = lmask.rgsf.RemoveGrain(22).rgsf.RemoveGrain(11)
            lmask = iterate(lmask, core.std.Inflate, 4)

        return lmask


# def chroma_recon(y: vs.VideoNode, u: vs.VideoNode, v: vs.VideoNode, radius: int) -> vs.VideoNode:
#     from regress import ReconstructMulti, Regress
#     y_m = y.resize.Bicubic(960, 540, src_left=-0.5, filter_param_a=1/3, filter_param_b=1/3)
#     y_m, u, v = [c.resize.Bicubic(1920, 1080, src_left=get_chroma_shift(540, 1080)) for c in [y_m, u, v]]

#     y_fixup = core.std.MakeDiff(y, y_m)
#     yu, yv = Regress(y_m, u, v, radius=radius, eps=1e-7)

#     u_fixup = ReconstructMulti(y_fixup, yu, radius=radius)
#     u_r = core.std.MergeDiff(u, u_fixup)

#     v_fixup = ReconstructMulti(y_fixup, yv, radius=radius)
#     v_r = core.std.MergeDiff(v, v_fixup)

#     return join([y.std.BlankClip(), u_r, v_r])


class GraigasmMore(Graigasm):
    enchance_grain = 1.6
    avgf = 3
    avgp = 0.2

    def _make_grained(self, clip: vs.VideoNode, strength: Tuple[float, float], size: float, sharp: float,
                      grainer: Grainer, neutral: List[float], mod: int) -> vs.VideoNode:
        ss_w = self._m__(round(clip.width / size), mod)
        ss_h = self._m__(round(clip.height / size), mod)
        b = sharp / -50 + 1
        c = (1 - b) / 2

        blank = core.std.BlankClip(clip, ss_w, ss_h, color=neutral)

        grained = grainer.grain(blank, strength=strength)
        enhanced = core.std.Expr(grained, [f'x {neutral[0]} - {self.enchance_grain} * {neutral[0]} +',
                                           f'x {neutral[1]} - {self.enchance_grain} * {neutral[1]} +'])
        resize = core.resize.Bicubic(enhanced, clip.width, clip.height, filter_param_a=b, filter_param_b=c)

        # avg = core.std.AverageFrames(resize, [1] * self.avgf, self.avgf, scenechange=True)
        # avg = core.std.Merge(resize, avg, self.avgp)

        return clip.std.MakeDiff(resize)


