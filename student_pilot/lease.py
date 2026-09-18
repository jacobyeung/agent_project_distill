import os
import socket
from datetime import datetime, timezone

from .common import binding, load_json


def check_lease(lease, hostname, visible_devices, now, fresh=True):
    if hostname.split(".")[0] != "trinity-1-8" or lease.get("host") != "trinity-1-8":
        raise ValueError("This supervisor launch is scoped only to trinity-1-8")
    if lease.get("gpu_index") != 1 or visible_devices != "1":
        raise ValueError("Only supervisor-leased physical GPU1 may be exposed")
    for key in ("ownership_check_passed", "coordination_lease_passed", "vnice_wrapped"):
        if lease.get(key) is not True:
            raise ValueError(f"Supervisor evidence must attest {key}=true")
    for key in ("owner", "work_id", "coordination_lease_evidence"):
        if not isinstance(lease.get(key), str) or not lease[key].strip():
            raise ValueError(f"Missing supervisor evidence: {key}")
    checked = datetime.fromisoformat(lease["ownership_checked_at"].replace("Z", "+00:00"))
    expires = datetime.fromisoformat(lease["expires_at"].replace("Z", "+00:00"))
    if checked.tzinfo is None or expires.tzinfo is None or checked > now or expires <= now or expires <= checked:
        raise ValueError("Lease timestamps are missing a timezone, future-dated, or expired")
    if fresh and (now - checked).total_seconds() > 300:
        raise ValueError("Supervisor ownership check is older than five minutes")
    return lease


def require_lease(path, fresh=True):
    lease = check_lease(load_json(path), socket.gethostname(), os.environ.get("CUDA_VISIBLE_DEVICES"), datetime.now(timezone.utc), fresh)
    return {**lease, "evidence_file": binding(path)}
