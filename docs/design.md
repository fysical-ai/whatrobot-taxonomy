# whatrobot taxonomy — design notes

> Design rationale and decision log for the whatrobot taxonomy. Licence: CC BY 4.0.
> This is the document the repository implements; where the two differ, `data/` is authoritative and this file is updated afterwards.

---

## 0. Governing principle

Every robot and every component sits in **exactly one leaf** of **one hierarchy**. The hierarchy answers *"what is this thing, physically?"* and is assigned from hardware facts only (spec sheet, photo), never from who buys it or what it is used for.

Everything else is a **typed attribute**: segment, application, autonomy, specs, compatibility, price. Attributes are filters, comparison columns, badges and cross-links — never tree branches.

**Four tests** for a hierarchy node (all must pass):

| Test | Question |
|---|---|
| Exclusive | Does every item fit exactly one bucket, decided from the hardware alone? |
| Exhaustive | Do the buckets cover everything we intend to list, without a permanent "Other"? |
| Stable | Will the answer survive a firmware update, a price change, a new customer group? |
| Navigable | Would a newcomer browse *into* it, rather than filter *by* it? |

Anything failing one test is an attribute.

**Consequences for the site**
- Hierarchy → URL, breadcrumb, sitemap, one canonical page per item.
- Attributes → filters, comparison tables, "works with" links.
- Segment and application landing pages (`/for/research`, `/for/manufacturing`) are **saved filters** over the tree, not branches.

**Relationship to existing taxonomies.** No published taxonomy is MECE by hardware across robots and components. We reuse ISO 8373 vocabulary and the IFR industrial structure classes where they exist, locomotion/morphology axes from the literature for the rest, and our own tie-break rules. Standards and marketplace taxonomies are reached through *mappings* (§9.5), not by copying their trees.

---

## 1. Identifiers and naming (Shopify-style)

Every category, attribute and value carries three identifiers, following Shopify's product taxonomy:

| Field | Purpose | Rule | Example |
|---|---|---|---|
| `id` | Permanent key | Categories: positional path `<root>-<n>-<n>…` (numbers never reused; retired nodes leave gaps). Attributes/values: integer. | `rb-3-1`, `cp-1-1-2`, attribute `12` |
| `friendly_id` | Key used in data files | Categories: dotted path of kebab slugs. Attributes: `snake_case`. Values: `<attribute>__<value>`. | `robot.legged.quadruped`, `drive_config`, `drive_config__differential` |
| `handle` | URL slug | kebab-case, derived from name; may change, `id` never does | `quadruped`, `drive-config`, `differential` |

Additional rules:

- Roots: `rb` = robot, `cp` = component.
- Node names describe hardware, never use: "Quadruped", not "Robot dog" (→ `aliases`).
- Every category record has `id`, `name`, `friendly_id`, `handle`, `description` (one sentence), `aliases[]`, `inclusion_rule`, `children[]`, `attributes[]`, `examples[]`.
- Max depth 3 below the root.
- "Other" **category** leaves are review queues, not categories: >5 items in one → propose a new leaf. "Other" **attribute values** (`<attr>__other`) are allowed on every enum, as in Shopify.
- A category is never moved or renumbered. Restructuring = retire old id + create new id + add a mapping rule (§9.5) from old to new.

---

## 2. Robot hierarchy (by body plan)

Root: `rb` / `robot`

```
rb      robot
rb-1    ├─ arm                 Fixed-base manipulator
rb-1-1  │  ├─ articulated      ≥3 rotary joints in series (6/7-axis, incl. cobots, desktop arms)
rb-1-2  │  ├─ scara            Two parallel vertical rotary joints + vertical linear axis
rb-1-3  │  ├─ parallel         Parallel kinematics (delta, hexapod/Stewart, cable-driven)
rb-1-4  │  ├─ cartesian        Three prismatic axes (linear, gantry, XYZ)
rb-1-5  │  ├─ cylindrical      Cylindrical & spherical: rotary base + prismatic reach; lift is prismatic (cylindrical) or a tilt (spherical/polar)
rb-1-6  │  └─ continuum        Bends along its length: continuous backbone, or more bending segments than driven joints (snake-arms, robotic catheters)
rb-2    ├─ humanoid            Torso + two arms + head in human proportion
rb-2-1  │  ├─ bipedal          Walks on two legs
rb-2-2  │  ├─ wheeled-base     Humanoid upper body on a wheeled or tracked base
rb-2-3  │  └─ fixed-base       Humanoid upper body on a fixed mount (torso-only)
rb-3    ├─ legged              Legged locomotion, not humanoid in form
rb-3-1  │  ├─ quadruped        Four legs
rb-3-2  │  ├─ biped            Two legs, non-humanoid form
rb-3-3  │  └─ multi-legged     Six or more legs
rb-4    ├─ ground              Wheels or tracks, no legs, no integrated arm
rb-4-1  │  ├─ wheeled
rb-4-2  │  └─ tracked
rb-5    ├─ mobile-manipulator  Wheeled/tracked base + arm(s), one product, non-humanoid form
rb-6    ├─ aerial              Flies
rb-6-1  │  ├─ multirotor
rb-6-2  │  ├─ fixed-wing
rb-6-3  │  └─ hybrid-vtol
rb-7    ├─ aquatic             Operates on or in water
rb-7-1  │  ├─ rov              Remotely operated, tethered
rb-7-2  │  ├─ auv              Autonomous, untethered, submerged
rb-7-3  │  └─ usv              Surface vessel
rb-8    ├─ wearable            Worn on the human body
rb-8-1  │  ├─ exoskeleton      Powered exoskeleton / exosuit (assists an intact limb)
rb-8-2  │  └─ prosthesis       Powered prosthesis (replaces a limb or joint)
rb-9    ├─ stationary          Fixed, does not manipulate (desktop companions, social robots without arms)
rb-10   └─ kit                 Modular construction kit with no fixed body plan
```

Scope (D1): aerial, aquatic and wearable are in scope from launch. `kit` includes only kits that produce a programmable robot.

Medical and surgical robots are in scope as reference entries (2026-11-09). They are classified by body plan like any other robot (a surgical arm is `arm`, a robotic catheter is `continuum`, a rehabilitation exoskeleton is `wearable`). Medical use is recorded as `iso_category: medical`, user type `clinical`, application group `health` and `medical_clearance`; the catalogue records no clinical-performance claims.

### 2.1 Tie-break rules for hybrids

Apply in order; the first rule that matches decides the branch.

1. **Kit** — sold as parts to be assembled into user-chosen forms → `kit`.
2. **Wearable** — worn on the body and powered → `wearable`; a prosthesis (replaces a limb) → `prosthesis`, otherwise `exoskeleton`. Passive exoskeletons are out of scope.
3. **Humanoid** — torso + two arms **and** a head, in human proportion → `humanoid`; two legs → `bipedal`, wheels/tracks → `wheeled-base`, neither → `fixed-base`. A bimanual torso with a sensor mast but no head is not a humanoid (→ rule 6). A humanoid with a leg count other than two is unclassified until a case exists.
4. **Legged** — articulated legs → `legged`, even with wheels on the feet (`wheel_feet: true`) or an arm on the back (`has_arm: true`).
5. **Aquatic / Aerial** — primary operating medium. Amphibious → the medium it is marketed for. Aquatic: a tether decides (`rov`), even if it carries only power and the vehicle runs autonomously (corded pool cleaners); untethered submersible → `auv`; surface → `usv`. Aerial: one or more rotors and no wing → `multirotor` (helicopters included).
6. **Mobile manipulator** — ground base + arm(s) as one product → `mobile-manipulator`. Base and arm sold separately = two entries (`ground` + `arm`) linked by `compatible_with`.
7. **Ground** — wheels or tracks, no arm.

   Wherever the rules mention wheels or tracks (rules 3, 6 and 7), they count only when the robot moves itself on them as part of its task, including between work stations (a mobile manipulator that drives to a station and parks while its arm works is mobile). Wheels or casters on which people move it between jobs (a surgical patient cart, a cobot on a trolley, a humanoid torso on a caster stand), even with power assist, do not count, and nor do passive wheels on a robot that moves by bending its body. Such robots are fixed-base.

   An arm "manipulates" when it positions a tool, gripper or sensor head in space, so an inspection arm that only carries a camera is still an arm.

8. **Arm** — fixed base, manipulates.
9. **Stationary** — fixed base, does not manipulate, not humanoid in form.

Unplaced: limbless locomotors — snake, inchworm and peristaltic (worm) robots that move by changing their body shape — have no legs, wheels, medium or fixed base and raise *unclassifiable*; a branch will be added when a purchasable case exists. Passive wheels do not change that, and inchworm or peristaltic pipe robots are in this group too. Everything else called a snake or crawler robot already has a place: crawlers on driven wheels or tracks (pipe and tank inspection crawlers, snake-shaped robots on tracks) are `ground`; swimming snakes are `aquatic` (rule 5); snake-arms and vine robots, which reach in from a fixed base, are `continuum` arms.

### 2.2 Things that are deliberately NOT branches

| Looks like a category | Why it is an attribute | Attribute |
|---|---|---|
| Cobot / collaborative robot | A safety feature of an arm (power and force limiting); under ISO 10218:2025 the application, not the robot, is collaborative | `collaborative` |
| Robot dog | Marketing name for quadruped | `aliases` |
| Robot vacuum, lawn mower, pool cleaner | Wheeled robots with a domestic application | `application` |
| AMR / AGV | Wheeled; AMR vs AGV is a navigation distinction | `navigation` |
| Delivery / cleaning / inspection robot | Application | `application` |
| Industrial robot | Segment + application group | `segment: professional` + `application_group: manufacturing` |
| Dual-arm robot | Count of arms | `arm_count` |
| Desktop / hobby arm | Articulated arm, hobby segment | `segment` |
| Industrial / service / medical (ISO 8373) | Intended use, not hardware | `iso_category` |
| Drone | Aerial robot | `aliases` |
| Telepresence robot | Wheeled, application telepresence | `application` |
| Surgical / medical robot | Intended use and regulatory status; the body plan decides the branch | `iso_category: medical`, `segment: clinical`, `medical_clearance` |
| Soft robot / exosuit | A construction choice; the body plan decides the branch (soft grippers are a gripping principle, `cp-1-1-4`) | `construction` (exoskeletons) |
| Climbing / magnetic crawler | Wheeled or tracked robot that holds on to the surface | `adhesion` |

---

## 3. Robot attributes

### 3.1 Attribute record

Shopify attributes are enum-only. Robots need numbers with units, so the attribute record is extended:

| Field | Values |
|---|---|
| `type` | `enum`, `number`, `bool`, `text`, `ref` |
| `multi` | `true` for multi-select enums / lists |
| `unit` | SI unit for `number` (`kg`, `mm`, `m/s`, `min`, `Nm`, `N`, `Wh`, `V`, `m`, `TOPS`) |
| `values` | list of value `friendly_id`s (enum only); every enum ends with `<attr>__other` |
| `ref_target` | `robot`, `component`, `manufacturer` (ref only) |
| `question` | The one defining question an editor answers |
| `bases` | Number attributes only: the ways the figure can be measured (§3.5). The first is the default |

### 3.2 Universal attributes (bound at root `rb`, inherited by every robot)

| friendly_id | Type | Vocabulary / unit | Defining question |
|---|---|---|---|
| `manufacturer` | ref → manufacturer | | Who makes it? |
| `model` | text | | Official model name |
| `variant` | text | | Sub-model / configuration, if listed separately |
| `aliases` | text, multi | | Other names people search for |
| `segment` | enum, multi | `hobby`, `education`, `research`, `professional`, `consumer`, `clinical` | Which of these groups would plausibly buy this at list price? (D3; `clinical` added 2026-11-09) |
| `application_group` | enum, multi | derived from `application` | — |
| `application` | enum, multi | see 3.4 | What is it marketed to do? |
| `iso_category` | enum | `industrial`, `service`, `medical` | ISO 8373 intended use, as positioned by the manufacturer |
| `environment` | enum, multi | `indoor`, `outdoor`, `underwater`, `airborne`, `hazardous`, `space` | Where is it rated to operate? |
| `autonomy` | enum | `teleoperated`, `programmed`, `assisted`, `semi-autonomous`, `autonomous` | Highest level of unsupervised operation out of the box (`programmed`: runs a taught or coded sequence without sensing its surroundings) |
| `collaborative` | bool | | Does the maker state it meets the ISO 10218-1:2025 (or ISO/TS 15066) requirements for collaborative applications? |
| `medical_clearance` | enum, multi | `us-fda`, `eu-ce`, `cn-nmpa`, `jp-pmda` | In which markets does the maker state it is legally marketed as a medical device? (US: FDA cleared, approved, De Novo or 510(k)-exempt listing; EU: CE-marked; China: NMPA; Japan: MHLW after PMDA review) |
| `availability` | enum | `shipping`, `preorder`, `announced`, `research-only`, `discontinued` | Can you buy it today? |
| `price` | number + `currency`, `price_date`, `price_source` | | List price as published (date and source required) |
| `release_year` | number | year | First commercial availability |
| `country` | enum | ISO 3166 | Manufacturer HQ |
| `mass` | number | kg | |
| `payload` | number | kg | Rated payload (arm: at wrist; mobile: on deck) |
| `battery_runtime` | number | min | Manufacturer-rated |
| `ip_rating` | text | IPxx | |
| `open_source` | enum, multi | `hardware`, `software`, `none` | |
| `sdk` | enum, multi | `ros1`, `ros2`, `python`, `cpp`, `proprietary`, `none` | |
| `compatible_with` | ref → component/robot, multi | | Officially supported accessories / platforms |
| `sources` | text, multi | URL + date | Where each fact came from |

### 3.3 Branch-bound attributes (listed on the branch node, inherited by its children)

| Bound at | friendly_id | Type | Unit / vocab |
|---|---|---|---|
| `arm` | `axes` | number | count |
| `arm` | `reach` | number | mm |
| `arm` | `repeatability` | number | mm |
| `arm` | `arm_count` | number | 1, 2 |
| `arm` | `mounting` | enum, multi | `floor`, `table`, `wall`, `ceiling`, `mobile` |
| `humanoid`, `legged` | `height` | number | mm |
| `humanoid`, `legged` | `dof_total` | number | count, excl. hands |
| `humanoid`, `legged` | `hands_included` | enum | `none`, `gripper`, `dexterous-hand`, `optional` |
| `humanoid`, `legged` | `max_speed` | number | m/s |
| `legged` | `wheel_feet` | bool | |
| `legged`, `ground` | `has_arm` | bool | arm sold as an add-on |
| `ground`, `mobile-manipulator` | `drive_config` | enum | `differential`, `omnidirectional`, `ackermann`, `tracked`, `skid-steer`, `self-balancing` |
| `ground` | `adhesion` | enum | `none`, `magnetic`, `vacuum` |
| `ground` | `navigation` | enum | `line-following`, `marker-based`, `slam`, `none` |
| `aerial` | `flight_time` | number | min |
| `aerial` | `max_takeoff_weight` | number | kg |
| `aquatic` | `depth_rating` | number | m |
| `wearable` | `body_region` | enum, multi | `lower-limb`, `upper-limb`, `back`, `full-body` |
| `exoskeleton` | `construction` | enum | `rigid`, `soft` |
| `continuum` | `outer_diameter` | number | mm |

### 3.4 `application` vocabulary — two levels (D3)

`application_group` is derived from the value and is itself filterable.

| Group | Values |
|---|---|
| `manufacturing` | `handling`, `machine-tending`, `palletizing`, `welding`, `assembly`, `painting-dispensing`, `machining`, `inspection-qc` |
| `logistics` | `warehouse-logistics`, `delivery`, `transport` |
| `professional-service` | `professional-cleaning`, `inspection-maintenance`, `agriculture`, `construction`, `security`, `search-rescue`, `hospitality-retail` |
| `consumer` | `domestic-cleaning`, `lawn-garden`, `pool`, `companionship`, `entertainment`, `telepresence` |
| `health` | `surgery`, `rehabilitation`, `care-assistance` |
| `knowledge` | `education`, `research-platform` |
| — | `general-purpose` (platforms sold without a stated task, e.g. humanoids) |

"Industrial robots" on the site = saved filter `segment: professional` AND `application_group: manufacturing`. Seeded from IFR groups; we own the list.

---

### 3.5 Measurement bases (2026-11)

Makers publish the same quantity on different bases: a quadruped's payload walking or standing, a runtime with or without load, a top speed in normal use or a burst "limit". Products are compared side by side only if the basis is known, so every number attribute that is published in more than one way lists its **bases**. The first is the default.

- Record the figure on the **default basis**. If the source gives several, record only the default.
- If the source gives **only another basis**, record that figure and label it with the basis (e.g. payload 120 kg, basis `standing`). Catalogues store the label next to the value; displays show it ("120 kg · standing").
- Never derive one basis from another, and never record package or shipping weight as mass.

| Attribute | Default basis | Other bases |
|---|---|---|
| `mass` | `operating`: ready to operate, with battery, no payload; arm without controller | `without-battery`, `with-controller` |
| `payload` | `rated`: arm and mobile manipulator at the flange; mobile, legged or humanoid robot while moving; humanoid with both arms; end-effector held object | `max`, `standing`, `per-arm`, `towing` |
| `battery_runtime` | `rated`: the headline figure in normal use without payload; a range → its upper end | `loaded`, `standby` |
| `max_speed` | `rated`: normal operation | `limit` (burst / peak / record) |
| `flight_time` | `max`: the maker's maximum (no wind, no payload) | `hover`, `with-payload` |
| `height` | `standing`, including head | — |
| `reach` | `max`; SCARA = J1 + J2 arm length | — |
| `repeatability` | `pose` (ISO 9283), ± value as a positive number | — |
| `grip_force` | `max` | `continuous` |
| `range` | `max` | `at-10pct` (lidar at 10 % reflectivity) |
| `ai_tops` | `stated`: the maker's headline figure | `sparse` |
| `stall_torque` | `nominal-voltage`: at the voltage recorded in `voltage` | — |

**Conversions** (not bases): hours → minutes; km/h → m/s; kg·cm → Nm (× 0.0981); mAh → Wh only when the same source states the nominal voltage.

**Not applicable.** A product can lack a quantity altogether (a corded pool robot has no battery runtime). Catalogues record that separately from "not published", so displays can show *n/a* rather than a gap.

## 4. Component hierarchy (by component type)

Root: `cp` / `component`. Lists only things **sold separately**. Parts integrated into a robot are specs, not entries.

```
cp        component
cp-1      ├─ end-effector
cp-1-1    │  ├─ gripper
cp-1-1-1  │  │  ├─ finger          Mechanical fingers/jaws: parallel, angular, 2–3 finger adaptive
cp-1-1-2  │  │  ├─ vacuum          Suction cups, foam, area grippers
cp-1-1-3  │  │  ├─ magnetic
cp-1-1-4  │  │  └─ soft            Compliant / inflatable fingers
cp-1-2    │  ├─ hand               Anthropomorphic, ≥4 fingers incl. opposable thumb, multi-DOF
cp-1-3    │  ├─ tool               Process tools: welding torch, spindle, screwdriver, dispenser (a wrist camera is a sensor)
cp-1-4    │  └─ tool-changer       Quick-change couplings
cp-2      ├─ actuator
cp-2-1    │  ├─ joint-module       Integrated rotary unit: motor + reducer + encoder + driver
cp-2-2    │  ├─ servo              Hobby / smart servos with built-in control
cp-2-3    │  ├─ motor              Bare motors: BLDC, stepper, frameless
cp-2-4    │  ├─ reducer            Harmonic / strain-wave, cycloidal / RV, planetary
cp-2-5    │  └─ linear             Roller screw, ball screw, pneumatic / hydraulic cylinder
cp-3      ├─ sensor
cp-3-1    │  ├─ camera             RGB, depth, stereo, event
cp-3-2    │  ├─ lidar
cp-3-3    │  ├─ force-torque
cp-3-4    │  ├─ tactile
cp-3-5    │  ├─ inertial           IMU, encoders
cp-3-6    │  └─ range-positioning  GNSS, radar, ultrasonic / ToF rangefinders
cp-4      ├─ compute               Robot controllers, SBCs, edge-AI modules
cp-5      ├─ power                 Battery packs, chargers, docking stations
cp-6      ├─ structure             Frames, mounts, enclosures, flanges, cable management
cp-7      └─ teleoperation         Leader arms, haptic devices, VR / motion-capture rigs (D2)
```

### 4.1 Tie-break rules

1. **Hand vs gripper** — ≥4 fingers with an opposable thumb and ≥6 *actuated* DOF → `hand`; otherwise `gripper`.
2. **Gripper leaf** — by gripping principle (fingers / vacuum / magnetic / soft), not by actuation. Actuation is an attribute. Bernoulli and other non-contact suction → `vacuum`; granular-jamming → `soft`.
3. **Joint-module vs servo** — the bus does not decide (RS-485 and CAN appear on both sides). Integrated reducer + controller, sold as a robot joint (robot-grade packaging, torque rating, EtherCAT/CAN/high-speed RS-485) → `joint-module` (`joint_grade: true`); packaged hobby-grade servo on a daisy-chain bus → `servo`. A motor with a gearhead but no driver (gearmotor) → `motor`.
4. **Tool with gripping function** — by primary marketed purpose.
5. **Compute vs sensor** — a camera with onboard AI is still `sensor.camera`; a module without sensing is `compute`. A device with several sensing modalities is classified by its primary output; capacitive pre-touch skins are `tactile`.
6. **Teleoperation vs sensor** — anything sold to drive or teach a robot (gloves, leader arms, rigs) is `teleoperation`, however many sensors it contains.
7. **Power vs structure** — a docking station is `power`.

### 4.2 Why this differs from the brief's "actuators → grippers → hands"

Actuators are *inside* grippers and hands; they are not a parent category. `hand` and `gripper` are siblings under `end-effector`; `actuator` is a separate branch. A hand references the actuator it uses via `uses_components`. 

---

## 5. Component attributes

### 5.1 Universal (bound at `cp`)

`manufacturer`, `model`, `variant`, `aliases`, `segment`, `availability`, `price` (+date, source), `release_year`, `country`, `mass`, `ip_rating`, `open_source`, `sdk`, `sources` — as for robots — plus:

| friendly_id | Type | Vocabulary / unit |
|---|---|---|
| `compatible_with` | ref → robot, multi | Officially supported robots |
| `mounting` | enum, multi | `iso-9409-1-50`, `iso-9409-1-31`, `custom`, `na` |
| `interface` | enum, multi | `ethercat`, `can`, `modbus-tcp`, `rs485`, `usb`, `ethernet`, `io-link`, `digital-io`, `pneumatic` |
| `voltage` | number | V |
| `actuation` | enum | `electric`, `pneumatic`, `hydraulic`, `vacuum`, `passive` |

### 5.2 Branch-bound

| Bound at | friendly_id | Type | Unit / vocab |
|---|---|---|---|
| `gripper` | `grip_force` | number | N |
| `gripper` | `stroke` | number | mm |
| `gripper` | `finger_count` | number | |
| `gripper`, `hand` | `payload` | number | kg |
| `hand` | `dof` | number | active DOF |
| `hand` | `finger_count` | number | |
| `hand` | `tactile_sensing` | bool | |
| `joint-module`, `motor` | `rated_torque` | number | Nm |
| `joint-module`, `motor` | `peak_torque` | number | Nm |
| `joint-module`, `reducer` | `reducer_type` | enum | `harmonic`, `cycloidal`, `rv`, `planetary`, `quasi-direct`, `none` |
| `joint-module`, `reducer` | `gear_ratio` | number | :1 |
| `linear` | `stroke` | number | mm |
| `linear` | `rated_force` | number | N |
| `servo` | `stall_torque` | number | Nm |
| `servo` | `bus` | enum | `ttl`, `rs485`, `pwm` (`can` retained in values for legacy records) |
| `camera` | `modality` | enum, multi | `rgb`, `depth`, `stereo`, `thermal`, `event` |
| `lidar` | `dimensions` | enum | `2d`, `3d` |
| `lidar` | `range` | number | m |
| `force-torque` | `axes` | number | 3, 6 |
| `compute` | `ai_tops` | number | TOPS |
| `power` | `capacity` | number | Wh |
| `teleoperation` | `teleop_type` | enum | `leader-arm`, `haptic-device`, `vr-rig`, `mocap`, `gamepad` |

---

## 6. Worked examples → classification test set

These become `data/examples.yml` and run in CI: each entry asserts the expected category and must stay true after any change to the tree or tie-break rules.

| Product | Expected category | Key attributes |
|---|---|---|
| Universal Robots UR5e | `rb-1-1` arm › articulated | collaborative: true; segment: professional, research; application: handling, machine-tending |
| Dobot Magician | `rb-1-1` arm › articulated | segment: hobby, education |
| Unitree Go2 | `rb-3-1` legged › quadruped | segment: hobby, research, professional; application: research-platform, inspection-maintenance |
| Unitree B2-W | `rb-3-1` legged › quadruped | wheel_feet: true |
| Boston Dynamics Spot (with arm) | `rb-3-1` legged › quadruped | has_arm: true |
| Unitree G1 | `rb-2-1` humanoid › bipedal | hands_included: optional; application: general-purpose |
| iRobot Roomba | `rb-4-1` ground › wheeled | segment: consumer; application: domestic-cleaning |
| Hello Robot Stretch 3 | `rb-5` mobile-manipulator | segment: research |
| DJI Mavic | `rb-6-1` aerial › multirotor | segment: consumer, professional |
| Robotiq 2F-85 | `cp-1-1-1` gripper › finger | actuation: electric; finger_count: 2; mounting: iso-9409-1-50 |
| Shadow Dexterous Hand | `cp-1-2` hand | finger_count: 5 |
| Dynamixel XM430 | `cp-2-2` servo | bus: ttl / rs485 |
| LEGO Spike Prime | `rb-10` kit | segment: education |
| Intuitive Ion | `rb-1-6` arm › continuum (patient cart counts as fixed base) | segment: clinical; application: surgery; medical_clearance: us-fda, eu-ce, cn-nmpa |

(Product facts are illustrative for the classification test only; verified with dated sources before the first stable release.)

---

## 7. Decisions

### 7.1 Decisions (2026-10-27)

| # | Decision | Notes |
|---|---|---|
| D0 | Taxonomy = one MECE hierarchy per item (robots by body plan; components by component type), max 3 levels, assigned from hardware facts. Everything else is a typed attribute, never a tree branch. | Segment pages are saved filters over the tree. |
| D1 | Aerial, aquatic and wearable are in scope from launch as branches of the robot hierarchy. | §2 |
| D2 | `teleoperation` is a top-level component branch. | §4 |
| D3 | `segment` = hobby, education, research, professional, consumer. No `industrial` segment; manufacturing is an application group under professional use. `application` is a two-level vocabulary (group › value). | "Industrial" pages = saved filter professional + manufacturing. |
| D4 | Taxonomy data model and repository follow Shopify's product-taxonomy pattern: categories / attributes / values as separate source files; positional permanent IDs plus handles; per-category attribute binding; versioned mappings to external taxonomies; CalVer releases with dist files; published on GitHub. | Extended with typed/numeric attributes. §1, §9. |
| D5 | Robot top-level branches: arm, humanoid, legged, ground, mobile-manipulator, aerial, aquatic, wearable, stationary, kit. | Tie-break order §2.1. |
| D6 | Component top-level branches: end-effector, actuator, sensor, compute, power, structure, teleoperation. Grippers and hands are siblings under end-effector; actuators are a separate branch. | Replaces an earlier idea of "actuators → grippers → hands". |
| D7 | `stationary` (rb-9) kept as a robot branch for fixed-base, non-manipulating robots. | Desktop companions / social robots without arms. |
| D8 | Licence: MIT for tooling and schemas; CC BY 4.0 for taxonomy data, distributions and docs content. | Attribution required for reuse. |
| D9 | Repository `whatrobot-taxonomy` under the fysical.ai GitHub org. | Implies fysical.ai owns the taxonomy data. |
| D10 | ETL and validation tooling in Python (pydantic schemas, pytest CI). | Site stack still open (Phase 5). |
| D11 | Taxonomy localised in `en` and `zh-Hans` from the first release. Product content and site language are decided outside this repository. | |

### 7.2 Pending

None.

---

## 8. Open questions

None at taxonomy level. Site stack and Mandarin product content are decided outside this repository.

---

## 9. Data model and repository (Shopify-derived)

### 9.1 Who the repository serves

Three personas, as in Shopify's README:

1. **Integrators** — want stable distribution files (`dist/`) to load into a site, a database or an LLM.
2. **Taxonomists** — want to propose changes to the source files (`data/`) via issues or PRs.
3. **Developers** — maintain the tooling that validates `data/` and generates `dist/` and `docs/`.

### 9.2 Layout

```
whatrobot-taxonomy/                         # github.com/<fysical.ai org>/whatrobot-taxonomy (D9)
├── data/                                   # source of truth — CC BY 4.0 (D8)
│   ├── LICENSE                             # CC BY 4.0
│   ├── categories/
│   │   ├── rb_robot.yml                    # robot tree
│   │   └── cp_component.yml                # component tree
│   ├── attributes.yml
│   ├── values.yml
│   ├── examples.yml                        # classification test set (§6)
│   ├── integrations/                       # mappings to other taxonomies (§9.5)
│   │   ├── integrations.yml
│   │   ├── ifr-industrial/<version>/mappings/{from_whatrobot,to_whatrobot}.yml
│   │   ├── ifr-service/…
│   │   ├── iso-8373/…
│   │   ├── google/…
│   │   └── shopify/…
│   └── localizations/                      # D11
│       ├── en/{categories,attributes,values}.yml
│       └── zh-Hans/{categories,attributes,values}.yml
├── dist/                                   # generated, per locale: json + txt — CC BY 4.0
│   ├── en/{categories,attributes,values}.{json,txt}
│   ├── zh-Hans/…
│   └── integrations/all_mappings.json
├── docs/                                   # interactive explorer (GitHub Pages) — content CC BY 4.0
├── whatrobot_taxonomy/                     # Python package: models, loaders, validators (D10)
├── scripts/                                # one-off maintenance helpers
├── tests/                                  # pytest: schema, integrity, classification tests
├── pyproject.toml
├── VERSION                                 # CalVer, e.g. 2026-01
├── CHANGELOG.md
├── LICENSE                                 # MIT — tooling and schemas
└── README.md
```

Licence boundary (D8): everything under `data/`, `dist/` and the prose/content of `docs/` is CC BY 4.0; code (`whatrobot_taxonomy/`, `scripts/`, `tests/`, pydantic schemas) is MIT. The README states both and gives the attribution line to use.

### 9.3 Record formats

**Category** (`data/categories/rb_robot.yml`)

```yaml
- id: rb-3-1
  name: Quadruped
  friendly_id: robot.legged.quadruped
  handle: quadruped
  description: Legged robot with four legs, not humanoid in form.
  aliases: [robot dog, quadrupedal robot]
  inclusion_rule: Four articulated legs; wheels on feet or an add-on arm do not change the category.
  children: []
  attributes:            # bound here; universal ones are inherited from rb
    - height
    - dof_total
    - hands_included
    - max_speed
    - wheel_feet
    - has_arm
  examples: [unitree-go2, boston-dynamics-spot]
```

**Attribute** (`data/attributes.yml`) — Shopify's record plus `type`, `multi`, `unit`, `ref_target`, `question`:

```yaml
- id: 21
  name: Drive configuration
  friendly_id: drive_config
  handle: drive-config
  description: How a ground robot steers and propels itself.
  question: What drive configuration does the spec sheet state?
  type: enum
  multi: false
  values:
    - drive_config__differential
    - drive_config__omnidirectional
    - drive_config__ackermann
    - drive_config__tracked
    - drive_config__other

- id: 22
  name: Payload
  friendly_id: payload
  handle: payload
  description: Rated payload. Arm: at the wrist. Mobile robot: on the deck.
  type: number
  unit: kg
```

**Value** (`data/values.yml`)

```yaml
- id: 104
  name: Differential
  friendly_id: drive_config__differential
  handle: differential
```

### 9.4 Attribute binding and inheritance

A category's effective attribute set = its own `attributes` + every ancestor's. The two root nodes carry the universal attributes (§3.2, §5.1); branch nodes carry the branch-specific ones (§3.3, §5.2). Tooling resolves this when generating `dist/`, so each category in `dist/en/categories.json` lists its full effective attribute set, as Shopify does.

### 9.5 Integrations (mappings)

Shopify's pattern: per external taxonomy, per version, rules of the form `input → output[]`, plus an explicit `unmapped_product_category_ids` list that CI checks. For whatro.bot the external taxonomies are the standards and marketplaces from the Phase 2 research:

| Integration | Direction | Maps |
|---|---|---|
| `iso-8373` (2021) | from_whatro | category → ISO robot class (`industrial`, `service`, `medical`) — note: derived from `iso_category` attribute, not the tree |
| `ifr-industrial` | both | `rb-1-*` ↔ IFR type classes (articulated, cartesian/linear/gantry, SCARA, parallel, cylindrical, other) |
| `ifr-service` | from_whatro | `application` values → IFR professional / consumer / medical application groups |
| `google` (product taxonomy) | from_whatro | category → closest Google category id |
| `shopify` (product taxonomy) | from_whatro | category → closest Shopify category id |

Example rule:

```yaml
rules:
  - input:
      category_id: rb-1-2          # SCARA
    output:
      category_id:
        - '30'                     # IFR industrial robot type class: SCARA
unmapped_category_ids:
  - rb-10                          # kit — no IFR equivalent
```

### 9.6 Versioning and release

- `VERSION` holds a CalVer tag (`YYYY-MM`); a stable release at most quarterly; `unstable` tracks `main`.
- Every change to `data/` requires regenerating `dist/` and a `CHANGELOG.md` entry.
- Releases publish `dist/` as GitHub release assets, one set per locale (`categories.en.json`, `categories.zh-Hans.json`, …, `integrations.all_mappings.json`, plus `.txt` for humans).
- Categories are never renumbered; retirements leave gaps and get a `whatrobot/<old> → whatrobot/<new>` mapping.

### 9.7 Tooling (D10)

- Python ≥ 3.12. Source records are pydantic models (`whatrobot_taxonomy/models.py`); the JSON Schema for each data file is generated from them, not hand-written.
- YAML handled with ruamel.yaml so source files round-trip without reformatting.
- `whatrobot_taxonomy/cli.py` exposes a CLI (`validate`, `dist`, `docs`, `schema`, `classify`, `release`) — the same verbs as Shopify's `bin/product_taxonomy`.
- `docs/` explorer is a static site generated from `dist/` (must be hostable on GitHub Pages).

### 9.8 Validation (CI)

- Schema validation of every file in `data/` and `dist/`.
- Referential integrity: every `children` id exists; every attribute in a category exists; every value belongs to exactly one attribute; every enum has an `__other`.
- Structural rules: max depth 3; no cycles; every leaf has a `description`, `inclusion_rule` and ≥1 example.
- Classification tests: `data/examples.yml` entries resolve to the expected category under the tie-break rules.
- Mapping completeness: every category is either mapped or listed as unmapped for each integration.
- Localisation completeness: every `en` string has a counterpart in each locale (missing → CI warning, not failure, so English-first changes can land). A field reviewed against English that has since changed is reported as stale (warning).

### 9.9 Localisation (D11)

- Source language `en`; `zh-Hans` (Simplified Chinese, BCP 47) shipped from the first release.
- Scope: category names and descriptions, attribute names and descriptions, value names, and search terms (category aliases in the locale's own words, which replace the English aliases in that locale's dist). Not: inclusion rules or tie-break prose (English only, editorial).
- Review record: each localised entry may carry `source: {field: fingerprint}`. A listed field was reviewed by a native reader against the English text with that fingerprint (12 hex characters of SHA-256 over the whitespace-normalised English). A field not listed is an unreviewed draft; a listed field whose fingerprint no longer matches the English is stale.
- Workflow: `whatrobot-taxonomy l10n export` writes the rows to review (all, or `--only-needed`) → LLM first draft → native reviewers correct the text and tick an OK column in a shared review sheet → `whatrobot-taxonomy l10n import` writes only ticked rows, with fingerprints, into `data/localizations/<locale>/` → PR. Rows whose English changed after the sheet was made are held back and re-exported.
- `whatrobot-taxonomy l10n status` reports reviewed / stale / draft / missing per locale. A stable `release` requires every locale to be fully reviewed (`--allow-unreviewed` overrides).
- Further locales (e.g. `da`, `de`) are added by importing a first reviewed batch, which creates `localizations/<locale>/`; no structural change.

### 9.10 Contribution

- Issue templates: *category change request*, *attribute/value request*, *mapping fix*, *localisation fix*.
- PRs edit `data/` only; `dist/` is regenerated by tooling.
- CLA deferred until there are external contributors.

### 9.11 Not carried over from Shopify

`return_reasons`; default `color` / `pattern` on every node; Ruby + cue toolchain; MIT on the data.

---

## 10. Implementation notes (deltas from the text above)

Applied in `data/` during implementation; this document has not been rewritten around them.

| Change | Why |
|---|---|
| Component `mounting` → `flange_standard` | `mounting` already exists on arms with a different vocabulary. |
| Lidar `dimensions` → `scan_dimensions` | "dimensions" reads as physical size. |
| `axes`, `stroke`, `finger_count`, `payload` are single shared attributes bound in several places | Same meaning, type and unit. |
| `uses_components` added (component universal, ref → component) | Referenced in §4.2 but missing from §5.1. |
| `application_group__general` added | Every `application` value must belong to exactly one group. |
| `mobile-manipulator` additionally binds `axes`, `reach`, `arm_count` | A mobile manipulator has an arm. |
| Attribute record gains `companions` (price → currency, price_date, price_source) and `derived_from` (application_group → application) | Rules stated in prose become data. |
| Mapping files gain `input_kind: attribute_value` and `scope: [rb\|cp]` | IFR service and ISO 8373 map attributes, not the tree; IFR industrial covers robots only. |

### 10.1 Rulings from the catalogue and content work (2026-10-29)

| Change | Why |
|---|---|
| `rb-8-2` Prosthesis added; wearable rule excludes passive exoskeletons | Powered prostheses met the wearable rule but were not exoskeletons. |
| `cp-3-6` Range / positioning sensor added | GNSS, radar and ultrasonic sensors had no leaf. |
| Wheeled-base humanoid requires a head and human proportions; otherwise mobile manipulator | Galbot G1 / AgiBot G1 boundary. |
| Humanoid with legs ≠ 2 is unclassifiable (was: filed under bipedal) | Four legs under a torso is not "bipedal". |
| Joint module vs servo decided by `joint_grade`, not bus; CAN removed from servo rule | Dynamixel (RS-485) vs Unitree GO-M8010 (RS-485). |
| ROV = tethered, even if autonomous; multirotor = one or more rotors | Corded pool cleaners; helicopters. |
| Hand threshold = actuated DOF | Inspire RH56 (6 actuated / 12 joints). |
| `flange_standard`, `actuation` moved from `cp` root to end-effector (+ `actuation` on actuator); `stroke`, `finger_count` moved from gripper to finger and soft grippers | Meaningless on sensors, compute, power; on vacuum and magnetic grippers. |
| `rb-1-5` renamed Cylindrical & spherical arm (IFR class 30) | Description included polar arms the rule excluded. |
| Rule text: tool excludes camera heads; motor includes gearmotors; power includes docks; teleoperation wins over sensor; vacuum includes Bernoulli; soft includes granular jamming; tactile includes capacitive pre-touch; stationary is non-humanoid; multi-legged alias "hexapod walker" | Ambiguities found while writing the category pages. |
| `stall_torque` unit Nm (was kg·cm) | Matches rated_torque and the recorded data. |
| Components stay without `application` | Revisit when the site shows demand. |

### 10.2 Rulings from catalogue batch 1 (2026-11-09)

Proposed after the batch that filled every empty leaf (catalogue PR #13); accepted by Simon 2026-11-09. Additive except where noted.

| Change | Why |
|---|---|
| Aerial (`rb-6`): `max_speed`, `flight_range` (km); fixed-wing and hybrid VTOL: `wingspan` (mm), `cruise_speed` (m/s). `battery_runtime` stays universal but is recorded as not applicable on aerial robots | Survey drones publish these; `flight_time` is a drone's runtime. |
| `application` values `mapping-surveying` and `lab-automation` (group professional service; IFR: other professional service) | Six batch-1 records had to use `other` or `handling`. |
| `segment` value `clinical` | Prostheses are fitted and sold through clinicians. **Amends D3** (the user-type list). |
| Wearable (`rb-8`): `max_user_weight` (kg); prosthesis: `load_limit` (kg). `autonomy` is recorded as not applicable on prostheses | A hand's static load limit is not a payload; user-weight limits are what buyers check. |
| Cartesian arm: `stroke_x`, `stroke_y`, `stroke_z` (mm); cylindrical arm: `stroke_z`. `reach` is recorded as not applicable on Cartesian arms | Gantries publish a work envelope, not a reach. |
| `teleop_type` value `handheld-demonstrator` | UMI-style data-collection grippers (TRumi, PiKA Sense). |
| `interface` values `uart`, `i2c`, `spi`, `rs232`, `rs422`, `modbus-rtu`, `analog` | Sensors and small actuators fell back to `other`. |
| Component root: `voltage_min`, `voltage_max` (V). `voltage` stays the nominal voltage; a stated input range goes in min/max | Sensor and compute supplies are ranges (e.g. 19–54 V). |
| Range/positioning: `position_accuracy` (mm), `update_rate` (Hz); inertial: `heading_accuracy`, `attitude_accuracy` (deg), `update_rate`; force-torque: `force_range` (N), `torque_range` (Nm) | These leaves had no specific numbers. A maker's "Not rated" IP is recorded as not applicable. |
| `rated_force` gains bases `continuous` (default) and `max`; motors bind `stall_torque` (description generalised); linear actuators bind `linear_speed` (mm/s) and `repeatability` | Makers publish maximum force, not continuous force. |
| `payload` moves from end-effector (`cp-1`) to grippers, hands and tool changers, so Tool loses it; `payload` gains basis `shear`; soft grippers bind `grip_range` (mm) | Payload means nothing for a screwdriver or sander; magnetic and vacuum figures depend on load direction. |
| A gripper or tool sold with its own controller, feeder or pump is one product; the parts are listed in the record | Robotiq screwdriving kit, SRT soft gripper kit. |
| `rb-1-4` example `igus-drylin-gantry` → `igus-dle-rg-0001` | The example now exists as a catalogue record. |

### 10.4 Review of the multi-dimensional taxonomy, snake and soft robots, medical scope (2026-11-09)

Proposed while comparing the taxonomy with a six-axis "multi-dimensional" robot taxonomy (morphology, autonomy, human–robot interaction, actuation and scale, multi-agent organisation, application); accepted by Simon 2026-11-09. The structure stands: the other axes are already attributes. Additive except where noted.

| Change | Why |
|---|---|
| New leaf `rb-1-6` Continuum arm (binds `outer_diameter`, mm). Test: a continuous backbone, or more bending segments than independently driven joints; it wins over articulated; an arm whose every joint has its own drive stays articulated; with a positioning arm plus continuum instrument, the instrument decides. A continuum body counts as manipulating even if it only carries a camera | Snake-arm robots have many rotary segments and would otherwise land in articulated; robotic catheters have no discrete joints and fitted no leaf. IFR industrial: unmapped; Google and Shopify: as the other arms |
| Rules 3, 6, 7: wheels or tracks count only when the robot moves itself on them as part of its task, including between work stations; wheels or casters people move it on (even power-assisted) and passive wheels do not | Surgical patient carts, cobots on trolleys, humanoid torsos on caster stands; mobile manipulators that park at a station stay mobile |
| Unplaced robots narrowed to limbless locomotors (snake, inchworm, peristaltic); wheeled and tracked crawlers are ground robots, swimming snakes aquatic, snake-arms and vine robots continuum arms | "Crawler" in industry means a wheeled or tracked inspection vehicle |
| `adhesion` on ground robots: `none`, `magnetic`, `vacuum` | Wall-, tank- and hull-climbing inspection crawlers |
| `construction` on exoskeletons: `rigid`, `soft` | Soft exosuits and rigid exoskeletons differ in what buyers check (comfort, assistance) |
| `medical_clearance` on every robot: `us-fda`, `eu-ce`, `cn-nmpa`, `jp-pmda` — markets where the maker states it is legally marketed as a medical device (510(k)-exempt listing counts in the US) | Medical and surgical robots are in scope as reference entries; availability differs by market |
| `collaborative` reworded to ISO 10218-1:2025 ("collaborative applications"; the earlier ISO/TS 15066 still accepted). Same identifier and evidence bar: the maker must state it | ISO 10218:2025 drops the term "collaborative robot": an application, not a robot, is confirmed as collaborative |
| `autonomy` value `programmed` | Arms and gantries that run taught programs without sensing had no fitting value |
| `drive_config` values `skid-steer`, `self-balancing`; every value now defined in the attribute description; the value is what the maker states | Four- and six-wheel field robots describe themselves as skid-steer; two-wheel balancing robots had no value |
| Parallel arm rule, description and aliases cover cable-driven parallel robots | Cables pulled by winches are parallel kinematic chains |
| Medical and surgical robots in scope as reference entries (§2): classified by body plan; medical use is `iso_category: medical`, user type `clinical`, application group `health` and `medical_clearance` | The guide aims to be comprehensive; powered prostheses were already in |
