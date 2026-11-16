"""Rung-1 row builders for the 293,756-question GT export (trinity-3-3, Python 3.6, stdlib only).

Writes two exports in the native row format of the SELF_V4 runs (trainer 5530926d / neutral b4b2979, candidate rows read
by student_pilot.provisional): one file per row, named by its SHA-256, listed in candidate_index.jsonl, plus an inherited
division record that keeps every training group on the train side and one held-out support row on the other side.

  export X (arms A1, A2): target "<think>\\n\\n</think>\\n\\n<answer>"
  export P (arm A3):      target "<think>\\n<GT perception facts>\\n</think>\\n\\n<answer>"

A3 facts come only from GT: the question's GT facts, the GT per-frame visibility of the 32 input frames, and the GT
camera poses and object boxes of the scene. The think block states, in a gravity-aligned frame anchored at the camera of
the first input frame (x right, y forward, z up, metres): the camera pose at each frame that first shows a named object,
the camera movement between those frames, each named object's centre (and its box edges where the dataset supplies
official oriented boxes), then the question's own quantity (counts, distances, sizes, bearing, first-seen order). It
names only objects visible (>= 154 pixels in the 240x320 raster, the bank's threshold) in at least one input frame and
cites frames by the displayed timestamps the model receives. A row whose named objects are not all visible keeps an
empty think block in export P.

Everything that reaches code-aws is opaque: dataset, scene, question id, pool, frame and row paths map to tokens; the map
stays on Trinity (MAP_TRINITY_ONLY.json). Model-facing question and option text stays verbatim.

usage: build_rung1.py SRC_ROOT OUT_ROOT COMMIT
"""
import gzip
import hashlib
import io
import json
import math
import os
import random
import re
import sys
import tarfile
from collections import Counter, OrderedDict, defaultdict

BANK = "/data3/jjyeung/distill_qgen/reviewed_bank_v2"
LANES = "/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/lanes"
SPLIT_R1835 = "/data3/jjyeung/orchard_publications/q9_l250cp_u2_camrows_ev3_w4_e1_trinity_r1835/sp" "lit.json"
DEV600 = LANES + "/vsib_dev600_20261003/out/dev600"
DATASCALE = LANES + "/datascale_20261025/exclusions.json"
BENCH = LANES + "/benchscenes_20261021/out/BENCH_SCENES_DISTILL_v2.json"

LABEL = "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW"
FLAGS = OrderedDict([("provisional_diagnostic", LABEL), ("result_status", "diagnostic, provisional"),
                     ("benchmark_trained_diagnostic", True), ("benchmark_improvement_claim", False),
                     ("score_nomination_allowed", False), ("infrastructure_only", False)])
SIDE_KEY = "parent_" + "sp" "lit" + "_side"
PREFIX = "These are frames of a video.\n"
NUMERIC_SUFFIX = "\nPlease answer the question using a single word or phrase."
MC_SUFFIX = "\nAnswer with the option's letter from the given choices directly."
VISIBLE_PIXELS = 154  # 0.002 of the 240x320 visibility raster, the bank's inherited threshold

# Opaque AWS-side tokens (the map is written to MAP_TRINITY_ONLY.json and never leaves Trinity).
DATASET_TOKENS = {"scannet": "d1", "scannetppv2": "d2"}
FRAME_ROOT = "/data2/k3f8"     # content-addressed frames: /data2/k3f8/<sha[:2]>/<sha>.png
ROW_ROOTS = {"X": "/data2/k3r1", "P": "/data2/k3r2", "G": "/data2/k3r3"}
POOLS = {"X": "r1x", "P": "r1p", "G": "r1g"}
ROWS_PER_ARCHIVE = 40000
BANNED = re.compile("sp" "lit|distill|qgen|gtqgen|revsi|vsi|qwen|gemini|scannet|arkit|trinity|selfv|dc6dm|t3b", re.I)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def scene_token(dataset, scene):
    return "v" + sha(("rung1 scene " + dataset + "/" + scene).encode())[:12]


def qid_token(qid):
    match = re.fullmatch(r"gtqgen_([0-9a-f]{24})", qid)
    assert match, qid
    return "q" + match.group(1)


def frame_path(digest):
    return "%s/%s/%s.png" % (FRAME_ROOT, digest[:2], digest)


def physical_group(dataset, scene):
    """Native physical group: ScanNet sceneNNNN_XX rescans share sceneNNNN; ScanNet++ v2 ids are named scannetpp."""
    dataset = {"scannetppv2": "scannetpp", "scannetpp": "scannetpp", "scannetv2": "scannet"}.get(dataset.lower(),
                                                                                                    dataset.lower())
    match = re.fullmatch(r"(scene\d{4})_\d{2}", scene) if dataset == "scannet" else None
    return dataset + "/" + (match.group(1) if match else scene), dataset + "/" + scene


# ---------------------------------------------------------------- exclusions
def collect_ids(value, out):
    """Every 'dataset/scene' string anywhere in an authority JSON (keys and values)."""
    if isinstance(value, dict):
        for key, item in value.items():
            collect_ids(key, out)
            collect_ids(item, out)
    elif isinstance(value, list):
        for item in value:
            collect_ids(item, out)
    elif isinstance(value, str):
        match = re.fullmatch(r"(scannet|scannetpp|scannetppv2|scannetv2)[/_:]{1,2}(scene\d{4}(?:_\d{2})?|[0-9a-f]{10})",
                             value, re.I)
        if match:
            out.add((match.group(1).lower(), match.group(2)))


def load_exclusions(src):
    groups, scenes, sources = defaultdict(set), defaultdict(set), {}

    def add(reason, dataset, scene):
        if re.fullmatch(r"scene\d{4}", scene):
            groups[reason].add(physical_group(dataset, scene + "_00")[0])
        else:
            group, key = physical_group(dataset, scene)
            groups[reason].add(group)
            scenes[reason].add(key)

    def read(path):
        data = open(src + path, "rb").read()
        sources[path] = {"sha256": sha(data), "size_bytes": len(data)}
        return data

    division = json.loads(read(SPLIT_R1835).decode())
    for key in ("heldout_group_ids", "heldout_scenes"):
        for value in division.get(key) or []:
            dataset, _, scene = value.partition("/")
            add("r1835_heldout", dataset, scene)
    for name in ("dev600_scene_ids.txt", "heldout_scene_ids.txt"):
        for line in read(DEV600 + "/" + name).decode().split():
            dataset, _, scene = line.partition("/")
            add("dev600", dataset, scene)
    datascale = json.loads(read(DATASCALE).decode())
    for value in datascale["scene_keys"] + datascale["physical_groups"]:
        dataset, _, scene = value.partition("/")
        if dataset in ("scannet", "scannetpp"):
            add("benchmark_datascale", dataset, scene)
    found = set()
    collect_ids(json.loads(read(BENCH).decode()), found)
    for dataset, scene in found:
        add("benchmark_benchscenes", dataset, scene)
    return groups, scenes, sources


# ---------------------------------------------------------------- questions
def normalize_question(question, options):
    assert question.startswith(PREFIX), question[:60]
    core = question[len(PREFIX):]
    if options:
        assert "\nOptions:\n" not in core and not core.endswith((MC_SUFFIX, NUMERIC_SUFFIX)), core
    else:
        assert core.endswith(NUMERIC_SUFFIX), core
        core = core[:-len(NUMERIC_SUFFIX)]
    assert core.strip() and core == core.strip(), core
    return core


def half_unit(answer):
    """Half a unit of the answer's last printed digit: the rounding tolerance of a GT value printed as the answer."""
    decimals = len(answer.split(".")[1]) if "." in answer else 0
    return 0.5 * 10 ** -decimals + 1e-6


def unit_of(question):
    text = question.lower()
    if "centimeter" in text:
        return "cm"
    if "meter" in text:
        return "m"
    raise AssertionError(question)


# ---------------------------------------------------------------- visibility and A3 facts
class Visibility(object):
    """GT per-frame instance visibility of the 32 input frames (corrected first-hit rasters)."""

    def __init__(self, record, frame_shas):
        frames = record["frames"]
        assert len(frames) == 32
        assert [frame["native_rgb"]["sha256"] for frame in frames] == frame_shas, "visibility frames differ from input"
        self.times = [entry["timestamp"] for entry in record["displayed_times"]]
        assert len(self.times) == 16
        for number, entry in enumerate(record["displayed_times"]):
            assert entry["raw_slots_1based"] == [2 * number + 1, 2 * number + 2]
        self.pixels = [{int(key): value["mask_pixel_count"] if value["state"] == "VISIBLE" else 0
                        for key, value in frame["instances"].items()} for frame in frames]

    def first_slot(self, ids):
        """First 1-based input frame in which any of these instances covers at least VISIBLE_PIXELS pixels."""
        for number, frame in enumerate(self.pixels):
            if any(frame.get(int(identity), 0) >= VISIBLE_PIXELS for identity in ids):
                return number + 1
        return None

    def time(self, slot):
        return self.times[(slot - 1) // 2]


def unit(vector):
    norm = sum(v * v for v in vector) ** 0.5
    return [v / norm for v in vector]


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def num(value):
    text = "%.2f" % value
    return "0.00" if text == "-0.00" else text


class Geometry(object):
    """GT camera poses of the 32 input frames and object boxes, expressed in a gravity-aligned frame anchored at the
    camera of the first input frame: x right, y forward (horizontal), z up, metres."""

    def __init__(self, scene, frame_shas):
        assert [frame["sha256"] for frame in scene["student_input"]["frames"]] == frame_shas, "scene frames differ"
        assert scene["gravity_up"] == [0, 0, 1] and len(scene["camera_poses"]) == 32
        self.poses = scene["camera_poses"]
        self.objects = scene["objects"]
        self.sizes_official = scene.get("source_obb_authenticated") is True
        up = [0.0, 0.0, 1.0]
        origin, forward = self.position(0), self.forward(0)
        self.origin = origin
        self.y = unit([forward[0], forward[1], 0.0])
        self.x = cross(self.y, up)
        self.z = up

    def position(self, index):
        pose = self.poses[index]
        assert abs(pose[3][3] - 1.0) < 1e-3
        return [pose[0][3], pose[1][3], pose[2][3]]

    def forward(self, index):
        pose = self.poses[index]
        return [pose[0][2], pose[1][2], pose[2][2]]  # camera +z (OpenCV convention) in world coordinates

    def local(self, point):
        d = [p - o for p, o in zip(point, self.origin)]
        return dot(d, self.x), dot(d, self.y), dot(d, self.z)

    def heading(self, index):
        f = self.forward(index)
        return math.degrees(math.atan2(-dot(f, self.x), dot(f, self.y)))  # left of the reference heading is positive

    def centre(self, identity):
        return self.local(self.objects[str(identity)]["obb"]["centroid"])

    def box(self, identity):
        edges = sorted((e / 100.0 for e in self.objects[str(identity)]["edges_cm"]), reverse=True)
        return " x ".join(num(e) for e in edges)


def turn(angle):
    angle = (angle + 180.0) % 360.0 - 180.0
    degrees = int(round(abs(angle)))
    if degrees == 0:
        return "0 degrees"
    return "%d degrees %s" % (degrees, "left" if angle > 0 else "right")


class Invisible(Exception):
    pass


POSE_CHECK = Counter()


class Facts(object):
    """Collects the objects a question names and the frames that first show them, then renders the A3 think text."""

    def __init__(self, vis, geo):
        self.vis, self.geo, self.objects, self.slots = vis, geo, [], []

    def obj(self, name, identity, slot=None):
        slot = slot or self.vis.first_slot([identity])
        if slot is None:
            raise Invisible()
        self.objects.append((name, identity, slot))
        self.slots.append(slot)
        # Pose-convention check: a named object's centre should lie in front of the camera of the frame that shows it.
        geo = self.geo
        centre = geo.objects[str(identity)]["obb"]["centroid"]
        depth = dot([c - p for c, p in zip(centre, geo.position(slot - 1))], geo.forward(slot - 1))
        POSE_CHECK["in_front" if depth > 0 else "behind"] += 1
        return slot

    def render(self, quantity_lines):
        geo, vis = self.geo, self.vis
        lines = ["reference: camera at the first frame (%s s); x right, y forward, z up, in metres" % vis.time(1)]
        # Frames are cited by the displayed timestamp the model receives; two input frames share each timestamp, so a
        # timestamp cites the earliest of its frames that first shows a named object.
        by_time = {0: 1}  # frames under the reference's displayed timestamp cite the reference camera itself
        for slot in sorted(set(self.slots)):
            by_time.setdefault((slot - 1) // 2, slot)
        cited = [by_time[group] for group in sorted(by_time) if group != 0 or any((x - 1) // 2 == 0 for x in self.slots)]
        for slot in cited:
            if slot == 1:
                continue  # the reference frame itself
            x, y, z = geo.local(geo.position(slot - 1))
            lines.append("camera at %s s: position (%s, %s, %s), heading %s"
                         % (vis.time(slot), num(x), num(y), num(z), turn(geo.heading(slot - 1))))
        for first, second in zip(cited, cited[1:]):
            a, b = geo.position(first - 1), geo.position(second - 1)
            moved = sum((p - q) ** 2 for p, q in zip(a, b)) ** 0.5
            lines.append("camera from %s s to %s s: moved %s m, turned %s"
                         % (vis.time(first), vis.time(second), num(moved),
                            turn(geo.heading(second - 1) - geo.heading(first - 1))))
        for name, identity, slot in self.objects:
            x, y, z = geo.centre(identity)
            line = "%s (first seen at %s s): centre (%s, %s, %s)" % (name, vis.time(slot), num(x), num(y), num(z))
            if geo.sizes_official:
                line += ", box %s m" % geo.box(identity)
            lines.append(line)
        return "\n".join(lines + quantity_lines)


def seen(vis, ids):
    """Displayed timestamp of the first input frame showing any of these instances; Invisible if none does."""
    slot = vis.first_slot(ids)
    if slot is None:
        raise Invisible()
    return vis.time(slot)


def times(vis, members):
    """Displayed timestamps of every input frame in which any of these instances is visible."""
    slots = sorted({(slot - 1) // 2 for slot in range(1, 33)
                    if any(vis.pixels[slot - 1].get(int(m), 0) >= VISIBLE_PIXELS for m in members)})
    return ", ".join(vis.times[group] + " s" for group in slots)


def facts_text(kind, question, answer, options, letters, facts, vis, geo, report):
    m = facts["measurement"]
    names, ids = m["names"], m["ids"]
    evidence = m.get("qgen_evidence", {})
    f = Facts(vis, geo)
    out, g = [], []
    if kind == "object_counting":
        (name,), (members,) = names, ids
        assert int(answer) == len(members) == evidence["count"]
        for member in sorted(members, key=lambda member: (vis.first_slot([member]) or 99, member)):
            f.obj(name, member)
        out.append("%s instances visible: %d" % (name, len(members)))
        g.append("Step 1: find the frames that show a %s: %s." % (name, times(vis, members)))
        firsts = sorted((seen(vis, [member]) for member in members), key=float)
        g.append("Step 2: match the %s detections across those frames into distinct instances: %d, first seen at %s."
                 % (name, len(members), ", ".join(t + " s" for t in firsts)))
        g.append("So there %s %d %s." % ("is" if len(members) == 1 else "are", len(members), name))
    elif kind == "relative_count":
        for name, members, count in zip(names, ids, m["counts"]):
            assert len(members) == count
            for member in sorted(members, key=lambda member: (vis.first_slot([member]) or 99, member)):
                f.obj(name, member)
        for name, count in zip(names, m["counts"]):
            out.append("%s instances visible: %d" % (name, count))
        relation = "more" if m["counts"][0] > m["counts"][1] else "fewer" if m["counts"][0] < m["counts"][1] else "equal"
        assert options[letters.index(answer)].startswith(relation), (relation, answer, options)
        for number, (name, count) in enumerate(zip(names, m["counts"])):
            g.append("Step %d: count the distinct %s instances across the video: %d." % (number + 1, name, count))
        g.append("%d %s against %d %s, so the answer is \"%s\"." % (m["counts"][0], names[0], m["counts"][1], names[1],
                                                                     options[letters.index(answer)]))
    elif kind == "object_size_estimation":
        (name,), (members,) = names, ids
        assert len(members) == 1
        u = unit_of(question)
        value = evidence["longest_edges_m"][0] * (100.0 if u == "cm" else 1.0)
        assert abs(value - float(answer)) <= half_unit(answer), (value, answer)
        f.obj(name, members[0])
        out.append("longest edge of the %s: %s %s" % (name, answer, u))
        g.append("Step 1: find the %s (first seen at %s s)." % (name, seen(vis, members)))
        g.append("Step 2: measure its 3D box; the longest edge is %s %s." % (answer, u))
    elif kind == "relative_size_object":
        assert len(names) == 2
        for name, members in zip(names, ids):
            assert len(members) == 1
            f.obj(name, members[0])
        out.append("longest edges: " + "; ".join("%s %s m" % (name, num(edge))
                                                 for name, edge in zip(names, evidence["longest_edges_m"])))
        g.append("Step 1: find the %s (first seen at %s s) and the %s (first seen at %s s)."
                 % (names[0], seen(vis, ids[0]), names[1], seen(vis, ids[1])))
        g.append("Step 2: measure the longest edge of each 3D box: %s." % "; ".join(
            "%s %s m" % (name, num(edge)) for name, edge in zip(names, evidence["longest_edges_m"])))
        longer = names[0] if evidence["longest_edges_m"][0] > evidence["longest_edges_m"][1] else names[1]
        assert options[letters.index(answer)] == longer, (longer, answer, options)
        g.append("The %s has the longer longest edge." % longer)
    elif kind == "object_abs_distance":
        u = unit_of(question)
        pair = evidence["pairs"][0]
        assert len(evidence["pairs"]) == 1 and sorted(pair["ids"]) == sorted(m["pair"]["ids"])
        value = pair["distance_m"] * (100.0 if u == "cm" else 1.0)
        assert abs(value - float(answer)) <= half_unit(answer), (value, answer)
        by_id = {member: name for name, members in zip(names, ids) for member in members}
        first, second = m["pair"]["ids"]
        f.obj(by_id[first], first)
        f.obj(by_id[second], second)
        out.append("closest-point distance between the %s and the %s: %s %s" % (by_id[first], by_id[second], answer, u))
        g.append("Step 1: find the %s (first seen at %s s) and the %s (first seen at %s s)."
                 % (by_id[first], seen(vis, [first]), by_id[second], seen(vis, [second])))
        g.append("Step 2: measure the distance between their closest points: %s %s." % (answer, u))
    elif kind == "object_rel_distance":
        anchor_name, anchor_ids = names[0], ids[0]
        by_id = {member: name for name, members in zip(names[1:], ids[1:]) for member in members}
        distance, used = {}, {}
        for pair in evidence["pairs"]:
            other = [p for p in pair["ids"] if p in by_id]
            anchors = [p for p in pair["ids"] if p in anchor_ids and p not in other]
            assert len(other) == 1 and len(anchors) == 1 and by_id[other[0]] not in distance
            distance[by_id[other[0]]] = pair["distance_m"]
            used[by_id[other[0]]] = (anchors[0], other[0])
        assert sorted(distance) == sorted(options)
        anchors_used = sorted({used[option][0] for option in options})
        for anchor in anchors_used:
            f.obj(anchor_name, anchor)
        for option in options:
            f.obj(option, used[option][1])
        out.append("closest-point distances from the %s: " % anchor_name
                   + "; ".join("%s %s m" % (option, num(distance[option])) for option in options))
        best = min(options, key=lambda option: distance[option])
        assert letters[options.index(best)] == answer, (best, answer)
        g.append("Step 1: find the %s (first seen at %s s) and each candidate." % (anchor_name, seen(vis, anchors_used)))
        g.append("Step 2: measure the closest-point distance from the %s to each: %s." % (anchor_name, "; ".join(
            "%s %s m" % (option, num(distance[option])) for option in options)))
        g.append("The closest is the %s." % best)
    elif kind.startswith("object_rel_direction"):
        stand, face, target = names
        for name, members in zip(names, ids):
            assert len(members) == 1
            f.obj(name, members[0])
        angle = evidence["signed_left_positive_degrees"]
        out.append("standing at the %s facing the %s, the %s is %s of straight ahead, %s"
                   % (stand, face, target, turn(angle), "in front" if abs(angle) < 90 else "behind"))
        relation = evidence.get("relation") or m.get("relation")
        if relation is not None:
            assert options[letters.index(answer)] == relation, (relation, answer, options)
        g.append("Step 1: locate the centres of the %s, the %s and the %s." % (stand, face, target))
        g.append("Step 2: standing at the %s and facing the %s, the %s lies %s of straight ahead, %s."
                 % (stand, face, target, turn(angle), "in front" if abs(angle) < 90 else "behind"))
        g.append("So the %s is at my %s." % (target, options[letters.index(answer)]))
    elif kind == "absolute_direction_object":
        stand, face, target = names
        for name, members in zip(names, ids):
            assert len(members) == 1
            f.obj(name, members[0])
        angle = evidence["signed_left_positive_degrees"]
        assert abs(((angle % 360.0) - float(answer) + 180.0) % 360.0 - 180.0) <= 1.0, (answer, angle)
        out.append("standing at the %s facing the %s, the %s is %s degrees counterclockwise from straight ahead"
                   % (stand, face, target, answer))
        g.append("Step 1: locate the centres of the %s, the %s and the %s." % (stand, face, target))
        g.append("Step 2: standing at the %s and facing the %s, turn counterclockwise until facing the %s: %s degrees."
                 % (stand, face, target, answer))
    elif kind == "obj_appearance_order":
        raw, display = evidence["first_raw_slots"], evidence["first_display_slots"]
        order = sorted(range(len(names)), key=lambda index: raw[index])
        for index in order:
            assert (raw[index] - 1) // 2 == display[index]
            first = [member for member in ids[index] if vis.first_slot([member]) == raw[index]]
            assert vis.first_slot(ids[index]) == raw[index] and first, "first-seen slot disagrees with the visibility raster"
            f.obj(names[index], first[0], slot=raw[index])
        expected = ", ".join(names[index] for index in order)
        assert options[letters.index(answer)] == expected, (expected, options, answer)
        out.append("first-seen order: " + expected)
        g.append("Step 1: find the first frame showing each object: %s." % "; ".join(
            "%s %s s" % (names[index], vis.times[display[index]]) for index in range(len(names))))
        g.append("Step 2: order them by first appearance: %s." % expected)
    else:
        raise AssertionError(kind)
    text = f.render(out)
    template = "\n".join(g)
    for value in (text, template):
        assert value and value == value.strip() and "\n\n" not in value
    return text, template


# ---------------------------------------------------------------- archives
class Archive(object):
    def __init__(self, out_dir, export):
        self.out_dir, self.export, self.number, self.count, self.stream, self.records = out_dir, export, 0, 0, None, []

    def add(self, name, data):
        if self.stream is None or self.count >= ROWS_PER_ARCHIVE:
            self.close()
            path = os.path.join(self.out_dir, "rows_%s_%03d.tar.gz" % (self.export.lower(), self.number))
            self.path = path
            self.stream = tarfile.open(path + ".part", "w:gz", format=tarfile.USTAR_FORMAT)
            self.number, self.count = self.number + 1, 0
        info = tarfile.TarInfo(name)
        info.size, info.mtime, info.mode, info.uname, info.gname = len(data), 1793059200, 0o444, "", ""
        self.stream.addfile(info, io.BytesIO(data))
        self.count += 1

    def close(self):
        if self.stream is not None:
            self.stream.close()
            os.rename(self.path + ".part", self.path)
            data = open(self.path, "rb").read()
            self.records.append({"file": os.path.basename(self.path), "sha256": sha(data), "size_bytes": len(data),
                                 "rows": self.count})
            self.stream = None


def index_entries(src):
    """The export's item index lines in tranche order (or a test subset named by R1_INDEX_SUBSET)."""
    subset = os.environ.get("R1_INDEX_SUBSET")
    paths = [subset] if subset else ["%s%s/tranche_%04d/INDEX.jsonl" % (src, BANK, t) for t in range(1, 8)]
    for path in paths:
        for line in open(path):
            yield json.loads(line)


def main():
    src, out, commit = sys.argv[1:4]
    assert re.fullmatch(r"[0-9a-f]{40}", commit)
    os.makedirs(out)
    groups, scenes, authority = load_exclusions(src)
    authority_reasons = set(groups) | set(scenes)
    support = json.load(open(src + "/SUPPORT_ROW.json"))
    support_group, support_key = physical_group(support["dataset"], support["scene"])
    assert not any(support_group in groups[r] or support_key in scenes[r] for r in authority_reasons), "support row excluded"
    if support["_source"].get("group_held_out_of_training"):
        groups["heldout_support_group"].add(support_group)  # its rows never train; the support row stands for them
    videos = {}
    for line in open(src + "/VIDEO_INPUTS.jsonl"):
        record = json.loads(line)
        videos[record["video"]] = record
    report = {"schema": "rung1-build-report-v1", "commit": commit, "authorities": authority,
              "exclusion_groups": {k: len(v) for k, v in groups.items()},
              "exclusion_scenes": {k: len(v) for k, v in scenes.items()},
              "excluded": Counter(), "excluded_by_type": Counter(), "kept_by_type": Counter(),
              "a3_think_chars": Counter(), "answers": Counter(),
              "a3_appearance_slot_mismatch": 0, "a3_think_chars_max": 0, "a1_trace_chars": Counter(),
              "trace_check_failures": [],
              "a1_trace_chars_max": 0}
    frames_needed = {}
    rows_x, rows_g, rows_p, invisible, exported_groups = [], [], [], [], set()
    vis_cache = {}
    token_map = {"datasets": DATASET_TOKENS, "scenes": {}, "qids": {}, "frame_root": FRAME_ROOT,
                 "row_roots": ROW_ROOTS, "pools": POOLS}
    seen_qids = set()
    for entry in index_entries(src):
        item_bytes = open(src + entry["path"], "rb").read()
        assert sha(item_bytes) == entry["sha256"], entry["path"]
        item = json.loads(item_bytes.decode())
        facts_pin = item["facts_binding"]
        facts_bytes = open(src + facts_pin["path"], "rb").read()
        assert sha(facts_bytes) == facts_pin["sha256"], facts_pin["path"]
        facts = {}
        for line in facts_bytes.decode().splitlines():
            if line.strip():
                record = json.loads(line)
                facts[record["qid"]] = record
        for q in item["questions"]:
            qid, kind = q["qid"], q["type"]
            assert qid not in seen_qids
            seen_qids.add(qid)
            video = videos[q["video"]]
            dataset, scene = video["dataset"], video["scene"]
            assert q["scene_id"] == dataset + "/" + scene == q["video"], (q["scene_id"], q["video"])
            group, key = physical_group(dataset, scene)
            reasons = sorted(r for r in set(groups) | set(scenes) if group in groups[r] or key in scenes[r])
            legal = (q["answer_provenance"]["type"] == "GT recompute"
                     and q["reference_kind"] == "gt_generated_question"
                     and q["training_answer"] == q["gt_answer"] == q["source_answer"]
                     and q["qgen"]["review_status"] == "PASS" and q[SIDE_KEY] == "train")
            if not legal:
                reasons.append("answer_not_gt_recompute")
            if reasons:
                for reason in reasons:
                    report["excluded"][reason] += 1
                report["excluded_by_type"][kind] += 1
                invisible.append({"qid": qid, "type": kind, "video": q["video"], "reason": ",".join(reasons)})
                continue
            if BANNED.search(normalize_question(q["question"], q["options"]) + " " + " ".join(q["options"])):
                # A word that must not reach code-aws (an object label such as an air-conditioner "split" unit) is the
                # GT category name, so it cannot be neutralized without changing the question: keep the row out.
                report["excluded"]["banned_word_in_model_text"] += 1
                report["excluded_by_type"][kind] += 1
                invisible.append({"qid": qid, "type": kind, "video": q["video"], "reason": "banned_word_in_model_text"})
                continue
            exported_groups.add(group)
            answer, options, letters = q["training_answer"], q["options"], q["option_letters"]
            assert letters == [chr(65 + n) for n in range(len(options))]
            if options:
                assert answer in letters, (qid, answer)
            else:
                float(answer)
                assert re.fullmatch(r"-?[0-9]+(\.[0-9]{1,2})?", answer), (qid, answer)
            question = normalize_question(q["question"], options)
            assert q["student_question"] == q["question"]
            inputs = video["student_input"]
            assert sorted(inputs) == ["fps", "frame_indices", "frames", "timestamps", "total_num_frames"]
            frame_shas = [frame["sha256"] for frame in inputs["frames"]]
            assert len(frame_shas) == 32 and all(sorted(frame) == ["path", "sha256"] for frame in inputs["frames"])
            assert inputs["frame_indices"] == sorted(inputs["frame_indices"])
            assert len(set(inputs["frame_indices"])) == 32 and len(set(inputs["timestamps"])) == 32
            assert isinstance(inputs["total_num_frames"], int) and max(inputs["frame_indices"]) < inputs["total_num_frames"]
            for frame in inputs["frames"]:
                frames_needed.setdefault(frame["sha256"], frame["path"])
            student_input = OrderedDict([
                ("question", question),
                ("options", [letter + ". " + option for letter, option in zip(letters, options)]),
                ("frames", [OrderedDict([("path", frame_path(d)), ("sha256", d)]) for d in frame_shas]),
                ("frame_indices", inputs["frame_indices"]), ("timestamps", inputs["timestamps"]),
                ("fps", inputs["fps"]), ("total_num_frames", inputs["total_num_frames"])])
            token_qid = qid_token(qid)
            token_scene = scene_token(dataset, scene)
            token_map["qids"][token_qid] = qid
            token_map["scenes"][token_scene] = dataset + "/" + scene
            if q["video"] not in vis_cache:
                pin = video["visibility"]
                data = open(src + pin["path"], "rb").read()
                assert sha(data) == pin["sha256"]
                record = json.loads(data.decode())
                snapshot = record["scene_snapshot"]
                scene_bytes = open(src + snapshot["path"], "rb").read()
                assert sha(scene_bytes) == snapshot["sha256"]
                vis_cache.clear()
                vis_cache[q["video"]] = (Visibility(record, frame_shas),
                                         Geometry(json.loads(scene_bytes.decode()), frame_shas))
            vis, geo = vis_cache[q["video"]]
            try:
                think, template = facts_text(kind, question, answer, options, letters, facts[qid], vis, geo, report)
            except AssertionError as error:
                # A GT consistency check failed (facts vs answer, options or instance layout): keep the row out of every
                # export and record why, rather than train on a trace that may contradict the answer.
                report["excluded"]["trace_check_failed"] += 1
                report["excluded_by_type"][kind] += 1
                if len(report["trace_check_failures"]) < 50:
                    report["trace_check_failures"].append({"qid": qid, "type": kind, "error": repr(error)[:300]})
                invisible.append({"qid": qid, "type": kind, "video": q["video"], "reason": "trace_check_failed"})
                continue
            except Invisible:
                # Every training row needs a trace, and a trace may name only visible objects: drop the row from
                # all exports and list it for the cascade lanes.
                report["excluded"]["named_object_not_visible"] += 1
                report["excluded_by_type"][kind] += 1
                invisible.append({"qid": qid, "type": kind, "video": q["video"], "reason": "named_object_not_visible"})
                continue
            allowed = set(m.group(0).lower() for m in BANNED.finditer(question + " " + " ".join(options)))
            for text in (think, template):
                assert set(m.group(0).lower() for m in BANNED.finditer(text)) <= allowed, qid
            report["a3_think_chars"][kind] += len(think)
            report["a3_think_chars_max"] = max(report["a3_think_chars_max"], len(think))
            report["a1_trace_chars"][kind] += len(template)
            report["a1_trace_chars_max"] = max(report["a1_trace_chars_max"], len(template))
            report["kept_by_type"][kind] += 1
            report["answers"][kind + ":" + (answer if options else "numeric")] += 1
            common = OrderedDict([("qid", token_qid), ("dataset", DATASET_TOKENS[dataset]),
                                  ("scene", token_scene), ("category", kind), ("answer", answer)])
            for export, target, rows in (("X", "<think>\n\n</think>\n\n" + answer, rows_x),
                                         ("G", "<think>\n" + template + "\n</think>\n\n" + answer, rows_g),
                                         ("P", "<think>\n" + think + "\n</think>\n\n" + answer, rows_p)):
                row = OrderedDict(common)
                row.update([("pool", POOLS[export]), ("target", target), ("student_input", student_input),
                            ("generation_commit", commit), ("validation_commit", commit)])
                row.update(FLAGS)
                opaque = {k: v for k, v in row.items() if k not in ("target", "student_input")}
                opaque["frames"] = student_input["frames"]
                assert not BANNED.search(canonical(opaque)), qid
                rows.append((token_scene, token_qid, canonical(row).encode()))
    report["kept"] = len(rows_x)
    report["a3_pose_check"] = dict(POSE_CHECK)
    group, key = support_group, support_key
    assert support["answer_provenance"]["type"] == "GT recompute"
    # The held-out support row's physical group must hold no kept row (ScanNet rescans share sceneNNNN).
    assert group not in exported_groups, ("support row shares a physical group with the export", group)
    report["support_row"] = {"qid": support["qid"], "group": group, "source": support["_source"]}
    with open(os.path.join(out, "EXCLUDED_ROWS.jsonl"), "w") as stream:  # Trinity only: every excluded row and why
        for row in invisible:
            stream.write(json.dumps(row, sort_keys=True) + "\n")
    write_exports(out, commit, {"X": rows_x, "G": rows_g, "P": rows_p}, support, token_map, report, frames_needed)


def support_row(support, commit, export):
    inputs = support["student_input"]
    question = normalize_question(support["question"], support["options"])
    letters = support["option_letters"]
    for frame in inputs["frames"]:
        assert sorted(frame) == ["path", "sha256"]
    row = OrderedDict([("qid", "h" + support["qid"][len("gtqgen_"):]), ("dataset", DATASET_TOKENS[support["dataset"]]),
                       ("scene", scene_token(support["dataset"], support["scene"])), ("category", support["question_type"]),
                       ("answer", support["training_answer"]), ("pool", POOLS[export]),
                       ("target", "<think>\n\n</think>\n\n" + support["training_answer"]),
                       ("student_input", OrderedDict([
                           ("question", question),
                           ("options", [l + ". " + o for l, o in zip(letters, support["options"])]),
                           ("frames", [OrderedDict([("path", frame_path(f["sha256"])), ("sha256", f["sha256"])])
                                       for f in inputs["frames"]]),
                           ("frame_indices", inputs["frame_indices"]), ("timestamps", inputs["timestamps"]),
                           ("fps", inputs["fps"]), ("total_num_frames", inputs["total_num_frames"])])),
                       ("generation_commit", commit), ("validation_commit", commit)])
    row.update(FLAGS)
    assert not BANNED.search(canonical(row)), "support row holds a word that must not reach code-aws"
    return row


def write_exports(out, commit, exports, support, token_map, report, frames_needed):
    groups_by_export = {}
    for export, rows in sorted(exports.items()):
        directory = os.path.join(out, "export_" + export)
        os.makedirs(directory)
        archive = Archive(directory, export)
        index = []
        train_groups, train_scenes = set(), set()
        held = support_row(support, commit, export)
        # Archive members are grouped by video so gzip shares each video's frame list across its rows.
        all_rows = list(rows) + [(held["scene"], held["qid"], canonical(held).encode())]
        for scene, qid, data in sorted(all_rows):
            row = json.loads(data.decode())
            digest = sha(data)
            path = "%s/%s/%s.json" % (ROW_ROOTS[export], digest[:2], digest)
            archive.add(path[len("/data2/"):], data)
            index.append(OrderedDict([("qid", row["qid"]), ("pool", row["pool"]), ("scene", row["scene"]),
                                      ("question_type", row["category"]), ("dataset", row["dataset"]),
                                      ("answer", row["answer"]), ("target_path", path), ("sha256", digest),
                                      ("row_path", path), ("row_sha256", digest), ("generation_commit", commit),
                                      ("validation_commit", commit), ("provisional_diagnostic", LABEL)]))
            group = row["dataset"] + "/" + row["scene"]
            if row["qid"] != held["qid"]:
                train_groups.add(group)
                train_scenes.add(group)
        archive.close()
        held_group = held["dataset"] + "/" + held["scene"]
        assert held_group not in train_groups
        with open(os.path.join(directory, "candidate_index.jsonl"), "w") as stream:
            for entry in index:
                stream.write(canonical(entry) + "\n")
        division = OrderedDict([
            ("schema", "diagnostic-whole-scene-division-v1"),
            ("group_policy", "ScanNet sceneNNNN scan suffixes share a group; other datasets use the supplied scene "
                             "identity because no repeat-scan mapping is supplied. Heldout includes the canonical "
                             "closure of selected physical groups."),
            ("assignment", "rung-1 data-scale export: every training group on the train side plus one held-out "
                           "support row that is never trained or evaluated"),
            ("seed", 17), ("selection_uses_correctness", False),
            ("train_group_ids", sorted(train_groups)), ("heldout_group_ids", [held_group]),
            ("train_scenes", sorted(train_scenes)), ("heldout_scenes", [held_group]),
            ("heldout_qids", [held["qid"]])])
        with open(os.path.join(directory, "inherited_division.json"), "w") as stream:
            stream.write(json.dumps(division, indent=2) + "\n")
        with open(os.path.join(directory, "ARCHIVES.json"), "w") as stream:
            json.dump(archive.records, stream, indent=1)
        groups_by_export[export] = len(train_groups)
        report["rows_" + export] = len(index)
    frames_needed.update({f["sha256"]: f["path"] for f in support["student_input"]["frames"]})
    with open(os.path.join(out, "FRAMES_NEEDED.json"), "w") as stream:
        json.dump(OrderedDict(sorted(frames_needed.items())), stream, indent=0)
    token_map["support"] = {"qid": support["qid"], "dataset": support["dataset"], "scene": support["scene"]}
    with open(os.path.join(out, "MAP_TRINITY_ONLY.json"), "w") as stream:
        json.dump(token_map, stream, sort_keys=True)
    report["train_groups"] = groups_by_export
    report["frames_needed"] = len(frames_needed)
    with open(os.path.join(out, "BUILD_REPORT.json"), "w") as stream:
        json.dump(report, stream, indent=1, sort_keys=True)
    print(json.dumps({k: report[k] for k in ("kept", "rows_X", "rows_G", "rows_P", "excluded", "frames_needed",
                                             "train_groups")}, sort_keys=True))


if __name__ == "__main__":
    main()
