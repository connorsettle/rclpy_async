from dataclasses import dataclass
from typing import Any, Awaitable, Callable


@dataclass
class ServiceHandlerSpec:
    """Specification for a service handler.

    async_fn signature: (request: SrvType.Request, response: SrvType.Response) -> Awaitable[SrvType.Response]
    """

    srv_type: type
    srv_name: str
    kwargs: dict[str, Any]
    async_fn: Callable[[Any, Any], Awaitable[Any]]
