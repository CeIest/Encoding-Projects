from __future__ import annotations

from functools import partial
from typing import Any, Literal, NamedTuple, Protocol

import vapoursynth as vs
from vskernels import Kernel, Catrom
from vsutil import depth, get_depth

core = vs.core


class VSFunction(Protocol):
    def __call__(self, clip: vs.VideoNode, *args: Any, **kwargs: Any) -> vs.VideoNode:
        ...


CURVES = Literal[
    vs.TransferCharacteristics.TRANSFER_IEC_61966_2_1,
    vs.TransferCharacteristics.TRANSFER_BT709,
    vs.TransferCharacteristics.TRANSFER_BT601,
    vs.TransferCharacteristics.TRANSFER_ST240_M,
    vs.TransferCharacteristics.TRANSFER_BT2020_10,
    vs.TransferCharacteristics.TRANSFER_BT2020_12,
]


def ssim_downsample(
    clip: vs.VideoNode, width: int, height: int, smooth: int | float | VSFunction,
    kernel: Kernel = Catrom(), gamma: bool = False, curve: CURVES = vs.TransferCharacteristics.TRANSFER_BT709,
    sigmoid: bool = False, epsilon: float = 1e-6
) -> vs.VideoNode:
    if isinstance(smooth, int):
        filter_func = partial(core.std.BoxBlur, hradius=smooth, vradius=smooth)
    elif isinstance(smooth, float):
        filter_func = partial(core.tcanny.TCanny, sigma=smooth, mode=-1)
    else:
        filter_func = smooth

    clip = depth(clip, 32)

    if gamma:
        clip = gamma2linear(clip, curve, sigmoid=sigmoid, epsilon=epsilon)

    l = kernel.scale(clip, width, height)
    l2 = kernel.scale(clip.std.Expr('x dup *'), width, height)

    m = filter_func(l)

    sl_plus_m_square = filter_func(l.std.Expr('x dup *'))
    sh_plus_m_square = filter_func(l2)
    m_square = m.std.Expr('x dup *')
    r = core.std.Expr([sl_plus_m_square, sh_plus_m_square, m_square], f'x z - {epsilon} < 0 y z - x z - / sqrt ?')
    t = filter_func(core.std.Expr([r, m], 'x y *'))
    m = filter_func(m)
    r = filter_func(r)
    d = core.std.Expr([m, r, l, t], 'x y z * + a -')

    if gamma:
        d = linear2gamma(d, curve, sigmoid=sigmoid)

    return d


class Coefs(NamedTuple):
    k0: float
    phi: float
    alpha: float
    gamma: float


def get_coefs(curve: vs.TransferCharacteristics) -> Coefs:
    srgb = Coefs(0.04045, 12.92, 0.055, 2.4)
    bt709 = Coefs(0.08145, 4.5, 0.0993, 2.22222)
    smpte240m = Coefs(0.0912, 4.0, 0.1115, 2.22222)
    bt2020 = Coefs(0.08145, 4.5, 0.0993, 2.22222)

    gamma_linear_map = {
        vs.TransferCharacteristics.TRANSFER_IEC_61966_2_1: srgb,
        vs.TransferCharacteristics.TRANSFER_BT709: bt709,
        vs.TransferCharacteristics.TRANSFER_BT601: bt709,
        vs.TransferCharacteristics.TRANSFER_ST240_M: smpte240m,
        vs.TransferCharacteristics.TRANSFER_BT2020_10: bt2020,
        vs.TransferCharacteristics.TRANSFER_BT2020_12: bt2020
    }

    return gamma_linear_map[curve]



def gamma2linear(
    clip: vs.VideoNode, curve: CURVES, gcor: float = 1.0,
    sigmoid: bool = False, thr: float = 0.5, cont: float = 6.5,
    epsilon: float = 1e-6
) -> vs.VideoNode:
    assert clip.format
    if get_depth(clip) != 32 and clip.format.sample_type != vs.FLOAT:
        raise ValueError('Only 32 bits float is allowed')

    c = get_coefs(curve)

    expr = f'x {c.k0} <= x {c.phi} / x {c.alpha} + 1 {c.alpha} + / {c.gamma} pow ? {gcor} pow'
    if sigmoid:
        x0 = f'1 1 {cont} {thr} * exp + /'
        x1 = f'1 1 {cont} {thr} 1 - * exp + /'
        expr = f'{thr} 1 {expr} {x1} {x0} - * {x0} + {epsilon} max / 1 - {epsilon} max log {cont} / -'

    expr = f'{expr} 0.0 max 1.0 min'

    return core.std.Expr(clip, expr).std.SetFrameProps(_Transfer=8)


def linear2gamma(
    clip: vs.VideoNode, curve: CURVES, gcor: float = 1.0,
    sigmoid: bool = False, thr: float = 0.5, cont: float = 6.5,
) -> vs.VideoNode:
    assert clip.format
    if get_depth(clip) != 32 and clip.format.sample_type != vs.FLOAT:
        raise ValueError('Only 32 bits float is allowed')

    c = get_coefs(curve)

    expr = 'x'
    if sigmoid:
        x0 = f'1 1 {cont} {thr} * exp + /'
        x1 = f'1 1 {cont} {thr} 1 - * exp + /'
        expr = f'1 1 {cont} {thr} {expr} - * exp + / {x0} - {x1} {x0} - /'

    expr += f' {gcor} pow'
    expr = f'{expr} {c.k0} {c.phi} / <= {expr} {c.phi} * {expr} 1 {c.gamma} / pow {c.alpha} 1 + * {c.alpha} - ?'
    expr = f'{expr} 0.0 max 1.0 min'

    return core.std.Expr(clip, expr).std.SetFrameProps(_Transfer=curve)
