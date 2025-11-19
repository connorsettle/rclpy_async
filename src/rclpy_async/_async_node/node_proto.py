"""Abstract prototype for a ROS 2 Node.

This file intentionally strips all implementation details from the original
`rclpy.node.Node` class and leaves only the public interface shape so it can be
used as a base (InnerProto) for delegation or inheritance without bringing in
ROS graph side-effects. Each method raises NotImplementedError and MUST be
implemented by a concrete subclass or provided via composition.

Only a subset of the original interface is preserved here (the commonly used
APIs). Extend as needed by adding further stubs mirroring upstream signatures.
"""

from __future__ import annotations

from typing import (
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Optional,
    Protocol,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from rcl_interfaces.msg import ParameterDescriptor, ParameterValue, SetParametersResult
from rclpy.callback_groups import CallbackGroup
from rclpy.client import Client
from rclpy.clock import Clock
from rclpy.context import Context
from rclpy.executors import Executor
from rclpy.guard_condition import GuardCondition
from rclpy.impl.rcutils_logger import RcutilsLogger
from rclpy.parameter import Parameter

# ROS 2 interface types (mirroring rclpy.node.Node signatures)
from rclpy.publisher import Publisher
from rclpy.qos import QoSProfile
from rclpy.qos_event import PublisherEventCallbacks, SubscriptionEventCallbacks
from rclpy.qos_overriding_options import QoSOverridingOptions
from rclpy.service import Service
from rclpy.subscription import Subscription
from rclpy.timer import Rate, Timer
from rclpy.topic_endpoint_info import TopicEndpointInfo
from rclpy.waitable import Waitable

# Type variables (kept for signature parity; concrete types resolved in subclasses)
MsgType = TypeVar("MsgType")
SrvType = TypeVar("SrvType")
SrvTypeRequest = TypeVar("SrvTypeRequest")
SrvTypeResponse = TypeVar("SrvTypeResponse")


class NodeProto(Protocol):
    """Structural interface of a ROS 2 node (typing.Protocol).

    This protocol mirrors the public surface actually consumed by wrappers.
    Concrete implementations (e.g. `rclpy.node.Node`) satisfy it implicitly.
    Using a Protocol avoids inheritance side-effects and enables lightweight
    delegation where unimplemented members simply fall through to the inner node.
    """

    # ---- Lifecycle / basic introspection -------------------------------------------------
    def __init__(
        self,
        node_name: str,
        *,
        context: Optional[Any] = None,
        cli_args: Optional[List[str]] = None,
        namespace: Optional[str] = None,
        use_global_arguments: bool = True,
        enable_rosout: bool = True,
        start_parameter_services: bool = True,
        parameter_overrides: Optional[List[Any]] = None,
        allow_undeclared_parameters: bool = False,
        automatically_declare_parameters_from_overrides: bool = False,
    ) -> None: ...

    # ---- Entity collections ---------------------------------------------------------------
    @property
    def publishers(self) -> Iterator[Publisher]: ...

    @property
    def subscriptions(self) -> Iterator[Subscription]: ...

    @property
    def clients(self) -> Iterator[Client]: ...

    @property
    def services(self) -> Iterator[Service]: ...

    @property
    def timers(self) -> Iterator[Timer]: ...

    @property
    def guards(self) -> Iterator[GuardCondition]: ...

    @property
    def waitables(self) -> Iterator[Waitable]: ...

    # ---- Executor linkage -----------------------------------------------------------------
    @property
    def executor(self) -> Optional[Executor]: ...

    @executor.setter
    def executor(self, new_executor: Any) -> None:  # type: ignore[override]
        ...

    # ---- Core properties ------------------------------------------------------------------
    @property
    def context(self) -> Context: ...

    @property
    def default_callback_group(self) -> CallbackGroup: ...

    @property
    def handle(self) -> Any: ...

    @handle.setter
    def handle(self, value: Any) -> None:  # type: ignore[override]
        ...

    # ---- Introspection --------------------------------------------------------------------
    def get_name(self) -> str: ...

    def get_namespace(self) -> str: ...

    def get_clock(self) -> Clock: ...

    def get_logger(self) -> RcutilsLogger: ...

    # ---- Parameters -----------------------------------------------------------------------
    def declare_parameter(
        self,
        name: str,
        value: Any = None,
        descriptor: Optional[ParameterDescriptor] = None,
        ignore_override: bool = False,
    ) -> Parameter: ...

    def declare_parameters(
        self,
        namespace: str,
        parameters: List[
            Union[
                Tuple[str],
                Tuple[str, Parameter.Type],
                Tuple[str, Any, ParameterDescriptor],
            ]
        ],
        ignore_override: bool = False,
    ) -> List[Parameter]: ...

    def undeclare_parameter(self, name: str) -> None: ...

    def has_parameter(self, name: str) -> bool: ...

    def get_parameter_types(self, names: List[str]) -> List[Parameter.Type]: ...

    def get_parameter_type(self, name: str) -> Parameter.Type: ...

    def get_parameters(self, names: List[str]) -> List[Parameter]: ...

    def get_parameter(self, name: str) -> Parameter: ...

    def get_parameter_or(
        self, name: str, alternative_value: Optional[Parameter] = None
    ) -> Parameter: ...

    def get_parameters_by_prefix(
        self,
        prefix: str,
    ) -> Dict[
        str,
        Optional[
            Union[
                bool,
                int,
                float,
                str,
                bytes,
                Sequence[bool],
                Sequence[int],
                Sequence[float],
                Sequence[str],
            ]
        ],
    ]: ...

    def set_parameters(
        self, parameter_list: List[Parameter]
    ) -> List[SetParametersResult]: ...

    def set_parameters_atomically(
        self, parameter_list: List[Parameter]
    ) -> SetParametersResult: ...

    def add_on_set_parameters_callback(
        self, callback: Callable[[List[Parameter]], SetParametersResult]
    ) -> None: ...

    def remove_on_set_parameters_callback(
        self, callback: Callable[[List[Parameter]], SetParametersResult]
    ) -> None: ...

    def describe_parameter(self, name: str) -> ParameterDescriptor: ...

    def describe_parameters(self, names: List[str]) -> List[ParameterDescriptor]: ...

    def set_descriptor(
        self,
        name: str,
        descriptor: ParameterDescriptor,
        alternative_value: Optional[ParameterValue] = None,
    ) -> ParameterValue: ...

    # ---- Name resolution ------------------------------------------------------------------
    def resolve_topic_name(self, topic: str, *, only_expand: bool = False) -> str: ...

    def resolve_service_name(
        self, service: str, *, only_expand: bool = False
    ) -> str: ...

    # ---- Creation of entities -------------------------------------------------------------
    def create_publisher(
        self,
        msg_type: Type[MsgType],
        topic: str,
        qos_profile: Union[QoSProfile, int],
        *,
        callback_group: Optional[CallbackGroup] = None,
        event_callbacks: Optional[PublisherEventCallbacks] = None,
        qos_overriding_options: Optional[QoSOverridingOptions] = None,
        publisher_class: Type[Publisher] = Publisher,
    ) -> Publisher: ...

    def create_subscription(
        self,
        msg_type: Type[MsgType],
        topic: str,
        callback: Callable[[MsgType], None],
        qos_profile: Union[QoSProfile, int],
        *,
        callback_group: Optional[CallbackGroup] = None,
        event_callbacks: Optional[SubscriptionEventCallbacks] = None,
        qos_overriding_options: Optional[QoSOverridingOptions] = None,
        raw: bool = False,
    ) -> Subscription: ...

    def create_client(
        self,
        srv_type: Type[SrvType],
        srv_name: str,
        *,
        qos_profile: QoSProfile = QoSProfile(depth=10),
        callback_group: Optional[CallbackGroup] = None,
    ) -> Client: ...

    def create_service(
        self,
        srv_type: Type[SrvType],
        srv_name: str,
        callback: Callable[[SrvTypeRequest, SrvTypeResponse], SrvTypeResponse],
        *,
        qos_profile: QoSProfile = QoSProfile(depth=10),
        callback_group: Optional[CallbackGroup] = None,
    ) -> Service: ...

    def create_timer(
        self,
        timer_period_sec: float,
        callback: Callable,
        callback_group: Optional[CallbackGroup] = None,
        clock: Optional[Clock] = None,
    ) -> Timer: ...

    def create_guard_condition(
        self,
        callback: Callable,
        callback_group: Optional[CallbackGroup] = None,
    ) -> GuardCondition: ...

    def create_rate(
        self,
        frequency: float,
        clock: Optional[Clock] = None,
    ) -> Rate: ...

    # ---- Destruction of entities ----------------------------------------------------------
    def destroy_publisher(self, publisher: Any) -> bool: ...

    def destroy_subscription(self, subscription: Any) -> bool: ...

    def destroy_client(self, client: Any) -> bool: ...

    def destroy_service(self, service: Any) -> bool: ...

    def destroy_timer(self, timer: Any) -> bool: ...

    def destroy_guard_condition(self, guard: Any) -> bool: ...

    def destroy_rate(self, rate: Any) -> bool: ...

    def destroy_node(self) -> None: ...

    # ---- Discovery / graph introspection --------------------------------------------------
    def get_publisher_names_and_types_by_node(
        self,
        node_name: str,
        node_namespace: str,
        no_demangle: bool = False,
    ) -> List[Tuple[str, List[str]]]: ...

    def get_subscriber_names_and_types_by_node(
        self,
        node_name: str,
        node_namespace: str,
        no_demangle: bool = False,
    ) -> List[Tuple[str, List[str]]]: ...

    def get_service_names_and_types_by_node(
        self,
        node_name: str,
        node_namespace: str,
    ) -> List[Tuple[str, List[str]]]: ...

    def get_client_names_and_types_by_node(
        self,
        node_name: str,
        node_namespace: str,
    ) -> List[Tuple[str, List[str]]]: ...

    def get_topic_names_and_types(
        self, no_demangle: bool = False
    ) -> List[Tuple[str, List[str]]]: ...

    def get_service_names_and_types(self) -> List[Tuple[str, List[str]]]: ...

    def get_node_names(self) -> List[str]: ...

    def get_node_names_and_namespaces(self) -> List[Tuple[str, str]]: ...

    def get_node_names_and_namespaces_with_enclaves(
        self,
    ) -> List[Tuple[str, str, str]]: ...

    def get_fully_qualified_name(self) -> str: ...

    # ---- Counting / endpoint info ---------------------------------------------------------
    def count_publishers(self, topic_name: str) -> int: ...

    def count_subscribers(self, topic_name: str) -> int: ...

    def get_publishers_info_by_topic(
        self,
        topic_name: str,
        no_mangle: bool = False,
    ) -> List[TopicEndpointInfo]: ...

    def get_subscriptions_info_by_topic(
        self,
        topic_name: str,
        no_mangle: bool = False,
    ) -> List[TopicEndpointInfo]: ...

    # ---- Utility --------------------------------------------------------------------------
    def __repr__(self) -> str:  # Helpful debug hook
        return f"<{self.__class__.__name__} (Protocol)>"
