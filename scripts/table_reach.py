#!/usr/bin/env python3
"""Table reachability sweep for the 5-DOF arm with the gripper pointing straight down.

Uses the closed-form inverse kinematics from docs/kinematics.md (section 5) and
reports how far from the base axis the tool can reach at a few heights, within
the joint limits. Geometry and limits below mirror my_arm.urdf; keep them in sync
(Phase 3 will read them from the xacro parameters instead).

Usage:
    python3 scripts/table_reach.py
"""
import numpy as np

H = 0.35    # shoulder axis height (m)
L2 = 0.30   # upper arm
L3 = 0.20   # forearm
L4 = 0.11   # wrist pitch joint to tool0
LIMITS_DEG = {"shoulder": 120, "elbow": 135, "wrist_pitch": 90}
MIN_CLEARANCE = 0.05  # elbow and wrist must stay this far above the table (m)


def ik_pointing_down(r, z, lim):
    """Return (q2, q3, q4) in radians reaching (r, z) with the tool pointing down, or None."""
    wr, wz = r, z + L4                       # wrist point is straight above the target
    dr, dz = wr, wz - H
    d = np.hypot(dr, dz)
    if not abs(L2 - L3) <= d <= L2 + L3:
        return None
    c3 = (d * d - L2 * L2 - L3 * L3) / (2 * L2 * L3)
    for sign in (1, -1):                     # elbow up / elbow down
        q3 = sign * np.arccos(np.clip(c3, -1, 1))
        q2 = np.arctan2(dr, dz) - np.arctan2(L3 * np.sin(q3), L2 + L3 * np.cos(q3))
        elbow_z = H + L2 * np.cos(q2)
        for theta in (np.pi, -np.pi):        # "pointing down" can be reached either way round
            q4 = theta - q2 - q3
            if (abs(q2) <= lim["shoulder"] and abs(q3) <= lim["elbow"]
                    and abs(q4) <= lim["wrist_pitch"]
                    and min(elbow_z, wz) >= MIN_CLEARANCE):
                return q2, q3, q4
    return None


def main():
    lim = {k: np.radians(v) for k, v in LIMITS_DEG.items()}
    print(f"Limits: {LIMITS_DEG} deg; gripper pointing straight down\n")
    for z in (0.02, 0.10, 0.20):
        rs = [r for r in np.arange(0.0, 0.65, 0.005) if ik_pointing_down(r, z, lim)]
        band = f"{min(rs):.2f}-{max(rs):.2f} m" if rs else "not reachable"
        print(f"Target height {z:.2f} m: reach {band}")


if __name__ == "__main__":
    main()
