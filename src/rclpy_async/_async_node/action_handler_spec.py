from dataclasses import dataclass
from typing import Any, Awaitable, Callable
from rclpy.action.server import ServerGoalHandle


@dataclass
class ActionHandlerSpec:
    """Specification for an action handler.

    async_fn signature: (goal_handle: ServerGoalHandle) -> Awaitable[Any]
    """

    action_type: type
    action_name: str
    kwargs: dict[str, Any]
    async_fn: Callable[[ServerGoalHandle], Awaitable[Any]]
