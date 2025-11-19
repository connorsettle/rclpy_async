import sys

import anyio
import rclpy
from example_interfaces.srv import AddTwoInts

import rclpy_async
from rclpy_async.async_node import AsyncNode

node = AsyncNode("minimal_client_async")


async def main():
    rclpy.init()
    node.initialize()

    async with rclpy_async.start_executor() as executor:
        executor.add_node(node)
        with rclpy_async.service_client(
            node,
            AddTwoInts,
            "add_two_ints",
        ) as cli:
            req = AddTwoInts.Request()
            req.a = int(sys.argv[1])
            req.b = int(sys.argv[2])
            response = await cli(req)
            node.get_logger().info(
                "Result of add_two_ints: for %d + %d = %d"
                % (int(sys.argv[1]), int(sys.argv[2]), response.sum)
            )


if __name__ == "__main__":
    anyio.run(main)
