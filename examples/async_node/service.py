import anyio
import rclpy
from example_interfaces.srv import AddTwoInts

from rclpy_async.async_node import AsyncNode

node = AsyncNode("minimal_service")


@node.service(AddTwoInts, "add_two_ints")
async def add_two_ints_callback(request, response):
    response.sum = request.a + request.b
    node.get_logger().info("Incoming request \ta: %d b: %d" % (request.a, request.b))

    return response


async def main():
    rclpy.init()
    node.initialize()

    await node.spin_one()


if __name__ == "__main__":
    anyio.run(main)
