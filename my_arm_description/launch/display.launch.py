"""View the arm in RViz2 and move each joint with sliders.

    ros2 launch my_arm_description display.launch.py
    ros2 launch my_arm_description display.launch.py gui:=false

Data flow:
    joint_state_publisher_gui --/joint_states--> robot_state_publisher --/tf--> RViz2
                                                   (reads the URDF from the
                                                    robot_description parameter)
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg_share = get_package_share_directory("my_arm_description")
    default_model = os.path.join(pkg_share, "urdf", "my_arm.urdf")
    default_rviz = os.path.join(pkg_share, "rviz", "display.rviz")

    model = LaunchConfiguration("model")
    gui = LaunchConfiguration("gui")
    rviz_config = LaunchConfiguration("rviz_config")

    # Run the file through xacro. A plain URDF passes through unchanged, and
    # this is already ready for the xacro version in Phase 3.
    robot_description = ParameterValue(Command(["xacro ", model]), value_type=str)

    return LaunchDescription([
        DeclareLaunchArgument("model", default_value=default_model,
                              description="Path to the URDF or xacro file"),
        DeclareLaunchArgument("gui", default_value="true",
                              description="Show joint sliders"),
        DeclareLaunchArgument("rviz_config", default_value=default_rviz,
                              description="RViz2 config file"),

        # Turns the URDF + current joint angles into TF frames.
        Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            parameters=[{"robot_description": robot_description}],
        ),
        # Publishes /joint_states: sliders if gui:=true, all zeros otherwise.
        Node(
            package="joint_state_publisher_gui",
            executable="joint_state_publisher_gui",
            condition=IfCondition(gui),
        ),
        Node(
            package="joint_state_publisher",
            executable="joint_state_publisher",
            condition=UnlessCondition(gui),
        ),
        Node(
            package="rviz2",
            executable="rviz2",
            arguments=["-d", rviz_config],
            output="screen",
        ),
    ])
