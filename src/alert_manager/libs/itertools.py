import math
import typing as t


def divide_seq(value: t.Sequence[t.Any]) -> tuple[t.Sequence[t.Any], t.Sequence[t.Any]]:
    middle = math.ceil(len(value) / 2)
    return value[:middle], value[middle:]
