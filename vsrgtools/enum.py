from __future__ import annotations

import operator

from enum import auto
from itertools import accumulate
from math import ceil, exp, log2, pi, sqrt
from typing import Any, Iterable, Literal, Self, Sequence, overload

from vsexprtools import ExprList, ExprOp, ExprToken, ExprVars
from vstools import (
    ConvMode, CustomIntEnum, CustomStrEnum, CustomValueError, KwargsT, Nb, PlanesT, check_variable, core, fallback,
    iterate, shift_clip_multi, to_singleton, vs
)

__all__ = [
    'LimitFilterMode',
    'RemoveGrainMode', 'RemoveGrainModeT',
    'RepairMode', 'RepairModeT',
    'VerticalCleanerMode', 'VerticalCleanerModeT',
    'ClenseMode', 'ClenseModeT',
    'BlurMatrixBase', 'BlurMatrix', 'BilateralBackend'
]


class LimitFilterModeMeta:
    force_expr = True


class LimitFilterMode(LimitFilterModeMeta, CustomIntEnum):
    """Two sources, one filtered"""
    SIMPLE_MIN = auto()
    SIMPLE_MAX = auto()
    """One source, two filtered"""
    SIMPLE2_MIN = auto()
    SIMPLE2_MAX = auto()
    DIFF_MIN = auto()
    DIFF_MAX = auto()
    """One/Two sources, one filtered"""
    CLAMPING = auto()

    @property
    def op(self) -> str:
        return '<' if 'MIN' in self._name_ else '>'

    def __call__(self, force_expr: bool = True) -> LimitFilterMode:
        self.force_expr = force_expr

        return self


class RemoveGrainMode(CustomIntEnum):
    NONE = 0
    MINMAX_AROUND1 = 1
    MINMAX_AROUND2 = 2
    MINMAX_AROUND3 = 3
    MINMAX_MEDIAN = 4
    EDGE_CLIP_STRONG = 5
    EDGE_CLIP_MODERATE = 6
    EDGE_CLIP_MEDIUM = 7
    EDGE_CLIP_LIGHT = 8
    LINE_CLIP_CLOSE = 9
    MIN_SHARP = 10
    BINOMIAL_BLUR = 11
    BOB_TOP_CLOSE = 13
    BOB_BOTTOM_CLOSE = 14
    BOB_TOP_INTER = 15
    BOB_BOTTOM_INTER = 16
    MINMAX_MEDIAN_OPP = 17
    LINE_CLIP_OPP = 18
    BOX_BLUR_NO_CENTER = 19
    BOX_BLUR = 20
    OPP_CLIP_AVG = 21
    OPP_CLIP_AVG_FAST = 22
    EDGE_DEHALO = 23
    EDGE_DEHALO2 = 24
    SMART_RGC = 26
    SMART_RGCL = 27
    SMART_RGCL2 = 28

    def __call__(self, clip: vs.VideoNode, planes: PlanesT = None) -> vs.VideoNode:
        from .rgtools import removegrain
        from .util import norm_rmode_planes
        return removegrain(clip, norm_rmode_planes(clip, self, planes))


RemoveGrainModeT = int | RemoveGrainMode | Sequence[int | RemoveGrainMode]


class RepairMode(CustomIntEnum):
    NONE = 0
    MINMAX_SQUARE1 = 1
    MINMAX_SQUARE2 = 2
    MINMAX_SQUARE3 = 3
    MINMAX_SQUARE4 = 4
    LINE_CLIP_MIN = 5
    LINE_CLIP_LIGHT = 6
    LINE_CLIP_MEDIUM = 7
    LINE_CLIP_STRONG = 8
    LINE_CLIP_CLOSE = 9
    MINMAX_SQUARE_REF_CLOSE = 10
    MINMAX_SQUARE_REF1 = 11
    MINMAX_SQUARE_REF2 = 12
    MINMAX_SQUARE_REF3 = 13
    MINMAX_SQUARE_REF4 = 14
    CLIP_REF_RG5 = 15
    CLIP_REF_RG6 = 16
    CLIP_REF_RG17 = 17
    CLIP_REF_RG18 = 18
    CLIP_REF_RG19 = 19
    CLIP_REF_RG20 = 20
    CLIP_REF_RG21 = 21
    CLIP_REF_RG22 = 22
    CLIP_REF_RG23 = 23
    CLIP_REF_RG24 = 24
    CLIP_REF_RG26 = 26
    CLIP_REF_RG27 = 27
    CLIP_REF_RG28 = 28

    def __call__(self, clip: vs.VideoNode, repairclip: vs.VideoNode, planes: PlanesT = None) -> vs.VideoNode:
        from .rgtools import repair
        from .util import norm_rmode_planes
        return repair(clip, repairclip, norm_rmode_planes(clip, self, planes))


RepairModeT = int | RepairMode | Sequence[int | RepairMode]


class VerticalCleanerMode(CustomIntEnum):
    NONE = 0
    MEDIAN = 1
    PRESERVING = 2

    def __call__(self, clip: vs.VideoNode, planes: PlanesT = None) -> vs.VideoNode:
        from .rgtools import verticalcleaner
        from .util import norm_rmode_planes
        return verticalcleaner(clip, norm_rmode_planes(clip, self, planes))


VerticalCleanerModeT = int | VerticalCleanerMode | Sequence[int | VerticalCleanerMode]


class ClenseMode(CustomStrEnum):
    NONE = ''
    BACKWARD = 'BackwardClense'
    FORWARD = 'ForwardClense'
    BOTH = 'Clense'

    def __call__(
            self, clip: vs.VideoNode, previous_clip: vs.VideoNode | None = None,
            next_clip: vs.VideoNode | None = None, planes: PlanesT = None
        ) -> vs.VideoNode:
        from .rgtools import clense
        return clense(clip, previous_clip, next_clip, self, planes)


ClenseModeT = str | ClenseMode


class BlurMatrixBase(list[Nb]):
    def __init__(
        self, __iterable: Iterable[Nb], /, mode: ConvMode = ConvMode.SQUARE,
    ) -> None:
        self.mode = mode
        super().__init__(__iterable)  # type: ignore[arg-type]

    def __call__(
        self, clip: vs.VideoNode, planes: PlanesT = None,
        bias: float | None = None, divisor: float | None = None, saturate: bool = True,
        passes: int = 1, expr_kwargs: KwargsT | None = None, **conv_kwargs: Any
    ) -> vs.VideoNode:
        """
        Performs a spatial or temporal convolution.
        It will either calls std.Convolution, std.AverageFrames or ExprOp.convolution
        based on the ConvMode mode picked.

        :param clip:            Clip to process.
        :param planes:          Specifies which planes will be processed.
        :param bias:            Value to add to the final result of the convolution
                                (before clamping the result to the format's range of valid values).
        :param divisor:         Divide the output of the convolution by this value (before adding bias).
                                The default is the sum of the elements of the matrix
        :param saturate:        If True, negative values become 0.
                                If False, absolute values are returned.
        :param passes:          Number of iterations.
        :param expr_kwargs:     A KwargsT of keyword arguments for ExprOp.convolution.__call__ when it is picked.
        :param **conv_kwargs:   Additional keyword arguments for std.Convolution, std.AverageFrames or ExprOp.convolution.

        :return:                Processed clip.
        """
        if len(self) <= 1:
            return clip

        assert (check_variable(clip, self.__call__))

        expr_kwargs = expr_kwargs or KwargsT()

        fp16 = clip.format.sample_type == vs.FLOAT and clip.format.bits_per_sample == 16

        if self.mode.is_spatial:
            # std.Convolution is limited to 25 numbers
            # SQUARE mode is not optimized
            # std.Convolution doesn't support float 16
            if len(self) <= 25 and self.mode != ConvMode.SQUARE and not fp16:
                return iterate(clip, core.std.Convolution, passes, self, bias, divisor, planes, saturate, self.mode)

            return iterate(
                clip, ExprOp.convolution("x", self, bias, fallback(divisor, True), saturate, self.mode, **conv_kwargs),
                passes, planes=planes, **expr_kwargs
            )

        if all([
            not fp16,
            len(self) <= 31,
            not bias,
            saturate,
            (len(conv_kwargs) == 0 or (len(conv_kwargs) == 1 and "scenechange" in conv_kwargs))
        ]):
            return iterate(clip, core.std.AverageFrames, passes, self, divisor, planes=planes, **conv_kwargs)

        return self._averageframes_akarin(clip, planes, bias, divisor, saturate, passes, expr_kwargs, **conv_kwargs)

    def _averageframes_akarin(self, *args: Any, **kwargs: Any) -> vs.VideoNode:
        clip, planes, bias, divisor, saturate, passes, expr_kwargs = args
        conv_kwargs = kwargs

        r = len(self) // 2

        if conv_kwargs.pop("scenechange", False) is False:
            expr_conv = ExprOp.convolution(
                ExprVars(len(self)), self, bias, fallback(divisor, True), saturate, self.mode, **conv_kwargs
            )
            return iterate(
                clip, lambda x: expr_conv(shift_clip_multi(x, (-r, r)), planes=planes, **expr_kwargs), passes
            )

        vars_, = ExprOp.matrix(ExprVars(len(self)), r, self.mode)

        # Conditionnal for backward frames
        condb = list([ExprList(["cond0!", "cond0@", 0])])

        for i, vv in enumerate(accumulate(vars_[:r][::-1], operator.add), 1):
            ww = list[Any]()

            for j, (v, w) in enumerate(zip(vv, self[:r][::-1])):
                ww.append([v, w, ExprOp.DUP, f"div{j}!", ExprOp.MUL])

            condb.append(ExprList([f"cond{i}!", f"cond{i}@", ww, [ExprOp.ADD] * (i - 1)]))

        # Conditionnal for forward frames
        condf = list([ExprList([f"cond{i + 1}!", f"cond{i + 1}@", 0])])

        for ii, vv in enumerate(accumulate(vars_[r + 1:], operator.add), i + 2):
            ww = list[Any]()

            for jj, (v, w) in enumerate(zip(vv, self[r + 1:]), j + 2):
                ww.append([v, w, ExprOp.DUP, f"div{jj}!", ExprOp.MUL])

            condf.append(ExprList([f"cond{ii}!", f"cond{ii}@", ww, [ExprOp.ADD] * (ii - i - 2)]))

        expr = ExprList()

        # Conditionnal for backward frames
        for i, (v, c) in enumerate(zip(vars_[:r][::-1], condb)):
            expr.append(f"{v}._SceneChangeNext", *c)

        expr.append(condb[-1][2:], ExprOp.TERN * r)

        # Conditionnal for forward frames
        for i, (v, c) in enumerate(zip(vars_[r + 1:], condf)):
            expr.append(f"{v}._SceneChangePrev", *c)

        expr.append(condf[-1][2:], ExprOp.TERN * r)

        expr.append(ExprOp.ADD, vars_[r], self[r])

        # Center frame
        weights_cum_b = ExprList(v for v in reversed(list(accumulate(self[:r]))))
        weights_cum_f = ExprList(v for v in reversed(list(accumulate(self[r + 1:][::-1]))))

        for k, ws in zip(range(ii), weights_cum_b + ExprList() + weights_cum_f):
            if k == r:
                continue
            expr.append(f"cond{k}@", ws, ExprOp.MUL)

        expr.extend([ExprOp.ADD] * k)
        expr.append(ExprOp.DUP, f"div{r}!", ExprOp.MUL, ExprOp.ADD)

        if (premultiply := conv_kwargs.get("premultiply", None)):
            expr.append(premultiply, ExprOp.MUL)

        if divisor:
            expr.append(divisor, ExprOp.DIV)
        else:
            # Divisor conditionnal
            for cond, rr in zip([condb, condf], [(0, r), (r + 1, r * 2 + 1)]):
                for n, m in zip(accumulate(([d] for d in range(*rr)), initial=[0]), cond[:-1]):
                    if (n := n[1:]):
                        div = list[str]()
                        for divn in n:
                            div.append(f"div{divn}@")
                    else:
                        div = [str(0)]

                    expr.append(str(m[0])[:5] + "@", div, [ExprOp.ADD] * max(0, len(n) - 1))

                expr.append(*div, f"div{divn + 1}@", ExprOp.ADD * len(div))
                expr.append(ExprOp.TERN * r)

            expr.append(ExprOp.ADD, f"div{r}@", ExprOp.ADD, ExprOp.DIV)

        if bias:
            expr.append(bias, ExprOp.ADD)

        if not saturate:
            expr.append(ExprOp.ABS)

        if (multiply := conv_kwargs.get("multiply", None)):
            expr.append(multiply, ExprOp.MUL)

        if conv_kwargs.get("clamp", False):
            expr.append(ExprOp.clamp(ExprToken.RangeMin, ExprToken.RangeMax))

        return iterate(clip, lambda x: expr(shift_clip_multi(x, (-r, r)), planes=planes, **expr_kwargs), passes)

    def outer(self) -> Self:
        from numpy import outer

        return self.__class__(outer(self, self).flatten().tolist(), self.mode)


class BlurMatrix(CustomIntEnum):
    MEAN_NO_CENTER = 0
    MEAN = 1
    BINOMIAL = 2
    LOG = 3

    @to_singleton.as_property
    class GAUSS:
        def __call__(
            self,
            taps: int | None = None,
            *,
            sigma: float = 0.5,
            mode: ConvMode = ConvMode.HV,
            **kwargs: Any
        ) -> BlurMatrixBase[float]:
            scale_value = kwargs.get("scale_value", 1023)

            if mode == ConvMode.SQUARE:
                scale_value = sqrt(scale_value)

            taps = self.get_taps(sigma, taps)

            if taps < 0:
                raise CustomValueError('Taps must be >= 0!')

            if sigma > 0.0:
                half_pisqrt = 1.0 / sqrt(2.0 * pi) * sigma
                doub_qsigma = 2 * sigma ** 2

                high, *mat = [half_pisqrt * exp(-x ** 2 / doub_qsigma) for x in range(taps + 1)]

                mat = [x * scale_value / high for x in mat]
                mat = [*mat[::-1], scale_value, *mat]
            else:
                mat = [scale_value]

            kernel = BlurMatrixBase(mat, mode)

            if mode == ConvMode.SQUARE:
                kernel = kernel.outer()

            return kernel

        def from_radius(self, radius: int) -> BlurMatrixBase[float]:
            return self(None, sigma=(radius + 1.0) / 3)

        @staticmethod
        def get_taps(sigma: float, taps: int | None = None) -> int:
            if taps is None:
                taps = ceil(abs(sigma) * 8 + 1) // 2

            return taps

    @overload
    def __call__(  # type: ignore[misc]
        self: Literal[BlurMatrix.MEAN_NO_CENTER], taps: int = 1, *, mode: ConvMode = ConvMode.SQUARE
    ) -> BlurMatrixBase[int]:
        ...

    @overload
    def __call__(  # type: ignore[misc]
        self: Literal[BlurMatrix.MEAN], taps: int = 1, *, mode: ConvMode = ConvMode.SQUARE
    ) -> BlurMatrixBase[int]:
        ...

    @overload
    def __call__(  # type: ignore[misc]
        self: Literal[BlurMatrix.BINOMIAL], taps: int = 1, *, mode: ConvMode = ConvMode.HV, **kwargs: Any
    ) -> BlurMatrixBase[int]:
        ...

    @overload
    def __call__(  # type: ignore[misc]
        self: Literal[BlurMatrix.LOG], taps: int = 1, *, strength: float = 100.0, mode: ConvMode = ConvMode.HV
    ) -> BlurMatrixBase[float]:
        ...

    def __call__(self, taps: int = 1, **kwargs: Any) -> Any:
        kernel: BlurMatrixBase[Any]

        match self:
            case BlurMatrix.MEAN_NO_CENTER:
                mode = kwargs.pop("mode", ConvMode.SQUARE)

                matrix = [1 for _ in range(((2 * taps + 1) ** (2 if mode == ConvMode.SQUARE else 1)) - 1)]
                matrix.insert(len(matrix) // 2, 0)

                return BlurMatrixBase[int](matrix, mode)

            case BlurMatrix.MEAN:
                mode = kwargs.pop("mode", ConvMode.SQUARE)

                kernel = BlurMatrixBase[int]([1 for _ in range(((2 * taps + 1)))], mode)

            case BlurMatrix.BINOMIAL:
                mode = kwargs.pop("mode", ConvMode.HV)

                c = 1
                n = taps * 2 + 1

                matrix = list[int]()

                for i in range(1, taps + 2):
                    matrix.append(c)
                    c = c * (n - i) // i

                kernel = BlurMatrixBase(matrix[:-1] + matrix[::-1], mode)

            case BlurMatrix.LOG:
                mode = kwargs.pop("mode", ConvMode.HV)
                strength = kwargs.get("strength", 100)

                strength = max(1e-6, min(log2(3) * strength / 100, log2(3)))

                weight = 0.5 ** strength / ((1 - 0.5 ** strength) * 0.5)

                matrixf = [1.0]

                for _ in range(taps):
                    matrixf.append(matrixf[-1] / weight)

                kernel = BlurMatrixBase([*matrixf[::-1], *matrixf[1:]], mode)

        if mode == ConvMode.SQUARE:
            kernel = kernel.outer()

        return kernel


class BilateralBackend(CustomIntEnum):
    CPU = 0
    GPU = 1
    GPU_RTC = 2