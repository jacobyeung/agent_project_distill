#!/usr/bin/env python3
"""Fail-closed physical-room exclusion guard for the Pilot-0 Gemini API Data Factory.

Enforces zero overlap against:
  1. BENCH v2 (VSI-Bench, ReVSI, VSTI-Bench, STI-Bench/ReSTI, MindCube-Tiny, + other_corpora)
  2. ReSTI ScanNet explicit train-split trap (all 150 rooms scene0000..scene0149, any visit _NN)
  3. R0-dev / R0 reserve (372 R0_ROOMS.txt + r0_scenes union)
  4. dev-S1 internal development rooms (100 rooms / 35+ active captures)
  5. K1-heldout rooms (50 held-out rooms / 58 captures incl. no_raster 45261532)
  6. withheld-80 rooms (80 withheld grounding rooms; removes 6 of 239 K1 pinned_train captures)
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

DEFAULT_EXCLUSION_BASE = Path("/scratch/jjyeung/orch_n30/sb_ktfix2/inputs/exclusions")
DEFAULT_K1_ROWSETS = Path("/scratch/jjyeung/n30_mirror/sb_headacc2/K1_ROWSETS")
DEFAULT_PINNED_TRAIN = Path("/scratch/jjyeung/orch_n30/sb_kbox4/pinned_train.json")

DATASET_MAP = {
    "d1": "scannet",
    "d2": "scannetpp",
    "d3": "arkitscenes",
    "scannet": "scannet",
    "scannetpp": "scannetpp",
    "scannetppv2": "scannetpp",
    "arkitscenes": "arkitscenes",
}
TOKEN_PREFIX = {
    "scannet": "d1",
    "scannetpp": "d2",
    "scannetppv2": "d2",
    "arkitscenes": "d3",
}


class LeakageFatalError(RuntimeError):
    """Raised immediately when any candidate scene/room hits a blocked set or fails resolution."""


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class RoomExclusionGuard:
    """SHA256-pinned, fail-closed room/venue/corpus exclusion guard."""

    def __init__(
        self,
        exclusion_base: Path = DEFAULT_EXCLUSION_BASE,
        k1_rowsets_dir: Path = DEFAULT_K1_ROWSETS,
    ) -> None:
        self.exclusion_base = Path(exclusion_base).resolve()
        self.k1_rowsets_dir = Path(k1_rowsets_dir).resolve()
        self.file_pins: Dict[str, str] = {}

        lists_dir = self.exclusion_base / "lists"
        manifest = self._read_json(lists_dir / "manifest.json")
        if manifest.get("schema") != "store-room-audit-inputs-v1":
            raise LeakageFatalError(f"Unexpected exclusion manifest schema: {manifest.get('schema')}")

        # 1. Load ARKit video_id -> visit_id venue mapping (3dod/metadata.csv)
        visits_pin = manifest["authority"]["visits"]
        visits_raw = self._read_pinned(lists_dir / visits_pin["path"], visits_pin["sha256"]).decode("utf-8")
        self.arkit_visits: Dict[str, str] = {}
        self.venue_witness: Dict[str, str] = {}
        for row in csv.DictReader(visits_raw.splitlines()):
            vid = row["video_id"].strip()
            visit = row["visit_id"].strip()
            self.arkit_visits[vid] = visit
            if visit and visit != "NA":
                self.venue_witness.setdefault(f"arkitscenes/venue{visit}", f"arkitscenes/{vid}")

        # 2. Load authority aliases + tiered alias map + quarantined tokens
        aliases_pin = manifest["authority"]["aliases"]
        auth_aliases = self._read_json(lists_dir / aliases_pin["path"], aliases_pin["sha256"])
        tiered_pin = manifest["alias_map"]
        tiered_doc = self._read_json(lists_dir / tiered_pin["path"], tiered_pin["sha256"])
        self.quarantined_tokens: Set[str] = set(tiered_doc.get("quarantined_tokens", []))
        self.aliases: Dict[str, str] = {}
        for tok, entry in tiered_doc.get("aliases", {}).items():
            self.aliases[tok] = self._normalize_canonical_pair(entry["canonical"])
        for tok, can in auth_aliases.items():
            norm_can = self._normalize_canonical_pair(can)
            if tok in self.aliases and self.aliases[tok] != norm_can:
                raise LeakageFatalError(f"Alias authority conflict on {tok}: {self.aliases[tok]} vs {norm_can}")
            self.aliases.setdefault(tok, norm_can)

        # 3. Load all pinned physical-room exclusion sets
        self.sets: Dict[str, Set[str]] = {}

        # 3a. BENCH v2 + explicit ReSTI ScanNet + other_corpora
        bench_pin = manifest["lists"]["BENCH v2"]
        bench_doc = self._read_json(lists_dir / bench_pin["path"], bench_pin["sha256"])
        self.sets["BENCH_v2"] = {self._room_from_list_entry(x) for x in bench_doc["physical_groups"]}
        for sc in bench_doc.get("scenes", []):
            self.sets["BENCH_v2"].add(self._room_from_list_entry(sc))

        resti_scenes = bench_doc.get("subsets", {}).get("ReSTI_scannet_scenes", [])
        resti_rooms = {self._room_from_list_entry(f"scannet/{s}") for s in resti_scenes}
        for idx in range(150):
            resti_rooms.add(f"scannet/scene{idx:04d}")
        if len(resti_rooms) < 150:
            raise LeakageFatalError("ReSTI_ScanNet room set incomplete")
        self.sets["ReSTI_ScanNet"] = resti_rooms

        self.other_corpora: Dict[str, Set[str]] = {}
        for corp, items in bench_doc.get("other_corpora", {}).items():
            self.other_corpora[corp.lower()] = {str(v).strip() for v in items}

        # 3b. R0-dev / R0 reserve (R0_ROOMS.txt + split r0_scenes)
        r0_pin = manifest["lists"]["R0"]
        r0_lines = self._read_pinned(lists_dir / r0_pin["path"], r0_pin["sha256"]).decode("utf-8").split()
        split_pin = manifest["authority"]["split"]
        split_doc = self._read_json(lists_dir / split_pin["path"], split_pin["sha256"])
        r0_rooms = {self._room_from_list_entry(x) for x in r0_lines}
        for cap_info in split_doc.get("r0_scenes", {}).get("captures", {}).values():
            r0_rooms.add(self._room_from_list_entry(cap_info["room"]))
        self.sets["R0_dev"] = r0_rooms

        # 3c. dev-S1
        devs1_pin = manifest["lists"]["dev-S1"]
        devs1_doc = self._read_json(lists_dir / devs1_pin["path"], devs1_pin["sha256"])
        self.sets["dev_S1"] = {self._room_from_list_entry(x) for x in devs1_doc["physical_groups"]}

        # 3d. K1-heldout (from TEACHER_K1.raw + K1_CAPTURES_HELDOUT_57.txt + K1_EXCLUSIONS heldout)
        k1_pin = manifest["lists"]["K1"]
        k1_doc = self._read_json(lists_dir / k1_pin["path"], k1_pin["sha256"])
        k1_rooms: Set[str] = set()
        for cap in k1_doc.get("captures", []):
            if cap.get("k1_split") == "heldout":
                k1_rooms.add(self._room_from_canonical(self._normalize_canonical_pair(cap["canonical"])))
        heldout_57 = self.k1_rowsets_dir / "K1_CAPTURES_HELDOUT_57.txt"
        if heldout_57.is_file():
            for line in self._read_pinned(heldout_57).decode("utf-8").splitlines():
                if line.strip():
                    k1_rooms.add(self._room_from_canonical(self._normalize_canonical_pair(line.strip())))
        k1_excl = self.k1_rowsets_dir / "K1_EXCLUSIONS.json"
        if k1_excl.is_file():
            for entry in self._read_json(k1_excl):
                if entry.get("split") == "heldout":
                    k1_rooms.add(self._room_from_canonical(self._normalize_canonical_pair(entry["capture"])))
        self.sets["K1_heldout"] = k1_rooms

        # 3e. withheld-80
        w80_pin = manifest["lists"]["withheld-80"]
        w80_doc = self._read_json(lists_dir / w80_pin["path"], w80_pin["sha256"])
        self.sets["withheld_80"] = {self._room_from_list_entry(x) for x in w80_doc["rooms"]}

        # Sanity count floors on every authority set
        expected_min = {
            "BENCH_v2": 511,
            "ReSTI_ScanNet": 150,
            "R0_dev": 372,
            "dev_S1": 35,
            "K1_heldout": 48,
            "withheld_80": 80,
        }
        for name, floor in expected_min.items():
            if len(self.sets[name]) < floor:
                raise LeakageFatalError(f"Exclusion set {name} below floor ({len(self.sets[name])} < {floor})")

        # Compute deterministic sealed manifest digest
        manifest_payload = {
            "files": dict(sorted(self.file_pins.items())),
            "set_sizes": {k: len(v) for k, v in sorted(self.sets.items())},
            "other_corpora_sizes": {k: len(v) for k, v in sorted(self.other_corpora.items())},
        }
        self.manifest_sha256 = _sha256_bytes(
            json.dumps(manifest_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        )

    def _read_pinned(self, path: Path, expected_sha256: Optional[str] = None) -> bytes:
        resolved = path.resolve()
        if not resolved.is_file():
            raise LeakageFatalError(f"Missing exclusion authority file: {resolved}")
        raw = resolved.read_bytes()
        digest = _sha256_bytes(raw)
        if expected_sha256 is not None and digest != expected_sha256:
            raise LeakageFatalError(
                f"SHA256 mismatch on {resolved}: got {digest}, expected {expected_sha256}"
            )
        self.file_pins[str(resolved)] = digest
        return raw

    def _read_json(self, path: Path, expected_sha256: Optional[str] = None) -> Any:
        return json.loads(self._read_pinned(path, expected_sha256))

    def _normalize_canonical_pair(self, value: str) -> str:
        if not isinstance(value, str):
            raise LeakageFatalError(f"Invalid scene identifier type: {type(value)}")
        cleaned = value.strip().replace("::", "/")
        if "/" not in cleaned:
            raise LeakageFatalError(f"Scene identifier missing dataset prefix: {value!r}")
        ds_raw, scene_raw = cleaned.split("/", 1)
        ds = DATASET_MAP.get(ds_raw.lower())
        if ds is None:
            raise LeakageFatalError(f"Unsupported or unknown dataset {ds_raw!r} in {value!r}")
        scene = scene_raw.strip()
        if ds == "scannet":
            # Accept sceneNNNN or sceneNNNN_MM (including synthetic test suffixes like _99)
            if not re.fullmatch(r"scene\d{4}(?:_\d{2})?", scene):
                raise LeakageFatalError(f"Invalid ScanNet scene id: {value!r}")
            return f"scannet/{scene}"
        if ds == "scannetpp":
            # Strip optional dslr/iphone prefixes or suffixes if present; preserve literal hex IDs
            m = re.fullmatch(r"(?:dslr_|iphone_)?([0-9a-f]{8,16})(?:_dslr|_iphone)?", scene.lower())
            if not m:
                raise LeakageFatalError(f"Invalid ScanNet++ scene id: {value!r}")
            return f"scannetpp/{m.group(1)}"
        if ds == "arkitscenes":
            if not scene.isdigit():
                raise LeakageFatalError(f"Invalid ARKitScenes video id: {value!r}")
            if scene not in self.arkit_visits:
                raise LeakageFatalError(f"ARKitScenes video id {scene!r} absent from pinned visits authority")
            return f"arkitscenes/{scene}"
        raise LeakageFatalError(f"Unhandled dataset {ds!r}")

    def _room_from_canonical(self, canonical: str) -> str:
        ds, cap = canonical.split("/", 1)
        if ds == "scannet":
            m = re.match(r"(scene\d{4})", cap)
            if not m:
                raise LeakageFatalError(f"Cannot extract ScanNet room from {canonical!r}")
            return f"scannet/{m.group(1)}"
        if ds == "scannetpp":
            return f"scannetpp/{cap}"
        if ds == "arkitscenes":
            visit = self.arkit_visits.get(cap)
            if visit is None:
                raise LeakageFatalError(f"ARKitScenes capture {cap!r} missing visit mapping")
            return f"arkitscenes/venue{visit}" if (visit and visit != "NA") else f"arkitscenes/capture{cap}"
        raise LeakageFatalError(f"Cannot extract room from {canonical!r}")

    def _room_from_list_entry(self, value: str) -> str:
        cleaned = value.strip().replace("::", "/")
        if "/" not in cleaned:
            raise LeakageFatalError(f"Invalid room list entry: {value!r}")
        ds_raw, rest = cleaned.split("/", 1)
        ds = DATASET_MAP.get(ds_raw.lower(), ds_raw.lower())
        if ds == "arkitscenes" and rest.startswith("venue"):
            room_key = f"arkitscenes/{rest}"
            if room_key not in self.venue_witness:
                raise LeakageFatalError(f"Unknown ARKit venue in exclusion list: {value!r}")
            return room_key
        if ds == "arkitscenes" and rest.startswith("capture"):
            vid = rest[len("capture"):]
            return self._room_from_canonical(self._normalize_canonical_pair(f"arkitscenes/{vid}"))
        if ds == "scannet" and re.fullmatch(r"scene\d{4}", rest):
            return f"scannet/{rest}"
        if ds == "scannetpp" and re.fullmatch(r"[0-9a-f]+", rest):
            return f"scannetpp/{rest}"
        return self._room_from_canonical(self._normalize_canonical_pair(f"{ds}/{rest}"))

    def resolve(self, item: Any) -> Dict[str, str]:
        """Resolve a string ID or row/capture dict into canonical scene and physical room."""
        if isinstance(item, str):
            raw_str = item.strip().replace("::", "/")
            if "/" not in raw_str:
                raise LeakageFatalError(f"Unqualified scene identifier: {item!r}")
            ds_part, sc_part = raw_str.split("/", 1)
            ds_low = ds_part.lower()
            if ds_low in self.other_corpora:
                return {
                    "dataset": ds_low,
                    "canonical_scene": f"{ds_low}/{sc_part}",
                    "canonical_room": f"{ds_low}::{sc_part}",
                    "format_room": f"{ds_low}::{sc_part}",
                }
            tok = f"{TOKEN_PREFIX.get(ds_low, ds_low)}/{sc_part}"
            if tok in self.quarantined_tokens:
                raise LeakageFatalError(f"Quarantined alias token refused: {tok}")
            if tok in self.aliases:
                can = self.aliases[tok]
            else:
                can = self._normalize_canonical_pair(raw_str)
            phys_room = self._room_from_canonical(can)
            return {
                "dataset": can.split("/", 1)[0],
                "canonical_scene": can,
                "canonical_room": phys_room,
                "format_room": phys_room.replace("/", "::"),
            }

        if isinstance(item, dict):
            candidates: List[str] = []
            for key in ("canonical", "canonical_scene", "capture"):
                val = item.get(key)
                if isinstance(val, str) and val.strip():
                    candidates.append(val.strip())
            ds = item.get("dataset")
            sc = item.get("scene")
            if isinstance(ds, str) and isinstance(sc, str) and ds.strip() and sc.strip():
                ds_s, sc_s = ds.strip(), sc.strip()
                tok = f"{TOKEN_PREFIX.get(ds_s.lower(), ds_s.lower())}/{sc_s}"
                if tok in self.quarantined_tokens:
                    raise LeakageFatalError(f"Quarantined alias token refused: {tok}")
                if tok in self.aliases:
                    candidates.append(self.aliases[tok])
                else:
                    candidates.append(f"{ds_s}/{sc_s}")
            if not candidates:
                raise LeakageFatalError(f"Row missing scene/canonical fields: {list(item.keys())}")
            resolved = [self.resolve(c) for c in candidates]
            rooms_found = {r["canonical_room"] for r in resolved}
            if len(rooms_found) != 1:
                raise LeakageFatalError(f"Conflicting scene witnesses in row: {resolved}")
            out = resolved[0]
            declared_room = item.get("room") or item.get("canonical_room")
            if isinstance(declared_room, str) and declared_room.strip():
                norm_decl = self._room_from_list_entry(declared_room.strip())
                if norm_decl != out["canonical_room"]:
                    raise LeakageFatalError(
                        f"Declared room {norm_decl} != resolved room {out['canonical_room']}"
                    )
            return out

        raise LeakageFatalError(f"Unsupported input type for exclusion check: {type(item)}")

    def check(self, item: Any) -> Dict[str, Any]:
        """Return exclusion check details without raising on blocked rooms (raises on malformed IDs)."""
        info = self.resolve(item)
        phys_room = info["canonical_room"]
        ds = info["dataset"]
        hits: List[str] = []

        if ds in self.other_corpora:
            seg = info["canonical_scene"].split("/", 1)[1]
            if seg in self.other_corpora[ds]:
                hits.append(f"BENCH_v2_other_corpora:{ds}")
        else:
            for set_name, room_set in self.sets.items():
                if phys_room in room_set:
                    hits.append(set_name)
            # Explicit numeric ScanNet 0000..0149 belt-and-suspenders trap check
            if phys_room.startswith("scannet/scene"):
                num_str = phys_room.split("scannet/scene", 1)[1]
                if num_str.isdigit() and 0 <= int(num_str) <= 149 and "ReSTI_ScanNet" not in hits:
                    hits.append("ReSTI_ScanNet")

        return {
            "allowed": len(hits) == 0,
            "dataset": ds,
            "canonical_scene": info["canonical_scene"],
            "canonical_room": phys_room,
            "format_room": info["format_room"],
            "hits": sorted(hits),
            "exclusion_sha256": self.manifest_sha256,
        }

    def assert_clean(self, item: Any) -> Dict[str, Any]:
        """Fail-closed gate: raises LeakageFatalError if item hits ANY exclusion list."""
        verdict = self.check(item)
        if not verdict["allowed"]:
            raise LeakageFatalError(
                f"REFUSED excluded room {verdict['canonical_room']} "
                f"(scene={verdict['canonical_scene']}) hitting {verdict['hits']}"
            )
        return verdict

    def assert_canaries(self) -> Dict[str, Any]:
        """Inject 8 planted canary leaks across all exclusion families; abort unless 8/8 raise."""
        bench_spp = next(r for r in sorted(self.sets["BENCH_v2"]) if r.startswith("scannetpp/"))
        r0_sample = next(r for r in sorted(self.sets["R0_dev"]) if r.startswith("scannet/"))
        devs1_sample = next(r for r in sorted(self.sets["dev_S1"]) if r.startswith("scannet/"))
        waymo_seg = next(iter(sorted(self.other_corpora["waymo"])))

        canaries: List[Tuple[str, Any, Optional[str]]] = [
            # 1. ARKit venue sibling trap (41159521 is Training video in venue 381879 of Val video 41159525)
            ("BENCH_v2_arkit_venue_sibling", "arkitscenes/41159521", "BENCH_v2"),
            # 2. ScanNet++ benchmark room
            ("BENCH_v2_scannetpp", bench_spp, "BENCH_v2"),
            # 3. ReSTI ScanNet train-split trap with synthetic rescan suffix _99
            ("ReSTI_ScanNet_train_trap", "scannet/scene0042_99", "ReSTI_ScanNet"),
            # 4. R0-dev room with synthetic rescan suffix _99
            ("R0_dev_room", f"{r0_sample}_99", "R0_dev"),
            # 5. dev-S1 calibration room
            ("dev_S1_room", f"{devs1_sample}_00", "dev_S1"),
            # 6. K1-heldout capture
            ("K1_heldout_capture", "arkitscenes/41069175", "K1_heldout"),
            # 7. withheld-80 room inside pinned_train.json
            ("withheld_80_room", "scannet/scene0201_02", "withheld_80"),
            # 8. Waymo ReSTI segment in other_corpora
            ("BENCH_v2_waymo_segment", f"waymo/{waymo_seg}", "BENCH_v2_other_corpora:waymo"),
        ]

        canary_results = {}
        for label, probe, expected_tag in canaries:
            caught = False
            err_msg = ""
            try:
                self.assert_clean(probe)
            except LeakageFatalError as exc:
                caught = True
                err_msg = str(exc)
            if not caught or (expected_tag and expected_tag not in err_msg):
                raise RuntimeError(
                    f"FATAL CANARY FAILURE on {label} ({probe!r}): caught={caught}, msg={err_msg!r}"
                )
            canary_results[label] = {"probe": str(probe), "blocked": True, "error": err_msg}

        # Also verify malformed / unknown scene fails closed
        malformed_caught = False
        try:
            self.assert_clean("unknown_corpus/mystery_room_01")
        except LeakageFatalError:
            malformed_caught = True
        if not malformed_caught:
            raise RuntimeError("FATAL CANARY FAILURE: unknown dataset did not fail closed")
        canary_results["malformed_unknown_fail_closed"] = {"blocked": True}

        return {
            "passed": len(canary_results),
            "total": len(canary_results),
            "manifest_sha256": self.manifest_sha256,
            "set_sizes": {k: len(v) for k, v in sorted(self.sets.items())},
            "canaries": canary_results,
        }

    def filter_captures(
        self, captures: Iterable[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Partition capture dicts into (clean_captures, blocked_records)."""
        clean: List[Dict[str, Any]] = []
        blocked: List[Dict[str, Any]] = []
        for cap in captures:
            verdict = self.check(cap)
            if verdict["allowed"]:
                clean.append(cap)
            else:
                blocked.append(verdict)
        return clean, blocked


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pinned", type=Path, default=DEFAULT_PINNED_TRAIN)
    parser.add_argument("--assert-canaries", action="store_true")
    args = parser.parse_args(argv)

    guard = RoomExclusionGuard()
    report: Dict[str, Any] = {"exclusion_sha256": guard.manifest_sha256}
    if args.assert_canaries:
        report["canary_audit"] = guard.assert_canaries()
    if args.pinned and args.pinned.is_file():
        doc = json.loads(args.pinned.read_bytes())
        clean, blocked = guard.filter_captures(doc["captures"])
        report["pinned_filter"] = {
            "input_captures": len(doc["captures"]),
            "clean_captures": len(clean),
            "clean_unique_rooms": len({c["room"] for c in clean}),
            "blocked_captures": len(blocked),
            "blocked_details": blocked,
        }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
