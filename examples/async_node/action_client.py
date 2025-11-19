import anyio
import rclpy
from example_interfaces.action import Fibonacci

import rclpy_async
from rclpy_async.async_node import AsyncNode

node = AsyncNode("fibonacci_action_client")


async def main():
    rclpy.init()
    node.initialize()

    async with rclpy_async.start_executor() as xtor:
        xtor.add_node(node)

        with rclpy_async.action_client(node, Fibonacci, "fibonacci") as action_client:
            result = await action_client(
                Fibonacci.Goal(order=10),
                lambda msg: node.get_logger().info(f"Fibonacci feedback: {msg.feedback}"),  # type: ignore
            )
            node.get_logger().info(f"Fibonacci result: {result}")


if __name__ == "__main__":
    anyio.run(main)
