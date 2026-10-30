# Torque check — Draft v0

## 1. Why this check
Before choosing motors, I needed to know how much torque each joint has to hold, so that every joint gets a motor (and gearbox) that is strong enough without being heavier than necessary. This check decides which motor goes at which joint and how much gear reduction each one needs, and it is the basis for the [parts list](parts-list.md). It had to come before the parts list: a wrong motor choice is expensive to undo once parts are ordered and printed parts are designed around them.

## 2. Method
- **Formula.** The torque a joint must hold is the sum, over everything beyond that joint, of mass × 9.81 × horizontal distance from the joint's axis:

  τ = Σ (m × 9.81 × d)  (τ in N·m, m in kg, d in m)

- **Pose.** The arm is checked stretched out horizontally, because it is the worst-case position: every part is as far from each joint as it can get. If the arm can hold the payload in this position, it can hold it in any position.
- **Which joints.** Gravity can only twist a joint whose axis is horizontal (like a trapdoor hinge; a normal door on a vertical hinge does not swing by itself).
  - Shoulder, elbow and wrist pitch turn about horizontal axes, so these three are checked.
  - Base yaw turns about a vertical axis, parallel to gravity, so gravity puts no torque on it. The arm's weight goes into the base bearing; the motor only has to start and stop the rotation.
  - Wrist roll's axis runs along the tool, through the gripper's mass, so the lever is only a few millimetres: negligible.
  - The gripper's squeezing force is a separate check, not part of this one.
- **Where weight acts.** A link's weight acts at its middle (the centre of mass of a uniform part). A motor's weight acts at its joint. A motor sitting on the joint it drives adds no torque to that joint (distance 0), but it loads every joint before it.
- **2× safety margin.** Each joint's load is kept at or below half of its motor's rated torque (stall torque for servos, holding torque for steppers). The calculation assumes the arm is holding still; the margin covers what it leaves out: the extra torque needed to speed the arm up and slow it down, friction in the joints, datasheet figures that are best case (especially for cheap servos), and heating when a servo works close to stall.
- **Gear ratio.** ratio = (load × 2) ÷ (motor torque × 0.7). The 0.7 is the gearbox efficiency: friction between gear teeth turns some torque into heat, so only about 70% of (motor torque × ratio) reaches the joint. 0.7 is a cautious value for 3D-printed gears, which lose more to friction than precision metal ones.
- **Units.** Servo datasheets give torque in kg·cm. 1 kg·cm = 9.81 N × 0.01 m = 0.0981 N·m.

## 3. Inputs

Positions along the arm, measured from the shoulder (m):
shoulder 0.00, elbow 0.30, wrist pitch 0.50, wrist roll 0.56, tool0 0.61.
Gripper parts and payload assumed at 0.63–0.66.

| Item | Mass (kg) | Source |
|------|-----------|--------|
| Upper arm (printed) | 0.28 | Estimate: PLA shell + 15% infill, +20% for mounts |
| Elbow module (NEMA 17 40 mm + gearbox) | 0.38 | 17HS4401 280 g (Hanpose catalog) + ~100 g gearbox estimate |
| Forearm (printed) | 0.10 | Estimate, as above |
| Wrist pitch module (MG996R) | 0.075 | MG996R 55 g (datasheet) + mounting |
| Wrist bracket (printed) | 0.04 | Estimate |
| Wrist roll servo (SG90) | 0.009 | Datasheet |
| Tool mount (printed) | 0.05 | Estimate |
| Gripper servo (MG90S) | 0.0134 | Datasheet |
| Gripper body (printed) | 0.06 | Guess, 40–80 g range |
| Payload | 0.20 | Working assumption, pending CEO |

## 4. Results (200 g payload)

### Shoulder (distances from 0.00)
| Item | Distance (m) | Torque (Nm) |
|------|--------------|-------------|
| Upper arm | 0.15 | 0.41 |
| Elbow module | 0.30 | 1.12 |
| Forearm | 0.40 | 0.39 |
| Wrist pitch module | 0.50 | 0.37 |
| Wrist bracket | 0.53 | 0.21 |
| Wrist roll servo | 0.56 | 0.05 |
| Tool mount | 0.585 | 0.29 |
| Gripper servo | 0.63 | 0.08 |
| Gripper body | 0.64 | 0.38 |
| Payload | 0.66 | 1.29 |
| **Total** | | **4.59** |

### Elbow (distances from 0.30)
| Item | Distance (m) | Torque (Nm) |
|------|--------------|-------------|
| Forearm | 0.10 | 0.10 |
| Wrist pitch module | 0.20 | 0.15 |
| Wrist bracket | 0.23 | 0.09 |
| Wrist roll servo | 0.26 | 0.02 |
| Tool mount | 0.285 | 0.14 |
| Gripper servo | 0.33 | 0.04 |
| Gripper body | 0.34 | 0.20 |
| Payload | 0.36 | 0.71 |
| **Total** | | **1.45** |

### Wrist pitch (distances from 0.50)
| Item | Distance (m) | Torque (Nm) |
|------|--------------|-------------|
| Wrist bracket | 0.03 | 0.01 |
| Wrist roll servo | 0.06 | 0.01 |
| Tool mount | 0.085 | 0.04 |
| Gripper servo | 0.13 | 0.02 |
| Gripper body | 0.14 | 0.08 |
| Payload | 0.16 | 0.31 |
| **Total** | | **0.47** |

### Summary
| Joint | Load (Nm) | Motor | Needs |
|-------|-----------|-------|-------|
| Shoulder | 4.59 | NEMA 17, 48 mm (0.52 Nm) | ~25:1 reduction |
| Elbow | 1.45 | NEMA 17, 40 mm (0.40 Nm) | ~10:1 reduction |
| Wrist pitch | 0.47 | MG996R (1.08 Nm stall at 6 V) | direct drive, 6 V supply |

## 5. What the numbers say
- **Motors are about a third of the shoulder load.** The four motor rows (elbow module, wrist pitch module, wrist roll servo, gripper servo) add up to 1.62 Nm, about 35% of 4.59 Nm. Without them the total is 2.97 Nm, almost exactly the earlier 2.9 Nm estimate that left the motors out. Two separate calculations agree, which is good evidence the method is right, and it shows exactly what the old estimate was missing.
- **The payload matters more the closer a joint is to the tip.** The payload's share of the load is about 28% at the shoulder (1.29 of 4.59 Nm), 49% at the elbow (0.71 of 1.45) and 66% at the wrist (0.31 of 0.47). Near the tip there is little else for the joint to hold, so the payload dominates. This is why the wrist is the first joint to run out as the payload grows.
- **The elbow cannot be a hobby servo.** It needs ±135° (270° of travel), and hobby servos turn about 180°. Gearing a servo down would shrink its range even further, so the elbow is a geared stepper.
- **The servos need a 6 V supply.** The MG996R's stall torque is 0.92 Nm at 4.8 V, which gives a 1.95× margin on the wrist's 0.47 Nm, just under the 2× rule. At 6 V it is 1.08 Nm, a 2.3× margin, which passes.
- **The shoulder needs heavy gearing even with no payload.** At 0 g the shoulder still holds about 3.3 Nm (~18:1 with a 48 mm NEMA 17). That is the arm's own weight, mostly the elbow module.
- **The first motor choice would not have worked.** An MG996R at the elbow and an SG90 at the wrist pitch, with no gearing, fail at any payload. The check caught this before any parts were ordered.

## 6. Payload options
| Payload | What changes |
|---------|--------------|
| ~100 g | Easiest; most tolerant of estimate errors |
| ~200 g | Highest without redesign; wrist near its limit |
| ~300 g | Wrist needs a different actuator; shoulder ~29:1 |
| 500 g+ | Bigger motors (NEMA 23) or metal gearboxes: a different arm |

## 7. What this means for modularity
In a plug-and-play arm, every module carries its own motor at its own joint, and that motor's mass loads every joint before it. The elbow module alone (0.38 kg at 0.30 m) costs the shoulder 1.12 Nm, about as much as 170 g of payload at the tip. So the payload and the number of modules draw on the same torque budget at the base and shoulder: a heavier payload leaves room for fewer modules, a lighter one for more.

Consequences for the design:
- Every module must be an **actuator** (motor + built-in gearbox), because bare motors are too weak. Commercial modular systems such as HEBI Robotics' actuators work this way.
- Modules should be as light as possible, especially the ones far from the base.
- A **module budget**: each module's torque rating must cover everything attached after it. In Stage 3, modules could report their mass and torque at power-up, so the software can warn when a chain is too heavy before anything is damaged.

A fixed (non-modular) arm could keep its motors near the base and drive the joints with belts. Carrying each motor at its own joint is the real cost of modularity, but it is manageable.

## 8. Limits of this check
- **Static only.** It assumes the arm is holding still. Fast moves need extra torque, which the 2× margin only partly covers.
- **Estimated masses.** The printed parts, gearbox (~100 g) and gripper body are estimates. Real parts must be weighed and the check redone.
- **Stepper torque falls with speed.** Holding torque is the best case; a stepper is weaker while it is turning quickly.
- **Gear strength is unknown.** It is not yet known whether printed gear teeth survive ~25:1 at the shoulder; a fit-test print has to confirm this.
- **Gearbox efficiency (0.7) is an assumption** until a gearbox is designed and tested.
- **Gripping force is not checked.**
- **The payload (200 g) is pending** the CEO's decision.

## Sources
- NEMA 17 masses and torques: [Hanpose 17HS series catalog](https://baa.vn/document/17hs-series-hanpose-dong-co-buoc-2-pha-lai-6877-catalog1.pdf)
- [MG996R](https://components101.com/node/467), [MG90S](https://components101.com/motors/mg90s-metal-gear-servo-motor), [SG90 datasheet](https://tams.informatik.uni-hamburg.de/lehre/2023ss/vorlesung/es/doc/sg90.pdf)
