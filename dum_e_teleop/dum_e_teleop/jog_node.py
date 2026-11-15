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
TIMEOUT = 0.5

# Joint limits in radians, copied from my_arm.urdf. Keep them in sync!
LIMITS = {
    "base_yaw_joint": (-3.14159, 3.14159),
    "shoulder_pitch_joint": (-2.0944, 2.0944),
    "elbow_pitch_joint": (-2.3562, 2.3562),
    "wrist_pitch_joint": (-1.5708, 1.5708),
    "wrist_roll_joint": (-1.5708, 1.5708),
}


class JogNode(Node):
    def __init__(self):
        super().__init__("jog_node")
        self.speeds = {}
        self.angles = {}
        for name in JOINT_NAMES:
            self.speeds[name] = 0.0
            self.angles[name] = 0.0
        self.last_jog_time = self.get_clock().now().nanoseconds / 1e9
        self.create_subscription(JointJog, "joint_jog", self.on_jog, 10)
        self.publisher = self.create_publisher(JointState, "joint_states", 10)
        self.create_timer(DT, self.on_tick)

    def on_jog(self, msg):
        self.last_jog_time = self.get_clock().now().nanoseconds / 1e9
        for name, speed in zip(msg.joint_names, msg.velocities):
            if name in self.speeds:
                self.speeds[name] = speed 
            else:
                self.get_logger().warn(f"unknown joint: {name}")
        self.get_logger().info(f"speeds: {self.speeds}")

    def on_tick(self):
        now = self.get_clock().now().nanoseconds / 1e9
        if now - self.last_jog_time > TIMEOUT:
            for name in JOINT_NAMES:
                self.speeds[name] = 0.0
        for name in JOINT_NAMES:
            self.angles[name] = self.angles[name] + self.speeds[name] * DT

            lower, upper = LIMITS[name]
            if self.angles[name] > upper:
                self.angles[name] = upper

            if self.angles[name] < lower:
                self.angles[name] = lower

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