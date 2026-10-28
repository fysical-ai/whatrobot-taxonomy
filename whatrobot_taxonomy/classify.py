"""Tie-break rules (docs/design.md §2.1 and §4.1), as code.

`classify(facts)` takes hardware facts and returns the category id. The order of the rules IS the
specification: the first rule that matches decides. data/examples.yml is the regression suite.

Robot facts (all optional; missing = false / none):
  is_kit, worn_on_body, humanoid_form           bool
  legs                                           int   (0, 2, 4, 6+)
  wheels_or_tracks                               none | wheels | tracks
  medium                                         ground | air | water
  aerial_lift                                    multirotor | fixed-wing | hybrid-vtol
  aquatic_mode                                   rov | auv | usv
  integrated_arm, manipulates, fixed_base        bool
  arm_kinematics                                 articulated | scara | parallel | cartesian | cylindrical

Component facts:
  component_kind   end-effector | actuator | sensor | compute | power | structure | teleoperation
  end-effector:    grasps bool, fingers int, opposable_thumb bool, dof int,
                   gripping_principle finger|vacuum|magnetic|soft, process_tool bool, tool_changer bool
  actuator:        motion rotary|linear, reducer_only bool, integrated_control bool, has_reducer bool, industrial_bus bool
  sensor:          sensor_type camera|lidar|force-torque|tactile|inertial
"""
from __future__ import annotations

from typing import Any

Facts = dict[str, Any]


class Unclassifiable(ValueError):
    pass


ARM_LEAF = {"articulated": "rb-1-1", "scara": "rb-1-2", "parallel": "rb-1-3", "cartesian": "rb-1-4", "cylindrical": "rb-1-5"}
AERIAL_LEAF = {"multirotor": "rb-6-1", "fixed-wing": "rb-6-2", "hybrid-vtol": "rb-6-3"}
AQUATIC_LEAF = {"rov": "rb-7-1", "auv": "rb-7-2", "usv": "rb-7-3"}
GRIPPER_LEAF = {"finger": "cp-1-1-1", "vacuum": "cp-1-1-2", "magnetic": "cp-1-1-3", "soft": "cp-1-1-4"}
SENSOR_LEAF = {"camera": "cp-3-1", "lidar": "cp-3-2", "force-torque": "cp-3-3", "tactile": "cp-3-4", "inertial": "cp-3-5"}
SIMPLE_COMPONENT = {"compute": "cp-4", "power": "cp-5", "structure": "cp-6", "teleoperation": "cp-7"}


def classify(facts: Facts) -> str:
    if "component_kind" in facts:
        return classify_component(facts)
    return classify_robot(facts)


def _int(f: Facts, key: str) -> int:
    v = f.get(key, 0) or 0
    try:
        return int(v)
    except (TypeError, ValueError) as e:
        raise Unclassifiable(f"{key} must be an integer, got {v!r}") from e


def classify_robot(f: Facts) -> str:
    legs = _int(f, "legs")
    wheels = f.get("wheels_or_tracks", "none") or "none"

    # 1. Kit
    if f.get("is_kit"):
        return "rb-10"
    # 2. Wearable
    if f.get("worn_on_body"):
        return "rb-8-1"
    # 3. Humanoid — locomotion decides level 2
    if f.get("humanoid_form"):
        if legs >= 2:
            return "rb-2-1"
        if wheels in ("wheels", "tracks"):
            return "rb-2-2"
        return "rb-2-3"
    # 4. Legged — wheel-feet and add-on arms do not change the branch
    if legs >= 6:
        return "rb-3-3"
    if legs == 4:
        return "rb-3-1"
    if legs == 2:
        return "rb-3-2"
    if legs in (1, 3, 5):
        raise Unclassifiable(f"no category for {legs} legs")
    # 5. Aquatic / aerial — primary operating medium
    medium = f.get("medium")
    if medium == "air":
        lift = f.get("aerial_lift")
        if not isinstance(lift, str) or lift not in AERIAL_LEAF:
            raise Unclassifiable("aerial robot needs aerial_lift")
        return AERIAL_LEAF[lift]
    if medium == "water":
        mode = f.get("aquatic_mode")
        if not isinstance(mode, str) or mode not in AQUATIC_LEAF:
            raise Unclassifiable("aquatic robot needs aquatic_mode")
        return AQUATIC_LEAF[mode]
    # 6. Mobile manipulator — ground base + arm(s) as one product
    if wheels in ("wheels", "tracks") and f.get("integrated_arm"):
        return "rb-5"
    # 7. Ground — wheels or tracks, no arm
    if wheels == "wheels":
        return "rb-4-1"
    if wheels == "tracks":
        return "rb-4-2"
    # 8. Arm — fixed base, manipulates
    if f.get("fixed_base") and f.get("manipulates"):
        kin = f.get("arm_kinematics")
        if kin not in ARM_LEAF:
            raise Unclassifiable("arm needs arm_kinematics")
        return ARM_LEAF[kin]
    # 9. Stationary — fixed base, does not manipulate
    if f.get("fixed_base"):
        return "rb-9"
    raise Unclassifiable(f"no rule matched robot facts {f}")


def classify_component(f: Facts) -> str:
    kind = f.get("component_kind")
    if kind in SIMPLE_COMPONENT:
        return SIMPLE_COMPONENT[kind]

    if kind == "end-effector":
        if f.get("tool_changer"):
            return "cp-1-4"
        if f.get("grasps"):
            # 4.1.1 hand vs gripper
            if _int(f, "fingers") >= 4 and f.get("opposable_thumb") and _int(f, "dof") >= 6:
                return "cp-1-2"
            # 4.1.2 gripper leaf by gripping principle
            principle = f.get("gripping_principle")
            if not isinstance(principle, str) or principle not in GRIPPER_LEAF:
                raise Unclassifiable("gripper needs gripping_principle")
            return GRIPPER_LEAF[principle]
        if f.get("process_tool"):
            return "cp-1-3"
        raise Unclassifiable("end-effector neither grasps, processes nor changes tools")

    if kind == "actuator":
        if f.get("motion") == "linear":
            return "cp-2-5"
        if f.get("reducer_only"):
            return "cp-2-4"
        if f.get("integrated_control"):
            # 4.1.3 joint-module vs servo
            return "cp-2-1" if (f.get("has_reducer") and f.get("industrial_bus")) else "cp-2-2"
        return "cp-2-3"

    if kind == "sensor":
        st = f.get("sensor_type")
        if not isinstance(st, str) or st not in SENSOR_LEAF:
            raise Unclassifiable("sensor needs sensor_type")
        return SENSOR_LEAF[st]

    raise Unclassifiable(f"unknown component_kind {kind!r}")
