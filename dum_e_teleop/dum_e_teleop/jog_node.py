import rclpy
from rclpy.node import Node
from control_msgs.msg import JointJog


class JogNode(Node):
    def __init__(self):
        super().__init__("jog_node")
        self.create_subscription(JointJog, "joint_jog", self.on_jog, 10)

    def on_jog(self, msg):
        self.get_logger().info(f"got {msg.joint_names} at {msg.velocities}")


def main():
    rclpy.init()
    node = JogNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()