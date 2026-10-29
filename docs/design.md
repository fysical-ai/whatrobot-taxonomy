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
rb-1-3  │  ├─ parallel         Parallel kinematics (delta, hexapod/Stewart)
rb-1-4  │  ├─ cartesian        Three prismatic axes (linear, gantry, XYZ)
rb-1-5  │  └─ cylindrical      Rotary base + prismatic lift + prismatic reach (incl. polar/spherical)
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
rb-8-1  │  └─ exoskeleton      Powered exoskeleton / exosuit
rb-9    ├─ stationary          Fixed, does not manipulate (desktop companions, social robots without arms)
rb-10   └─ kit                 Modular construction kit with no fixed body plan
```

Scope (D1): aerial, aquatic and wearable are in scope from launch. `kit` includes only kits that produce a programmable robot.

### 2.1 Tie-break rules for hybrids

Apply in order; the first rule that matches decides the branch.

1. **Kit** — sold as parts to be assembled into user-chosen forms → `kit`.
2. **Wearable** — worn on the body → `wearable`.
3. **Humanoid** — torso + two arms + head in human proportion → `humanoid` (locomotion decides level 2).
4. **Legged** — articulated legs → `legged`, even with wheels on the feet (`wheel_feet: true`) or an arm on the back (`has_arm: true`).
5. **Aquatic / Aerial** — primary operating medium. Amphibious → the medium it is marketed for.
6. **Mobile manipulator** — ground base + arm(s) as one product → `mobile-manipulator`. Base and arm sold separately = two entries (`ground` + `arm`) linked by `compatible_with`.
7. **Ground** — wheels or tracks, no arm.
8. **Arm** — fixed base, manipulates.
9. **Stationary** — fixed base, does not manipulate.

### 2.2 Things that are deliberately NOT branches

| Looks like a category | Why it is an attribute | Attribute |
|---|---|---|
| Cobot / collaborative robot | Safety rating of an articulated arm, not a structure | `collaborative` |
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

### 3.2 Universal attributes (bound at root `rb`, inherited by every robot)

| friendly_id | Type | Vocabulary / unit | Defining question |
|---|---|---|---|
| `manufacturer` | ref → manufacturer | | Who makes it? |
| `model` | text | | Official model name |
| `variant` | text | | Sub-model / configuration, if listed separately |
| `aliases` | text, multi | | Other names people search for |
| `segment` | enum, multi | `hobby`, `education`, `research`, `professional`, `consumer` | Which of these groups would plausibly buy this at list price? (D3) |
| `application_group` | enum, multi | derived from `application` | — |
| `application` | enum, multi | see 3.4 | What is it marketed to do? |
| `iso_category` | enum | `industrial`, `service`, `medical` | ISO 8373 intended use, as positioned by the manufacturer |
| `environment` | enum, multi | `indoor`, `outdoor`, `underwater`, `airborne`, `hazardous`, `space` | Where is it rated to operate? |
| `autonomy` | enum | `teleoperated`, `assisted`, `semi-autonomous`, `autonomous` | Highest level of unsupervised operation out of the box |
| `collaborative` | bool | | Rated for unguarded operation alongside people (ISO 10218 / ISO/TS 15066)? |
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
| `ground`, `mobile-manipulator` | `drive_config` | enum | `differential`, `omnidirectional`, `ackermann`, `tracked` |
| `ground` | `navigation` | enum | `line-following`, `marker-based`, `slam`, `none` |
| `aerial` | `flight_time` | number | min |
| `aerial` | `max_takeoff_weight` | number | kg |
| `aquatic` | `depth_rating` | number | m |
| `wearable` | `body_region` | enum, multi | `lower-limb`, `upper-limb`, `back`, `full-body` |

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
cp-1-3    │  ├─ tool               Process tools: welding torch, spindle, screwdriver, dispenser, camera head
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
cp-3-5    │  └─ inertial           IMU, encoders
cp-4      ├─ compute               Robot controllers, SBCs, edge-AI modules
cp-5      ├─ power                 Battery packs, chargers, docking stations
cp-6      ├─ structure             Frames, mounts, enclosures, flanges, cable management
cp-7      └─ teleoperation         Leader arms, haptic devices, VR / motion-capture rigs (D2)
```

### 4.1 Tie-break rules

1. **Hand vs gripper** — ≥4 fingers with an opposable thumb and ≥6 DOF → `hand`; otherwise `gripper`.
2. **Gripper leaf** — by gripping principle (fingers / vacuum / magnetic / soft), not by actuation. Actuation is an attribute.
3. **Joint-module vs servo** — reducer + industrial comms (EtherCAT/CAN), sold for robot joints → `joint-module`; packaged hobby-grade servo with daisy-chain bus → `servo`.
4. **Tool with gripping function** — by primary marketed purpose.
5. **Compute vs sensor** — a camera with onboard AI is still `sensor.camera`; a module without sensing is `compute`.

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
| `servo` | `bus` | enum | `ttl`, `rs485`, `can`, `pwm` |
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
- Localisation completeness: every `en` string has a `zh-Hans` counterpart (missing → CI warning, not failure, so English-first changes can land).

### 9.9 Localisation (D11)

- Source language `en`; `zh-Hans` (Simplified Chinese, BCP 47) shipped from the first release.
- Scope: category names and descriptions, attribute names and descriptions, value names, alias lists. Not: inclusion rules or tie-break prose (English only, editorial).
- Workflow: LLM-drafted translation → native-reader review → PR. Translators edit `data/localizations/zh-Hans/` only.
- Further locales (e.g. `da`) are added by creating a new `localizations/<locale>/` folder; no structural change.

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
