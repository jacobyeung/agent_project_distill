"""Offline style and length gates. This module never calls an inference service."""
import importlib.util
import math
import re
from collections import Counter, defaultdict

from .common import ProvenanceError, Refusal, digest, pinned, sha256, source_module

NUMBER = re.compile(r"(?<![\w])[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?")
ROUTE = re.compile(r"<(?:depth_at|move|pose|box_3d)\b[^>]*>")


def rewrite_gate(original, candidate, evidence):
    """A parent-produced rewrite must preserve numeric bytes and route bytes.

    Numeric equality alone cannot establish that new prose has no unsupported
    claim. Require a parent-reviewed claim receipt rather than asserting that it can.
    """
    if ROUTE.findall(original) != ROUTE.findall(candidate):
        raise Refusal("rewrite_routing_bytes_changed")
    if NUMBER.findall(original) != NUMBER.findall(candidate):
        raise Refusal("rewrite_numeric_bytes_changed")
    if original.rsplit('</think>', 1)[-1] != candidate.rsplit('</think>', 1)[-1]:
        raise Refusal("rewrite_answer_changed")
    from .trace import remap_tool_spans
    remap_tool_spans(original, candidate, [])
    if not candidate.startswith('<think>\nPLAN:'):
        raise Refusal("rewrite_plan_missing")
    if (evidence.get("claims_reviewed_by") != "parent" or evidence.get("no_unsupported_claims") is not True
            or evidence.get("plan_content_preserved") is not True):
        raise Refusal("rewrite_claim_review_missing")
    if evidence.get("original_sha256") != digest(original) or evidence.get("rewrite_sha256") != digest(candidate):
        raise ProvenanceError("rewrite text hashes mismatch")
    ll = evidence.get("likelihood", {})
    if (ll.get("text_spans_only") is not True or not ll.get("model_sha256")
            or not ll.get("reference_trace_bank_sha256")
            or not isinstance(ll.get("original_mean_logp"), (int, float))
            or not isinstance(ll.get("rewrite_mean_logp"), (int, float))
            or not math.isfinite(ll["original_mean_logp"]) or not math.isfinite(ll["rewrite_mean_logp"])):
        raise Refusal("rewrite_likelihood_evidence_missing")
    return candidate if ll["rewrite_mean_logp"] > ll["original_mean_logp"] else original


class Lengths:
    def __init__(self, config):
        self.count = None
        self.distributions = defaultdict(lambda: defaultdict(Counter))
        self.counter_pin = config.get("token_counter")
        if self.counter_pin:
            module = source_module("derivgen_parent_token_counter", self.counter_pin)
            self.count = module.count_tokens

    def observe(self, family, target):
        lengths = {"characters": len(target), "utf8_bytes": len(target.encode()), "whitespace_words": len(target.split())}
        if self.count:
            n = self.count(target)
            if type(n) is not int or n < 1: raise ProvenanceError("token counter returned an invalid length")
            lengths["tokens"] = n
        for metric, n in lengths.items(): self.distributions[family][metric][n] += 1
        return lengths

    def report(self):
        def summary(c):
            n = sum(c.values())
            def percentile(p):
                rank, seen = max(1, int((n*p+99)//100)), 0
                for length, count in sorted(c.items()):
                    seen += count
                    if seen >= rank: return length
            return {"n": n, "min": min(c), "p50": percentile(50), "p90": percentile(90), "p99": percentile(99),
                    "max": max(c), "mean": sum(x*n for x, n in c.items())/n,
                    "proportion_above_8192": sum(v for x, v in c.items() if x > 8192)/n,
                    "proportion_above_16384": sum(v for x, v in c.items() if x > 16384)/n}
        return {"types": {t: {m: summary(c) for m, c in metrics.items()} for t, metrics in self.distributions.items()},
                "token_counter": self.counter_pin, "hard_cap": None, "nominal_tokens": 16384,
                "exact_tokens_measured": self.count is not None,
                "limitation": None if self.count else "Parent must supply a pinned local Qwen tokenizer before claiming token-cap compliance."}
