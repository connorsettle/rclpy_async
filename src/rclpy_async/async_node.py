import inspect
from dataclasses import dataclass
from typing import (
    Any,
    Awaitable,
    Callable,
    Generic,
    List,
    Optional,
    Type,
    TypeVar,
    Union,
)

import anyio
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile

import rclpy_async

from ._node_proto import NodeProto

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
    async_fn: Callable[[Any], Awaitable[None]]


TParams = TypeVar("TParams")


@dataclass
class TimerHandlerSpec(Generic[TParams]):
    """Specification for a timer handler.

    async_fn signature: () -> Awaitable[None]
    timer_period_sec may be float or a callable taking params -> float.
    """

    timer_period_sec: Union[float, Callable[[TParams], float]]
    max_queue_size: int
    drop_oldest: bool
    async_fn: Callable[[], Awaitable[None]]


class State:
    """
    An object that can be used to store arbitrary state.

    Used for `request.state` and `app.state`.
    """

    _state: dict[str, Any]

    def __init__(self, state: dict[str, Any] | None = None):
        if state is None:
            state = {}
        super().__setattr__("_state", state)

    def __setattr__(self, key: Any, value: Any) -> None:
        self._state[key] = value

    def __getattr__(self, key: Any) -> Any:
        try:
            return self._state[key]
        except KeyError:
            message = "'{}' object has no attribute '{}'"
            raise AttributeError(message.format(self.__class__.__name__, key))

    def __delattr__(self, key: Any) -> None:
        del self._state[key]


class AsyncNode(NodeProto):
    """Asynchronous wrapper around a ROS 2 `Node` using dynamic delegation.

    Delegates all protocol-defined attributes/methods to `__inner` unless overridden.
    Provides decorators for subscription and timer handlers executed with anyio.
    """

    __inner: Optional[Node] = None  # Underlying rclpy Node instance
    __node_name: str
    __params_type: Optional[Type[TParams]]
    __timer_handler_specs: List[TimerHandlerSpec[TParams]] = []
    __topic_handler_specs: List[TopicHandlerSpec] = []
    params: Optional[TParams] = None
    state = State()  # Arbitrary user state container

    def __init__(self, node_name: str, params_type: Type[TParams] = None):
        self.__node_name = node_name
        self.__params_type = params_type  # Parameter schema type or None

    @property
    def inner(self) -> Optional[Node]:
        """Return underlying `Node` (read-only reference)."""
        return self.__inner

    def initialize(self, **kwargs) -> None:
        """Create underlying rclpy Node and declare parameters if a schema is provided."""
        if self.__inner is not None:
            raise RuntimeError("AsyncNode already initialized")
        self.__inner = rclpy.create_node(self.__node_name)

        if self.__params_type is not None:
            self.__inner.declare_parameters(
                namespace=(
                    kwargs.get("namespace")
                    if kwargs.get("namespace", None) is not None
                    else ""
                ),
                parameters=self.__params_type.as_parameters(),
            )

            self.params = self.__params_type.from_parameters(self.__inner.get_parameter)
            self.__inner.get_logger().info(f"PubSub parameters: {self.params}")

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
        # Delegate protocol-defined members unless overridden in AsyncNode.
        if (
            inner is not None
            and name in _DELEGATE_NAMES
            and not _is_overridden(type(self), name)
        ):
            return getattr(inner, name)
        return super().__getattribute__(name)

    def __setattr__(self, name: str, value: Any) -> None:
        # Allow normal setting for our private / known attributes.
        if (
            name.startswith("_AsyncNode__")
            or name in {"params", "state"}
            or hasattr(type(self), name)
        ):
            super().__setattr__(name, value)
            return
        inner = getattr(self, "_AsyncNode__inner", None)
        if inner is not None and hasattr(inner, name):
            setattr(inner, name, value)
        else:
            super().__setattr__(name, value)

    def __dir__(self) -> List[str]:
        inner = self.__inner
        names = set(super().__dir__())
        if inner is not None:
            names.update(dir(inner))
        return sorted(names)

    def __repr__(self) -> str:
        return f"<AsyncNode name={self.__node_name} inner={self.__inner!r}>"

    def subscription(
        self,
        msg_type: type,
        topic_name: str,
        qos_profile: QoSProfile = 10,
        max_queue_size: int = 0,
        drop_oldest: bool = False,
    ) -> Callable[[Callable[[Any], Awaitable[None]]], Callable[[Any], Awaitable[None]]]:
        """Decorator registering an async subscription handler."""

        def _decorator(async_fn: Callable[[Any], Awaitable[None]]):
            spec = TopicHandlerSpec(
                msg_type=msg_type,
                topic_name=topic_name,
                qos_profile=qos_profile,
                max_queue_size=max_queue_size,
                drop_oldest=drop_oldest,
                async_fn=async_fn,
            )
            self.__topic_handler_specs.append(spec)
            return async_fn

        return _decorator

    def timer(
        self,
        timer_period_sec: Union[float, Callable[[TParams], float]],
        max_queue_size: int = 0,
        drop_oldest: bool = False,
    ) -> Callable[[Callable[[], Awaitable[None]]], Callable[[], Awaitable[None]]]:
        """Decorator registering an async timer handler."""

        def _decorator(async_fn: Callable[[], Awaitable[None]]):
            spec = TimerHandlerSpec(
                timer_period_sec=timer_period_sec,
                max_queue_size=max_queue_size,
                drop_oldest=drop_oldest,
                async_fn=async_fn,
            )
            self.__timer_handler_specs.append(spec)
            return async_fn

        return _decorator

    async def spin(self) -> None:
        """Start processing subscription and timer handlers until cancelled."""
        if self.__inner is None:
            raise RuntimeError("AsyncNode not initialized; call initialize() first")

        async with anyio.create_task_group() as tg:
            _attached_consumers = []

            for spec in self.__topic_handler_specs:
                async_fn = spec.async_fn  # expects (ctx, msg)
                msg_type = spec.msg_type
                topic_name = spec.topic_name
                qos_profile = spec.qos_profile
                max_queue_size = spec.max_queue_size
                drop_oldest = spec.drop_oldest

                send_stream, receive_stream = anyio.create_memory_object_stream(
                    max_queue_size
                )

                def _sub_callback(msg, *, _send=send_stream, _recv=receive_stream):
                    try:
                        _send.send_nowait(msg)
                    except anyio.WouldBlock:
                        if max_queue_size == 0:
                            return
                        if drop_oldest:
                            try:
                                _ = _recv.receive_nowait()
                            except anyio.WouldBlock:
                                return
                            try:
                                _send.send_nowait(msg)
                            except anyio.WouldBlock:
                                pass

                self.__inner.create_subscription(
                    msg_type, topic_name, _sub_callback, qos_profile=qos_profile
                )

                async def _consumer_task(fn=async_fn, _recv=receive_stream):
                    async for _msg in _recv:
                        await fn(_msg)

                _attached_consumers.append(_consumer_task)

            for spec in self.__timer_handler_specs:
                async_fn = spec.async_fn  # expects (ctx)
                timer_period_sec = spec.timer_period_sec
                if callable(timer_period_sec):
                    try:
                        period_value = float(timer_period_sec(self.params))
                    except Exception:
                        period_value = 1.0
                else:
                    period_value = float(timer_period_sec)
                max_queue_size = spec.max_queue_size
                drop_oldest = spec.drop_oldest

                send_stream, receive_stream = anyio.create_memory_object_stream(
                    max_queue_size
                )

                def _timer_callback(_send=send_stream, _recv=receive_stream):
                    try:
                        _send.send_nowait(None)
                    except anyio.WouldBlock:
                        if max_queue_size == 0:
                            return
                        if drop_oldest:
                            try:
                                _ = _recv.receive_nowait()
                            except anyio.WouldBlock:
                                return
                            try:
                                _send.send_nowait(None)
                            except anyio.WouldBlock:
                                pass

                self.__inner.create_timer(period_value, _timer_callback)

                async def _consumer_task(fn=async_fn, _recv=receive_stream):
                    async for _ in _recv:
                        await fn()

                _attached_consumers.append(_consumer_task)

            for consumer_task in _attached_consumers:
                tg.start_soon(consumer_task)

            # Sleep forever; cancellation of the task group stops processing.
            await anyio.sleep(float("inf"))

    async def spin_one(self) -> None:
        """Run a single executor managing this node and spin handlers concurrently."""
        if self.__inner is None:
            raise RuntimeError("AsyncNode not initialized; call initialize() first")
        async with rclpy_async.start_executor() as xtor:
            xtor.add_node(self.__inner)
            await self.spin()
