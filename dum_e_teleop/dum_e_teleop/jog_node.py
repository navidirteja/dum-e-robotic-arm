import rclpy
from rclpy.node import Node
from control_msgs.msg import JointJog

JOINT_NAMES = [
    "base_yaw_joint",
    "shoulder_pitch_joint",
    "elbow_pitch_joint",
    "wrist_pitch_joint",
    "wrist_roll_joint",
]


class JogNode(Node):
    def __init__(self):
        super().__init__("jog_node")
        self.speeds = {}
        for name in JOINT_NAMES:
            self.speeds[name] = 0.0
        self.create_subscription(JointJog, "joint_jog", self.on_jog, 10)

    def on_jog(self, msg):
        for name, speed in zip(msg.joint_names, msg.velocities):
            if name in self.speeds:
                self.speeds[name] = speed 
            else:
                self.get_logger().warn(f"unknown joint: {name}")
        self.get_logger().info(f"speeds: {self.speeds}")


def main():
    rclpy.init()
    node = JogNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()