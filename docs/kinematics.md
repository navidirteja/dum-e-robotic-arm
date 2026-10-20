# Kinematics

How the arm's joint angles determine where its tool is, how to go the other way, and where that relationship breaks down. This describes the 5-DOF reference build ([ADR-007](design-decisions.md)).

## 1. Conventions

- **REP-103:** right-handed frames, X forward, Y left, Z up. Meters, radians, kilograms.
- In RViz2, axes are drawn **red = X, green = Y, blue = Z**.
- **Zero pose:** arm straight up, all frames aligned with `base_link` (ADR-002, ADR-003).
- **Positive rotation** follows the right-hand rule: thumb along the axis, fingers curl in the positive direction.

## 2. Joint-link tree

```
base_link
 └─ base_yaw_joint        (yaw about Z)     origin z = 0.05
    └─ shoulder_link
       └─ shoulder_pitch_joint  (pitch about Y)  origin z = 0.30
          └─ upper_arm_link
             └─ elbow_pitch_joint   (pitch about Y)  origin z = 0.30
                └─ forearm_link
                   └─ wrist_pitch_joint   (pitch about Y)  origin z = 0.20
                      └─ wrist_pitch_link
                         └─ wrist_roll_joint  (roll about Z)  origin z = 0.06
                            └─ wrist_roll_link
                               └─ tool0_joint (fixed)       origin z = 0.05
                                  └─ tool0
```

## 3. Joint table

| Joint | Axis | Limits | Positive direction |
|-------|------|--------|--------------------|
| `base_yaw_joint` | Z | ±180° | Counter-clockwise seen from above (+X turns toward +Y) |
| `shoulder_pitch_joint` | Y | ±120° | Arm tips forward (+Z turns toward +X) |
| `elbow_pitch_joint` | Y | ±135° | Forearm tips forward, relative to the upper arm |
| `wrist_pitch_joint` | Y | ±90° | Tool tips forward, relative to the forearm |
| `wrist_roll_joint` | Z | ±90° | Counter-clockwise looking down the tool axis toward the tool |

These signs must match the motor directions in the ESP32 firmware. Limit choices for the shoulder and elbow are explained in ADR-009.

## 4. Forward kinematics

A URDF is a chain of transforms. The tool pose is the product of each joint's fixed origin and its rotation:

$$
T_{\text{base}\to\text{tool0}} = T_{o_1} R_z(q_1)\; T_{o_2} R_y(q_2)\; T_{o_3} R_y(q_3)\; T_{o_4} R_y(q_4)\; T_{o_5} R_z(q_5)\; T_{\text{tool}}
$$

Because every origin is a pure translation along Z, the tool **position** has a simple closed form. Define:

- $h = 0.35$ m — height of the shoulder axis (plate 0.05 + column 0.30)
- $L_2 = 0.30$ m — upper arm (shoulder to elbow)
- $L_3 = 0.20$ m — forearm (elbow to wrist pitch)
- $L_4 = 0.11$ m — wrist pitch to `tool0` (bracket 0.06 + tool mount 0.05)

The three pitch joints act in a vertical plane, which the base yaw then rotates. Let $\theta = q_2 + q_3 + q_4$ be the tool's angle from vertical ($\theta = \pi$ means pointing straight down):

$$
r = L_2 \sin q_2 + L_3 \sin(q_2+q_3) + L_4 \sin\theta
$$
$$
x = r\cos q_1, \qquad y = r\sin q_1, \qquad z = h + L_2 \cos q_2 + L_3 \cos(q_2+q_3) + L_4 \cos\theta
$$

The wrist roll $q_5$ does not appear: it rotates the fingers about the tool axis without moving the tool.

## 5. Inverse kinematics (closed form)

Going backwards, from a desired tool position $(x, y, z)$, approach angle $\theta$ and finger rotation $\psi$ to joint angles:

1. **Base yaw** faces the target: $q_1 = \operatorname{atan2}(y, x)$, and $r = \sqrt{x^2 + y^2}$.
2. **Wrist point.** Step back from the target along the tool axis by $L_4$: $\;w_r = r - L_4 \sin\theta,\;\; w_z = z - L_4\cos\theta$.
3. **Shoulder and elbow** form a 2-link arm reaching the wrist point from the shoulder $(0, h)$. With $d$ the distance from shoulder to wrist point, the law of cosines gives $\cos q_3 = \dfrac{d^2 - L_2^2 - L_3^2}{2 L_2 L_3}$. The sign of $q_3$ picks "elbow up" or "elbow down", then $q_2 = \operatorname{atan2}(w_r, w_z - h) - \operatorname{atan2}(L_3 \sin q_3,\; L_2 + L_3\cos q_3)$.
4. **Wrist pitch** makes up the difference: $q_4 = \theta - q_2 - q_3$.
5. **Wrist roll** sets the fingers: $q_5 = \psi$ (measured relative to the base yaw).

A solution exists only if $|L_2 - L_3| \le d \le L_2 + L_3$ and every angle is within its limit.

This is why the 5-DOF layout was chosen: step 4 is only possible because there is a third pitch joint. With two (the original 4-DOF layout), $\theta$ is fixed by $q_2$ and $q_3$ and cannot be chosen.

## 6. Verification

`scripts/urdf_fk_check.py` reads the URDF directly and checks it independently of the hand derivation above.

| Check | Expected | URDF result |
|-------|----------|-------------|
| `tool0` at zero pose | (0, 0, 0.96) | (0, 0, 0.96) |
| Table pick: target (0.30, 0, 0.02), pointing down. IK gives q = (0°, 93.8°, 86.0°, 0.2°, 22.9°) | (0.30, 0, 0.02), tool axis (0, 0, −1) | (0.30, 0, 0.02), tool axis (0, 0, −1) |
| Tip motion when only the roll joint moves | 0 | 0.00 cm |
| Full Jacobian rank at a general pose | 5 (all joints independent) | 5 |

## 7. Singularities

A singularity is a pose where the arm loses the ability to move its tool in some direction, however the joints move. Near one, inverse kinematics asks for very large joint speeds to produce tiny tool motions.

For the shoulder–elbow pair, the in-plane Jacobian has determinant $L_2 L_3 \sin q_3$, so this arm is singular when:

1. **The elbow is straight ($q_3 = 0$).** Shoulder and elbow move the wrist point in the same direction, so it cannot move along the arm. This is the edge of the workspace.
2. **The wrist point is on the base yaw axis.** Base yaw then spins the arm without moving the wrist point.

The zero pose has both at once: the full Jacobian has rank 3 instead of 5. This is why the zero pose is used only for homing and motion planning starts from a bent "ready" pose.

## 8. Workspace on the table

The most important workspace for pick-and-place is the table surface with the gripper pointing straight down. Sweeping targets 2 cm above the table, within all joint limits and with the elbow kept at least 5 cm above the table:

| Target height | Reachable distance from base axis |
|---|---|
| 0.02 m | 0.07–0.45 m |
| 0.10 m | 0.16–0.48 m |
| 0.20 m | 0.21–0.49 m |

Targets closer than about 0.12 m are blocked in practice by the 0.10 m radius base plate. With the original ±90° shoulder and elbow limits the table was not reachable at all (ADR-009).
