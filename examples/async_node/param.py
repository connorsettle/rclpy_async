import anyio
import rclpy
from rclpy.parameter import Parameter

import rclpy_async
from rclpy_async import AsyncNode, async_run

node = AsyncNode("minimal_param_node")


@node.timer(
    lambda: node.get_parameter("timer_period").get_parameter_value().double_value
)
async def timer_callback():
    node.get_logger().info(
        f"Hello {node.get_parameter('my_parameter').get_parameter_value().string_value}!"
    )
    node.set_parameters(
        [
            Parameter("my_parameter", Parameter.Type.STRING, "world"),
            Parameter(
                "timer_period",
                Parameter.Type.DOUBLE,
                node.get_parameter("timer_period").get_parameter_value().double_value,
            ),
        ]
    )


async def main():
    rclpy.init()
    node.initialize()
    node.declare_parameters(
        namespace="", parameters=[("my_parameter", "world"), ("timer_period", 2.0)]
    )

    async with rclpy_async.start_executor() as xtor:
        xtor.add_node(node)
        await async_run(node)


if __name__ == "__main__":
    anyio.run(main)
