from __future__ import annotations
import warnings

from typing import cast

from vsexprtools import norm_expr
from vstools import PlanesT, check_variable, core, normalize_seq, pick_func_stype, vs, KwargsNotNone

from .aka_expr import removegrain_aka_exprs, repair_aka_exprs
from .enum import (
    RemoveGrainMode, RemoveGrainModeT, RepairModeT, VerticalCleanerMode, VerticalCleanerModeT, ClenseMode, ClenseModeT
)

__all__ = [
    'repair', 'removegrain',
    'clense', 'verticalcleaner'
]


def repair(clip: vs.VideoNode, repairclip: vs.VideoNode, mode: RepairModeT) -> vs.VideoNode:
    assert check_variable(clip, repair)
    assert check_variable(repairclip, repair)

    mode = normalize_seq(mode, clip.format.num_planes)

    if not sum(mode):
        return clip
    
    if clip.format.sample_type == vs.INTEGER and all(m in range(24 + 1) for m in mode):
        return core.rgvs.Repair(clip, repairclip, mode)

    return norm_expr([clip, repairclip], tuple([repair_aka_exprs[m]() for m in mode]))


def removegrain(clip: vs.VideoNode, mode: RemoveGrainModeT) -> vs.VideoNode:
    assert check_variable(clip, removegrain)

    mode = normalize_seq(mode, clip.format.num_planes)

    for m in mode:
        if m in (
            RemoveGrainMode.MINMAX_MEDIAN, RemoveGrainMode.BINOMIAL_BLUR,
            RemoveGrainMode.BOX_BLUR_NO_CENTER, RemoveGrainMode.BOX_BLUR
        ):
            warnings.warn(
                f'Deprecated removegrain mode {m}! '
                f'Use {'median_blur' if m == RemoveGrainMode.MINMAX_MEDIAN else 'BlurMatrix'} instead!',
                DeprecationWarning
            )

    if not sum(mode):
        return clip

    if all(m in range(24 + 1) for m in mode):
        return clip.zsmooth.RemoveGrain(mode)

    return norm_expr(clip, tuple([removegrain_aka_exprs[m]() for m in mode]))


def clense(
    clip: vs.VideoNode, previous_clip: vs.VideoNode | None = None, next_clip: vs.VideoNode | None = None,
    mode: ClenseModeT = ClenseMode.NONE, planes: PlanesT = None
) -> vs.VideoNode:
    warnings.warn('clense is deprecated! Use MeanMode instead!', DeprecationWarning)
    
    kwargs = KwargsNotNone(previous=previous_clip, next=next_clip)

    if mode == ClenseMode.NONE:
        return clip

    return cast(
        vs.VideoNode,
        pick_func_stype(clip, getattr(core.lazy.rgvs, mode), getattr(core.lazy.rgsf, mode))(
            clip, planes=planes, **kwargs
        ),
    )


def verticalcleaner(clip: vs.VideoNode, mode: VerticalCleanerModeT) -> vs.VideoNode:
    assert check_variable(clip, verticalcleaner)

    mode = normalize_seq(mode, clip.format.num_planes)

    if not sum(mode):
        return clip
    
    for m in mode:
        if m == VerticalCleanerMode.MEDIAN:
            warnings.warn(f'Deprecated verticalcleaner mode {m}! Use median_blur instead!', DeprecationWarning)

    return pick_func_stype(clip, core.lazy.rgvs.VerticalCleaner, core.lazy.rgsf.VerticalCleaner)(clip, mode)
