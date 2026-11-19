from collections import Counter, deque
from copy import deepcopy
import hashlib
import json
import re

DECODE_BUDGET = dict(thinking_tokens=2048, answer_tokens=64,
                     max_new_tokens=16384, max_calls=200, call_window_tokens=96,
                     counting="sampled_callbacks")
CLOSE = "\n</think>\n\n"
UNIVERSE = "capture_normalized_mask_cache_phrases"
CALL_NAMES = ("depth_at", "move", "pose", "turn", "box_3d", "ground", "gap", "surface_pair",
              "extent_ends", "dist", "closest", "cam_dist", "angle", "area")
OPEN_CALL = re.compile(r"<([a-z_0-9]*)([ \t\r\n][^<>]*)?$")
REPORT_SEMANTICS = dict(
    universe_rule="Both arms use the normalized phrases in the current capture's frozen mask cache.",
    plural_calls="A plural model call can be refused when only its singular form is cached; runtime name normalization does not apply the cache's singularization aliases.",
    comparison_scope="Distance scores are comparable only across reads with the same candidate-universe rule, because the universe changes candidate competition in both arms.",
    training_responses="The model was trained on responses from ground-truth instances; this read serves the same calls from frozen mask proposals selected among the capture's cached phrases.")


class ThinkingBudget:
    def __init__(self, tokenizer, policy=None, *, openers=()):
        policy = DECODE_BUDGET if policy is None else policy
        if policy != DECODE_BUDGET:
            raise ValueError("The bound reader decode budget differs")
        self.policy = dict(policy)
        self.tokenizer, self.openers = tokenizer, set(openers)
        closing = tokenizer.encode("</think>", add_special_tokens=False)
        self.close_ids = tokenizer.encode(CLOSE, add_special_tokens=False)
        self.eos = tokenizer.eos_token_id
        if (len(closing) != 1 or not self.close_ids or closing[0] not in self.close_ids
                or type(self.eos) is not int or self.eos < 0):
            raise ValueError("The tokenizer cannot implement the bound forced-answer policy")
        self.close_id = closing[0]
        self.close_pieces = [tokenizer.convert_ids_to_tokens(token) for token in self.close_ids]
        self.trigger = None
        self.trigger_sampled = None
        self.natural_close = False
        self.forced_eos = False
        self.eos_position = None
        self.callbacks = 0
        self.close_emitted = 0
        self.answer_samples = 0
        self.forced_tokens = 0
        self.previous_position = None
        self.active_call = None
        self.open_call_at_trigger = None
        self.deferred_samples = 0
        self.force_position = None
        self.sample_positions = deque(maxlen=self.policy["call_window_tokens"])

    def text_call_start(self, ids):
        positions = list(self.sample_positions)
        tail = [ids[position] for position in positions]
        def pending(tokens):
            match = OPEN_CALL.search(self.tokenizer.decode(tokens, skip_special_tokens=False))
            return match is not None and (
                match[1] in CALL_NAMES if match[2] is not None
                else any(name.startswith(match[1]) for name in CALL_NAMES))
        if not pending(tail):
            return None
        for offset in range(1, len(tail)+1):
            if not pending(tail[offset:]):
                return positions[offset-1]
        raise ValueError("An open call has no bounded token start")

    def __call__(self, ids, logits):
        if self.previous_position is None:
            if ids:
                raise ValueError("A budget must observe the decode from its first sampled token")
        elif len(ids) <= self.previous_position:
            raise ValueError("The decoder reused a budget across different items")
        if self.previous_position is not None:
            self.sample_positions.append(self.previous_position)
            if ids[self.previous_position] in self.openers:
                self.active_call = self.previous_position
            if self.active_call is not None:
                tail = ids[self.active_call:self.previous_position+1]
                if (len(tail) > self.policy["call_window_tokens"]
                        or self.tokenizer.decode(tail, skip_special_tokens=False).endswith(">")):
                    self.active_call = None
        if (self.active_call is None and not self.natural_close and not self.close_emitted
                and self.callbacks >= self.policy["thinking_tokens"]):
            self.active_call = self.text_call_start(ids)
        if self.trigger is None:
            self.natural_close = self.natural_close or (
                self.previous_position is not None and ids[self.previous_position] == self.close_id)
            if self.natural_close or self.callbacks < self.policy["thinking_tokens"]:
                self.previous_position = len(ids)
                self.callbacks += 1
                return logits
            self.trigger = len(ids)
            self.trigger_sampled = self.callbacks
            self.open_call_at_trigger = self.active_call
        self.previous_position = len(ids)
        self.callbacks += 1
        if (not self.close_emitted and self.active_call is not None
                and self.deferred_samples < self.policy["call_window_tokens"]):
            self.deferred_samples += 1
            return logits
        if self.close_emitted < len(self.close_ids):
            if not self.close_emitted:
                self.force_position = len(ids)
            token = self.close_ids[self.close_emitted]
            self.close_emitted += 1
        elif self.answer_samples < self.policy["answer_tokens"]:
            self.answer_samples += 1
            return logits
        else:
            token = self.eos
            self.forced_eos = True
            self.eos_position = len(ids)
        self.forced_tokens += 1
        forced = logits.clone().fill_(-float("inf"))
        forced[:, token] = 0
        return forced

    def receipt(self, total_tokens=None):
        total_tokens = (self.previous_position + 1 if self.previous_position is not None else 0
                        ) if total_tokens is None else total_tokens
        if type(total_tokens) is not int or total_tokens < self.callbacks:
            raise ValueError("The returned decode cannot contain fewer ids than sampling callbacks")
        return dict(self.policy, close_text=CLOSE, close_token_ids=self.close_ids,
                    close_token_pieces=self.close_pieces,
                    eos_token_id=self.eos, fired=self.trigger is not None,
                    natural_close=self.natural_close, trigger_position=self.trigger,
                    trigger_sampled_tokens=self.trigger_sampled,
                    trigger_injected_tokens=0 if self.trigger is None else
                    self.trigger - self.trigger_sampled,
                    forced_eos=self.forced_eos, eos_position=self.eos_position,
                    sampled_tokens=self.callbacks, injected_tokens=total_tokens-self.callbacks,
                    total_tokens=total_tokens, forced_budget_tokens=self.forced_tokens,
                    ordinary_sampled_tokens=self.callbacks-self.forced_tokens,
                    forced_answer_sampled_tokens=self.answer_samples,
                    open_call_at_trigger=self.open_call_at_trigger,
                    deferred_sampled_tokens=self.deferred_samples, forced_close_position=self.force_position,
                    maximum_sampled_slots=(self.policy["thinking_tokens"]+self.policy["call_window_tokens"]
                                           +len(self.close_ids)+self.policy["answer_tokens"]+1),
                    normal_closed_policy="reuse_full_direct_answer",
                    callback_scope="One sampled slot per callback, including budget-forced closing/EOS ids")


def apply_budget(decoded, budget):
    result = dict(decoded, decode_budget=budget.receipt(decoded["generated_tokens"]))
    if budget.trigger is not None:
        result["calls"] = [dict(call, kind="budget_truncated", original_kind=call["kind"],
                               budget_truncated=True, original_verify_error=call.get("verify_error", False),
                               verify_error=False) if call["at_token"] >= budget.trigger else call
                           for call in decoded["calls"]]
        result["unadjusted_call_errors"] = decoded["errors"]
        result["errors"] = sum((call["kind"] == "error" or call.get("verify_error", False))
                               and not call.get("budget_truncated", False) for call in result["calls"])
    return result


def is_capped(decoded):
    return (decoded.get("finish") in ("max_new_tokens", "context_exhaustion", "call_limit")
            or decoded.get("decode_budget", {}).get("fired") is True)


def call_audit(decoded):
    longest = current = 0
    previous = None
    calls = decoded.get("calls", [])
    for call in calls:
        text = call.get("call")
        current = current + 1 if text == previous else 1
        longest = max(longest, current)
        previous = text
    return dict(call_count=len(calls), longest_identical_call_run=longest,
                budget_truncated_calls=sum(call.get("budget_truncated", False) for call in calls))


def journal_decode(decoded, keep_full):
    result = deepcopy(decoded)
    heads = result.get("heads", {})
    if "ground_queries" not in heads:
        return result
    queries = heads["ground_queries"]
    if isinstance(queries, dict) and queries == heads.get("ground_queries_digest"):
        return result
    if not isinstance(queries, list):
        raise ValueError("The ground-query journal is not a list")
    data = json.dumps(queries, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    summary = dict(sha256=hashlib.sha256(data).hexdigest(), bytes=len(data),
                   query_count=len(queries), encoding="canonical-json-utf8")
    heads["ground_queries_digest"] = summary
    if not keep_full:
        heads["ground_queries"] = summary
    return result


def journal_policy(items):
    counts = Counter()
    keys, retained = set(), []
    for item in items:
        if item["key"] in keys:
            raise ValueError("Duplicate item in query-journal policy")
        keys.add(item["key"])
        if counts[item["family"]] < 3:
            retained.append(item["key"])
        counts[item["family"]] += 1
    return dict(schema="evalx-ground-query-digest-v1", retain_per_type=3,
                keep_full_keys=retained, digest_encoding="canonical-json-utf8")


def question_unit(question):
    matches = re.findall(
        r"\b(square\s+)?(millimeters?|millimetres?|centimeters?|centimetres?|"
        r"meters?|metres?|inches|inch|feet|foot)\b", question, re.I)
    if not matches:
        return dict(unit="unknown", metric=None, meter_based=None)
    square, value = matches[-1]
    value = value.lower().replace("metre", "meter")
    unit = ("millimeters" if value.startswith("millimeter") else
            "centimeters" if value.startswith("centimeter") else
            "meters" if value.startswith("meter") else
            "inches" if value in ("inch", "inches") else "feet")
    return dict(unit=("square " if square else "") + unit,
                metric=unit in ("millimeters", "centimeters", "meters"),
                meter_based=unit == "meters")


def unit_report(rows):
    from r1 import family
    result = {}
    for typ in ("object_abs_distance", "room_size_estimation"):
        pairs = {}
        for row in rows:
            if family(row["question_type"]) == typ:
                pair = pairs.setdefault(row["key"], {})
                if row["arm"] in pair:
                    raise ValueError("Duplicate arm in unit report")
                pair[row["arm"]] = row
        for pair in pairs.values():
            if (set(pair) != {"unflagged", "scripted"}
                    or pair["unflagged"]["question_unit"] != pair["scripted"]["question_unit"]
                    or bool(pair["unflagged"].get("geometry_refusal")) != bool(pair["scripted"].get("geometry_refusal"))):
                raise ValueError("Unit report requires equally classified item pairs")
        predicates = dict(all=lambda u: True, metric=lambda u: u["metric"] is True,
                          nonmetric=lambda u: u["metric"] is False,
                          meter_based=lambda u: u["meter_based"] is True,
                          other_units=lambda u: u["meter_based"] is False,
                          unknown=lambda u: u["metric"] is None)
        groups = {}
        for name, include in predicates.items():
            selected = [pair for pair in pairs.values() if include(pair["unflagged"]["question_unit"])]
            model_rows = [pair for pair in selected if not pair["unflagged"].get("geometry_refusal")]
            scores, all_scores = {}, {}
            for arm in ("unflagged", "scripted"):
                values = [pair[arm]["scores"]["released_answer" if pair[arm]["stratum"] == "primary"
                                              else "answer"] for pair in selected]
                if any(value is None for value in values):
                    raise ValueError("Unit report is missing an authoritative score")
                all_scores[arm] = 100 * sum(values) / len(values) if values else None
                values = [pair[arm]["scores"]["released_answer" if pair[arm]["stratum"] == "primary"
                                              else "answer"] for pair in model_rows]
                scores[arm] = 100 * sum(values) / len(values) if values else None
            groups[name] = dict(items=len(model_rows), all_items=len(selected),
                geometry_refused_items=len(selected)-len(model_rows), scores_pct=scores,
                all_item_scores_pct=all_scores)
        groups["exact_units"] = dict(Counter(pair["unflagged"]["question_unit"]["unit"]
                                             for pair in pairs.values() if not pair["unflagged"].get("geometry_refusal")))
        groups["geometry_refused_exact_units"] = dict(Counter(pair["unflagged"]["question_unit"]["unit"]
                                             for pair in pairs.values() if pair["unflagged"].get("geometry_refusal")))
        result[typ] = groups
    return result
