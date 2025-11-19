import anyio
import rclpy

from rclpy_async.async_node import AsyncNode
from rclpy.parameter import Parameter



node = AsyncNode("minimal_param_node")


@node.timer(lambda: node.get_parameter("timer_period").get_parameter_value().double_value)
async def timer_callback():
    node.get_logger().info(f"Hello {node.get_parameter('my_parameter').get_parameter_value().string_value}!")
    node.set_parameters([
        Parameter(
            "my_parameter",
            Parameter.Type.STRING,
            "world"
        ),
        Parameter(
            "timer_period",
            Parameter.Type.DOUBLE,
            node.get_parameter("timer_period").get_parameter_value().double_value,
        )
    ])

async def main():
    rclpy.init()
    node.initialize()
    node.declare_parameters(namespace="", parameters=[('my_parameter', 'world'), ('timer_period', 2.0)])

    await node.spin_one()


if __name__ == "__main__":
    anyio.run(main)
