from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Optional

from rclpy.qos import QoSProfile

from ._base_handler_spec import BaseHandlerSpec


@dataclass
class TopicHandlerSpec(BaseHandlerSpec[[Any], None]):
    """Specification for a subscription handler.

    async_fn signature: (message: MsgType) -> Awaitable[None]

    Args:
        BaseHandlerSpec (_type_): Inherits from BaseHandlerSpec
    """

    msg_type: type
    topic_name: str
    qos_profile: QoSProfile
