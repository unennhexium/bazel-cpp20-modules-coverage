from __future__ import annotations

from abc import ABC, abstractmethod
from argparse import (
    Action,
)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from argparse import (
        ArgumentParser,
        Namespace,
    )
    from collections.abc import Sequence
    from typing import Any


class Action(Action, ABC):
    called = False

    @abstractmethod
    def prepare(
        self,
        option_arguments: Sequence[str],
        *,
        namespace: Namespace | None = None,
    ) -> Any: ...
    def __call__(
        self,
        _parser: ArgumentParser,
        namespace: Namespace,
        values: Sequence[str],
        _option_string=None,
    ) -> None:
        res = self.__class__.prepare(self, values, namespace=namespace)
        setattr(namespace, self.dest, res)
