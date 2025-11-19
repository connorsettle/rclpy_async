# Async Node samples

The following samples are based off the ROS2 documented [tutorials](https://docs.ros.org/en/humble/Tutorials.html).

## Usage

*All scripts assume terminals are open in the root of this repository and have installed `rclpy_async`*

A simple publisher and subscriber:
```sh
# Terminal 1:
python3 -m examples.async_node.subscriber

# Terminal 2:
python3 -m examples.async_node.publisher
```

A simple service and client:
```sh
# Terminal 1:
python3 -m examples.async_node.service

# Terminal 2:
python3 -m examples.async_node.client 1 2
```

Using parameters in a class:
```sh
# Start the node
python3 -m examples.async_node.param
# [Optionally] start the node with the parameter as something other that "world" by adding:
python3 -m examples.async_node.param --ros-args -p my_parameter:=world2

# In another terminal set the parameter again
ros2 param set /minimal_param_node my_parameter earth
```

An action server and client:
```sh
# Terminal 1:
python3 -m examples.async_node.action_server

# Terminal 2:
python3 -m examples.async_node.action_client
```
