import anyio
import rclpy
from std_msgs.msg import String

import rclpy_async
from rclpy_async import AsyncNode, BackpressureHandlerSpec

node = AsyncNode("minimal_subscriber")


@node.subscription(
    String,
    "topic",
    backpressure_handler=BackpressureHandlerSpec(max_queue_size=5, drop_oldest=True),
)
async def listener_callback(msg: String):
    node.get_logger().info('I heard: "%s"' % msg.data)


async def main():
    rclpy.init()
    node.initialize()

    async with rclpy_async.start_executor() as xtor:
        xtor.add_node(node)
        await rclpy_async.async_run(node)


if __name__ == "__main__":
    anyio.run(main)
