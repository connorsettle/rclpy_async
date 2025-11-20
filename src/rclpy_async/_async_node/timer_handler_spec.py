from dataclasses import dataclass
from typing import Callable, Union

from ._base_handler_spec import BaseHandlerSpec


@dataclass
class TimerHandlerSpec(BaseHandlerSpec[[], None]):
    """Specification for a ROS service handler

    async_fn signature: () -> Awaitable[None]

    Args:
        BaseHandlerSpec (_type_): Inherits from BaseHandlerSpec
    """

    timer_period_sec: Union[float, Callable[[], float]]
