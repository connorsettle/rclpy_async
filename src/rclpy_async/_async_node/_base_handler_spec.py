from abc import ABC
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Generic, Optional, TypeVar, ParamSpec

from .backpressure_handler_spec import BackpressureHandlerSpec

PInput = ParamSpec("PInput")
TOutput = TypeVar("TOutput")


@dataclass
class BaseHandlerSpec(ABC, Generic[PInput, TOutput]):
    """Base Handler spec for registering ROS callbacks

    Args:
        ABC (_type_): Abstract Base Class
        Generic (_type_): Generic class
    """

    backpressure_handler: Optional[BackpressureHandlerSpec]
    kwargs: dict[str, Any]

    async_fn: Callable[PInput, Awaitable[TOutput]]
