from typing import TypeGuard


def is_list_wo_none[T](ls: list[T | None]) -> TypeGuard[list[T]]:
    return all(e is not None for e in ls)


def plural(ind: int) -> str:
    return "s"[: ind + 1 ^ 1]
