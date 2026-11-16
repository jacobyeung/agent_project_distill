import re

from .p3_provenance import load, pinned


NAME = "frozen-table-no-flag-v1"


def validate(cfg, *, authenticate=True):
    value = cfg.get("s1_route_policy")
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != {"name", "table"} or value["name"] != NAME:
        raise ValueError("Unknown frozen route table contract")
    if cfg.get("tool_mode_flag") is not None:
        raise ValueError("The frozen route table requires no flag")
    table = value["table"]
    if (not isinstance(table, dict) or set(table) != {"path", "sha256"}
            or not isinstance(table["path"], str) or not table["path"]
            or not isinstance(table["sha256"], str) or not re.fullmatch("[0-9a-f]{64}", table["sha256"])):
        raise ValueError("The frozen route table needs an exact file pin")
    if authenticate and load(pinned(table)) != cfg.get("route_table"):
        raise ValueError("The embedded policy differs from the pinned frozen route table")
    return value
