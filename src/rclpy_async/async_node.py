import inspect
from contextlib import ExitStack
from typing import Any, Awaitable, Callable, List, Optional, Tuple, Type, Union

import anyio
import rclpy
from rclpy.action.server import ServerGoalHandle
from rclpy.node import Node
from rclpy.qos import QoSProfile

import rclpy_async

from ._async_node import (
    ActionHandlerSpec,
    BackpressureHandlerSpec,
    NodeProto,
    ServiceHandlerSpec,
    State,
    TimerHandlerSpec,
    TopicHandlerSpec,
)

# Public interface member names gathered from the Protocol; used for delegation.
_DELEGATE_NAMES = {
    name
    for name, member in vars(NodeProto).items()
    if not name.startswith("_")
    and (inspect.isfunction(member) or isinstance(member, property))
}


def _is_overridden(cls: Type[Any], name: str) -> bool:
    if not hasattr(NodeProto, name):
        return True  # Not part of proto; treat as overridden/local.
    member_cls = getattr(cls, name, None)
    member_proto = getattr(NodeProto, name, None)
    if inspect.isfunction(member_cls) and inspect.isfunction(member_proto):
        return member_cls is not member_proto
    if isinstance(member_proto, property) and isinstance(member_cls, property):
        return member_cls.fget is not member_proto.fget
    return True


class AsyncNode(NodeProto):
    """Asynchronous wrapper around a ROS 2 `Node` using dynamic delegation.

    Delegates all protocol-defined attributes/methods to `__inner` unless overridden.
    Provides decorators for subscription and timer handlers executed with anyio.
    """

    __inner: Optional[Node] = None  # Underlying rclpy Node instance
    state = State()  # Arbitrary user state container
    __node_name: str
    __exit_stack = ExitStack()
    __fallback_values: dict[str, Any] = (
        {}
    )  # Local storage for protocol-only properties when inner lacks them.

    __action_handler_specs: List[ActionHandlerSpec] = []
    __service_handler_specs: List[ServiceHandlerSpec] = []
    __timer_handler_specs: List[TimerHandlerSpec] = []
    __topic_handler_specs: List[TopicHandlerSpec] = []

    def __init__(self, node_name: str):
        self.__node_name = node_name

    def initialize(self) -> None:
        """Create underlying rclpy Node and declare parameters if a schema is provided."""
        if self.__inner is not None:
            raise RuntimeError("AsyncNode already initialized")
        self.__inner = rclpy.create_node(self.__node_name)

    def __getattr__(self, name: str) -> Any:
        """Delegate protocol members to inner node when not overridden locally."""
        inner = self.__inner
        if (
            inner is not None
            and name in _DELEGATE_NAMES
            and not _is_overridden(type(self), name)
        ):
            return getattr(inner, name)
        if inner is not None and hasattr(inner, name):
            return getattr(inner, name)
        raise AttributeError(name)

    def __getattribute__(self, name: str) -> Any:
        """Attribute access with delegation for Protocol stub members."""
        # Fast-path for private/internal attributes to avoid recursion.
        if name.startswith("_AsyncNode__"):
            return super().__getattribute__(name)

        inner = super().__getattribute__("_AsyncNode__inner")
        # For protocol-defined members not overridden locally, attempt delegation.
        if name in _DELEGATE_NAMES and not _is_overridden(type(self), name):
            if inner is not None and hasattr(inner, name):
                return getattr(inner, name)
            # Fallback to locally stored value if inner doesn't provide it.
            fb = super().__getattribute__("_AsyncNode__fallback_values")
            if name in fb:
                return fb[name]
        return super().__getattribute__(name)

    def __setattr__(self, name: str, value: Any) -> None:
        # Allow normal setting for private / explicitly implemented attributes on AsyncNode itself.
        if (
            name.startswith("_AsyncNode__")
            or name in {"params", "state"}
            or name in type(self).__dict__
        ):
            super().__setattr__(name, value)
            return
        # Delegation path for protocol-defined members not overridden here.
        if name in _DELEGATE_NAMES and not _is_overridden(type(self), name):
            inner = getattr(self, "_AsyncNode__inner", None)
            if inner is not None and hasattr(inner, name):
                setattr(inner, name, value)
                return
            # Store locally when inner lacks the attribute (e.g. protocol stub property).
            fb = getattr(self, "_AsyncNode__fallback_values")
            fb[name] = value
            return
        # Ordinary attribute (not protocol-defined): store on wrapper instance.
        super().__setattr__(name, value)

    def __dir__(self) -> List[str]:
        inner = self.__inner
        names = set(super().__dir__())
        if inner is not None:
            names.update(dir(inner))
        return sorted(names)

    def __repr__(self) -> str:
        return f"<AsyncNode inner={self.__inner!r}>"

    def action(
        self,
        action_type: type,
        action_name: str,
        backpressure_handler: Optional[BackpressureHandlerSpec] = None,
        **kwargs,
    ) -> Callable[
        [Callable[[ServerGoalHandle], Awaitable[Any]]],
        Callable[[ServerGoalHandle], Awaitable[Any]],
    ]:
        """Decorator registering an async action handler."""

        def _decorator(async_fn: Callable[[ServerGoalHandle], Awaitable[Any]]):
            self.__action_handler_specs.append(
                ActionHandlerSpec(
                    action_name=action_name,
                    action_type=action_type,
                    async_fn=async_fn,
                    backpressure_handler=backpressure_handler,
                    kwargs=kwargs,
                )
            )
            return async_fn

        return _decorator

    def service(
        self,
        srv_type: type,
        srv_name: str,
        backpressure_handler: Optional[BackpressureHandlerSpec] = None,
        **kwargs,
    ) -> Callable[[Callable[[Any], Awaitable[None]]], Callable[[Any], Awaitable[None]]]:
        """Decorator registering an async service handler."""

        def _decorator(async_fn: Callable[[Any], Awaitable[None]]):
            self.__service_handler_specs.append(
                ServiceHandlerSpec(
                    async_fn=async_fn,
                    backpressure_handler=backpressure_handler,
                    kwargs=kwargs,
                    srv_name=srv_name,
                    srv_type=srv_type,
                )
            )
            return async_fn

        return _decorator

    def subscription(
        self,
        msg_type: type,
        topic_name: str,
        qos_profile: QoSProfile = 10,
        backpressure_handler: Optional[BackpressureHandlerSpec] = None,
        **kwargs,
    ) -> Callable[[Callable[[Any], Awaitable[None]]], Callable[[Any], Awaitable[None]]]:
        """Decorator registering an async subscription handler."""

        def _decorator(async_fn: Callable[[Any], Awaitable[None]]):
            self.__topic_handler_specs.append(
                TopicHandlerSpec(
                    async_fn=async_fn,
                    backpressure_handler=backpressure_handler,
                    kwargs=kwargs,
                    msg_type=msg_type,
                    qos_profile=qos_profile,
                    topic_name=topic_name,
                )
            )
            return async_fn

        return _decorator

    def timer(
        self,
        timer_period_sec: Union[float, Callable[[], float]],
        backpressure_handler: Optional[BackpressureHandlerSpec] = None,
        **kwargs,
    ) -> Callable[[Callable[[], Awaitable[None]]], Callable[[], Awaitable[None]]]:
        """Decorator registering an async timer handler."""

        def _decorator(async_fn: Callable[[], Awaitable[None]]):
            self.__timer_handler_specs.append(
                TimerHandlerSpec(
                    async_fn=async_fn,
                    backpressure_handler=backpressure_handler,
                    kwargs=kwargs,
                    timer_period_sec=timer_period_sec,
                )
            )
            return async_fn

        return _decorator

    def destroy_node(self) -> None:
        """Ensure underlying node is properly destroyed."""
        self.__exit_stack.close()
        inner = self.__inner
        if inner is not None:
            inner.destroy_node()
            self.__inner = None

    def gather_coroutines(
        self,
    ) -> List[Callable[[], Awaitable[None]]]:
        """Start processing subscription and timer handlers until cancelled."""
        if self.__inner is None:
            raise RuntimeError("AsyncNode not initialized; call initialize() first")

        _attached_consumers = []

        for spec in self.__action_handler_specs:
            handler, coro = _wrap_handler_with_backpressure(
                spec.async_fn, spec.backpressure_handler
            )

            self.__exit_stack.enter_context(
                rclpy_async.action_server(
                    self.__inner,
                    spec.action_type,
                    spec.action_name,
                    handler,
                    **spec.kwargs,
                )
            )

            if coro is not None:
                _attached_consumers.append(coro)

        for spec in self.__service_handler_specs:
            async_fn = spec.async_fn
            srv_type = spec.srv_type
            srv_name = spec.srv_name

            handler, coro = _wrap_handler_with_backpressure(
                async_fn, spec.backpressure_handler
            )
            self.__inner.create_service(
                srv_type,
                srv_name,
                handler,
                **spec.kwargs,
            )

            if coro is not None:
                _attached_consumers.append(coro)

        for spec in self.__topic_handler_specs:
            async_fn = spec.async_fn
            msg_type = spec.msg_type
            topic_name = spec.topic_name
            qos_profile = spec.qos_profile

            handler, coro = _wrap_handler_with_backpressure(
                async_fn, spec.backpressure_handler
            )
            self.__inner.create_subscription(
                msg_type,
                topic_name,
                handler,
                qos_profile=qos_profile,
                **spec.kwargs,
            )

            if coro is not None:
                _attached_consumers.append(coro)

        for spec in self.__timer_handler_specs:
            timer_period_sec = spec.timer_period_sec
            async_fn = spec.async_fn
            if callable(timer_period_sec):
                try:
                    period_value = float(timer_period_sec())
                except Exception:
                    period_value = 1.0
            else:
                period_value = float(timer_period_sec)

            handler, coro = _wrap_handler_with_backpressure(
                async_fn, spec.backpressure_handler
            )
            self.__inner.create_timer(period_value, handler, **spec.kwargs)

            if coro is not None:
                _attached_consumers.append(coro)

        return _attached_consumers


def gather_nodes(*nodes: AsyncNode) -> List[Callable[[], Awaitable[None]]]:
    """Gather coroutines from multiple AsyncNode instances."""
    coroutines = []
    for node in nodes:
        coroutines.extend(node.gather_coroutines())
    return coroutines


async def run(*nodes: AsyncNode) -> None:
    async with anyio.create_task_group() as tg:
        coroutines = gather_nodes(*nodes)
        for consumer_task in coroutines:
            tg.start_soon(consumer_task)

        await anyio.sleep(float("inf"))


def _wrap_handler_with_backpressure(
    async_fn: Callable[..., Awaitable[None]],
    spec: Optional[BackpressureHandlerSpec] = None,
) -> Tuple[Callable[..., None], Callable[[], Awaitable[None]]]:
    """Wrap an async function with a memory object stream for backpressure handling."""

    if spec is None:
        return async_fn, None

    send_stream, receive_stream = anyio.create_memory_object_stream(spec.max_queue_size)

    def _sub_callback(*args, **kwargs):
        try:
            send_stream.send_nowait((args, kwargs))
        except anyio.WouldBlock:
            if spec.max_queue_size == 0:
                return
            if spec.drop_oldest:
                try:
                    _ = receive_stream.receive_nowait()
                except anyio.WouldBlock:
                    return
                try:
                    send_stream.send_nowait((args, kwargs))
                except anyio.WouldBlock:
                    pass

    async def _consumer_task():
        async for args, kwargs in receive_stream:
            await async_fn(*args, **kwargs)

    return _sub_callback, _consumer_task
