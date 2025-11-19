from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from rclpy.qos import QoSProfile


@dataclass
class TopicHandlerSpec:
    """Specification for a subscription handler.

    async_fn signature: (message: MsgType) -> Awaitable[None]
    """

    msg_type: type
    topic_name: str
    qos_profile: QoSProfile
    max_queue_size: int
    drop_oldest: bool
    kwargs: dict[str, Any]
    async_fn: Callable[[Any], Awaitable[None]]
