#!/usr/bin/env python3
"""Content-addressed, mechanically authoritative VSTIBench score records.

Sibling of ``score_index.py`` (VSIBench), sharing the benchmark-agnostic core in
``score_record_core.py`` (hashing/canonicalization, dataset + raw-trace loading, the
``category``/``seed_mean``/``composite`` record types, and the ``AGGREGATION_FORMULAS`` registry).
VSTIBench has no ``group`` concept -- every role here is a ``composite`` (per-category source map),
since VSTIBench's official score needs two independent 3-way collapses (``camera_obj_rel_dist_v1/2/3``
and ``obj_obj_relative_pos_lr/nf/ud``) into a 5-subtask score, which the VSIBench-only frozen
``group`` type cannot express.

This module's own scorer manifest hashes this file plus the shared core plus ``scoring.py`` --
never ``score_index.py`` -- so editing VSIBench's ``ROLE_POLICIES`` never staless this index's
records, and vice versa. Reuses the same ``agent/evaluation/records/`` directory as VSIBench
(content-addressed by hash; VSIBench and VSTIBench category names are disjoint, so there is no
collision risk).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from evaluation import scoring  # type: ignore[no-redef]
    from evaluation import score_record_core as core  # type: ignore[no-redef]
else:
    from . import scoring
    from . import score_record_core as core

ScoreIndexError = core.ScoreIndexError

INDEX_SCHEMA_VSTI = "score-index-vstibench-v1"
RECORD_SCHEMA = core.RECORD_SCHEMA
INDEX_RELATIVE_PATH = Path("agent/evaluation/SCORE_INDEX_VSTIBENCH.json")
RECORDS_RELATIVE_DIR = core.RECORDS_RELATIVE_DIR
VSTI_CATEGORIES = core.VSTI_CATEGORIES

# Nomination note validation for policy-pending roles.
# Any role in this set requires a non-empty string `note` field whose content contains
# POLICY_PENDING_NOTE_MARKER.  The validator enforces this so an index where the warning
# is absent, empty, non-string, or stripped of its marker is rejected rather than silently
# accepted.  Consuming code (query()) exposes the note; this set makes absence a hard error.
POLICY_PENDING_NOTE_MARKER = "USER POLICY DECISION"
# The upstream-erratum adoption closed the old per-seed/two-seed policy question.  Those
# nominations remain auditable history, while the exact-417 upstream construct is paper-primary.
VSTI_POLICY_PENDING_ROLES: frozenset[str] = frozenset()

VSTI_ROLE_POLICIES = {
    "vstibench_headline_66p91": {
        # 2-seed mean dev construct: 66.91 (raised from 66.73 on 2026-07-04, addendum 28).
        # NA arms = rv5 g3t_scaled_anchor seed_mean over s1+s2; MC arms = rv3 g3t_scaled_anchor.
        # Whether the paper headline is per-seed s1 (vstibench_rv5_s1_composite = 67.09) or
        # 2-seed mean (this record = 66.91) is a USER POLICY DECISION pending confirmation.
        "aggregation_schema": "vstibench-official-5subtask-v1",
        "dataset_id": "vstibench_repr_450",
        "dataset_sha256": "sha256:10972cd0f916f39ac36570f3932f4d926ef21620af1f5f92191a89f60d289c39",
        "question_count": 450,
        "category_policy": {
            "camera_displacement": {
                "kind": "seed_mean",
                "source_ids": ["rv5_g3t_scaled_anchor_s1", "rv5_g3t_scaled_anchor_s2"],
                "qid_set_sha256": "sha256:3d87c5c0e723eeb55cd85d7d612b13b54256f631238e861e3e7bf507e0db9618",
            },
            "camera_movement_direction": {
                "kind": "category",
                "source_ids": ["rv3_g3t_scaled_anchor"],
                "qid_set_sha256": "sha256:359be268d81195e374e99ddb561a0b87274ff91cfed6c71b287e40f6a4b1d83f",
            },
            "camera_obj_abs_dist": {
                "kind": "seed_mean",
                "source_ids": ["rv5_g3t_scaled_anchor_s1", "rv5_g3t_scaled_anchor_s2"],
                "qid_set_sha256": "sha256:d9c803205b487dd287a96531c141b7cd4624225699202b20bf588bf3a36ec402",
            },
            "camera_obj_rel_dist_v1": {
                "kind": "category",
                "source_ids": ["rv3_g3t_scaled_anchor"],
                "qid_set_sha256": "sha256:f41ed6c62ae1d79d7763b665790668ce148701f3d43c6270e42583a12ce2a13a",
            },
            "camera_obj_rel_dist_v2": {
                "kind": "category",
                "source_ids": ["rv3_g3t_scaled_anchor"],
                "qid_set_sha256": "sha256:e31400cb066bd3c401e5779d8da27666dceea4b1feadb96150974b202f4c3341",
            },
            "camera_obj_rel_dist_v3": {
                "kind": "category",
                "source_ids": ["rv3_g3t_scaled_anchor"],
                "qid_set_sha256": "sha256:3d86bf8a0355ab9ed755748e1b11c3e80f35e0e07f5037a6e232832f5d27cf69",
            },
            "obj_obj_relative_pos_lr": {
                "kind": "category",
                "source_ids": ["rv3_g3t_scaled_anchor"],
                "qid_set_sha256": "sha256:b2099f513a30a9651946dfd928b0e8ba09e3a45542a7b9c6b09c95cdd5440311",
            },
            "obj_obj_relative_pos_nf": {
                "kind": "category",
                "source_ids": ["rv3_g3t_scaled_anchor"],
                "qid_set_sha256": "sha256:11b97eea31368ed6cc7a77e8b7dcf2c9c4addbfd002d8bdca26b41f750facee0",
            },
            "obj_obj_relative_pos_ud": {
                "kind": "category",
                "source_ids": ["rv3_g3t_scaled_anchor"],
                "qid_set_sha256": "sha256:a352aadced806d7088eb0e35290316945068a4bbf142b9bfb6be848ae8903b5f",
            },
        },
    },
    "vstibench_headline_66p73": {
        # Superseded predecessor: 66.73, rv3 g3t_scaled_anchor (all types) with UniK3D 2-seed
        # on camera_obj_abs_dist.  Kept as an auditable anchor; replaced by vstibench_headline_66p91.
        "aggregation_schema": "vstibench-official-5subtask-v1",
        "dataset_id": "vstibench_repr_450",
        "dataset_sha256": "sha256:10972cd0f916f39ac36570f3932f4d926ef21620af1f5f92191a89f60d289c39",
        "question_count": 450,
        "category_policy": {
            "camera_displacement": {
                "kind": "category",
                "source_ids": ["rv3_g3t_scaled_anchor"],
                "qid_set_sha256": "sha256:3d87c5c0e723eeb55cd85d7d612b13b54256f631238e861e3e7bf507e0db9618",
            },
            "camera_movement_direction": {
                "kind": "category",
                "source_ids": ["rv3_g3t_scaled_anchor"],
                "qid_set_sha256": "sha256:359be268d81195e374e99ddb561a0b87274ff91cfed6c71b287e40f6a4b1d83f",
            },
            "camera_obj_abs_dist": {
                "kind": "seed_mean",
                "source_ids": ["rv3_unik3d_NA_s1", "rv3_unik3d_absonly_s2"],
                "qid_set_sha256": "sha256:d9c803205b487dd287a96531c141b7cd4624225699202b20bf588bf3a36ec402",
            },
            "camera_obj_rel_dist_v1": {
                "kind": "category",
                "source_ids": ["rv3_g3t_scaled_anchor"],
                "qid_set_sha256": "sha256:f41ed6c62ae1d79d7763b665790668ce148701f3d43c6270e42583a12ce2a13a",
            },
            "camera_obj_rel_dist_v2": {
                "kind": "category",
                "source_ids": ["rv3_g3t_scaled_anchor"],
                "qid_set_sha256": "sha256:e31400cb066bd3c401e5779d8da27666dceea4b1feadb96150974b202f4c3341",
            },
            "camera_obj_rel_dist_v3": {
                "kind": "category",
                "source_ids": ["rv3_g3t_scaled_anchor"],
                "qid_set_sha256": "sha256:3d86bf8a0355ab9ed755748e1b11c3e80f35e0e07f5037a6e232832f5d27cf69",
            },
            "obj_obj_relative_pos_lr": {
                "kind": "category",
                "source_ids": ["rv3_g3t_scaled_anchor"],
                "qid_set_sha256": "sha256:b2099f513a30a9651946dfd928b0e8ba09e3a45542a7b9c6b09c95cdd5440311",
            },
            "obj_obj_relative_pos_nf": {
                "kind": "category",
                "source_ids": ["rv3_g3t_scaled_anchor"],
                "qid_set_sha256": "sha256:11b97eea31368ed6cc7a77e8b7dcf2c9c4addbfd002d8bdca26b41f750facee0",
            },
            "obj_obj_relative_pos_ud": {
                "kind": "category",
                "source_ids": ["rv3_g3t_scaled_anchor"],
                "qid_set_sha256": "sha256:a352aadced806d7088eb0e35290316945068a4bbf142b9bfb6be848ae8903b5f",
            },
        },
    },
    "vstibench_rv5_s1_composite": {
        # Per-seed mixed-era composite, rv5 g3t_scaled_anchor seed-1 for both NA types;
        # rv3 g3t_scaled_anchor for all 7 MC types.
        # 5-subtask official = 67.09 (cam_obj_abs_dist 37.40, disp 35.40, movdir 100.00,
        # relpos 94.00, reldist 68.67).  This is what the paper draft cites; whether it is
        # the reportable headline (per-seed s1) or vstibench_headline_66p91 (2-seed mean)
        # is a USER POLICY DECISION pending confirmation.
        "aggregation_schema": "vstibench-official-5subtask-v1",
        "dataset_id": "vstibench_repr_450",
        "dataset_sha256": "sha256:10972cd0f916f39ac36570f3932f4d926ef21620af1f5f92191a89f60d289c39",
        "question_count": 450,
        "category_policy": {
            "camera_displacement": {
                "kind": "category",
                "source_ids": ["rv5_g3t_scaled_anchor_s1"],
                "qid_set_sha256": "sha256:3d87c5c0e723eeb55cd85d7d612b13b54256f631238e861e3e7bf507e0db9618",
            },
            "camera_movement_direction": {
                "kind": "category",
                "source_ids": ["rv3_g3t_scaled_anchor"],
                "qid_set_sha256": "sha256:359be268d81195e374e99ddb561a0b87274ff91cfed6c71b287e40f6a4b1d83f",
            },
            "camera_obj_abs_dist": {
                "kind": "category",
                "source_ids": ["rv5_g3t_scaled_anchor_s1"],
                "qid_set_sha256": "sha256:d9c803205b487dd287a96531c141b7cd4624225699202b20bf588bf3a36ec402",
            },
            "camera_obj_rel_dist_v1": {
                "kind": "category",
                "source_ids": ["rv3_g3t_scaled_anchor"],
                "qid_set_sha256": "sha256:f41ed6c62ae1d79d7763b665790668ce148701f3d43c6270e42583a12ce2a13a",
            },
            "camera_obj_rel_dist_v2": {
                "kind": "category",
                "source_ids": ["rv3_g3t_scaled_anchor"],
                "qid_set_sha256": "sha256:e31400cb066bd3c401e5779d8da27666dceea4b1feadb96150974b202f4c3341",
            },
            "camera_obj_rel_dist_v3": {
                "kind": "category",
                "source_ids": ["rv3_g3t_scaled_anchor"],
                "qid_set_sha256": "sha256:3d86bf8a0355ab9ed755748e1b11c3e80f35e0e07f5037a6e232832f5d27cf69",
            },
            "obj_obj_relative_pos_lr": {
                "kind": "category",
                "source_ids": ["rv3_g3t_scaled_anchor"],
                "qid_set_sha256": "sha256:b2099f513a30a9651946dfd928b0e8ba09e3a45542a7b9c6b09c95cdd5440311",
            },
            "obj_obj_relative_pos_nf": {
                "kind": "category",
                "source_ids": ["rv3_g3t_scaled_anchor"],
                "qid_set_sha256": "sha256:11b97eea31368ed6cc7a77e8b7dcf2c9c4addbfd002d8bdca26b41f750facee0",
            },
            "obj_obj_relative_pos_ud": {
                "kind": "category",
                "source_ids": ["rv3_g3t_scaled_anchor"],
                "qid_set_sha256": "sha256:a352aadced806d7088eb0e35290316945068a4bbf142b9bfb6be848ae8903b5f",
            },
        },
    },
    "vstibench_rv5_s2_composite": {
        # Per-seed mixed-era composite, rv5 g3t_scaled_anchor seed-2 for both NA types;
        # rv3 g3t_scaled_anchor for all 7 MC types.
        # 5-subtask official ≈ 66.73 (cam_obj_abs_dist 35.60, disp 35.40, movdir 100.00,
        # relpos 94.00, reldist 68.67).  Auditable companion to vstibench_rv5_s1_composite;
        # together they show the per-seed NA variance around the 66.91 2-seed mean.
        "aggregation_schema": "vstibench-official-5subtask-v1",
        "dataset_id": "vstibench_repr_450",
        "dataset_sha256": "sha256:10972cd0f916f39ac36570f3932f4d926ef21620af1f5f92191a89f60d289c39",
        "question_count": 450,
        "category_policy": {
            "camera_displacement": {
                "kind": "category",
                "source_ids": ["rv5_g3t_scaled_anchor_s2"],
                "qid_set_sha256": "sha256:3d87c5c0e723eeb55cd85d7d612b13b54256f631238e861e3e7bf507e0db9618",
            },
            "camera_movement_direction": {
                "kind": "category",
                "source_ids": ["rv3_g3t_scaled_anchor"],
                "qid_set_sha256": "sha256:359be268d81195e374e99ddb561a0b87274ff91cfed6c71b287e40f6a4b1d83f",
            },
            "camera_obj_abs_dist": {
                "kind": "category",
                "source_ids": ["rv5_g3t_scaled_anchor_s2"],
                "qid_set_sha256": "sha256:d9c803205b487dd287a96531c141b7cd4624225699202b20bf588bf3a36ec402",
            },
            "camera_obj_rel_dist_v1": {
                "kind": "category",
                "source_ids": ["rv3_g3t_scaled_anchor"],
                "qid_set_sha256": "sha256:f41ed6c62ae1d79d7763b665790668ce148701f3d43c6270e42583a12ce2a13a",
            },
            "camera_obj_rel_dist_v2": {
                "kind": "category",
                "source_ids": ["rv3_g3t_scaled_anchor"],
                "qid_set_sha256": "sha256:e31400cb066bd3c401e5779d8da27666dceea4b1feadb96150974b202f4c3341",
            },
            "camera_obj_rel_dist_v3": {
                "kind": "category",
                "source_ids": ["rv3_g3t_scaled_anchor"],
                "qid_set_sha256": "sha256:3d86bf8a0355ab9ed755748e1b11c3e80f35e0e07f5037a6e232832f5d27cf69",
            },
            "obj_obj_relative_pos_lr": {
                "kind": "category",
                "source_ids": ["rv3_g3t_scaled_anchor"],
                "qid_set_sha256": "sha256:b2099f513a30a9651946dfd928b0e8ba09e3a45542a7b9c6b09c95cdd5440311",
            },
            "obj_obj_relative_pos_nf": {
                "kind": "category",
                "source_ids": ["rv3_g3t_scaled_anchor"],
                "qid_set_sha256": "sha256:11b97eea31368ed6cc7a77e8b7dcf2c9c4addbfd002d8bdca26b41f750facee0",
            },
            "obj_obj_relative_pos_ud": {
                "kind": "category",
                "source_ids": ["rv3_g3t_scaled_anchor"],
                "qid_set_sha256": "sha256:a352aadced806d7088eb0e35290316945068a4bbf142b9bfb6be848ae8903b5f",
            },
        },
    },
    "vstibench_fullrepr450_official": {
        # First single-window single-era rv5 measurement across all 9 task types.
        # Official released labels (vstibench_repr_450.json). Pass A scores (n=50/type):
        # movdir=100.00, reldist=68.67 (v1/v2/v3=62/70/74), relpos=94.67 (lr/nf/ud=96/96/92),
        # abs=32.80, disp=35.40. 5-subtask composite 66.31 (addendum 112, 2026-07-06).
        # Supersedes the mixed-era 66.91/67.09 construct as the authoritative single-era
        # measurement (per addendum 104 GO). Whether 66.31 becomes the paper headline
        # (superseding banked 66.91) or is reported as a single-era comparison point is
        # a USER POLICY DECISION pending user confirmation.
        "aggregation_schema": "vstibench-official-5subtask-v1",
        "dataset_id": "vstibench_repr_450",
        "dataset_sha256": "sha256:10972cd0f916f39ac36570f3932f4d926ef21620af1f5f92191a89f60d289c39",
        "question_count": 450,
        "category_policy": {
            "camera_displacement": {
                "kind": "category",
                "source_ids": ["rv5_fullrepr450_s1"],
                "qid_set_sha256": "sha256:3d87c5c0e723eeb55cd85d7d612b13b54256f631238e861e3e7bf507e0db9618",
            },
            "camera_movement_direction": {
                "kind": "category",
                "source_ids": ["rv5_fullrepr450_s1"],
                "qid_set_sha256": "sha256:359be268d81195e374e99ddb561a0b87274ff91cfed6c71b287e40f6a4b1d83f",
            },
            "camera_obj_abs_dist": {
                "kind": "category",
                "source_ids": ["rv5_fullrepr450_s1"],
                "qid_set_sha256": "sha256:d9c803205b487dd287a96531c141b7cd4624225699202b20bf588bf3a36ec402",
            },
            "camera_obj_rel_dist_v1": {
                "kind": "category",
                "source_ids": ["rv5_fullrepr450_s1"],
                "qid_set_sha256": "sha256:f41ed6c62ae1d79d7763b665790668ce148701f3d43c6270e42583a12ce2a13a",
            },
            "camera_obj_rel_dist_v2": {
                "kind": "category",
                "source_ids": ["rv5_fullrepr450_s1"],
                "qid_set_sha256": "sha256:e31400cb066bd3c401e5779d8da27666dceea4b1feadb96150974b202f4c3341",
            },
            "camera_obj_rel_dist_v3": {
                "kind": "category",
                "source_ids": ["rv5_fullrepr450_s1"],
                "qid_set_sha256": "sha256:3d86bf8a0355ab9ed755748e1b11c3e80f35e0e07f5037a6e232832f5d27cf69",
            },
            "obj_obj_relative_pos_lr": {
                "kind": "category",
                "source_ids": ["rv5_fullrepr450_s1"],
                "qid_set_sha256": "sha256:b2099f513a30a9651946dfd928b0e8ba09e3a45542a7b9c6b09c95cdd5440311",
            },
            "obj_obj_relative_pos_nf": {
                "kind": "category",
                "source_ids": ["rv5_fullrepr450_s1"],
                "qid_set_sha256": "sha256:11b97eea31368ed6cc7a77e8b7dcf2c9c4addbfd002d8bdca26b41f750facee0",
            },
            "obj_obj_relative_pos_ud": {
                "kind": "category",
                "source_ids": ["rv5_fullrepr450_s1"],
                "qid_set_sha256": "sha256:a352aadced806d7088eb0e35290316945068a4bbf142b9bfb6be848ae8903b5f",
            },
        },
    },
    "vstibench_fullrepr450_corrected": {
        # First single-window single-era rv5 measurement, corrected labels construct.
        # Corrected labels (vstibench_repr450_corrected_labels.json, addendum 103 pose-
        # inversion bug fix). Pass B scores (n=50/type): movdir=100.00, reldist=68.67,
        # relpos=94.67 (identical to Pass A), abs=69.80, disp=85.20.
        # 5-subtask composite 83.67 (addendum 112, 2026-07-06).
        # 3 uncertain camera_obj_abs_dist qids: 1388, 1636, 1984 (scorer includes them;
        # annotator uncertainty flagged in corrected labels file).
        # Physically meaningful result on corrected annotations; NOT comparable to published
        # baselines (which use official released labels). Whether and how this figure appears
        # in the paper is a USER POLICY DECISION pending user confirmation.
        "aggregation_schema": "vstibench-official-5subtask-v1",
        "dataset_id": "vstibench_repr_450",
        "dataset_sha256": "sha256:950b67f2f3bb300a717ce74f1f2ee81030dfe095e7ba0b78e1427a30d82b0ef4",
        "question_count": 450,
        "category_policy": {
            "camera_displacement": {
                "kind": "category",
                "source_ids": ["rv5_fullrepr450_s1"],
                "qid_set_sha256": "sha256:3d87c5c0e723eeb55cd85d7d612b13b54256f631238e861e3e7bf507e0db9618",
            },
            "camera_movement_direction": {
                "kind": "category",
                "source_ids": ["rv5_fullrepr450_s1"],
                "qid_set_sha256": "sha256:359be268d81195e374e99ddb561a0b87274ff91cfed6c71b287e40f6a4b1d83f",
            },
            "camera_obj_abs_dist": {
                "kind": "category",
                "source_ids": ["rv5_fullrepr450_s1"],
                "qid_set_sha256": "sha256:d9c803205b487dd287a96531c141b7cd4624225699202b20bf588bf3a36ec402",
            },
            "camera_obj_rel_dist_v1": {
                "kind": "category",
                "source_ids": ["rv5_fullrepr450_s1"],
                "qid_set_sha256": "sha256:f41ed6c62ae1d79d7763b665790668ce148701f3d43c6270e42583a12ce2a13a",
            },
            "camera_obj_rel_dist_v2": {
                "kind": "category",
                "source_ids": ["rv5_fullrepr450_s1"],
                "qid_set_sha256": "sha256:e31400cb066bd3c401e5779d8da27666dceea4b1feadb96150974b202f4c3341",
            },
            "camera_obj_rel_dist_v3": {
                "kind": "category",
                "source_ids": ["rv5_fullrepr450_s1"],
                "qid_set_sha256": "sha256:3d86bf8a0355ab9ed755748e1b11c3e80f35e0e07f5037a6e232832f5d27cf69",
            },
            "obj_obj_relative_pos_lr": {
                "kind": "category",
                "source_ids": ["rv5_fullrepr450_s1"],
                "qid_set_sha256": "sha256:b2099f513a30a9651946dfd928b0e8ba09e3a45542a7b9c6b09c95cdd5440311",
            },
            "obj_obj_relative_pos_nf": {
                "kind": "category",
                "source_ids": ["rv5_fullrepr450_s1"],
                "qid_set_sha256": "sha256:11b97eea31368ed6cc7a77e8b7dcf2c9c4addbfd002d8bdca26b41f750facee0",
            },
            "obj_obj_relative_pos_ud": {
                "kind": "category",
                "source_ids": ["rv5_fullrepr450_s1"],
                "qid_set_sha256": "sha256:a352aadced806d7088eb0e35290316945068a4bbf142b9bfb6be848ae8903b5f",
            },
        },
    },
}


UPSTREAM417_QID_SET_SHA256 = {
    "camera_displacement": "sha256:3d87c5c0e723eeb55cd85d7d612b13b54256f631238e861e3e7bf507e0db9618",
    "camera_movement_direction": "sha256:359be268d81195e374e99ddb561a0b87274ff91cfed6c71b287e40f6a4b1d83f",
    "camera_obj_abs_dist": "sha256:d9c803205b487dd287a96531c141b7cd4624225699202b20bf588bf3a36ec402",
    "camera_obj_rel_dist_v1": "sha256:747d226ddd7c47552516afa2093a7b4c4fef57aa5cfeaeeab9e767dc6aaf38e4",
    "camera_obj_rel_dist_v2": "sha256:49e7edbd887cccec1794e6b663b98d909d8a3ee1159b4fde92030808c1f62424",
    "camera_obj_rel_dist_v3": "sha256:7828162bc11b81df86d8565343ac95f6d01d7d6d9eea73088cee87bc73e009fc",
    "obj_obj_relative_pos_lr": "sha256:b2099f513a30a9651946dfd928b0e8ba09e3a45542a7b9c6b09c95cdd5440311",
    "obj_obj_relative_pos_nf": "sha256:11b97eea31368ed6cc7a77e8b7dcf2c9c4addbfd002d8bdca26b41f750facee0",
    "obj_obj_relative_pos_ud": "sha256:a352aadced806d7088eb0e35290316945068a4bbf142b9bfb6be848ae8903b5f",
}


REPR450V2_QID_SET_SHA256 = {
    "camera_displacement": "sha256:3d87c5c0e723eeb55cd85d7d612b13b54256f631238e861e3e7bf507e0db9618",
    "camera_movement_direction": "sha256:359be268d81195e374e99ddb561a0b87274ff91cfed6c71b287e40f6a4b1d83f",
    "camera_obj_abs_dist": "sha256:d9c803205b487dd287a96531c141b7cd4624225699202b20bf588bf3a36ec402",
    "camera_obj_rel_dist_v1": "sha256:136da3593776ffd95800d2e874cf84d45060e53f33ad487f576cda41bc53b4d8",
    "camera_obj_rel_dist_v2": "sha256:2493c1b875b57af9ad1379da019700b7e51b11f0a2dd0669b60b881fe8bed58c",
    "camera_obj_rel_dist_v3": "sha256:9b6b0541c9727494f9e76cbfbae6b28256df5715e60503a32816cfbfc5fc352a",
    "obj_obj_relative_pos_lr": "sha256:b2099f513a30a9651946dfd928b0e8ba09e3a45542a7b9c6b09c95cdd5440311",
    "obj_obj_relative_pos_nf": "sha256:11b97eea31368ed6cc7a77e8b7dcf2c9c4addbfd002d8bdca26b41f750facee0",
    "obj_obj_relative_pos_ud": "sha256:a352aadced806d7088eb0e35290316945068a4bbf142b9bfb6be848ae8903b5f",
}


R726_REQ03_QID_SET_SHA256 = {
    "camera_displacement": "sha256:3d87c5c0e723eeb55cd85d7d612b13b54256f631238e861e3e7bf507e0db9618",
    "camera_movement_direction": "sha256:359be268d81195e374e99ddb561a0b87274ff91cfed6c71b287e40f6a4b1d83f",
    "camera_obj_abs_dist": "sha256:d9c803205b487dd287a96531c141b7cd4624225699202b20bf588bf3a36ec402",
    "camera_obj_rel_dist_v1": "sha256:f41ed6c62ae1d79d7763b665790668ce148701f3d43c6270e42583a12ce2a13a",
    "camera_obj_rel_dist_v2": "sha256:e31400cb066bd3c401e5779d8da27666dceea4b1feadb96150974b202f4c3341",
    "camera_obj_rel_dist_v3": "sha256:3d86bf8a0355ab9ed755748e1b11c3e80f35e0e07f5037a6e232832f5d27cf69",
    "obj_obj_relative_pos_lr": "sha256:b2099f513a30a9651946dfd928b0e8ba09e3a45542a7b9c6b09c95cdd5440311",
    "obj_obj_relative_pos_nf": "sha256:11b97eea31368ed6cc7a77e8b7dcf2c9c4addbfd002d8bdca26b41f750facee0",
    "obj_obj_relative_pos_ud": "sha256:a352aadced806d7088eb0e35290316945068a4bbf142b9bfb6be848ae8903b5f",
}


def _r726_req03_single_source_policy(dataset_sha256: str) -> dict[str, Any]:
    return {
        "aggregation_schema": "vstibench-official-5subtask-v1",
        "dataset_id": "vstibench_repr_450",
        "dataset_sha256": dataset_sha256,
        "question_count": 450,
        "category_policy": {
            category: {
                "kind": "category",
                "source_ids": ["r726_req03_final_s1"],
                "qid_set_sha256": qid_set_sha256,
            }
            for category, qid_set_sha256 in R726_REQ03_QID_SET_SHA256.items()
        },
    }


def _upstream417_single_source_policy(source_id: str) -> dict[str, Any]:
    return {
        "aggregation_schema": "vstibench-official-5subtask-v1",
        "dataset_id": "vstibench_repr450_upstream_corrected_official_417",
        "dataset_sha256": "sha256:4686770fd7e064a5573652bdabbba092343e43f91e10a597b788027387193b0a",
        "question_count": 417,
        "category_policy": {
            category: {
                "kind": "category",
                "source_ids": [source_id],
                "qid_set_sha256": qid_set_sha256,
            }
            for category, qid_set_sha256 in UPSTREAM417_QID_SET_SHA256.items()
        },
    }


def _repr450v2_single_source_policy(source_id: str) -> dict[str, Any]:
    return {
        "aggregation_schema": "vstibench-official-5subtask-v1",
        "dataset_id": "vstibench_repr450_v2_upstream_official_450",
        "dataset_sha256": "sha256:90e1c69af81d292d26e0d4bc785b372516a7b24e66a4d08e43452e9f5417f05f",
        "question_count": 450,
        "category_policy": {
            category: {
                "kind": "category",
                "source_ids": [source_id],
                "qid_set_sha256": qid_set_sha256,
            }
            for category, qid_set_sha256 in REPR450V2_QID_SET_SHA256.items()
        },
    }


VSTI_ROLE_POLICIES.update({
    "vstibench_r726_req03_official": _r726_req03_single_source_policy(
        "sha256:10972cd0f916f39ac36570f3932f4d926ef21620af1f5f92191a89f60d289c39"
    ),
    "vstibench_r726_req03_corrected": _r726_req03_single_source_policy(
        "sha256:950b67f2f3bb300a717ce74f1f2ee81030dfe095e7ba0b78e1427a30d82b0ef4"
    ),
    "vstibench_upstream417_r726_agent": _upstream417_single_source_policy(
        "r726_req03_final_s1_upstream_official417"
    ),
    "vstibench_upstream417_r755_no_tool": _upstream417_single_source_policy(
        "r755_vsti_notool_s1_upstream_official417"
    ),
    "vstibench_repr450v2_r779_agent": _repr450v2_single_source_policy(
        "r779_repr450v2_composite"
    ),
    "vstibench_repr450v2_r780_no_tool": _repr450v2_single_source_policy(
        "r780_repr450v2_composite"
    ),
})


# Verifiable-450 (round r920): the 450-question analysis subset (50 per category) drawn as the
# 318 pose-complete members of the sealed repr450-v2 cohort plus 132 deterministic same-category
# replacements. All three arms grade the identical 450 members against the corrected projection_v2
# labels (restricted dataset sha256 5ee04360). The per-category qid sets are shared across arms.
VERIFIABLE450_QID_SET_SHA256 = {
    "camera_displacement": "sha256:0d21d008979917cb9734ba2079ec4ff03aa0e5fe0e99c9a9b719d61ab2646773",
    "camera_movement_direction": "sha256:6c89c4c718bb0143a58a0e4f8a7126a4feb1ed4825a13903465b5af78d924f10",
    "camera_obj_abs_dist": "sha256:e2f056fe7bdb23a93768f9bc77382fadafef401d883f1a6e2bbe8399fd5927b2",
    "camera_obj_rel_dist_v1": "sha256:7b5685dc84cb2b009eb091e4dbcff5e651d4c041e90148a1f345634c1150e0ac",
    "camera_obj_rel_dist_v2": "sha256:e4d65b46a980b0830812ca5d3875bb97cfd180375e746bd5500a2bd73c7fcba1",
    "camera_obj_rel_dist_v3": "sha256:4d10478e8da3c20d61fe156245f46a2a56643927263efa51cc4159eb8d213257",
    "obj_obj_relative_pos_lr": "sha256:eb691a2518483dfda62b4f989b1763d0f1b751df35a675581da82f04e8dacb5d",
    "obj_obj_relative_pos_nf": "sha256:d4abaa714b4f8b8e5874fca01aeb01cf93a88df84dd8e435cd48722125d0f6f4",
    "obj_obj_relative_pos_ud": "sha256:bb2f7dbe9b8a864287f26e373c4d8410bcecb0109161ea09fda4ba61eb3d5735",
}


def _verifiable450_single_source_policy(source_id: str) -> dict[str, Any]:
    return {
        "aggregation_schema": "vstibench-official-5subtask-v1",
        "dataset_id": "vstibench_verifiable450_projv2",
        "dataset_sha256": "sha256:5ee04360e52c6d65e5c80eb9f4387526065c22938528a9a5a1e764c5db7eee08",
        "question_count": 450,
        "category_policy": {
            category: {
                "kind": "category",
                "source_ids": [source_id],
                "qid_set_sha256": qid_set_sha256,
            }
            for category, qid_set_sha256 in VERIFIABLE450_QID_SET_SHA256.items()
        },
    }


VSTI_ROLE_POLICIES.update({
    "vstibench_verifiable450_r915_r920_gt": _verifiable450_single_source_policy(
        "r915r920_verifiable450_gt"
    ),
    "vstibench_verifiable450_r850_agent": _verifiable450_single_source_policy(
        "r850_verifiable450_agent"
    ),
    "vstibench_verifiable450_r816_no_tool": _verifiable450_single_source_policy(
        "r816_verifiable450_notool"
    ),
})


# Verifiable-450 corrected-centre ground-truth arm (REQ-20260920-235, r1340). The printed
# distance_full merge (r915 186 kept, r920 64 replacements, r957 185 corrected-serving distance
# episodes) with 15 episodes re-served on a ground-truth store whose principal point sits at the
# image centre. Same 450 members and same per-category qid sets as the arms above, so it shares
# the verifiable-450 policy shape; the uncorrected-serving arm
# `vstibench_verifiable450_r915_r920_gt` measures a different thing and stays valid.
VSTI_ROLE_POLICIES.update({
    "vstibench_verifiable450_r1340_cyfix_gt_95p75": _verifiable450_single_source_policy(
        "r1340_gt_frustum_cyfix_topup15"
    ),
})


# Verifiable-450 corrected-centre ground-truth arm with the source-guard replacements
# (REQ-20260920-235, r1362/r1381). Identical in cohort, serving and grading to
# `vstibench_verifiable450_r1340_cyfix_gt_95p75`, with four questions (3720, 3843, 4044, 4083)
# replaced by recorded episodes that a guard refusing repository and sealed-package reads
# cleared, under the user ruling of 2026-09-21. Every per-category value and the composite are
# unchanged, because each replacement row scores exactly what the row it replaces scored. Same
# 450 members and the same per-category qid sets, so it shares the verifiable-450 policy shape;
# the r1340 role it supersedes is retained as history and never deleted.
VSTI_ROLE_POLICIES.update({
    "vstibench_verifiable450_r1381_sourceguard_gt_95p75": _verifiable450_single_source_policy(
        "r1381_gt_sourceguard_topup4"
    ),
})


# Verifiable-450 corrected-centre ground-truth arm after the X1 hardened-sandbox reruns (REQ-20260924-243,
# r1549). Identical in cohort, serving and grading to
# `vstibench_verifiable450_r1381_sourceguard_gt_95p75`, with three questions (4041, 4051, 4191) rerun under a
# code-tool sandbox that refuses directory listing of run and repository roots. The X1 audit selected them because
# their recorded transcripts listed run directories; the selection used no correctness and each rerun answer is
# kept. Every per-category value and the composite are unchanged. Same 450 members and per-category qid sets; the
# r1381 role it supersedes is retained as history and never deleted.
VSTI_ROLE_POLICIES.update({
    "vstibench_verifiable450_r1549_x1_hardened_gt_95p75": _verifiable450_single_source_policy(
        "r1549_gt_x1_hardened_topup3"
    ),
})


# Verifiable-450 Gemini 3.1 Pro SPLIT agent with the usage-sink wiring fixed (REQ-20260925-249, round r1569; batch 22 of
# the score-index nomination lane, 2026-09-25). The R850 program with the plan verifier and Gemini grounding calls
# working; one fresh single-seed pass over the printed R850 cell's 450 questions, graded against the same strict label
# projection v2. Same 450 members and per-category qid sets, so it shares the verifiable-450 policy shape; the R850
# role stays as a record-only history row.
VSTI_ROLE_POLICIES.update({
    "vstibench_verifiable450_r1569_split_fixedwiring": _verifiable450_single_source_policy(
        "r1569_verifiable450_split_fixedwiring"
    ),
})


# Verifiable-450 corrected-projection-v2 CANONICAL cohort (dataset agent/vstibench_repr_450_v2.json,
# sha256 54d93aee, dataset_id vstibench_repr450_v2_canonical_450). Same 9x50 membership
# (f4b6b2b341) and identical per-category qid sets as the repr450-v2 upstream cohort above, graded
# against the canonical projection_v2 label file. Three within-planner arms share these exact
# members: r962 Qwen3.6-27B no-tool (REQ-159), r964 Gemma-4-31B no-tool, and r964 Gemma-4-31B agent
# (REQ-160). Each is a single-seed single_run per category; the official five-subtask composite is
# recomputed from raw finalized traces by ``verify-sources``.
def _repr450v2_canonical_single_source_policy(source_id: str) -> dict[str, Any]:
    return {
        "aggregation_schema": "vstibench-official-5subtask-v1",
        "dataset_id": "vstibench_repr450_v2_canonical_450",
        "dataset_sha256": "sha256:54d93aeecf16921d0c26df732103d7838095dc8931938f0108abef5a819e8294",
        "question_count": 450,
        "category_policy": {
            category: {
                "kind": "category",
                "source_ids": [source_id],
                "qid_set_sha256": qid_set_sha256,
            }
            for category, qid_set_sha256 in REPR450V2_QID_SET_SHA256.items()
        },
    }


VSTI_ROLE_POLICIES.update({
    "vstibench_repr450v2_r962_qwen_no_tool": _repr450v2_canonical_single_source_policy(
        "r962_qwen_notool_vsti450"
    ),
    "vstibench_repr450v2_r964_gemma_no_tool": _repr450v2_canonical_single_source_policy(
        "r964_gemma_notool_vsti450"
    ),
    "vstibench_repr450v2_r964_gemma_agent": _repr450v2_canonical_single_source_policy(
        "r964_gemma_agent_vsti450"
    ),
})


# Repr-450 v2 Gemini 3.1 Pro SPLIT agent with the usage-sink wiring fixed (batch 22 configuration; batch 33 of the
# score-index nomination lane, 2026-09-25): the 318 questions shared with the verifiable-450 come from r1569 and the 132
# others from r1662, the same configuration. Canonical repr-450 v2 contract (agent/vstibench_repr_450_v2.json, 54d93aee).
VSTI_ROLE_POLICIES.update({
    "vstibench_repr450v2_gemini_split_r1569_r1662": _repr450v2_canonical_single_source_policy(
        "r1569_r1662_repr450v2_split_fixedwiring"
    ),
})


# Printed Gemma SPLIT VSTIBench cell (batch 43 of the score-index nomination lane, 2026-09-25): Gemma-4-31B-it-FP8 SPLIT
# agent with Gemma itself as the tool VLM, one fresh temperature-0.6 pass of round r1658 (revision g) on the canonical
# repr-450 v2 contract (agent/vstibench_repr_450_v2.json, 54d93aee).
VSTI_ROLE_POLICIES.update({
    "vsti450_gemma_selfvlm_temp06_onepass_r1658g": _repr450v2_canonical_single_source_policy(
        "r1658g_gemma_selfvlm_repr450v2"
    ),
})


# Gemma SPLIT verifiable-450 composition (batch 43): the 318 verifiable-450 questions shared with repr-450 v2 come from
# r1658g and the 132 others from r1663h, the same Gemma self-VLM configuration; graded on the verifiable-450 projv2 file.
VSTI_ROLE_POLICIES.update({
    "vstibench_verifiable450_gemma_selfvlm_r1658g_r1663h": _verifiable450_single_source_policy(
        "r1658g_r1663h_gemma_selfvlm_verifiable450"
    ),
})


# Record-only Qwen SPLIT VSTIBench pass (batch 43): round r1617 on code-aws, the port of r1665tb (Qwen3.6-27B as its own
# tool VLM, tool-VLM thinking budget 2,048), one temperature-0.6 pass on the canonical repr-450 v2 contract.
VSTI_ROLE_POLICIES.update({
    "vsti450_qwen_tool_temp06_selfvlm_thinkbudget2048_r1617": _repr450v2_canonical_single_source_policy(
        "r1617_qwen_selfvlm_thinkbudget2048_repr450v2"
    ),
})


# Batch 48 (score-index nomination lane, 2026-09-25): the printed Qwen SPLIT VSTIBench cell r1675 (fixed point/box reply
# parser; 441 finals carried from r1617 + 9 reruns) on repr-450 v2; its verifiable-450 composition with the r1677
# complement; and the record-only Gemma all-inputs ground-truth arm r1653b on verifiable-450.
VSTI_ROLE_POLICIES.update({
    "vsti450_qwen_selfvlm_pointalias_temp06_r1675": _repr450v2_canonical_single_source_policy(
        "r1675_qwen_selfvlm_pointalias_repr450v2"
    ),
    "vstibench_verifiable450_qwen_selfvlm_r1675_r1677": _verifiable450_single_source_policy(
        "r1675_r1677_qwen_selfvlm_pointalias_verifiable450"
    ),
    "vstibench_verifiable450_gemma_gtall_r1653b_diagnostic": _verifiable450_single_source_policy(
        "r1653b_gemma_gtall_verifiable450"
    ),
})


# Batch 52 (score-index nomination lane, 2026-09-25): the record-only Qwen all-inputs ground-truth arm r1654 on
# verifiable-450 (449 finals; qid 1660, blocked by the per-episode source guard, counted wrong).
VSTI_ROLE_POLICIES.update({
    "vstibench_verifiable450_qwen_gtall_r1654_diagnostic": _verifiable450_single_source_policy(
        "r1654_qwen_gtall_verifiable450"
    ),
})


# Batch 59 (score-index nomination lane, 2026-09-26): provisional rerun compositions of the ground-truth VSTIBench arms
# (USER-RULING 2026-09-26: rerun only the unanswered questions with the same code; sealed per-run audits not rerun).
# The Qwen arm is scored over 449 questions: qid 1660, which the source guard blocked, leaves the denominator.
VERIFIABLE449_NO1660_QID_SET_SHA256 = {
    "camera_displacement": "sha256:0d21d008979917cb9734ba2079ec4ff03aa0e5fe0e99c9a9b719d61ab2646773",
    "camera_movement_direction": "sha256:6c89c4c718bb0143a58a0e4f8a7126a4feb1ed4825a13903465b5af78d924f10",
    "camera_obj_abs_dist": "sha256:4b0ec8442984be65dc4f201214e92312f7514ca4bef4eb7813f6cab346228388",
    "camera_obj_rel_dist_v1": "sha256:7b5685dc84cb2b009eb091e4dbcff5e651d4c041e90148a1f345634c1150e0ac",
    "camera_obj_rel_dist_v2": "sha256:e4d65b46a980b0830812ca5d3875bb97cfd180375e746bd5500a2bd73c7fcba1",
    "camera_obj_rel_dist_v3": "sha256:4d10478e8da3c20d61fe156245f46a2a56643927263efa51cc4159eb8d213257",
    "obj_obj_relative_pos_lr": "sha256:eb691a2518483dfda62b4f989b1763d0f1b751df35a675581da82f04e8dacb5d",
    "obj_obj_relative_pos_nf": "sha256:d4abaa714b4f8b8e5874fca01aeb01cf93a88df84dd8e435cd48722125d0f6f4",
    "obj_obj_relative_pos_ud": "sha256:bb2f7dbe9b8a864287f26e373c4d8410bcecb0109161ea09fda4ba61eb3d5735",
}


def _verifiable449_no1660_single_source_policy(source_id: str) -> dict[str, Any]:
    return {
        "aggregation_schema": "vstibench-official-5subtask-v1",
        "dataset_id": "vstibench_verifiable450_projv2_minus1660",
        "dataset_sha256": "sha256:f2d60084fcd3730f5ce3057ba5a435fb3ae1f1a233d5bd72083cd7a78e2e2cbc",
        "question_count": 449,
        "category_policy": {
            category: {
                "kind": "category",
                "source_ids": [source_id],
                "qid_set_sha256": qid_set_sha256,
            }
            for category, qid_set_sha256 in VERIFIABLE449_NO1660_QID_SET_SHA256.items()
        },
    }


VSTI_ROLE_POLICIES.update({
    "vstibench_verifiable450_gemma_gtall_r1653b_req255_rerun_diagnostic": _verifiable450_single_source_policy(
        "r1653b_req255_gemma_gtall_rerun7_verifiable450"
    ),
    "vstibench_verifiable449_qwen_gtall_r1654_req256_rerun_diagnostic": _verifiable449_no1660_single_source_policy(
        "r1654_req256_qwen_gtall_rerun25_verifiable449"
    ),
})


# Batch 67 (score-index nomination lane, 2026-09-26): the printed Gemma SPLIT VSTIBench cell after REQ-20260926-257, the
# r1658g pass with its one unanswered-by-method question (587) rerun once with a 131,072-token window and a 65,536-token
# output allowance (request seed 2). Supersedes vsti450_gemma_selfvlm_temp06_onepass_r1658g; same canonical repr-450 v2 contract.
VSTI_ROLE_POLICIES.update({
    "vsti450_gemma_selfvlm_temp06_r1658g_req257_ctx131k": _repr450v2_canonical_single_source_policy(
        "r1658g_req257_gemma_selfvlm_repr450v2"
    ),
})


# Batch bypass01 (score-index nomination lane, 2026-09-26): the printed Qwen tool-free VSTIBench cell after
# REQ-20260926-257, the r1513 pass with its four unanswered questions (880, 893, 4592, 5815) rerun once with a
# 131,072-token window and a 65,536-token output allowance (request seed 2). Supersedes vsti450_qwen_notool_temp06_onepass; same canonical
# repr-450 v2 contract.
VSTI_ROLE_POLICIES.update({
    "vsti450_qwen_notool_temp06_r1513_req257_ctx131k": _repr450v2_canonical_single_source_policy(
        "r1513_req257_qwen_notool_repr450v2"
    ),
})


# Batch 73 (score-index nomination lane, 2026-09-26): the printed Qwen SPLIT VSTIBench cell after REQ-20260926-257, the
# r1675 pass with three of its unanswered questions (1822, 3736, 4548) rerun once with a 131,072-token window and a
# 65,536-token output allowance (request seed 2). Supersedes vsti450_qwen_selfvlm_pointalias_temp06_r1675; same canonical
# repr-450 v2 contract.
VSTI_ROLE_POLICIES.update({
    "vsti450_qwen_selfvlm_pointalias_temp06_r1675_req257_ctx131k": _repr450v2_canonical_single_source_policy(
        "r1675_req257_qwen_selfvlm_pointalias_repr450v2"
    ),
})


# Full 5,736-question VSTIBench release (score-index nomination lane, 2026-09-24). Every question of
# the corrected release, graded against its strict label projection (multiple-choice ground truth :=
# the corrected-release mc_answer; numeric ground truth unchanged), file
# r850_vsti_fullset_agent_20260725/postrun_full5736_terminal_v11_projection_v2/
# vstibench_test_strict_projection.json, sha256 b91e5f0f. This is the full-benchmark scope; the
# canonical repr-450 contract (agent/vstibench_repr_450_v2.json, sha256 54d93aee) governs the
# 450-question roles above and is not this role's dataset. Each arm is a single-seed single_run per
# category over the traces its postrun scorer staged and scored: r850 agent (the published 450 plus
# the r850 complement of 5,286) and r816 no-tool. The paper prints these two composites.
FULL5736_QID_SET_SHA256 = {
    "camera_displacement": "sha256:88247488e8482ba27b3f93f6952c3a964dc9032c92354c12bb9f06e96f5f8a10",
    "camera_movement_direction": "sha256:bedb6bbf6c4cb9117e5653186f75804b779fc0132da794fc5289bef65353eba6",
    "camera_obj_abs_dist": "sha256:6fc431f187d1e3818169f02f757231ec026da3963a4b985263a41f0c06f9408e",
    "camera_obj_rel_dist_v1": "sha256:e2f2e7bb2a09f4048f7711b0c957604d01b4a94590a5ced4349afefece4b85a3",
    "camera_obj_rel_dist_v2": "sha256:30ab0224d834fc2f0238554101c22363fcf731f86ecdfe3857fb3ba24c4c2d7b",
    "camera_obj_rel_dist_v3": "sha256:f82ba72e1923e55386127847de99b9fc9e2fcea024722dbd5bfa1fa316fe199a",
    "obj_obj_relative_pos_lr": "sha256:fb3d7a24363df3aa1c4c9a84707476bb558286562d90e653f49d4d214307c320",
    "obj_obj_relative_pos_nf": "sha256:39f52bd31d5a275767c965c9af3ae6adb7b2389a5677a162d6b1c29bb55439be",
    "obj_obj_relative_pos_ud": "sha256:4494c0ca1ed576dd80f86c1218c497361d757411dfa96f114307e7a00e74e25e",
}


def _full5736_projv2_single_source_policy(source_id: str) -> dict[str, Any]:
    return {
        "aggregation_schema": "vstibench-official-5subtask-v1",
        "dataset_id": "vstibench_full5736_strict_projection_v2",
        "dataset_sha256": "sha256:b91e5f0f7eb40a9d362a6076a6cad8ccc909533e9432e5d9787a1fa1328386ca",
        "question_count": 5736,
        "category_policy": {
            category: {
                "kind": "category",
                "source_ids": [source_id],
                "qid_set_sha256": qid_set_sha256,
            }
            for category, qid_set_sha256 in FULL5736_QID_SET_SHA256.items()
        },
    }


VSTI_ROLE_POLICIES.update({
    "vstibench_full5736_r850_split_78p25": _full5736_projv2_single_source_policy("r850_full5736_agent"),
    "vstibench_full5736_r816_notool_57p67": _full5736_projv2_single_source_policy("r816_full5736_notool"),
})


# Temperature-0.6 rerun compositions (score-index nomination lane, 2026-09-24; USER 2026-09-24 04:25 PT:
# "Nominate today's compositions."). Same canonical repr-450 v2 contract and per-category qid sets as the
# roles above; each category is a single_run over the composition's scored traces (kept base traces plus
# the rerun traces that replace every wrong base answer), linked without copying into the lane's source root.
VSTI_ROLE_POLICIES.update({
    "vsti450_qwen_tool_temp06_allwrong": _repr450v2_canonical_single_source_policy(
        "r1476_qwen_tool_temp06_allwrong"
    ),
})
VSTI_ROLE_POLICIES.update({
    "vsti450_gemma_notool_temp06_allwrong": _repr450v2_canonical_single_source_policy(
        "r1477_gemma_notool_temp06_allwrong"
    ),
})
VSTI_ROLE_POLICIES.update({
    "vsti450_gemma_tool_temp06_allwrong": _repr450v2_canonical_single_source_policy(
        "r1478_gemma_tool_temp06_allwrong"
    ),
})
# Single temperature-0.6 pass (no rerun composition): Qwen3.6-27B tool-free, REQ-20260924-242, round r1513.
VSTI_ROLE_POLICIES.update({
    "vsti450_qwen_notool_temp06_onepass": _repr450v2_canonical_single_source_policy(
        "r1513_qwen_notool_temp06_onepass"
    ),
})
# Single temperature-0.6 passes (score-index nomination lane, 2026-09-24 evening batch 15): Qwen3.6-27B SPLIT
# tool arm (round r1525) and Gemma-4-31B tool-free arm (round r1526); one episode per question, no rerun for
# correctness.
VSTI_ROLE_POLICIES.update({
    "vsti450_qwen_tool_temp06_onepass": _repr450v2_canonical_single_source_policy(
        "r1525_qwen_tool_temp06_onepass"
    ),
    "vsti450_gemma_notool_temp06_onepass": _repr450v2_canonical_single_source_policy(
        "r1526_gemma_notool_temp06_onepass"
    ),
})


# DIAGNOSTIC oracle-perception roles (batch 15), never benchmark scores: Gemini 3.1 Pro SPLIT with privileged
# inputs from the source scans' annotations on the 72 ScanNet questions of the canonical repr-450 v2 contract.
# The dataset file holds those 72 items copied unchanged, in file order, from agent/vstibench_repr_450_v2.json
# (SHA-256 54d93aee...), so every label and answer mapping is the canonical one; each category's question set is
# pinned below. The dataset id names the subset so a composite of these roles cannot pass as a 450 role.
SCANNET72_ORACLE_QID_SET_SHA256 = {
    "camera_displacement": "sha256:98abbf24535347c97af135589d7062c9ea47241f5542d4576606fab5e0e7b291",
    "camera_movement_direction": "sha256:19b71fcaaf3df8f0c6dfb9720f9072039dd6dc8e741b385f4f8a6c188966f19c",
    "camera_obj_abs_dist": "sha256:fcae8d6e82209388986941f197319ba27e6082478e0f6e081871ce8118d609c8",
    "camera_obj_rel_dist_v1": "sha256:f51ae60ad3dc642a8b9756be9ddf35a9af65de62b38f2935e639a0b3f5b6bd8c",
    "camera_obj_rel_dist_v2": "sha256:d34afdf37c8de3f94478aec13f49baf0bd6b2e8714ad2cd92b2442f177c1af33",
    "camera_obj_rel_dist_v3": "sha256:df2997647d70ff20455db143ea495282c7db99c8832d01f08ac85f62f6b11631",
    "obj_obj_relative_pos_lr": "sha256:20dd95acf50953583f60bb7933219c270608efc5c5c8fa3362a144c36512582d",
    "obj_obj_relative_pos_nf": "sha256:a4e777ca15373ee3fc4b194368083d6f9a5e7a5053e1db7778531d124bb95eb9",
    "obj_obj_relative_pos_ud": "sha256:c4b2298af696d01f7aaba4c048fa83df536a4edea76d4d227c9971ba8ce62618",
}


def _scannet72_oracle_single_source_policy(source_id: str) -> dict[str, Any]:
    return {
        "aggregation_schema": "vstibench-official-5subtask-v1",
        "dataset_id": "vstibench_repr450_v2_scannet72_oracle_subset",
        "dataset_sha256": "sha256:21cdcf95eb7f0594ad5f4b9cec3e281b5d817a231172872568476774609ae140",
        "question_count": 72,
        "category_policy": {
            category: {
                "kind": "category",
                "source_ids": [source_id],
                "qid_set_sha256": qid_set_sha256,
            }
            for category, qid_set_sha256 in SCANNET72_ORACLE_QID_SET_SHA256.items()
        },
    }


VSTI_ROLE_POLICIES.update({
    "vsti72_oracle_grounding_gemini": _scannet72_oracle_single_source_policy(
        "r1503_oracle_grounding_gemini_vsti72"
    ),
    "vsti72_oracle_both_gemini": _scannet72_oracle_single_source_policy(
        "r1504_oracle_both_gemini_vsti72"
    ),
    "vsti72_oracle_geometry_gemini": _scannet72_oracle_single_source_policy(
        "r1502_oracle_geometry_gemini_vsti72"
    ),
})


def current_scorer_manifest() -> dict[str, Any]:
    fragment = core.core_manifest_fragment(scoring)
    self_path = Path(__file__).resolve()
    return {
        "manifest_schema": "mechanical-scorer-manifest-v1",
        **fragment,
        "score_index_vstibench_py_sha256": core._sha256_bytes(self_path.read_bytes()),
    }


def current_scorer_id() -> str:
    return core._sha256_bytes(core.canonical_json_bytes(current_scorer_manifest()))


def build_category_record(
    dataset_path: str | Path,
    artifact_dir: str | Path,
    *,
    dataset_id: str,
    category: str,
    source_id: str,
    artifact_key: str,
    source_kind: str = "single_run",
) -> dict[str, Any]:
    """Build one raw-only category record without writing it."""

    return core.build_category_record(
        dataset_path,
        artifact_dir,
        dataset_id=dataset_id,
        category=category,
        source_id=source_id,
        artifact_key=artifact_key,
        scorer_id=current_scorer_id(),
        source_kind=source_kind,
    )


def build_seed_mean_record(constituent_records) -> dict[str, Any]:
    """Build a ``seed_mean`` record averaging >=2 same-category category records."""

    return core.build_seed_mean_record(constituent_records, scorer_id=current_scorer_id())


def build_composite_record(aggregation_schema: str, category_source_records) -> dict[str, Any]:
    """Build a ``composite`` record from a per-category map of category/seed_mean records."""

    return core.build_composite_record(
        aggregation_schema, category_source_records, scorer_id=current_scorer_id()
    )


def write_record(record: Mapping[str, Any], records_dir: str | Path) -> Path:
    """Atomically create a content-addressed record; never overwrite."""

    _validate_record(record, require_current_scorer=True, records_dir=Path(records_dir))
    return core.write_record_bytes(record, records_dir)


def _validate_record(
    record: Mapping[str, Any],
    *,
    require_current_scorer: bool,
    records_dir: Path | None = None,
) -> None:
    resolve = None
    if records_dir is not None:
        resolve = lambda record_id: _load_record_from_dir(records_dir, record_id)  # noqa: E731
    core.validate_record(
        record,
        expected_scorer_id=current_scorer_id() if require_current_scorer else None,
        resolve=resolve,
    )


def _load_record_from_dir(records_dir: Path, record_id: str) -> dict[str, Any]:
    record = core.read_canonical_record(records_dir, record_id)
    _validate_record(record, require_current_scorer=True, records_dir=records_dir)
    return record


def _load_record(repo_root: Path, record_id: str) -> dict[str, Any]:
    records_dir = repo_root / RECORDS_RELATIVE_DIR
    return _load_record_from_dir(records_dir, record_id)


def _artifact_path(artifact_root: Path, artifact_key: str) -> Path:
    return core.artifact_path(artifact_root, artifact_key)


def _validate_evidence(repo_root: Path, role: str, evidence: Any) -> None:
    if not isinstance(evidence, list) or not evidence:
        raise ScoreIndexError(f"{role} requires at least one evidence file")
    seen_paths: set[str] = set()
    for item in evidence:
        if not isinstance(item, Mapping):
            raise ScoreIndexError(f"{role} evidence entry is not an object")
        core._expect_keys(item, {"path", "sha256"}, f"{role} evidence")
        if item["path"] in seen_paths:
            raise ScoreIndexError(f"{role} repeats evidence path {item['path']}")
        seen_paths.add(item["path"])
        core._validate_sha256(item["sha256"], "evidence sha256")
        path = core.safe_repo_file(repo_root, item["path"])
        if core._sha256_bytes(core._read_stable_bytes(path)) != item["sha256"]:
            raise ScoreIndexError(f"{role} evidence hash mismatch: {item['path']}")


def _validate_composite_role(
    repo_root: Path,
    role: str,
    nomination: Mapping[str, Any],
) -> dict[str, Any]:
    # Validate note: policy-pending roles require a non-empty string containing the marker.
    if role in VSTI_POLICY_PENDING_ROLES:
        note = nomination.get("note", "")
        if not isinstance(note, str) or not note.strip():
            raise ScoreIndexError(
                f"{role} requires a non-empty string note (policy-pending role)"
            )
        if POLICY_PENDING_NOTE_MARKER not in note:
            raise ScoreIndexError(
                f"{role} note must contain '{POLICY_PENDING_NOTE_MARKER}'"
            )
    # Strip optional `note` field before key-set check (does not affect scoring content).
    nom_for_check = {k: v for k, v in nomination.items() if k != "note"}
    core._expect_keys(nom_for_check, {"composite_record_id", "evidence"}, role)
    policy = VSTI_ROLE_POLICIES[role]
    composite = _load_record(repo_root, nomination["composite_record_id"])
    if composite["record_type"] != "composite":
        raise ScoreIndexError(f"{role} composite_record_id does not name a composite")
    if composite["aggregation"]["schema"] != policy["aggregation_schema"]:
        raise ScoreIndexError(f"{role} names an unapproved aggregation schema")
    if composite["dataset"]["dataset_id"] != policy["dataset_id"]:
        raise ScoreIndexError(f"{role} names an unapproved dataset")
    if composite["dataset"]["sha256"] != policy["dataset_sha256"]:
        raise ScoreIndexError(f"{role} dataset hash does not match the closed scope")
    if composite["scope"]["question_count"] != policy["question_count"]:
        raise ScoreIndexError(f"{role} question count does not match its closed scope")
    if set(policy["category_policy"]) != set(VSTI_CATEGORIES):
        raise ScoreIndexError(f"{role} category_policy does not cover the exact VSTI scope")

    core.validate_composite_role_policy(
        composite, policy, resolve=lambda record_id: _load_record(repo_root, record_id)
    )
    _validate_evidence(repo_root, role, nomination["evidence"])
    return composite


def validate_checked_in_score_index(repo_root: str | Path) -> dict[str, Any]:
    """Validate the checked-in index and records without reading raw traces."""

    repo_root = Path(repo_root)
    index_path = repo_root / INDEX_RELATIVE_PATH
    index = _read_canonical_json(index_path, str(index_path))
    if not isinstance(index, dict):
        raise ScoreIndexError("SCORE_INDEX_VSTIBENCH.json is not an object")
    core._expect_keys(index, {"nominations", "schema_version", "scorer_id"}, "score index")
    if index["schema_version"] != INDEX_SCHEMA_VSTI:
        raise ScoreIndexError("unsupported score index schema")
    if index["scorer_id"] != current_scorer_id():
        raise ScoreIndexError("score index scorer_id is stale")
    nominations = index["nominations"]
    if not isinstance(nominations, Mapping) or set(nominations) != set(VSTI_ROLE_POLICIES):
        raise ScoreIndexError(
            "score index must contain only the approved VSTIBench roles: "
            + ", ".join(sorted(VSTI_ROLE_POLICIES))
        )
    loaded: dict[str, Any] = {}
    for role in VSTI_ROLE_POLICIES:
        composite = _validate_composite_role(repo_root, role, nominations[role])
        loaded[role] = {"composite": composite}
    return {"index": index, "records": loaded, "scorer_id": index["scorer_id"]}


def _read_canonical_json(path: Path, label: str) -> Any:
    data = core._read_stable_bytes(path)
    parsed = core._loads_json(data, label)
    if data != core.canonical_json_bytes(parsed):
        raise ScoreIndexError(f"{label} is not canonical JSON")
    return parsed


def validate_repository(repo_root: str | Path) -> list[str]:
    """Return validation errors; an empty list means the repository is valid."""

    try:
        validate_checked_in_score_index(repo_root)
    except (ScoreIndexError, OSError) as exc:
        return [str(exc)]
    return []


def verify_nomination_sources(
    repo_root: str | Path,
    role: str,
    dataset_path: str | Path,
    artifact_root: str | Path,
) -> dict[str, Any]:
    """Replay one nomination from raw sources and require exact record equality."""

    if role not in VSTI_ROLE_POLICIES:
        raise ScoreIndexError(f"unsupported score role {role!r}")
    repo_root = Path(repo_root)
    validated = validate_checked_in_score_index(repo_root)
    checked_composite = validated["records"][role]["composite"]
    policy = VSTI_ROLE_POLICIES[role]
    rebuilt_composite = core.verify_composite_role_sources(
        dataset_path=dataset_path,
        artifact_root=artifact_root,
        checked_composite=checked_composite,
        policy=policy,
        load_record=lambda record_id: _load_record(repo_root, record_id),
        scorer_id=current_scorer_id(),
    )
    return {
        "composite_record_id": rebuilt_composite["record_id"],
        "role": role,
        "scorer_id": rebuilt_composite["scorer_id"],
        "verified": True,
    }


def query(repo_root: str | Path, role: str, category: str | None = None) -> dict[str, Any]:
    if role not in VSTI_ROLE_POLICIES:
        raise ScoreIndexError(f"unsupported score role {role!r}")
    validated = validate_checked_in_score_index(repo_root)
    nomination = validated["index"]["nominations"][role]
    composite = validated["records"][role]["composite"]
    if category is None:
        record = composite
    else:
        if category not in VSTI_CATEGORIES:
            raise ScoreIndexError(f"unsupported VSTI category {category!r}")
        entry = composite["category_sources"][category]
        record = _load_record(Path(repo_root), entry["record_id"])
    result: dict[str, Any] = {"evidence": nomination["evidence"], "record": record, "role": role}
    if "note" in nomination:
        result["note"] = nomination["note"]
    return result


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    verify = subparsers.add_parser("verify", help="validate the checked-in score index")
    verify.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[2]))
    query_parser = subparsers.add_parser("query", help="read one reviewed nomination")
    query_parser.add_argument("role", choices=tuple(VSTI_ROLE_POLICIES))
    query_parser.add_argument("--category", choices=VSTI_CATEGORIES)
    query_parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[2]))
    source_parser = subparsers.add_parser(
        "verify-sources", help="replay one nomination from its raw traces"
    )
    source_parser.add_argument("role", choices=tuple(VSTI_ROLE_POLICIES))
    source_parser.add_argument("--dataset-path", required=True)
    source_parser.add_argument("--artifact-root", required=True)
    source_parser.add_argument(
        "--repo-root", default=str(Path(__file__).resolve().parents[2])
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "verify":
            errors = validate_repository(args.repo_root)
            payload = {
                "errors": errors,
                "scorer_id": current_scorer_id(),
                "valid": not errors,
            }
            print(json.dumps(payload, sort_keys=True))
            return 0 if not errors else 1
        if args.command == "verify-sources":
            payload = verify_nomination_sources(
                args.repo_root,
                args.role,
                args.dataset_path,
                args.artifact_root,
            )
        else:
            payload = query(args.repo_root, args.role, args.category)
        print(json.dumps(payload, allow_nan=False, sort_keys=True))
        return 0
    except (ScoreIndexError, OSError) as exc:
        print(json.dumps({"error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
