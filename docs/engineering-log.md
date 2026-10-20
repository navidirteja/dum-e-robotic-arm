# Engineering Log

A dated record of the project: what was done, what went wrong, how it was found, and what I learned. Newest entries at the bottom.

Each entry has a **Reflection** section written in my own words.

---

## Phase 1 — Digital model and ROS 2 package
**Date:** July 2026

### Done
- Wrote the first URDF (`my_arm.urdf`) for a 4-DOF arm: base yaw, shoulder pitch, elbow pitch, wrist roll. Links are simple primitives (cylinders and a box) so the kinematics could be checked before any CAD meshes exist.
- Planned the `my_arm_description` ROS 2 package (`ament_cmake`) and a `display.launch.py` that starts `robot_state_publisher` (turns the URDF plus joint angles into TF frames), `joint_state_publisher_gui` (sliders for each joint) and RViz2. (These package files turned out to be missing from the development machine and were recreated on 2026-10-21; see Phase 2c.)

### Reflection
<!-- TODO: in your own words. What did you understand about how robot_state_publisher, joint states and TF fit together? What confused you at first? -->

---

## Phase 2 — URDF audit against ROS conventions
**Date:** 2026-10-21

### Goal
Check the joint-link tree against REP-103 (X forward, Y left, Z up) *before* MoveIt 2 configuration, because MoveIt's IK, collision checking and controllers are all built on top of these frames. A frame error found later is much more expensive to fix.

### What was already correct
- Single root (`base_link`) and a strict serial chain.
- Every joint origin uses `rpy="0 0 0"`, so at zero pose every frame is aligned with `base_link` and joint axes can be read directly (`0 0 1` = yaw, `0 1 0` = pitch).

### Bugs found

**1. The "wrist roll" joint was actually a sideways tilt.**
The wrist axis was `1 0 0` (X). Because frames are aligned, local X is a horizontal axis, but the forearm points along Z. So the joint tilted the wrist instead of twisting it.
*How it was found:* a forward-kinematics script (`scripts/urdf_fk_check.py`) moved only the wrist by 0.6 rad. The tool tip moved 2.8 cm sideways; a true roll about the tool's own axis must leave the tip fixed.
*Fix:* axis changed to `0 0 1`. Re-running the script shows zero tip displacement during roll.

**2. `base_link` origin was in the middle of the base plate.**
URDF cylinders are centred on their origin, so half the plate was below z = 0. Convention puts `base_link` at the mounting surface, so a table in the planning scene sits at z = 0.
*Fix:* plate visual shifted up 2.5 cm; joint 1 origin moved to z = 0.05.

### Gaps filled
- Added a fixed `tool0` frame at the tool-mount face, as the planning tip for MoveIt.
- Added `<collision>` geometry to every link (without it, MoveIt cannot detect self-collision).
- Added placeholder `<inertial>` data to moving links (to be replaced with real masses). Left the fixed root link without inertia, which avoids a KDL warning.
- Wrote limits as exact π and π/2 instead of 3.14 and 1.57.

### Finding: the zero pose is singular
At zero the arm is fully stretched and its tip lies on the base yaw axis. The position Jacobian there has rank 1: base yaw does not move the tip, and shoulder and elbow move it in the same direction. Straight-up is still a good *homing* pose, but motion planning should start from a bent "ready" pose.

### Open design question
Yaw + 2 pitch + roll can place the tool anywhere in reach but cannot choose the angle it arrives at. A yaw + 3 pitch layout (adding wrist pitch) can. See ADR-007 in [design-decisions.md](design-decisions.md).

### Reflection
<!-- TODO: in your own words. e.g. why a visual check in RViz did not catch the wrist bug, but a numerical check did. -->

---

## Phase 2b — Redesign to 5 DOF
**Date:** 2026-10-21

### Decision
Changed the joint layout to yaw + shoulder pitch + elbow pitch + wrist pitch + wrist roll (ADR-007). The original layout could not choose the gripper's approach angle, which top-down picking needs. Five joints is the smallest arm that can pick from above *and* rotate its fingers to match an object. The 5-DOF arm is now the reference build; other DOF counts will be generated from it in Phase 3.

### Done
- Rewrote `my_arm.urdf` for 5 DOF: new `wrist_pitch_joint` and `wrist_pitch_link`, roll moved to the end of the chain.
- Renamed joints and links to a descriptive pattern (`shoulder_pitch_joint`, `upper_arm_link`, ...) before anything else depends on the names (ADR-008).
- Set wrist limits to ±90° to match 180° hobby servos, and gave each joint placeholder effort and velocity values sized to its planned motor.
- Extended `scripts/urdf_fk_check.py` to compute the full 6 × n geometric Jacobian. Its rank must equal the number of joints; a lower rank would mean two joints duplicate each other's motion. Result: rank 5 at a general pose.
- Derived closed-form inverse kinematics (docs/kinematics.md, section 5) and checked it against the URDF: a table pick at (0.30, 0, 0.02) m pointing down lands exactly on target.

### Problem found: the arm could not reach the table
A sweep of table targets with the gripper pointing down found **no reachable point at any distance** with the first set of limits (shoulder ±90°, elbow ±135°).
*Why:* the shoulder axis is 0.35 m above the table. To reach a low target, the upper arm must tip slightly past horizontal: 93.8° for a target 0.30 m out, just beyond the 90° limit. RViz would never have shown this, because the sliders simply stop at the limit.
*Fix:* shoulder widened to ±120° (it is stepper-driven, so not limited to a servo's range). Table band with the gripper pointing down is now 0.07–0.45 m. A shorter column was also evaluated and kept as an option for the mechanical design (ADR-009).

### Reflection
<!-- TODO: in your own words. e.g. what "counting degrees of freedom" taught you about choosing a joint layout, and why a reachability sweep caught a problem that moving sliders in RViz would not. -->

---

## Phase 2c — Making the description a real ROS 2 package
**Date:** 2026-10-21

### Problem found: colcon could not find the package
`colcon build --packages-select my_arm_description` printed *ignoring unknown package*.
*Why:* colcon finds packages by searching the workspace for `package.xml` files, and uses the `<name>` inside each one. A search of the whole home folder found no `package.xml` at all: the URDF lived in an ordinary folder, so there was nothing for colcon to build.
*Fix:* added the missing package files to the repository (`package.xml`, `CMakeLists.txt`, `launch/display.launch.py`, `rviz/display.rviz`), so the repository itself is placed in `~/ros2_ws/src/` and builds directly. One copy of every file, under version control.

### Done
- `package.xml` declares the run-time dependencies, so `rosdep` can install them in one command.
- `CMakeLists.txt` installs `urdf/`, `launch/` and `rviz/` into the package's share directory, which is where the launch file reads them from after a build.
- `display.launch.py` passes the robot model through `xacro` (a plain URDF passes through unchanged), so it already works for the Phase 3 xacro file. A `gui:=false` argument replaces the sliders with a publisher that holds every joint at zero.
- The RViz config opens with `base_link` as the fixed frame, the robot model, and TF axes with frame names.

### Reflection
<!-- TODO: in your own words. e.g. what you learned about how colcon discovers packages and why files are installed before they are used. -->
