import anyio
import rclpy
from std_msgs.msg import String

from rclpy_async.async_node import AsyncNode

node = AsyncNode("minimal_subscriber")


@node.subscription(String, "topic")
async def listener_callback(msg: String):
    node.get_logger().info('I heard: "%s"' % msg.data)


async def main():
    rclpy.init()
    node.initialize()

    await node.spin_one()


if __name__ == "__main__":
    anyio.run(main)
