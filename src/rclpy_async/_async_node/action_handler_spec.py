from dataclasses import dataclass
from typing import Any

from rclpy.action.server import ServerGoalHandle

from ._base_handler_spec import BaseHandlerSpec


@dataclass
class ActionHandlerSpec(BaseHandlerSpec[[ServerGoalHandle], Any]):
    """Specification for a ROS action handler

    async_fn signature: (goal: ServerGoalHandle) -> Awaitable[Any]

    Args:
        BaseHandlerSpec (_type_): Inherits from BaseHandlerSpec
    """

    action_type: type
    action_name: str
