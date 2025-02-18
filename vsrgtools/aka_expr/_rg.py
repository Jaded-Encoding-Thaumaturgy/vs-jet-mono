A1 = 'x[-1,-1]'
A2 = 'x[0,-1]'
A3 = 'x[1,-1]'
A4 = 'x[-1,0]'
A5 = 'x[1,0]'
A6 = 'x[-1,1]'
A7 = 'x[0,1]'
A8 = 'x[1,1]'
c = 'x'
PIXELS = ' '.join([A1, A2, A3, A4, A5, A6, A7, A8])


def aka_removegrain_expr_1() -> str:
    return f'x {PIXELS} min min min min min min min {PIXELS} max max max max max max max clamp'


def aka_removegrain_expr_2_4(m: int) -> str:
    return f'{PIXELS} sort8 dup{8 - m} max_val! dup{m - 1} min_val! drop8 x min_val@ max_val@ clamp'


def aka_removegrain_expr_5() -> str:
    return (
        f'x {A1} {A8} min {A1} {A8} max clamp clamp1! '
        f'x {A2} {A7} min {A2} {A7} max clamp clamp2! '
        f'x {A3} {A6} min {A3} {A6} max clamp clamp3! '
        f'x {A4} {A5} min {A4} {A5} max clamp clamp4! '
        'x clamp1@ - abs c1! '
        'x clamp2@ - abs c2! '
        'x clamp3@ - abs c3! '
        'x clamp4@ - abs c4! '
        'c1@ c2@ c3@ c4@ min min min mindiff! '
        'mindiff@ c4@ = clamp4@ mindiff@ c2@ = clamp2@ mindiff@ c3@ = clamp3@ clamp1@ ? ? ?'
    )


def aka_removegrain_expr_6() -> str:
    return (
        f'{A1} {A8} min mil1! '
        f'{A1} {A8} max mal1! '
        f'{A2} {A7} min mil2! '
        f'{A2} {A7} max mal2! '
        f'{A3} {A6} min mil3! '
        f'{A3} {A6} max mal3! '
        f'{A4} {A5} min mil4! '
        f'{A4} {A5} max mal4! '
        'mal1@ mil1@ - d1! '
        'mal2@ mil2@ - d2! '
        'mal3@ mil3@ - d3! '
        'mal4@ mil4@ - d4! '
        'x mil1@ mal1@ clamp clamp1! '
        'x mil2@ mal2@ clamp clamp2! '
        'x mil3@ mal3@ clamp clamp3! '
        'x mil4@ mal4@ clamp clamp4! '
        'x clamp1@ - abs 2 * d1@ + c1! '
        'x clamp2@ - abs 2 * d2@ + c2! '
        'x clamp3@ - abs 2 * d3@ + c3! '
        'x clamp4@ - abs 2 * d4@ + c4! '
        'c1@ c2@ c3@ c4@ min min min mindiff! '
        'mindiff@ c4@ = clamp4@ mindiff@ c2@ = clamp2@ mindiff@ c3@ = clamp3@ clamp1@ ? ? ?'
    )


def aka_removegrain_expr_7() -> str:
    return (
        f'{A1} {A8} min mil1! '
        f'{A1} {A8} max mal1! '
        f'{A2} {A7} min mil2! '
        f'{A2} {A7} max mal2! '
        f'{A3} {A6} min mil3! '
        f'{A3} {A6} max mal3! '
        f'{A4} {A5} min mil4! '
        f'{A4} {A5} max mal4! '
        'mal1@ mil1@ - d1! '
        'mal2@ mil2@ - d2! '
        'mal3@ mil3@ - d3! '
        'mal4@ mil4@ - d4! '
        'x mil1@ mal1@ clamp clamp1! '
        'x mil2@ mal2@ clamp clamp2! '
        'x mil3@ mal3@ clamp clamp3! '
        'x mil4@ mal4@ clamp clamp4! '
        # Only change is removing the "* 2"
        'x clamp1@ - abs d1@ + c1! '
        'x clamp2@ - abs d2@ + c2! '
        'x clamp3@ - abs d3@ + c3! '
        'x clamp4@ - abs d4@ + c4! '
        'c1@ c2@ c3@ c4@ min min min mindiff! '
        'mindiff@ c4@ = clamp4@ mindiff@ c2@ = clamp2@ mindiff@ c3@ = clamp3@ clamp1@ ? ? ?'
    )


def aka_removegrain_expr_8() -> str:
    return (
        f'{A1} {A8} min mil1! '
        f'{A1} {A8} max mal1! '
        f'{A2} {A7} min mil2! '
        f'{A2} {A7} max mal2! '
        f'{A3} {A6} min mil3! '
        f'{A3} {A6} max mal3! '
        f'{A4} {A5} min mil4! '
        f'{A4} {A5} max mal4! '
        'mal1@ mil1@ - d1! '
        'mal2@ mil2@ - d2! '
        'mal3@ mil3@ - d3! '
        'mal4@ mil4@ - d4! '
        'x mil1@ mal1@ clamp clamp1! '
        'x mil2@ mal2@ clamp clamp2! '
        'x mil3@ mal3@ clamp clamp3! '
        'x mil4@ mal4@ clamp clamp4! '
        'x clamp1@ - abs d1@ 2 * + c1! '
        'x clamp2@ - abs d2@ 2 * + c2! '
        'x clamp3@ - abs d3@ 2 * + c3! '
        'x clamp4@ - abs d4@ 2 * + c4! '
        'c1@ c2@ c3@ c4@ min min min mindiff! '
        'mindiff@ c4@ = clamp4@ mindiff@ c2@ = clamp2@ mindiff@ c3@ = clamp3@ clamp1@ ? ? ?'
    )


def aka_removegrain_expr_9() -> str:
    return (
        f'{A1} {A8} min mil1! '
        f'{A1} {A8} max mal1! '
        f'{A2} {A7} min mil2! '
        f'{A2} {A7} max mal2! '
        f'{A3} {A6} min mil3! '
        f'{A3} {A6} max mal3! '
        f'{A4} {A5} min mil4! '
        f'{A4} {A5} max mal4! '
        'mal1@ mil1@ - d1! '
        'mal2@ mil2@ - d2! '
        'mal3@ mil3@ - d3! '
        'mal4@ mil4@ - d4! '
        'd1@ d2@ d3@ d4@ min min min mindiff! '
        'mindiff@ d4@ = x mil4@ mal4@ clamp mindiff@ d2@ = x mil2@ mal2@ clamp '
        'mindiff@ d3@ = x mil3@ mal3@ clamp x mil1@ mal1@ clamp ? ? ?'
    )


def aka_removegrain_expr_10() -> str:
    return (
        f'x {A1} - abs d1! '
        f'x {A2} - abs d2! '
        f'x {A3} - abs d3! '
        f'x {A4} - abs d4! '
        f'x {A5} - abs d5! '
        f'x {A6} - abs d6! '
        f'x {A7} - abs d7! '
        f'x {A8} - abs d8! '
        'd1@ d2@ d3@ d4@ d5@ d6@ d7@ d8@ min min min min min min min mindiff! '
        f'mindiff@ d7@ = {A7} mindiff@ d8@ = {A8} mindiff@ d6@ = {A6} mindiff@ d2@ = {A2} '
        f'mindiff@ d3@ = {A3} mindiff@ d1@ = {A1} mindiff@ d5@ = {A5} {A4} ? ? ? ? ? ? ?'
    )


def aka_removegrain_expr_11_12() -> str:
    return f'x 4 * {A2} {A4} {A5} {A7} + + + 2 * + {A1} {A3} {A6} {A8} + + + + 16 /'


def aka_removegrain_expr_17() -> str:
    return (
        f'{A1} {A8} min mil1! '
        f'{A1} {A8} max mal1! '
        f'{A2} {A7} min mil2! '
        f'{A2} {A7} max mal2! '
        f'{A3} {A6} min mil3! '
        f'{A3} {A6} max mal3! '
        f'{A4} {A5} min mil4! '
        f'{A4} {A5} max mal4! '
        'mil1@ mil2@ mil3@ mil4@ max max max maxmil! '
        'mal1@ mal2@ mal3@ mal4@ min min min minmal! '
        'x maxmil@ minmal@ min maxmil@ minmal@ max clamp'
    )


def aka_removegrain_expr_18() -> str:
    return (
        f'x {A1} - abs x {A8} - abs max d1! '
        f'x {A2} - abs x {A7} - abs max d2! '
        f'x {A3} - abs x {A6} - abs max d3! '
        f'x {A4} - abs x {A5} - abs max d4! '
        'd1@ d2@ d3@ d4@ min min min mindiff! '
        f'mindiff@ d4@ = x {A4} {A5} min {A4} {A5} max clamp '
        f'mindiff@ d2@ = x {A2} {A7} min {A2} {A7} max clamp '
        f'mindiff@ d3@ = x {A3} {A6} min {A3} {A6} max clamp '
        f'x {A1} {A8} min {A1} {A8} max clamp ? ? ?'
    )


def aka_removegrain_expr_19() -> str:
    return f'{A1} {A2} {A3} {A4} {A5} {A6} {A7} {A8} + + + + + + + 8.0 /'


def aka_removegrain_expr_20() -> str:
    return f'x {A1} {A2} {A3} {A4} {A5} {A6} {A7} {A8} + + + + + + + + 9.0 /'


def aka_removegrain_expr_21_22() -> str:
    return (
        f'{A1} {A8} + 2 / av1! '
        f'{A2} {A7} + 2 / av2! '
        f'{A3} {A6} + 2 / av3! '
        f'{A4} {A5} + 2 / av4! '
        'x av1@ av2@ av3@ av4@ min min min av1@ av2@ av3@ av4@ max max max clamp'
    )


def aka_removegrain_expr_23() -> str:
    minmax = 'min max max max range_min max'
    u = f'x mal1@ - linediff1@ min x mal2@ - linediff2@ min x mal3@ - linediff3@ min x mal4@ - linediff4@ {minmax}'
    d = f'mil1@ x - linediff1@ min mil2@ x - linediff2@ min mil3@ x - linediff3@ min mil4@ x - linediff4@ {minmax}'

    return (
        f'{A1} {A8} min mil1! '
        f'{A1} {A8} max mal1! '
        f'{A2} {A7} min mil2! '
        f'{A2} {A7} max mal2! '
        f'{A3} {A6} min mil3! '
        f'{A3} {A6} max mal3! '
        f'{A4} {A5} min mil4! '
        f'{A4} {A5} max mal4! '
        'mal1@ mil1@ - linediff1! '
        'mal2@ mil2@ - linediff2! '
        'mal3@ mil3@ - linediff3! '
        'mal4@ mil4@ - linediff4! '
        f'x {u} - {d} +'
    )


def aka_removegrain_expr_24() -> str:
    linediff_minmax = (
        'linediff1@ t1@ - t1@ min linediff2@ t2@ - t2@ min '
        'linediff3@ t3@ - t3@ min linediff4@ t4@ - t4@ min '
        'max max max range_min max'
    )

    return (
        f'{A1} {A8} min mil1! '
        f'{A1} {A8} max mal1! '
        f'{A2} {A7} min mil2! '
        f'{A2} {A7} max mal2! '
        f'{A3} {A6} min mil3! '
        f'{A3} {A6} max mal3! '
        f'{A4} {A5} min mil4! '
        f'{A4} {A5} max mal4! '
        'mal1@ mil1@ - linediff1! '
        'mal2@ mil2@ - linediff2! '
        'mal3@ mil3@ - linediff3! '
        'mal4@ mil4@ - linediff4! '
        'x mal1@ - t1! '
        'x mal2@ - t2! '
        'x mal3@ - t3! '
        'x mal4@ - t4! '
        f'{linediff_minmax} u! '
        'mil1@ x - t1! '
        'mil2@ x - t2! '
        'mil3@ x - t3! '
        'mil4@ x - t4! '
        f'{linediff_minmax} d! '
        f'x u@ - d@ +'
    )


def aka_removegrain_expr_26() -> str:
    return (
        f'{A1} {A2} min mil1! '
        f'{A1} {A2} max mal1! '
        f'{A2} {A3} min mil2! '
        f'{A2} {A3} max mal2! '
        f'{A3} {A5} min mil3! '
        f'{A3} {A5} max mal3! '
        f'{A5} {A8} min mil4! '
        f'{A5} {A8} max mal4! '
        'mil1@ mil2@ mil3@ mil4@ max max max maxmil! '
        'mal1@ mal2@ mal3@ mal4@ min min min minmal! '
        f'{A7} {A8} min mil1! '
        f'{A7} {A8} max mal1! '
        f'{A6} {A7} min mil2! '
        f'{A6} {A7} max mal2! '
        f'{A4} {A6} min mil3! '
        f'{A4} {A6} max mal3! '
        f'{A1} {A4} min mil4! '
        f'{A1} {A4} max mal4! '
        'mil1@ mil2@ mil3@ mil4@ maxmil@ max max max max maxmil! '
        'mal1@ mal2@ mal3@ mal4@ minmal@ min min min min minmal! '
        'x maxmil@ minmal@ min maxmil@ minmal@ max clamp'
    )


def aka_removegrain_expr_27() -> str:
    return (
        f'{A1} {A8} min mil1! '
        f'{A1} {A8} max mal1! '
        f'{A1} {A2} min mil2! '
        f'{A1} {A2} max mal2! '
        f'{A7} {A8} min mil3! '
        f'{A7} {A8} max mal3! '
        f'{A2} {A7} min mil4! '
        f'{A2} {A7} max mal4! '
        'mil1@ mil2@ mil3@ mil4@ max max max maxmil! '
        'mal1@ mal2@ mal3@ mal4@ min min min minmal! '
        f'{A2} {A3} min mil1! '
        f'{A2} {A3} max mal1! '
        f'{A6} {A7} min mil2! '
        f'{A6} {A7} max mal2! '
        f'{A3} {A6} min mil3! '
        f'{A3} {A6} max mal3! '
        f'{A3} {A5} min mil4! '
        f'{A3} {A5} max mal4! '
        'mil1@ mil2@ mil3@ mil4@ maxmil@ max max max max maxmil! '
        'mal1@ mal2@ mal3@ mal4@ minmal@ min min min min minmal! '
        f'{A4} {A6} min mil1! '
        f'{A4} {A6} max mal1! '
        f'{A4} {A5} min mil2! '
        f'{A4} {A5} max mal2! '
        f'{A5} {A8} min mil3! '
        f'{A5} {A8} max mal3! '
        f'{A1} {A4} min mil4! '
        f'{A1} {A4} max mal4! '
        'mil1@ mil2@ mil3@ mil4@ maxmil@ max max max max maxmil! '
        'mal1@ mal2@ mal3@ mal4@ minmal@ min min min min minmal! '
        'x maxmil@ minmal@ min maxmil@ minmal@ max clamp'
    )


def aka_removegrain_expr_28() -> str:
    return (
        f'{A1} {A2} min mil1! '
        f'{A1} {A2} max mal1! '
        f'{A2} {A3} min mil2! '
        f'{A2} {A3} max mal2! '
        f'{A3} {A5} min mil3! '
        f'{A3} {A5} max mal3! '
        f'{A5} {A8} min mil4! '
        f'{A5} {A8} max mal4! '
        'mil1@ mil2@ mil3@ mil4@ max max max maxmil! '
        'mal1@ mal2@ mal3@ mal4@ min min min minmal! '
        f'{A7} {A8} min mil1! '
        f'{A7} {A8} max mal1! '
        f'{A6} {A7} min mil2! '
        f'{A6} {A7} max mal2! '
        f'{A4} {A6} min mil3! '
        f'{A4} {A6} max mal3! '
        f'{A1} {A5} min mil4! '
        f'{A1} {A5} max mal4! '
        'mil1@ mil2@ mil3@ mil4@ maxmil@ max max max max maxmil! '
        'mal1@ mal2@ mal3@ mal4@ minmal@ min min min min minmal! '
        f'{A1} {A8} min mil1! '
        f'{A1} {A8} max mal1! '
        f'{A3} {A6} min mil2! '
        f'{A3} {A6} max mal2! '
        f'{A2} {A7} min mil3! '
        f'{A2} {A7} max mal3! '
        f'{A4} {A5} min mil4! '
        f'{A4} {A5} max mal4! '
        'mil1@ mil2@ mil3@ mil4@ maxmil@ max max max max maxmil! '
        'mal1@ mal2@ mal3@ mal4@ minmal@ min min min min minmal! '
        'x maxmil@ minmal@ min maxmil@ minmal@ max clamp'
    )
