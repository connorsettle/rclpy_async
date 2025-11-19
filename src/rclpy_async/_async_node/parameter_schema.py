from abc import ABC
from dataclasses import fields, is_dataclass
from typing import Any, List, Optional, Tuple

from rcl_interfaces.msg import ParameterValue
from rclpy.node import Node
from rclpy.parameter import Parameter


class ParameterSchema(ABC):
    """Base class enabling dynamic ROS 2 parameter get/set with strong typing.

    Subclasses should be declared as dataclasses. Field names and default values are
    used to declare parameters. When attached to a node, attribute reads reflect the
    current parameter value in the node and writes propagate through `set_parameters`.
    """

    _node: Optional[Node] = None
    _dynamic: bool = False

    # --- Declaration helpers -------------------------------------------------
    @classmethod
    def as_parameters(cls) -> List[Tuple[str, Any]]:
        if not is_dataclass(cls):
            raise TypeError("ParameterSchema subclasses must be dataclasses")
        params: List[Tuple[str, Any]] = []
        for f in fields(cls):
            params.append((f.name, getattr(cls, f.name)))
        return params

    @classmethod
    def from_node(cls, node: Node) -> "ParameterSchema":
        if not is_dataclass(cls):
            raise TypeError("ParameterSchema subclasses must be dataclasses")
        values: dict[str, Any] = {}
        for f in fields(cls):
            try:
                values[f.name] = _parameter_value_to_python(
                    node.get_parameter(f.name).get_parameter_value()
                )
            except Exception:
                values[f.name] = getattr(cls, f.name)
        obj = cls(**values)
        obj._dynamic = True
        obj._node = node
        return obj

    # --- Internal helpers ----------------------------------------------------
    def _get_parameter(self, name: str) -> ParameterValue:
        if not self._dynamic or self._node is None:
            raise RuntimeError("Schema not attached to node")
        return self._node.get_parameter(name).get_parameter_value()

    def _set_parameters(self, parameters: List[Parameter]) -> None:
        if not self._dynamic or self._node is None:
            raise RuntimeError("Schema not attached to node")
        self._node.set_parameters(parameters)

    def __getattribute__(self, name: str) -> Any:
        # Intercept dataclass field reads when dynamic.
        dynamic: bool = object.__getattribute__(self, "_dynamic")
        node: Node = object.__getattribute__(self, "_node")

        if (
            dynamic
            and node is not None
            and name in getattr(type(self), "__dataclass_fields__", {})
        ):
            try:
                pv = node.get_parameter(name).get_parameter_value()
                return _parameter_value_to_python(pv)
            except Exception:
                pass
        return object.__getattribute__(self, name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_") or name in {"_node", "_dynamic"}:
            object.__setattr__(self, name, value)
            return
        if (
            self._dynamic
            and self._node is not None
            and name in getattr(type(self), "__dataclass_fields__", {})
        ):
            self._node.set_parameters(
                [Parameter(name, _python_value_to_param_type(value), value)]
            )
        object.__setattr__(self, name, value)


def _parameter_value_to_python(pv: ParameterValue) -> Any:
    t = Parameter.Type(pv.type)
    if t == Parameter.Type.NOT_SET:
        return None
    if t == Parameter.Type.BOOL:
        return pv.bool_value
    if t == Parameter.Type.INTEGER:
        return pv.integer_value
    if t == Parameter.Type.DOUBLE:
        return pv.double_value
    if t == Parameter.Type.STRING:
        return pv.string_value
    if t == Parameter.Type.BOOL_ARRAY:
        return list(pv.bool_array_value)
    if t == Parameter.Type.INTEGER_ARRAY:
        return list(pv.integer_array_value)
    if t == Parameter.Type.DOUBLE_ARRAY:
        return list(pv.double_array_value)
    if t == Parameter.Type.STRING_ARRAY:
        return list(pv.string_array_value)
    return None


def _python_value_to_param_type(value: Any) -> int:
    if isinstance(value, bool):
        return Parameter.Type.BOOL
    if isinstance(value, int) and not isinstance(value, bool):
        return Parameter.Type.INTEGER
    if isinstance(value, float):
        return Parameter.Type.DOUBLE
    if isinstance(value, str):
        return Parameter.Type.STRING
    if isinstance(value, (list, tuple)):
        if all(isinstance(v, bool) for v in value):
            return Parameter.Type.BOOL_ARRAY
        if all(isinstance(v, int) and not isinstance(v, bool) for v in value):
            return Parameter.Type.INTEGER_ARRAY
        if all(isinstance(v, float) for v in value):
            return Parameter.Type.DOUBLE_ARRAY
        if all(isinstance(v, str) for v in value):
            return Parameter.Type.STRING_ARRAY
    raise TypeError(f"Unsupported parameter value type for {value!r}")
