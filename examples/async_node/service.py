import anyio
import rclpy
from example_interfaces.srv import AddTwoInts

import rclpy_async
from rclpy_async import AsyncNode, async_run

node = AsyncNode("minimal_service")


@node.service(AddTwoInts, "add_two_ints")
async def add_two_ints_callback(request, response):
    response.sum = request.a + request.b
    node.get_logger().info("Incoming request \ta: %d b: %d" % (request.a, request.b))

    return response


async def main():
    rclpy.init()
    node.initialize()

    async with rclpy_async.start_executor() as xtor:
        xtor.add_node(node)
        await async_run(node)


if __name__ == "__main__":
    anyio.run(main)
