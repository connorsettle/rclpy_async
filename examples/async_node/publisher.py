import anyio
import rclpy
import rclpy_async
from rclpy_async import AsyncNode, async_run
from std_msgs.msg import String

node = AsyncNode("minimal_publisher")


@node.timer(0.5)
async def timer_callback():
    msg = String(data="Hello World: %d" % node.state.i)
    node.state.publisher_.publish(msg)
    node.get_logger().info('Publishing: "%s"' % msg.data)
    node.state.i += 1


async def main():
    rclpy.init()
    node.initialize()

    node.state.i = 0
    node.state.publisher_ = node.create_publisher(String, "topic", 10)

    async with rclpy_async.start_executor() as xtor:
        xtor.add_node(node)
        await async_run(node)


if __name__ == "__main__":
    anyio.run(main)
