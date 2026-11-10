"""Read-only upgrade coverage checklist; never grades risk or sends alerts."""

import json
import math
import os
import stat
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

GROUPS = ("surfaces", "topics", "active_cases")
STATES = {"checked", "partial", "gap", "not_applicable"}
CASE_STATES = {"unresolved", "unknown", "resolved", "inactive"}
MAX_INPUT_BYTES = 2 * 1024 * 1024
MAX_JSON_DEPTH = 64


def timestamp(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("timestamp must be a nonempty string")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timezone required")
    return parsed


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def public_url(value):
    """Check syntax only; never resolve or fetch an evidence URL."""
    if not isinstance(value, str) or any(c.isspace() or ord(c) < 32 for c in value):
        return False
    try:
        parsed = urlsplit(value)
        return (parsed.scheme in {"http", "https"} and bool(parsed.hostname)
                and parsed.username is None and parsed.password is None
                and parsed.port != 0)
    except (ValueError, TypeError):
        return False


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key: " + key)
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError("non-finite JSON number: " + value)


def read_text(path):
    # Bound the actual read, not just a prior stat that may race with a writer.
    # Nonblocking open lets us reject FIFOs/devices without hanging on open().
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NONBLOCK", 0))
    with os.fdopen(descriptor, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError("input_must_be_regular_file")
        data = stream.read(MAX_INPUT_BYTES + 1)
    if len(data) > MAX_INPUT_BYTES:
        raise ValueError("input_exceeds_2_mib")
    return data.decode("utf-8-sig")


def load_json(path):
    try:
        result = json.loads(read_text(path), object_pairs_hook=_unique_object,
                            parse_constant=_reject_constant)
    except RecursionError as exc:
        raise ValueError("JSON nesting is too deep") from exc
    pending = [(result, 0)]
    while pending:
        value, depth = pending.pop()
        if depth > MAX_JSON_DEPTH:
            raise ValueError("JSON nesting is too deep")
        if isinstance(value, dict):
            pending.extend((item, depth + 1) for item in value.values())
            pending.extend((key, depth + 1) for key in value)
        elif isinstance(value, list):
            pending.extend((item, depth + 1) for item in value)
        elif isinstance(value, float) and not math.isfinite(value):
            raise ValueError("non-finite JSON number")
        elif isinstance(value, str) and any(0xD800 <= ord(char) <= 0xDFFF for char in value):
            raise ValueError("unpaired Unicode surrogate in JSON string")
    return result


def validate_plan(plan):
    """Validate the portable coverage shape without inferring a watch scope."""
    if not isinstance(plan, dict):
        return ["watch_plan_must_be_object"]
    errors = []
    if not nonempty(plan.get("watch_id")):
        errors.append("nonempty_watch_id_required")
    try:
        timestamp(plan.get("review_after"))
    except (ValueError, TypeError, OverflowError):
        errors.append("timezone_aware_review_after_required")
    for group in GROUPS:
        items = plan.get(group)
        if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
            errors.append(group + ":coverage_objects_required")
            continue
        ids = [item.get("id") for item in items]
        if any(not nonempty(key) for key in ids):
            errors.append(group + ":nonempty_string_ids_required")
        elif len(ids) != len(set(ids)):
            errors.append(group + ":duplicate_ids")
        if group != "active_cases" and not items:
            errors.append(group + ":coverage_scope_required")
    return errors


def template(plan):
    errors = validate_plan(plan)
    if errors:
        raise ValueError("invalid plan: " + "; ".join(errors))
    result = {
        "watch_id": plan["watch_id"], "started_at": "", "ended_at": "",
        "newSignals": [], "plan_review": "",
    }
    for group in GROUPS:
        result[group] = []
        for spec in plan[group]:
            item = {"id": spec["id"], "status": "", "observed_at": "",
                    "summary": "", "links": [], "reason": ""}
            if group == "active_cases":
                item.update(case_state="unknown", lastMaterialUpdate="",
                            next_check="", resolution_evidence="")
            result[group].append(item)
    return result


def _result(errors, gaps, warnings):
    return {"status": "incomplete" if errors else "partial" if gaps else "documented",
            "errors": errors, "coverage_gaps": gaps, "warnings": warnings,
            "scope": "Coverage accounting only; not proof of completeness, risk or resolution."}


def check(plan, record):
    errors, gaps, warnings = validate_plan(plan), [], []
    if not isinstance(record, dict):
        errors.append("record must be a JSON object")
    if errors:
        return _result(errors, gaps, warnings)
    if record.get("watch_id") != plan["watch_id"]:
        errors.append("watch_id does not match the plan")
    start = end = None
    try:
        start, end = timestamp(record.get("started_at")), timestamp(record.get("ended_at"))
        if end < start:
            errors.append("ended_at precedes started_at")
        if (end - start).total_seconds() > 50 * 60:
            warnings.append("Run exceeded the 50-minute closeout budget; report the overrun.")
        if end >= timestamp(plan["review_after"]) and not nonempty(record.get("plan_review")):
            warnings.append("Review dated plan relevance; elapsed time never resolves cases.")
    except (ValueError, TypeError, OverflowError):
        errors.append("valid timezone-aware started_at/ended_at required")
    if "plan_review" in record and not isinstance(record["plan_review"], str):
        errors.append("plan_review must be a string")
    signals = record.get("newSignals")
    if not isinstance(signals, list) or any(not isinstance(item, dict) for item in signals):
        errors.append("newSignals must be a list of objects, separate from active-case follow-up")
    for group in GROUPS:
        items = record.get(group)
        if not isinstance(items, list) or any(not isinstance(i, dict) for i in items):
            errors.append(f"{group}: expected list of coverage objects")
            continue
        ids = [item.get("id") for item in items]
        valid_ids = [key for key in ids if nonempty(key)]
        required = {item["id"] for item in plan[group]}
        errors.extend(f"{group}/{key}: omitted" for key in sorted(required - set(valid_ids)))
        if len(valid_ids) != len(set(valid_ids)):
            errors.append(f"{group}: duplicate IDs")
        for index, item in enumerate(items):
            label = f"{group}/{item['id']}" if nonempty(item.get("id")) else f"{group}/item[{index}]"
            state = item.get("status")
            if not nonempty(item.get("id")) or not isinstance(state, str) or state not in STATES:
                errors.append(f"{label}: valid ID and explicit status required")
                continue
            if not nonempty(item.get("summary")):
                errors.append(f"{label}: observation summary required")
            for field in ("reason", "observed_at"):
                if field in item and not isinstance(item[field], str):
                    errors.append(f"{label}: {field} must be a string")
            links = item.get("links", [])
            if not isinstance(links, list) or any(not public_url(link) for link in links):
                errors.append(f"{label}: links must contain only valid credential-free HTTP(S) URLs")
            if state in {"checked", "partial"}:
                if not isinstance(links, list) or not links or not all(public_url(link) for link in links):
                    errors.append(f"{label}: actual read/query URL required")
            if state in {"checked", "partial"} or nonempty(item.get("observed_at")):
                try:
                    seen = timestamp(item.get("observed_at"))
                    if start and end and not start <= seen <= end:
                        errors.append(f"{label}: observation is outside this run")
                except (ValueError, TypeError, OverflowError):
                    errors.append(f"{label}: observed_at required for an actual read")
            if state != "checked" and not nonempty(item.get("reason")):
                errors.append(f"{label}: concrete reason required for {state}")
            if state in {"partial", "gap"}:
                gaps.append({"surface": label, "reason": item.get("reason")
                             if isinstance(item.get("reason"), str) else ""})
            if group == "active_cases":
                case = item.get("case_state")
                if not isinstance(case, str) or case not in CASE_STATES:
                    errors.append(f"{label}: case_state required")
                    continue
                for field in ("lastMaterialUpdate", "next_check", "resolution_evidence"):
                    if field in item and not isinstance(item[field], str):
                        errors.append(f"{label}: {field} must be a string")
                if case in {"resolved", "inactive"}:
                    if not nonempty(item.get("resolution_evidence")):
                        errors.append(f"{label}: case-specific closure/inactive rationale required")
                    if case == "resolved" and state not in {"checked", "partial"}:
                        errors.append(f"{label}: resolved requires an actual case-evidence read")
                if case in {"unresolved", "unknown"} and not nonempty(item.get("next_check")):
                    errors.append(f"{label}: next follow-up target required")
                if nonempty(item.get("lastMaterialUpdate")):
                    try:
                        material = timestamp(item["lastMaterialUpdate"])
                        if end and material > end:
                            errors.append(f"{label}: lastMaterialUpdate is after this run")
                    except (ValueError, TypeError, OverflowError):
                        errors.append(f"{label}: timezone-aware lastMaterialUpdate required")
    return _result(errors, gaps, warnings)

