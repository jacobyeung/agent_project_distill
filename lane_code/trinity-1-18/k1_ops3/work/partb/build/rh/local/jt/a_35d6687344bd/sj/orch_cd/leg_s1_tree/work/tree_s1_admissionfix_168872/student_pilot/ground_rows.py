import copy
import re


FORMS = {"3.14": "spec-v3.14-ground-v1", "3.13": "spec-v3.13-ground-v1",
         "3.12.2": "spec-v3.12-ground-v1"}


def is_ground(events):
    return bool(events and events[0].get("kind") == "ground_trace_start")


def render_ground(events, answer):
    if not is_ground(events):
        raise ValueError("Missing grounding event header")
    text, spans, segments, cursor = [], [], [], 0
    for index, event in enumerate(events[1:], 1):
        kind = event["kind"]
        value = event.get("text", event.get("token"))
        if kind not in ("canonical_text", "ground_call", "ground_response") or not isinstance(value, str):
            raise ValueError("Invalid grounding event")
        start = cursor
        cursor += len(value)
        text.append(value)
        if kind == "ground_response":
            if not value.startswith("<tool_response>") or not value.endswith("</tool_response>"):
                raise ValueError("Unwrapped grounding response")
            spans.append(dict(start=start, end=cursor, call_id=event["call_id"], event_index=index))
            segments.append((start, cursor, "tool"))
        elif kind == "ground_call":
            match = re.match(r"<[a-z][a-z_0-9]*", value)
            if match is None:
                raise ValueError("Invalid grounding call")
            segments.extend([(start, start+match.end(), "opener" if value.startswith("<ground") else "calculator"),
                             (start+match.end(), cursor, "arguments")])
        else:
            segments.append((start, cursor, "answer" if "<answer>" in value else "prose"))
    target = "".join(text)
    if not target.startswith("<think>\n") or not target.endswith("\n</think>\n<answer>"+str(answer)+"</answer>"):
        raise ValueError("Grounding final answer mismatch")
    return target, spans, segments


def pack(row, provenance):
    from trace_format.ground_v312 import validate_evidence
    validate_evidence(row)
    events = [dict(kind="ground_trace_start", trace_revision=row["spec_version"])]
    cursor = 0
    for index, event in enumerate(row["events"]):
        block = event["call"] + "\n" + event["response"]
        start = row["suffix"].index(block, cursor)
        if start > cursor:
            events.append(dict(kind="canonical_text", text=row["suffix"][cursor:start]))
        events.append(dict(kind="ground_call", token=event["call"]+"\n", call_id=f"ground-{index}"))
        events.append(dict(kind="ground_response", text=event["response"], call_id=f"ground-{index}"))
        cursor = start + len(block)
    events.append(dict(kind="canonical_text", text=row["suffix"][cursor:]))
    target, spans, _ = render_ground(events, row["answer"])
    return dict(schema="derivgen-row-v2", form=FORMS[row["spec_version"]],
                trace_revision=row["spec_version"], qid=row["qid"], source_qid=row["qid"],
                candidate_id=row["candidate_id"], question_type=row["type"], question=row["question"],
                options=row["options"], answer=row["answer"], gt_answer=row["gt_answer"],
                target=target, events=events, tool_output_spans=spans, provenance=copy.deepcopy(provenance),
                category="route", head_layout="ground_aggregate", infrastructure_only=False,
                training_admitted=False, gt_accepted=True,
                ground_record={key: value for key, value in row.items() if key != "suffix"})


def validate(row):
    from trace_format.ground_v312 import validate_evidence, option_map
    if row.get("schema") != "derivgen-row-v2" or row.get("form") != FORMS.get(row.get("trace_revision")):
        raise ValueError("Invalid packed grounding schema/form/revision")
    if row.get("infrastructure_only") is not False or row.get("gt_accepted") is not True:
        raise ValueError("Unadmitted grounding record")
    record = dict(row["ground_record"], suffix=row["target"])
    for key in ("qid", "answer", "gt_answer", "question", "options", "candidate_id"):
        if row[key] != record[key]:
            raise ValueError("Packed grounding field mismatch: " + key)
    if row["question_type"] != record["type"] or record["spec_version"] != row["trace_revision"]:
        raise ValueError("Packed grounding type mismatch")
    if record.get("not_seen") or record.get("gt_agrees") is not True or record.get("training_admitted") is not False:
        raise ValueError("Grounding membership flags differ")
    validate_evidence(record)
    target, spans, _ = render_ground(row["events"], row["answer"])
    if target != row["target"] or spans != row["tool_output_spans"]:
        raise ValueError("Packed grounding target/spans mismatch")
    if [target[s["start"]:s["end"]] for s in spans] != [e["response"] for e in record["events"]]:
        raise ValueError("Packed response audit mismatch")
    if record["type"] == "object_abs_distance":
        from generator.derivgen_v7.derivgen.ground_v313_distance import agrees
        if not agrees(record["answer"], record["gt_answer"]):
            raise ValueError("Absolute label mismatch")
    elif record["type"] == "absolute_direction_object":
        from generator.derivgen_v7.derivgen.gaps_v314 import circular_error
        if circular_error(record["answer"], record["gt_answer"]) > 15:
            raise ValueError("Rotation label mismatch")
    elif record["type"] == "room_size_estimation":
        from generator.derivgen_v7.derivgen.room_rows_v314 import validate_computation
        validate_computation(record)
    elif str(record["answer"]) != str(record["gt_answer"]):
        raise ValueError("Grounding label mismatch")
    elif record.get("options") and option_map(record["options"])[record["answer"]] != record["answer_content"]:
        raise ValueError("Categorical label mismatch")
    return target, spans
