"""One-off helper: generate data/values.yml entries for enum values that do not yet exist.

Usage: python scripts/scaffold_values.py
Existing values keep their ids; new ones get the next free integer id.
values.yml remains the source of truth after generation — edit names there, not here.
"""
from __future__ import annotations

from pathlib import Path

from ruamel.yaml import YAML

ROOT = Path(__file__).resolve().parents[1]
yaml = YAML()
yaml.default_flow_style = False
yaml.width = 120

NAME_OVERRIDES = {
    "ros1": "ROS 1",
    "ros2": "ROS 2",
    "cpp": "C++",
    "rv": "RV",
    "ttl": "TTL",
    "rs485": "RS-485",
    "can": "CAN",
    "pwm": "PWM",
    "rgb": "RGB",
    "2d": "2D",
    "3d": "3D",
    "usb": "USB",
    "io-link": "IO-Link",
    "modbus-tcp": "Modbus TCP",
    "ethercat": "EtherCAT",
    "digital-io": "Digital I/O",
    "iso-9409-1-50": "ISO 9409-1-50",
    "iso-9409-1-31": "ISO 9409-1-31",
    "na": "Not applicable",
    "vr-rig": "VR rig",
    "mocap": "Motion capture",
    "slam": "SLAM",
    "inspection-qc": "Inspection & QC",
    "painting-dispensing": "Painting & dispensing",
    "lawn-garden": "Lawn & garden",
    "hospitality-retail": "Hospitality & retail",
    "search-rescue": "Search & rescue",
    "research-only": "Research only",
    "quasi-direct": "Quasi-direct drive",
    "professional-service": "Professional service",
}


def pretty(slug: str) -> str:
    if slug in NAME_OVERRIDES:
        return NAME_OVERRIDES[slug]
    return slug.replace("-", " ").capitalize()


def main() -> None:
    attrs = yaml.load((ROOT / "data/attributes.yml").read_text())
    values_path = ROOT / "data/values.yml"
    values = yaml.load(values_path.read_text()) if values_path.exists() else []
    values = values or []
    existing = {v["friendly_id"] for v in values}
    next_id = max((v["id"] for v in values), default=0) + 1

    for attr in attrs:
        if attr.get("type") != "enum":
            continue
        for fid in attr["values"]:
            if fid in existing:
                continue
            attr_part, val_part = fid.split("__", 1)
            assert attr_part == attr["friendly_id"], fid
            values.append(
                {
                    "id": next_id,
                    "name": pretty(val_part),
                    "friendly_id": fid,
                    "handle": attr["handle"] + "__" + val_part,
                }
            )
            existing.add(fid)
            next_id += 1

    header = (
        "# whatrobot taxonomy — attribute values\n"
        "# Source of truth. Licence: CC BY 4.0 (see data/LICENSE).\n"
        "# friendly_id = <attribute friendly_id>__<value>. Integer ids are permanent.\n"
    )
    with values_path.open("w") as fh:
        fh.write(header)
        yaml.dump(values, fh)
    print(f"{len(values)} values written to {values_path}")


if __name__ == "__main__":
    main()
