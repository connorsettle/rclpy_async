import anyio
import rclpy
from std_msgs.msg import String

from rclpy_async.async_node import AsyncNode

node = AsyncNode("minimal_publisher")


@node.timer(0.5)
async def timer_callback():
    msg = String()
    msg.data = "Hello World: %d" % node.state.i
    node.state.publisher_.publish(msg)
    node.get_logger().info('Publishing: "%s"' % msg.data)
    node.state.i += 1


async def main():
    rclpy.init()
    node.initialize()

    node.state.i = 0
    node.state.publisher_ = node.create_publisher(String, "topic", 10)

    await node.spin_one()


if __name__ == "__main__":
    anyio.run(main)
