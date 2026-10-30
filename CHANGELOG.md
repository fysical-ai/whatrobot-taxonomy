# Changelog

All notable changes to the taxonomy data are recorded here. Versions are CalVer (`YYYY-MM`). The newest section is the version `main` is preparing; it is marked *unreleased* until tagged.

## 2026-01 — unreleased (first release candidate)

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
