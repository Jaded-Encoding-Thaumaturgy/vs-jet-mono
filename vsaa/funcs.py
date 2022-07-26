import vapoursynth as vs
from vsexprtools.util import PlanesT, norm_expr_planes, normalise_planes
from vskernels import Catrom, Kernel, Spline144
from vsmask.edge import EdgeDetect, ScharrTCanny
from vsrgtools import RepairMode, box_blur, contrasharpening_median, median_clips, repair
from vsutil import get_depth, get_peak_value, get_w, join, scale_value, split

from .abstract import SingleRater, SuperSampler
from .antialiasers import Eedi3SR, Nnedi3SR, Nnedi3SS
from .enums import AADirection

core = vs.core


def upscaled_sraa(
    clip: vs.VideoNode, rfactor: float = 1.5,
    width: int | None = None, height: int | None = None,
    ssfunc: SuperSampler = Nnedi3SS(), aafunc: SingleRater = Eedi3SR(),
    direction: AADirection = AADirection.BOTH,
    downscaler: Kernel = Catrom()
) -> vs.VideoNode:
    """
    :param clip:            Clip to process, only luma will be processed.
    :param rfactor:         Image enlargement factor.
                            It is not recommended to go below 1.3
    :param width:           Target resolution width. If None, determined from `height`.
    :param height:          Target resolution height.
    :param ssfunc:          Super-sampler used for upscaling before AA.
    :param aafunc:          Downscaler to use after super-sampling.
    :param aafun:           Function used to antialias after super-sampling.

    :return:                Antialiased clip.

    :raises ValueError:     ``rfactor`` is not above 1.
    """
    assert clip.format

    work_clip, *chroma = split(clip)

    if rfactor <= 1:
        raise ValueError('upscaled_sraa: rfactor must be above 1!')

    ssw = (round(work_clip.width * rfactor) + 1) & ~1
    ssh = (round(work_clip.height * rfactor) + 1) & ~1

    if height is None:
        height = work_clip.height

    if width is None:
        if height == work_clip.height:
            width = work_clip.width
        else:
            width = get_w(height, aspect_ratio=clip.width / clip.height)

    up_y = ssfunc.scale(work_clip, ssw, ssh)

    aa_y = aafunc.aa(up_y, *direction.to_yx())

    if downscaler:
        aa_y = downscaler.scale(aa_y, width, height)
    elif not chroma or (clip.width, clip.height) != (width, height):
        return aa_y

    return join([aa_y, *chroma], clip.format.color_family)


def transpose_aa(clip: vs.VideoNode, aafunc: SingleRater) -> vs.VideoNode:
    """
    Perform transposed AA.

    :param clip:        Clip to process.
    :param aafun:       Antialiasing function.
    :return:            Antialiased clip.
    """
    assert clip.format

    work_clip, *chroma = split(clip)

    aafunc.transpose_first = True
    aafunc.drop_fields = False

    aa_y = aafunc.aa(work_clip, AADirection.BOTH)

    if not chroma:
        return aa_y

    return join([aa_y, *chroma], clip.format.color_family)


def clamp_aa(
    src: vs.VideoNode, weak: vs.VideoNode, strong: vs.VideoNode,
    strength: float = 1, planes: PlanesT = 0
) -> vs.VideoNode:
    """
    Clamp stronger AAs to weaker AAs.
    Useful for clamping :py:func:`upscaled_sraa` or :py:func:`Eedi3SR`
    to :py:func:`Nnedi3SR` for a strong but more precise AA.

    :param src:         Non-AA'd source clip.
    :param weak:        Weakly-AA'd clip.
    :param strong:      Strongly-AA'd clip.
    :param strength:    Clamping strength.
    :param planes:      Planes to process.

    :return:            Clip with clamped anti-aliasing.
    """
    assert src.format

    planes = normalise_planes(src, planes)

    if src.format.sample_type == vs.INTEGER:
        thr = strength * get_peak_value(src)
    else:
        thr = strength / 219

    if thr == 0:
        return median_clips([src, weak, strong], planes)

    expr = f'x y - XYD! XYD@ x z - XZD! XZD@ xor x XYD@ abs XZD@ abs < z y {thr} + min y {thr} - max z ? ?'

    return core.akarin.Expr([src, weak, strong], norm_expr_planes(src, expr, planes))


def masked_clamp_aa(
    clip: vs.VideoNode, strength: float = 1,
    mthr: float = 0.25, mask: vs.VideoNode | EdgeDetect | None = None,
    weak_aa: SingleRater | None = None, strong_aa: SingleRater | None = None,
    opencl: bool | None = True
) -> vs.VideoNode:
    """
    Clamp a strong aa to a weaker one for the purpose of reducing the stronger's artifacts.

    :param clip:                Clip to process.
    :param strength:            Set threshold strength for over/underflow value for clamping.
    :param mthr:                Binarize threshold for the mask, float.
    :param mask:                Clip to use for custom mask or an EdgeDetect to use custom masker.
    :param weak_aa:             SingleRater for the weaker aa.
    :param strong_aa:           SingleRater for the stronger aa.
    :param opencl:              Wheter to force OpenCL acceleration, None to leave as is.

    :return:                    Antialiased clip.
    """
    assert clip.format

    work_clip, *chroma = split(clip)

    if mask is None:
        mask = ScharrTCanny()

    if isinstance(mask, EdgeDetect):
        bin_thr = scale_value(mthr, 32, get_depth(clip))

        mask = mask.edgemask(work_clip)
        mask = mask.std.Binarize(bin_thr)
        mask = mask.std.Maximum()
        mask = box_blur(mask)
        mask = mask.std.Minimum().std.Deflate()

    if weak_aa is None:
        weak_aa = Nnedi3SR(
            opencl=hasattr(core, 'nnedi3cl') if opencl is None else opencl
        )
    elif opencl is not None and hasattr(weak_aa, 'opencl'):
        weak_aa.opencl = opencl  # type: ignore

    if strong_aa is None:
        strong_aa = Eedi3SR(opencl=opencl is None or opencl)
    elif opencl is not None and hasattr(strong_aa, 'opencl'):
        strong_aa.opencl = opencl  # type: ignore

    weak = transpose_aa(work_clip, weak_aa)
    strong = transpose_aa(work_clip, strong_aa)

    clamped = clamp_aa(work_clip, weak, strong, strength)

    merged = work_clip.std.MaskedMerge(clamped, mask)

    if not chroma:
        return merged

    return join([merged, *chroma], clip.format.color_family)


def fine_aa(
    clip: vs.VideoNode, taa: bool = False,
    singlerater: SingleRater = Eedi3SR(),
    rep: int | RepairMode = RepairMode.LINE_CLIP_STRONG
) -> vs.VideoNode:
    """
    Taa and optionally repair clip that results in overall lighter anti-aliasing, downscaled with Spline kernel.

    :param clip:            Clip to process.
    :param singlerater:     Singlerater used for aa.
    :param rep:             Repair mode.

    :return:                Antialiased clip.
    """
    assert clip.format

    singlerater.shifter = Spline144()

    work_clip, *chroma = split(clip)

    if taa:
        aa = transpose_aa(work_clip, singlerater)
    else:
        aa = singlerater.aa(work_clip, AADirection.BOTH)

    contra = contrasharpening_median(work_clip, aa)

    repaired = repair(contra, work_clip, rep)

    if not chroma:
        return repaired

    return join([repaired, *chroma], clip.format.color_family)
