# Design Decisions

Each decision is recorded as a short Architecture Decision Record (ADR): the context, the choice, and its consequences. Decisions are never deleted; if one is reversed, a new ADR supersedes it.

**Status values:** Accepted · Proposed · Superseded

---

## ADR-001: `ament_cmake` for the description package
**Status:** Accepted

**Context.** ROS 2 packages are built with either `ament_cmake` or `ament_python`. The description package contains only data files (URDF, launch, RViz config, later meshes) and no compiled or importable code.

**Decision.** Use `ament_cmake` and install the data directories with `install(DIRECTORY ...)`.

**Consequences.** This is the convention used by most robot description packages, and it lets other packages locate files through `package://my_arm_description/...` paths.

---

## ADR-002: All joint frames aligned at zero pose (`rpy="0 0 0"`)
**Status:** Accepted

**Context.** A joint's `<axis>` is expressed in the child frame. If a joint origin has a non-zero rotation, the same `axis` value means a different physical direction, which is the most common source of URDF bugs.

**Decision.** Every joint origin has zero rotation. Yaw joints use axis `0 0 1`, pitch joints `0 1 0`, roll joints the direction the link points.

**Consequences.** Axes are readable at a glance and every frame matches `base_link` at q = 0. Links that need a rotated shape rotate their `<visual>` or `<collision>` origin instead of the joint frame.

---

## ADR-003: Zero pose is "arm straight up"
**Status:** Accepted

**Context.** The URDF zero pose must match the physical position the robot returns to on startup, because stepper motors have no absolute position sense.

**Decision.** At q = 0 the arm points straight up along +Z.

**Consequences.**
- Easy to reproduce physically with limit switches or a level.
- Keeps all joint rotations at zero (ADR-002).
- This pose is a **kinematic singularity** (see [kinematics.md](kinematics.md)). It is used for homing only; planning starts from a separate bent "ready" pose defined in MoveIt.

---

## ADR-004: `base_link` origin at the mounting surface
**Status:** Accepted

**Context.** The planning scene, tables and other robots are positioned relative to `base_link`. If its origin is inside the base plate, every external object needs an offset.

**Decision.** The `base_link` origin is at the bottom-centre of the base plate.

**Consequences.** A table surface is simply z = 0. Joint 1 sits at z = 0.05 (top of the plate).

---

## ADR-005: Dedicated `tool0` frame as the planning tip
**Status:** Accepted

**Context.** The last moving link's origin is at the wrist joint, not where the tool does its work. MoveIt plans for a single tip frame.

**Decision.** Add a fixed `tool0` link at the tool-mount face. When a gripper is added, `tool0` moves to the centre between the fingertips.

**Consequences.** Swapping end effectors changes one fixed joint, not the planning setup.

---

## ADR-006: No inertial on the root link
**Status:** Accepted

**Context.** KDL (the default kinematics library in ROS) does not support inertia on the root link of a tree and prints a warning if one exists.

**Decision.** `base_link` has no `<inertial>`. It is bolted to the world, so its mass does not affect motion. If simulation later needs it, a massless `world` root will be added above it.

---

## ADR-007: Joint layout: 5-DOF reference build
**Status:** Accepted (2026-10-21)

**Context.** The original layout was yaw + shoulder pitch + elbow pitch + wrist roll. Seen from the side, a top-down grasp asks for three things: reach, height and approach angle. That layout had only two bending joints (shoulder, elbow), so once the target position was fixed the approach angle was forced by the geometry. Roll only spins the tool about its own axis and cannot help.

**Options.**
1. Keep yaw + 2 pitch + roll. Cannot choose the approach angle.
2. Yaw + 3 pitch (add wrist pitch, drop roll). Chooses the approach angle, but finger orientation is then tied to the base yaw.
3. 5 DOF: yaw + 3 pitch + wrist roll. Position (3) + approach angle (1) + finger rotation (1).

**Decision.** Option 3. The 5-DOF arm is the physical reference build. The xacro description (Phase 3) will generate 3-, 4-, 5- and 6-DOF variants from one macro, each verified with `scripts/urdf_fk_check.py`.

**Consequences.**
- Covers top-down pick-and-place with the fingers aligned to the object.
- Still cannot tilt the tool sideways: its axis always lies in the vertical plane through the base axis. A 6th joint removes this; it is the planned scaling step.
- More weight far from the shoulder. Rough worst-case static shoulder torque with the arm horizontal is about 2.9 Nm (assumed masses), about three times a typical MG996R servo. Steppers go at base, shoulder (geared) and elbow; hobby servos at the wrist.
- MoveIt's default KDL solver handles full-pose goals poorly on arms with fewer than 6 DOF. Plan to use `pick_ik`.

---

## ADR-008: Descriptive joint and link names
**Status:** Accepted (2026-10-21)

**Context.** Joint names are referenced by the controllers, the MoveIt configuration and the ESP32 bridge. Renaming them later means changing all of those.

**Decision.** Rename now, while nothing depends on them: `<location>_<motion>_joint` (e.g. `shoulder_pitch_joint`) and links named after the body part they are (`upper_arm_link`, `forearm_link`). Robot name `dum_e` (no hyphen, so it is a valid identifier in generated config files).

**Consequences.** Names say what each joint does, and the pattern extends naturally when joints are added.

---

## ADR-009: Wider shoulder and elbow limits for table reach
**Status:** Accepted (2026-10-21)

**Context.** A reachability check of the 5-DOF model showed that with shoulder and elbow limited to ±90°, the arm could not reach the table surface with the gripper pointing down **at any distance**. The shoulder axis sits 0.35 m above the table, so a low target needs the upper arm to tip slightly past horizontal (about 94° for a target 0.30 m out).

**Options considered** (table reach with gripper pointing down, target 2 cm above the table):

| Shoulder axis height | Shoulder limit | Elbow limit | Table reach |
|---|---|---|---|
| 0.35 m (current) | ±90° | ±135° | none |
| 0.35 m (current) | ±120° | ±90° | 0.29–0.45 m |
| 0.35 m (current) | ±120° | ±135° | 0.07–0.45 m |
| 0.25 m (shorter column) | ±90° | ±135° | 0.18–0.46 m |

**Decision.** Keep the current column and widen the limits to shoulder ±120°, elbow ±135°. Both joints are stepper-driven, so they are not limited to a servo's 180° range.

**Consequences.**
- Widest table band of the options. The inner part (below about 0.12 m) is blocked by the base plate in practice.
- A shorter column remains a good option for the mechanical design (lower centre of mass, less wobble). Revisit in Phase 6 when the printed parts are designed.
- The physical joints must actually allow these ranges without the arm hitting its own structure or cables.

---

## ADR-010: Optional linear rail under the base
**Status:** Accepted (software planned in Phase 3; hardware deferred until the fixed arm works)

**Context.** The arm reaches about 0.45 m. Mounting it on a carriage that slides along one axis (a prismatic joint, often called a "7th axis" or linear track in industry) would let it cover a whole desk.

**Decision.** The Phase 3 xacro gets a `world` root frame and an optional prismatic `rail_joint` between `world` and `base_link`, switched off by default (`rail:=false`). With the rail off, `world` is joined to `base_link` by a fixed joint. The rail axis defaults to Y, so the arm, which faces +X, slides along the edge of a desk. The physical rail is built only after the fixed 5-DOF arm is commissioned.

**Consequences.**
- The description scales by joint *type* (sliding as well as rotating), not only by joint count, and is verified by the same scripts.
- With the rail on, the arm is redundant (6 joints for a 5-DOF task), so MoveIt can use the extra freedom to avoid obstacles.
- `world` as the root also satisfies ADR-006: the root link carries no inertia.
- Hardware cost when built: a stiff carriage (it must resist the arm's tipping moment), one more stepper and driver, a homing switch, and a cable chain. Likely parts: aluminium V-slot extrusion, NEMA 17, GT2 belt.
- The rail adds reach only, not orientation: the tool still cannot tilt sideways.
