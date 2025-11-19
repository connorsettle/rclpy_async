from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Generic, TypeVar, Union

from .parameter_schema import ParameterSchema

TParams = TypeVar("TParams", bound=ParameterSchema)


@dataclass
class TimerHandlerSpec(Generic[TParams]):
    """Specification for a timer handler.

    async_fn signature: () -> Awaitable[None]
    timer_period_sec may be float or a callable taking params -> float.
    """

    timer_period_sec: Union[float, Callable[[TParams], float]]
    max_queue_size: int
    drop_oldest: bool
    kwargs: dict[str, Any]
    async_fn: Callable[[], Awaitable[None]]
