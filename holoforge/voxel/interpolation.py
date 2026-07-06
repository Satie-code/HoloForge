from typing import Tuple, List


def lerp(a: Tuple[float, float, float], b: Tuple[float, float, float], t: float) -> Tuple[float, float, float]:
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


def interpolate_positions(pos_a: Tuple[int, int, int], pos_b: Tuple[int, int, int]) -> List[Tuple[int, int, int]]:
    da = (pos_b[0] - pos_a[0], pos_b[1] - pos_a[1], pos_b[2] - pos_a[2])
    steps = max(abs(da[0]), abs(da[1]), abs(da[2]))
    if steps == 0:
        return [pos_a]
    out = []
    for i in range(steps + 1):
        t = i / float(steps)
        p = lerp(pos_a, pos_b, t)
        out.append((round(p[0]), round(p[1]), round(p[2])))
    return out
