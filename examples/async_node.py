"""AsyncNode example demonstrating parameter schema, subscription, and timer.

This example shows how to:
1. Define a `ParameterSchema` (here `NodeParameters`) to declare and retrieve ROS 2
    parameters via the `AsyncNode` abstraction.
2. Register an asynchronous subscription handler using `@node.subscription` that
    logs incoming `std_msgs/msg/String` messages on the `chatter` topic.
3. Register an asynchronous timer via `@node.timer`, whose period is computed
    dynamically from declared parameters, publishing incrementing counter messages
    on the `timer_event` topic.
4. Use `node.state` for mutable runtime state shared across handlers (counter and
    publisher reference).

Run this file and in another shell publish test data:
     ros2 topic pub /chatter std_msgs/msg/String '{data: "Hello World"}' --once
Observe timer events:
     ros2 topic echo /timer_event std_msgs/msg/String
"""

from dataclasses import dataclass

import anyio
import rclpy
from std_msgs.msg import String

from rclpy_async.async_node import AsyncNode, ParameterSchema


@dataclass
class NodeParameters(ParameterSchema):
    timed_event_counter: int = 0
    timed_event_periodicity: float = 2.0


node = AsyncNode("mynode", NodeParameters)


@node.subscription(String, "chatter")
async def chatter_callback(msg):
    node.get_logger().info(f"I heard: {msg.data}")


@node.timer(lambda params: params.timed_event_periodicity)
async def timer_callback():
    msg = String(data=f"Timer event {node.state.timed_event_counter}")
    node.state.timed_event_counter += 1
    node.state.publisher_.publish(msg)


async def main():
    rclpy.init()
    node.initialize()

    node.state.timed_event_counter = node.params.timed_event_counter
    node.state.publisher_ = node.create_publisher(String, "timer_event", 10)

    print(
        "Node started. Listening on 'chatter' and publishing to 'timer_event'.\n"
        + "To test, you can publish messages using:\n"
        + "\tros2 topic pub /chatter std_msgs/msg/String '{data: \"Hello World\"}' --once\n"
        + "You should see the messages printed.\n"
        + "To see the published messages, you can subscribe using:\n"
        + "\tros2 topic echo /timer_event std_msgs/msg/String\n"
        + "Press Ctrl+C to stop the node.\n"
    )
    await node.spin_one()


anyio.run(main)
