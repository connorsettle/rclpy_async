from dataclasses import dataclass
from typing import Any

from ._base_handler_spec import BaseHandlerSpec


@dataclass
class ServiceHandlerSpec(BaseHandlerSpec[[Any, Any], Any]):
    """Specification for a ROS service handler

    async_fn signature: (request: SrvType.Request, response: SrvType.Response) -> Awaitable[SrvType.Response]

    Args:
        BaseHandlerSpec (_type_): Inherits from BaseHandlerSpec
    """

    srv_type: type
    srv_name: str
