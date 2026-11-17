import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.substitutions import Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg_share = get_package_share_directory("my_arm_description")
    model = os.path.join(pkg_share, "urdf", "my_arm.urdf")
    rviz_config = os.path.join(pkg_share, "rviz", "display.rviz")
    robot_description = ParameterValue(Command(["xacro ", model]), value_type=str)

    return LaunchDescription([
        Node(
            package="dum_e_teleop",
            executable="jog_node",
            output="screen",        
        ),
        Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            parameters=[{"robot_description": robot_description}],
        ),
        Node(
            package="rviz2",
            executable="rviz2",
            arguments=["-d", rviz_config],
            output="screen",
        ),
        Node(
            package="rosbridge_server",
            executable="rosbridge_websocket",
            output="screen",
        ),
        Node(
            package="rosapi",
            executable="rosapi_node",
        ),
    ])