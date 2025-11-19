import anyio
import rclpy
from dataclasses import dataclass

from rclpy_async.async_node import AsyncNode, ParameterSchema


@dataclass
class NodeParameters(ParameterSchema):
    my_parameter: str = "world"


node = AsyncNode("minimal_param_node", NodeParameters)


@node.timer(0.5)
async def timer_callback():
    # Read current value from ROS parameter server (dynamic) and then update it.
    node.get_logger().info(f"Hello {node.params.my_parameter}!")
    node.params.my_parameter = "world"


async def main():
    rclpy.init()
    node.initialize()

    await node.spin_one()


if __name__ == "__main__":
    anyio.run(main)
