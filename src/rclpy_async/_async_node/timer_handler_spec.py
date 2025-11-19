from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Union


@dataclass
class TimerHandlerSpec():
    """Specification for a timer handler.

    async_fn signature: () -> Awaitable[None]
    timer_period_sec may be float or a callable None -> float.
    """

    timer_period_sec: Union[float, Callable[[], float]]
    max_queue_size: int
    drop_oldest: bool
    kwargs: dict[str, Any]
    async_fn: Callable[[], Awaitable[None]]
