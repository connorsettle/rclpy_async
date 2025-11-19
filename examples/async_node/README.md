# Async Node samples

The following samples are based off the ROS2 documented [tutorials](https://docs.ros.org/en/humble/Tutorials.html).

## Usage

*All scripts assume terminals are open in the root of this repository and have installed `rclpy_async`*

A simple publisher and subscriber:
```sh
# Terminal 1:
python3 ./examples/async_node/subscriber.py

# Terminal 2:
python3 ./examples/async_node/publisher.py
```

A simple service and client:
```sh
# Terminal 1:
python3 ./examples/async_node/service.py

# Terminal 2:
python3 ./examples/async_node/client.py 1 2
```

Using parameters in a class:
```sh
# Start the node
python3 ./examples/async_node/param.py
# [Optionally] start the node with the parameter as something other that "world" by adding:
python3 ./examples/async_node/param.py --ros-args -p my_parameter:=world2

# In another terminal set the parameter again
ros2 param set /minimal_param_node my_parameter earth
```

An action server and client:
```sh
# Terminal 1:
python3 ./examples/async_node/action_server.py

# Terminal 2:
python3 ./examples/async_node/action_client.py
```
