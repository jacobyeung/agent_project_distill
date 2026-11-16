import copy
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest

from student_pilot import carrier_c1_run as run
from student_pilot.p3_provenance import file_pin, load, pinned, write
from student_pilot.row_removals import Removals


ROOT = Path("/scratch/jjyeung/orch_cd/leg_s1_tree")
KIT = Path(os.environ.get("S1_REMOVE_ADMISSION_KIT", ROOT / "work/fixture/kit_full_r12_frozen_bound"))


class RemoveAdmissionTests(unittest.TestCase):
    @unittest.skipUnless((KIT / "k/authorization.json").is_file() and os.environ.get("S1_CPU_REHEARSAL") == "1",
                         "Requires an authenticated tiny preparation and explicit CPU rehearsal")
    def test_native_admission_rejects_a_listed_row_inside_valid_source_pins(self):
        root = Path(tempfile.mkdtemp(dir=os.environ["LANE_TEST_OUTPUT"]))
        cfg = load(pinned(load(KIT / "k/authorization.json")["config"]))
        receipt = load(pinned(cfg["preparation"]))
        selected = receipt["streams"]["vqa"]
        original = selected["scene_source"]
        source = load(pinned(original["receipt"]))
        index = load(pinned(selected["indices"]))[0]
        database = root / "rows.sqlite"
        with sqlite3.connect(pinned(source["database"]).as_uri()+"?mode=ro", uri=True) as before:
            with sqlite3.connect(database) as after:
                before.backup(after)
        rules = Removals(cfg["remove_files"])
        removed_key = min(rules.keys[0])
        with sqlite3.connect(database) as connection:
            row = json.loads(connection.execute("SELECT row FROM rows WHERE i=?", (index,)).fetchone()[0])
            row["label_row_keys"] = [removed_key]
            connection.execute("UPDATE rows SET row=? WHERE i=?", (json.dumps(row), index))
        source["database"] = file_pin(database)
        write(root / "source.json", source)
        source_pin = file_pin(root / "source.json")
        cfg["streams"]["vqa"] = source_pin
        for value in (selected, original):
            value.update(receipt=source_pin, database=source["database"])
        from student_pilot.s1_exclusions import apply
        original_streams = {name: value["scene_source"] for name, value in receipt["streams"].items()}
        streams, report = apply(original_streams, cfg["dev_scene_exclusions"], root / "scenes",
                                cfg.get("benchmark_scene_exclusions"), coverage=cfg.get("scene_coverage"))
        receipt.update(config_sha256=run.identity(cfg), trainer_commit=run.authenticate(cfg),
                       streams=streams, scene_filter_report=report)
        from student_pilot.source_seal import binding
        receipt["source_seal"] = binding(load(pinned(cfg["code"])), run.identity(cfg))
        write(root / "receipt.json", receipt)
        cfg["preparation"] = file_pin(root / "receipt.json")
        with self.assertRaisesRegex(ValueError, "REMOVE-listed row remains in admitted receipt"):
            run.prepared(cfg, admission=True)
        write(root / "result.json", dict(status="PASS", case="remove_listed_row_in_native_receipt",
              preparation=cfg["preparation"], source=source_pin, database=source["database"],
              removed_key=removed_key, native_admission=True, model_function_replacements=0))

    def test_selection_audit_checks_only_selected_rows(self):
        root = Path(tempfile.mkdtemp(dir=os.environ["LANE_TEST_OUTPUT"]))
        removed = root / "remove.jsonl"
        removed.write_text(json.dumps(dict(row_key="removed"))+"\n")
        database = root / "rows.sqlite"
        with sqlite3.connect(database) as connection:
            connection.execute("CREATE TABLE rows(i INTEGER PRIMARY KEY, row TEXT)")
            connection.executemany("INSERT INTO rows VALUES (?,?)",
                                   [(0, json.dumps(dict(qid="removed"))), (1, json.dumps(dict(qid="kept")))])
        write(root / "indices.json", [1])
        write(root / "order.json", [[0, 1]])
        rules = Removals([file_pin(removed)])
        streams = dict(vqa=dict(count=1, database=file_pin(database), indices=file_pin(root / "indices.json")),
                       pose=dict(kind="mix", count=1, order=file_pin(root / "order.json"),
                                 sources=[dict(kind="rows", count=2, database=file_pin(database))]))
        rules.verify_streams(streams)
        altered = copy.deepcopy(streams)
        write(root / "leaked.json", [[0, 0]])
        altered["pose"]["order"] = file_pin(root / "leaked.json")
        with self.assertRaisesRegex(ValueError, "REMOVE-listed row"):
            rules.verify_streams(altered)


if __name__ == "__main__":
    unittest.main()
