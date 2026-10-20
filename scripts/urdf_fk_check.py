#!/usr/bin/env python3
"""Independent forward-kinematics check for a serial-chain URDF.

Reads the URDF directly (no ROS needed), chains each joint's origin and
rotation, and reports:
  * the tool-frame position for a few test poses
  * whether moving only the last joint moves the tool tip (a true roll should not)
  * the rank of the full 6 x n geometric Jacobian: it should equal the number
    of joints; a lower rank means two joints duplicate each other's motion
  * the rank of the 3 x n position Jacobian (rank < 3 = singular pose)

Usage:
    python3 scripts/urdf_fk_check.py my_arm_description/urdf/my_arm.urdf
"""
import sys
import xml.etree.ElementTree as ET

import numpy as np
from scipy.spatial.transform import Rotation

MOVING = ("revolute", "continuous")


def parse_vec(text, default="0 0 0"):
    return np.array([float(v) for v in (text or default).split()])


def load_chain(path):
    """Return joints in parent-to-child order as (name, type, T_origin, axis, limits)."""
    root = ET.parse(path).getroot()
    by_parent = {}
    for j in root.findall("joint"):
        origin = j.find("origin")
        T = np.eye(4)
        T[:3, :3] = Rotation.from_euler(
            "xyz", parse_vec(origin.get("rpy") if origin is not None else None)).as_matrix()
        T[:3, 3] = parse_vec(origin.get("xyz") if origin is not None else None)
        axis_el = j.find("axis")
        axis = parse_vec(axis_el.get("xyz") if axis_el is not None else "1 0 0")
        lim = j.find("limit")
        limits = (float(lim.get("lower")), float(lim.get("upper"))) if lim is not None else None
        by_parent[j.find("parent").get("link")] = (
            j.get("name"), j.get("type"), T, axis, limits, j.find("child").get("link"))
    children = {v[5] for v in by_parent.values()}
    link = next(p for p in by_parent if p not in children)  # root link
    chain = []
    while link in by_parent:
        *joint, link = by_parent[link]
        chain.append(tuple(joint))
    return chain, link  # link is now the tip frame


def forward(chain, q):
    """Return tip position and, for each moving joint, (world axis, world position)."""
    T = np.eye(4)
    qi = 0
    joints = []
    for _, jtype, T_origin, axis, _ in chain:
        T = T @ T_origin
        if jtype in MOVING:
            joints.append((T[:3, :3] @ axis, T[:3, 3].copy()))
            Rq = np.eye(4)
            Rq[:3, :3] = Rotation.from_rotvec(axis * q[qi]).as_matrix()
            T = T @ Rq
            qi += 1
    return T[:3, 3], joints


def geometric_jacobian(chain, q):
    """6 x n Jacobian: top rows = tip linear velocity, bottom rows = angular velocity."""
    tip, joints = forward(chain, q)
    return np.column_stack([np.r_[np.cross(z, tip - p), z] for z, p in joints])


def rank(M, tol=1e-6):
    return int(np.sum(np.linalg.svd(M, compute_uv=False) > tol))


def main(path):
    np.set_printoptions(precision=3, suppress=True)
    chain, tip = load_chain(path)
    moving = [j for j in chain if j[1] in MOVING]
    n = len(moving)
    print(f"Chain ({n} DOF, tip frame '{tip}'):")
    for name, jtype, T, axis, lim in chain:
        lim_txt = f"[{np.degrees(lim[0]):.0f}, {np.degrees(lim[1]):.0f}] deg" if lim else ""
        print(f"  {name:<22} {jtype:<9} axis {axis}  origin {T[:3, 3]}  {lim_txt}")

    rng = np.random.default_rng(0)
    lows = np.array([j[4][0] for j in moving])
    highs = np.array([j[4][1] for j in moving])
    poses = [np.zeros(n), rng.uniform(lows, highs) * 0.6]

    print()
    for q in poses:
        print(f"q = {q}  ->  {tip} at {forward(chain, q)[0]} m")

    q = poses[1]
    q_rolled = q.copy()
    q_rolled[-1] += 0.6
    drift = np.linalg.norm(forward(chain, q_rolled)[0] - forward(chain, q)[0])
    print(f"\nTip displacement when only the last joint moves 0.6 rad: {drift * 100:.2f} cm")

    for q in poses:
        J = geometric_jacobian(chain, q)
        print(f"At q = {q}: full Jacobian rank {rank(J)}/{min(6, n)}, "
              f"position Jacobian rank {rank(J[:3])}/3")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
