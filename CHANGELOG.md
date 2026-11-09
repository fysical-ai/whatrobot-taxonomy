# Changelog

All notable changes to the taxonomy data are recorded here. Versions are CalVer (`YYYY-MM`). The newest section is the version `main` is preparing; it is marked *unreleased* until tagged.

## 2026-01 — unreleased (first release candidate)

### Review: continuum arm, crawlers, medical scope (2026-11-09)
- New leaf `rb-1-6` Continuum arm (60 categories): arms that bend along their length — a continuous backbone, or more bending segments than independently driven joints (snake-arm robots, robotic catheters, vine robots). Classifier fact `arm_kinematics: continuum`; a continuum body counts as manipulating even if it only carries a camera. The articulated rule now excludes them. IFR industrial: unmapped; Google `1470` and Shopify `bi-17` as the other arms.
- 4 new attributes (ids 85–88): `medical_clearance` (robot root; `us-fda`, `eu-ce`, `cn-nmpa`, `jp-pmda`), `adhesion` (ground; `none`, `magnetic`, `vacuum`), `construction` (exoskeleton; `rigid`, `soft`), `outer_diameter` (continuum arm, mm).
- 15 new values (ids 165–179; 164 is `availability__limited` from the batch-2 rulings), including `autonomy__programmed`, `drive_config__skid-steer` and `drive_config__self-balancing`.
- `collaborative` reworded to ISO 10218-1:2025 ("collaborative applications"; ISO/TS 15066 still accepted). Identifier, type and evidence bar unchanged.
- Rule text: wheels or tracks count only when the robot moves itself on them as part of its task, including between work stations (carts and casters people move it on, even power-assisted, and passive wheels → fixed base; applies to rules 3, 6 and 7); unplaced robots narrowed to limbless locomotors; wheeled and tracked crawlers are ground robots; parallel arms include cable-driven robots; medical and surgical robots in scope (design notes §2, §2.1, §10.4).
- 6 new classification examples (83): `intuitive-ion`, plus illustrative `oc-robotics-snake-arm`, `cobot-on-trolley`, `vine-robot-inspection`, `humanoid-torso-on-casters` and `mobile-manipulator-between-stations`.
- `drive_config` values defined in the attribute description; `segment` row in design notes lists `clinical`; README notes that continuum arms have no IFR class.
- zh-Hans drafts written for the new and changed entries (LLM draft, awaiting native review).

### Batch-1 rulings (2026-11-09)
- 18 new number attributes (ids 67–84): `wingspan`, `cruise_speed`, `flight_range`, `max_user_weight`, `load_limit`, `stroke_x`, `stroke_y`, `stroke_z`, `voltage_min`, `voltage_max`, `position_accuracy`, `update_rate`, `heading_accuracy`, `attitude_accuracy`, `force_range`, `torque_range`, `linear_speed`, `grip_range`.
- 11 new values (ids 153–163): applications `mapping-surveying`, `lab-automation`; user type `clinical` (amends D3); teleop type `handheld-demonstrator`; interfaces `uart`, `i2c`, `spi`, `rs232`, `rs422`, `modbus-rtu`, `analog`.
- Bindings: `max_speed` and `flight_range` on aerial; `wingspan`, `cruise_speed` on fixed-wing and hybrid VTOL; `max_user_weight` on wearable, `load_limit` on prosthesis; X/Y/Z strokes on Cartesian arm, `stroke_z` on cylindrical arm; `voltage_min`/`voltage_max` on the component root; sensor accuracies, rates and ranges on range/positioning, inertial and force-torque; `stall_torque` on motor; `linear_speed` and `repeatability` on linear actuator; `grip_range` on soft gripper.
- **Breaking for data:** `payload` moves from end-effector to gripper, hand and tool changer, so Tool no longer binds it.
- Bases: `rated_force` gains `continuous` (default) and `max`; `payload` gains `shear`. `stall_torque` description now covers motors.
- Rules in design notes §10.2 (not-applicable conventions, kits as one product). IFR service mapping: both new applications → other professional service.
- Example `igus-drylin-gantry` renamed `igus-dle-rg-0001`. zh-Hans entries for the new attributes and values are not written yet (validation warns).

### Measurement bases (2026-11-07)
- Number attributes gain an optional `bases` list: the ways a figure can be measured, default first (design notes §3.5). Twelve attributes carry bases: `mass`, `payload`, `battery_runtime`, `max_speed`, `flight_time`, `height`, `reach`, `repeatability`, `grip_force`, `range`, `ai_tops`, `stall_torque`.
- `dist/<locale>/attributes.json` lists them as `bases: [{handle, description, default}]`. Basis descriptions are English only for now (not yet in the localisation review).
- No change to ids, names, descriptions or values; existing data stays valid.

### Localisation review (2026-11-02)
- Localised entries carry a per-field review record, `source: {field: fingerprint}`; unreviewed drafts and stale reviews (English changed since) are now distinguishable. Categories gain localised search terms (`aliases`), which replace the English aliases in that locale's dist.
- New `whatrobot-taxonomy l10n status | export | import` for the native-review round trip; validation warns on stale reviews; `release` refuses unreviewed locales unless `--allow-unreviewed`.
- `scripts/sheet_values_to_csv.py` turns the shared review sheet into an import CSV.
- No change to ids, English data or existing translations; `da` and the `zh-Hans` review follow as reviewed batches.

### Wording (2026-10-30)
- Root `rb` description is now the site's definition of a robot: "A machine that senses and acts on its environment — by moving, manipulating objects, or interacting with people. Robots are classified by physical form, not by user group or application." The ISO 8373:2021 reference moves to the inclusion rule.
- Attribute `segment` display name "Segment" → "User type"; description and question reworded ("buyer groups" → "user types"). The identifier `segment` and its values are unchanged, so no data or integration breaks. zh-Hans updated accordingly (still an LLM draft).

### Rulings (2026-10-29)
- New leaves: `rb-8-2` Prosthesis, `cp-3-6` Range / positioning sensor (59 categories).
- Rule changes: wheeled-base humanoid needs a head and human proportions; humanoid with legs ≠ 2 is unclassifiable; joint module vs servo decided by `joint_grade` (fact `industrial_bus` kept as alias); ROV = tethered even if autonomous; multirotor = one or more rotors; hand threshold = actuated DOF; stationary = non-humanoid.
- Rule text clarified for tool (no camera heads), motor (gearmotors), power (docks), teleoperation (wins over sensor), vacuum (Bernoulli), soft (granular jamming), tactile (capacitive pre-touch); `rb-1-5` renamed Cylindrical & spherical arm.
- Attribute bindings: `flange_standard` and `actuation` off the component root (end-effector; `actuation` also on actuator); `stroke`/`finger_count` on finger and soft grippers only; `stall_torque` in Nm.
- 8 new classification examples (77).

- Initial robot hierarchy (`rb`): 10 top-level branches, 31 nodes.
- Initial component hierarchy (`cp`): 7 top-level branches, 26 nodes.
- 66 typed attributes, 152 enum values, two-level `application` vocabulary.
- Integrations: ifr-industrial/2026 (codes verified against World Robotics 2022 ch.1), ifr-service/2026, iso-8373/2021, google/2021-09-21 and shopify/2026-08 — complete in both directions for all 57 categories.
- CITATION.cff for citation and Zenodo archiving.
- Localisations: `en` (source), `zh-Hans` (LLM draft, pending native review).
- 69 classification examples as CI regression suite.
