import anyio
import rclpy
from example_interfaces.action import Fibonacci
from rclpy.action.server import ServerGoalHandle

from rclpy_async.async_node import AsyncNode

node = AsyncNode("fibonacci_action_server_node")


@node.action(Fibonacci, "fibonacci")
async def execute_callback(goal_handle: ServerGoalHandle):
    node.get_logger().info("Executing goal...")

    feedback_msg = Fibonacci.Feedback()
    feedback_msg.sequence = [0, 1]

    for i in range(1, goal_handle.request.order):
        feedback_msg.sequence.append(
            feedback_msg.sequence[i] + feedback_msg.sequence[i - 1]
        )
        node.get_logger().info("Feedback: {0}".format(feedback_msg.sequence))
        goal_handle.publish_feedback(feedback_msg)
        await anyio.sleep(1)

    goal_handle.succeed()

    result = Fibonacci.Result()
    result.sequence = feedback_msg.sequence
    return result


async def main():
    rclpy.init()
    node.initialize()

    await node.spin_one()


if __name__ == "__main__":
    anyio.run(main)
