from functools import partial
from typing import Callable

from ._rg import (
    aka_removegrain_expr_1,
    aka_removegrain_expr_2_4,
    aka_removegrain_expr_5,
    aka_removegrain_expr_6,
    aka_removegrain_expr_7,
    aka_removegrain_expr_8,
    aka_removegrain_expr_9,
    aka_removegrain_expr_10,
    aka_removegrain_expr_11_12,
    aka_removegrain_expr_17,
    aka_removegrain_expr_18,
    aka_removegrain_expr_19,
    aka_removegrain_expr_20,
    aka_removegrain_expr_21_22,
    aka_removegrain_expr_23,
    aka_removegrain_expr_24,
    aka_removegrain_expr_26,
    aka_removegrain_expr_27,
    aka_removegrain_expr_28,
)
from ._rp import (
    aka_repair_expr_1_4,
    aka_repair_expr_5,
    aka_repair_expr_6,
    aka_repair_expr_7,
    aka_repair_expr_8,
    aka_repair_expr_9,
    aka_repair_expr_10,
    aka_repair_expr_11_14,
    aka_repair_expr_15,
    aka_repair_expr_16,
    aka_repair_expr_17,
    aka_repair_expr_18,
    aka_repair_expr_19,
    aka_repair_expr_20,
    aka_repair_expr_21,
    aka_repair_expr_22,
    aka_repair_expr_23,
    aka_repair_expr_24,
    aka_repair_expr_26,
    aka_repair_expr_27,
    aka_repair_expr_28,
)


def _noop_expr() -> str:
    return ''


def _unimpl_expr() -> str:
    raise NotImplementedError('Unimplemented RGTools expr mode!', _unimpl_expr)


removegrain_aka_exprs = list[Callable[[], str]](
    [
        _noop_expr,
        aka_removegrain_expr_1,
        partial(aka_removegrain_expr_2_4, 2),
        partial(aka_removegrain_expr_2_4, 3),
        partial(aka_removegrain_expr_2_4, 4),
        aka_removegrain_expr_5,
        aka_removegrain_expr_6,
        aka_removegrain_expr_7,
        aka_removegrain_expr_8,
        aka_removegrain_expr_9,
        aka_removegrain_expr_10,
        aka_removegrain_expr_11_12,
        aka_removegrain_expr_11_12,
        _unimpl_expr,
        _unimpl_expr,
        _unimpl_expr,
        _unimpl_expr,
        aka_removegrain_expr_17,
        aka_removegrain_expr_18,
        aka_removegrain_expr_19,
        aka_removegrain_expr_20,
        aka_removegrain_expr_21_22,
        aka_removegrain_expr_21_22,
        aka_removegrain_expr_23,
        aka_removegrain_expr_24,
        _unimpl_expr,
        aka_removegrain_expr_26,
        aka_removegrain_expr_27,
        aka_removegrain_expr_28,
    ]
)

repair_aka_exprs = list[Callable[[], str]](
    [
        _noop_expr,
        partial(aka_repair_expr_1_4, 1),
        partial(aka_repair_expr_1_4, 2),
        partial(aka_repair_expr_1_4, 3),
        partial(aka_repair_expr_1_4, 4),
        aka_repair_expr_5,
        aka_repair_expr_6,
        aka_repair_expr_7,
        aka_repair_expr_8,
        aka_repair_expr_9,
        aka_repair_expr_10,
        partial(aka_repair_expr_11_14, 1),
        partial(aka_repair_expr_11_14, 2),
        partial(aka_repair_expr_11_14, 3),
        partial(aka_repair_expr_11_14, 4),
        aka_repair_expr_15,
        aka_repair_expr_16,
        aka_repair_expr_17,
        aka_repair_expr_18,
        aka_repair_expr_19,
        aka_repair_expr_20,
        aka_repair_expr_21,
        aka_repair_expr_22,
        aka_repair_expr_23,
        aka_repair_expr_24,
        _unimpl_expr,
        aka_repair_expr_26,
        aka_repair_expr_27,
        aka_repair_expr_28,
    ]
)
