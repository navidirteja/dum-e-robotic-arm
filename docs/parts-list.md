# Parts list — Draft v0 (pending decisions)

For the Stage 1 arm: 5 DOF (base yaw, shoulder, elbow, wrist pitch, wrist roll) + gripper.
Motor sizes come from a torque calculation for the worst pose (arm fully stretched out), with a 2× safety margin, assuming a 200 g (not yet confirmed) payload.

| # | Part | Qty | Used for | Why |
|---|------|-----|----------|-----|
| 1 | NEMA 17, 48 mm (17HS8401 or ≥0.52 Nm holding) | 1 | Shoulder | Load 4.59 Nm → needs the strongest NEMA 17 plus ~25:1 gearbox |
| 2 | NEMA 17, 40 mm (17HS4401, 0.40 Nm holding) | 2 | Elbow, base yaw | Elbow load 1.45 Nm → ~10:1 gearbox; a servo can't cover the elbow's ±135°. Base carries almost no gravity torque |
| 3 | MG996R servo | 1 | Wrist pitch | Load 0.47 Nm; 2.3× margin at 6 V |
| 4 | SG90 servo | 1 | Wrist roll | Almost no gravity load (mass centred on its axis) |
| 5 | MG90S servo (SG90 as fallback) | 1 | Gripper | Holds at stall while gripping; metal gears survive that |
| 6 | TMC2209 stepper driver | 3 | One per NEMA 17 | Precise current control, quiet |
| 7 | ESP32 dev board | 1 | Controller | Runs the motors and talks to ROS |
| 8 | Limit switch | 3 | Stepper homing | Steppers don't know their position at power-up |
| 9 | 100 µF electrolytic capacitor | 3 | One per driver | Absorbs voltage spikes that can damage drivers |
| 10 | 12 V power supply, ≥5 A | 1 | Stepper power | |
| 11 | 6 V regulator / UBEC, ≥5 A | 1 | Servo power | Wrist needs 6 V; one MG996R can draw ~2.5 A at stall |
| 12 | Base bearing (lazy-susan / slewing, ~100 mm) | 1 | Base | Carries the arm's weight so the base motor only rotates it |
| 13 | Gearbox hardware (bearings, pins, belts) | TBD | Shoulder, elbow | Depends on the gearbox design |
| 14 | Main power switch + fuse | 1 | Safety | One switch stops all motors; fuse protects against shorts |
| 15 | M3 screws, nuts, heat-set inserts | set | Assembly | |
| 16 | PLA filament | ~1 kg | Printed parts | Arm ≈ 0.5 kg + gearboxes + test prints |
| 17 | Wire, connectors, heat-shrink | set | Wiring | |

## Open questions for Sanzim bhai
- Payload target (100 g / 200 g / 300 g changes rows 1–3 and the gearboxes)
- Printer: bed size, material, tolerances
- Power supply: available 12 V / 6 V supplies?
- Exact motor models available (NEMA 17 body lengths, MG90S)
