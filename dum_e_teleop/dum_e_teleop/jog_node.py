import rclpy
from rclpy.node import Node
from control_msgs.msg import JointJog
from sensor_msgs.msg import JointState

JOINT_NAMES = [
    "base_yaw_joint",
    "shoulder_pitch_joint",
    "elbow_pitch_joint",
    "wrist_pitch_joint",
    "wrist_roll_joint",
]

DT = 0.02


class JogNode(Node):
    def __init__(self):
        super().__init__("jog_node")
        self.speeds = {}
        self.angles = {}
        for name in JOINT_NAMES:
            self.speeds[name] = 0.0
            self.angles[name] = 0.0
        self.create_subscription(JointJog, "joint_jog", self.on_jog, 10)
        self.publisher = self.create_publisher(JointState, "joint_states", 10)
        self.create_timer(DT, self.on_tick)

    def on_jog(self, msg):
        for name, speed in zip(msg.joint_names, msg.velocities):
            if name in self.speeds:
                self.speeds[name] = speed 
            else:
                self.get_logger().warn(f"unknown joint: {name}")
        self.get_logger().info(f"speeds: {self.speeds}")

    def on_tick(self):
        for name in JOINT_NAMES:
            self.angles[name] = self.angles[name] + self.speeds[name] * DT

        positions = []
        for name in JOINT_NAMES:
            positions.append(self.angles[name])

        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = JOINT_NAMES
        msg.position = positions
        self.publisher.publish(msg)


def main():
    rclpy.init()
    node = JogNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()