import vapoursynth as vs

from vsutil import depth
from jvsfunc import ccdmod
from vsdenoise import BM3DCuda
from vsutil import get_y, split
from debandshit import dumb3kdb

from sao_common.finedehalo import fine_dehalo
from sao_common import GraigasmMore, Mask, Thr, graigasm_args, lehmer_merge

from vardautomation import (
    JAPANESE, X265, FileInfo,
    PresetAAC, PresetBDWAV64, get_vs_core
)
from vardefunc import (DebugOutput, Eedi3SR, YUVPlanes, 
    finalise_output, initialise_input, remap_rfs, upscaled_sraa
)

core = get_vs_core()



JPBD = FileInfo('H:/Sword Art Online BDMV/Anime/JP/劇場版 ソードアート・オンライン -プログレッシブ- 星なき夜のアリア/ANZX-14040/BDMV/STREAM/00002.m2ts', preset=[PresetBDWAV64, PresetAAC])
ITBD = FileInfo('G:/New folder/00007.m2ts', preset=[PresetBDWAV64, PresetAAC])



DEBUG = DebugOutput(
    JPBD.clip_cut,
    props=0
)


@DEBUG.catch(op='@=')
@finalise_output(bits=10)
@initialise_input(bits=16)
def filtering(src: vs.VideoNode = JPBD.clip_cut) -> vs.VideoNode:
    global DEBUG
    it_bd = ITBD.clip_cut
    it_bd = depth(it_bd, 16)


    merge = lehmer_merge([it_bd, src])
    out = merge
    

    with YUVPlanes(out, 16) as c:
        out = c.Y

        denoise = BM3DCuda(out, 1.25, 1).clip
        out = denoise

        unwarp = core.warp.AWarpSharp2(out, depth=-1)
        dehalo = fine_dehalo(unwarp, None, 1.4, None, 0)

        aaa = upscaled_sraa(dehalo, 2, singlerater=Eedi3SR(True, True, 0.2, 0.55, gamma=200, mdis=15))
        aaa = remap_rfs(aaa, denoise, [(133925, None)])
        c.Y = aaa
    out = c.clip

    
    denoise = ccdmod(out, 3.5, 1)
    out = denoise

    
    deband_mask = Mask().lineart_deband_mask(
        out.resize.Bilinear(format=vs.YUV444PS).rgsf.RemoveGrain(3),
        brz_rg=2000/65536, brz_ed=1000/65536, brz_ed_ret=10000/65536,
        ret_thrs=Thr(lo=(16 - 16) / 219, hi=(30 - 16) / 219)
    )
    deband_mask = core.std.Expr(
        split(deband_mask) + [get_y(out)],
        f'a {(18 - 16) / 219} > x y z max max 0 ?'
    ).rgsf.RemoveGrain(3).rgsf.RemoveGrain(22).rgsf.RemoveGrain(11)

    deband = dumb3kdb(out, 31, 30, 24)
    deband = remap_rfs(deband, out, [(41262, 41357), (41690, 41845)]) #inc exc
    deband = core.std.MaskedMerge(deband, out, deband_mask.resize.Point(format=vs.GRAY16))
    out = deband

    
    grain = GraigasmMore(**graigasm_args).graining(out)  # type: ignore
    out = grain


    return out




if __name__ == '__main__':
    clip = filtering()
    v_enc = X265('sao_common/x265_settings')
    v_enc.resumable = True
    v_enc.run_enc(clip, JPBD)
else:
    filtering()
    pass
