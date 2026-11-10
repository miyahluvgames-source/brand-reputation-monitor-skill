"""Render declared observations, not a generated risk verdict."""

import html
import json
import re

from .coverage import GROUPS, check


def escape(value):
    """Encode user-controlled text for literal Markdown table/bullet content."""
    text = html.escape(str(value), quote=True)
    text = text.replace("\r", " ").replace("\n", " ").replace("\t", " ")
    text = "".join(char for char in text if ord(char) >= 32 and ord(char) != 127)
    # Escape Markdown, including image/link/autolink syntax. No source content
    # becomes HTML, a heading, an image, or an executable link in this report.
    return re.sub(r"([\\`*_{}\[\]()#+.!|~>\-])", r"\\\1", text)


def render_report(plan, record, validation=None):
    """Validate again at the boundary; a caller cannot pass a forged verdict."""
    validation = check(plan, record)
    if validation["errors"]:
        raise ValueError("cannot render an invalid coverage record")
    lines = ["# Reputation observation report", "",
             f"**Watch:** {escape(record['watch_id'])}",
             f"**Observation interval:** {escape(record['started_at'])} — {escape(record['ended_at'])}",
             f"**Coverage accounting:** {validation['status']}", "",
             "> This report reproduces declared observations. Validation does not verify sources,",
             "> calculate risk, prove exhaustive coverage, or establish case resolution.", "",
             "## New signals", ""]
    if not record["newSignals"]:
        lines.append("No new, updated, or resurfaced signals were recorded. This does not establish absence of risk.")
    else:
        lines.append("Operator-supplied signal objects (not automatically graded):")
        lines.append("")
        for signal in record["newSignals"]:
            lines.append("- " + escape(json.dumps(signal, ensure_ascii=False, sort_keys=True)))
    names = {"surfaces": "Platform and source coverage", "topics": "Topic coverage", "active_cases": "Open case status"}
    for group in GROUPS:
        lines += ["", "## " + names[group], ""]
        if not record[group]:
            lines.append("No items in this scope.")
            continue
        lines += ["| ID | Coverage | Observed at | Observation | Reason / next action |",
                  "| --- | --- | --- | --- | --- |"]
        for item in record[group]:
            detail = item["summary"]
            if group == "active_cases":
                detail += " | case state: " + item["case_state"]
            action = item.get("reason", "")
            if group == "active_cases":
                action += " | next: " + item.get("next_check", "")
            lines.append("| " + " | ".join(escape(value) for value in (
                item["id"], item["status"], item.get("observed_at", ""), detail, action)) + " |")
        lines += ["", "Evidence references (literal URLs; not fetched by this tool):", ""]
        for item in record[group]:
            for link in item.get("links", []):
                lines.append(f"- {escape(item['id'])}: {escape(link)}")
            if group == "active_cases":
                if item.get("lastMaterialUpdate"):
                    lines.append(f"- {escape(item['id'])} — last material update: {escape(item['lastMaterialUpdate'])}")
                if item.get("resolution_evidence"):
                    lines.append(f"- {escape(item['id'])} — closure rationale: {escape(item['resolution_evidence'])}")
    lines += ["", "## Coverage gaps", ""]
    if validation["coverage_gaps"]:
        for gap in validation["coverage_gaps"]:
            lines.append(f"- {escape(gap['surface'])}: {escape(gap['reason'])}")
    else:
        lines.append("No explicit gaps were recorded. Sampling limits still apply.")
    if validation["warnings"]:
        lines += ["", "## Review notes", ""]
        lines.extend("- " + escape(warning) for warning in validation["warnings"])
    if record.get("plan_review"):
        lines += ["", "**Plan review:** " + escape(record["plan_review"])]
    return "\n".join(lines) + "\n"
