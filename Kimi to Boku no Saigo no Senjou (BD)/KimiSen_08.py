import vapoursynth as vs
from vardautomation import FileInfo, PresetAAC, PresetBD, VPath
core = vs.core

from crusade_common import Encoding, GraigasmMore, Mask, Thr, graigasm_args

#1 = Episodes 01, 02, 03, 04
#2 = Episodes 05, 06, 07, 08
#3 = Episodes 09, 10, 11, 12
vol = "2"


BDMV_PATH = VPath("H:/Projects/Crusade/[BDMV] Our Last Crusade or the Rise of a New World/KIMISEN_" + vol + "\BDMV\STREAM")
#16 = 5, 17 = 6, 18 = 7, 19 = 8
JPBD = FileInfo(BDMV_PATH / r'00019.m2ts', (None, -24), preset=[PresetBD, PresetAAC])


def main() -> vs.VideoNode:
    from vsutil import depth, get_y, split, get_w
    from adptvgrnMod import adptvgrnMod
    import havsfunc as hvf
    import lvsfunc as lvf
    import vardefunc as vdf
    from debandshit import dumb3kdb
    from vardefunc import DebugOutput, Eedi3SR, YUVPlanes, finalise_output, initialise_input, remap_rfs, upscaled_sraa
    from vsdenoise import BM3DCuda
    from muvsfunc import SSIM_downsample
    from vskernels import kernels, Catrom
    import vapoursynth as vs

    src = JPBD.clip_cut
    src = depth(src, 16)
    out = src


    src_y = depth(get_y(src), 32)
    descale = kernels.Catrom().descale(src_y, get_w(810), 810)
    double = vdf.scale.nnedi3cl_double(descale, pscrn=1)
    rescale = depth(SSIM_downsample(double, 1920, 1080), 16)

    scaled = vdf.misc.merge_chroma(rescale, src)
    out = scaled

    with YUVPlanes(out, 16) as c:
        out = c.Y

        denoise = BM3DCuda(out, sigma=[0.55, 0.35]).clip
        c.Y = denoise
    out = c.clip

    ### DEBAND ###
    deband_mask = Mask().lineart_deband_mask(
        out.resize.Bilinear(format=vs.YUV444PS).rgsf.RemoveGrain(3),
        brz_rg=2000/65536, brz_ed=1000/65536, brz_ed_ret=10000/65536,
        ret_thrs=Thr(lo=(16 - 16) / 219, hi=(30 - 16) / 219)
    )
    deband_mask = core.std.Expr(
        split(deband_mask) + [get_y(out)],
        f'a {(18 - 16) / 219} > x y z max max 0 ?'
    ).rgsf.RemoveGrain(3).rgsf.RemoveGrain(22).rgsf.RemoveGrain(11)

    deband = dumb3kdb(out, threshold=[32, 28, 20], grain=2)
    deband = core.std.MaskedMerge(deband, out, deband_mask.resize.Point(format=vs.GRAY16))
    out = deband

    ### GRAINING ###
    grain: vs.VideoNode = adptvgrnMod(deband, seed=42069, strength=0.25, luma_scaling=12,
                                      size=1.15, sharp=60, static=False)
    out = grain

    final = depth(out, 10)
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