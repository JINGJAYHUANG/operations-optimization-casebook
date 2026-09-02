from __future__ import annotations

import html
from typing import Any


def _fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:,.6f}".rstrip("0").rstrip(".")
    if isinstance(value, dict):
        return ", ".join(f"{key}={_fmt(item)}" for key, item in sorted(value.items()))
    if isinstance(value, list):
        return ", ".join(_fmt(item) for item in value)
    return str(value)


def render_case_markdown(case: dict[str, Any], solution: dict[str, Any], audit: dict[str, Any], sensitivity: dict[str, Any], decision: dict[str, Any]) -> str:
    lines = [
        f"# {case['title']}",
        "",
        f"**Case ID:** `{case['case_id']}`  ",
        f"**Model type:** `{case['case_type']}`  ",
        f"**Decision status:** **{decision['status'].upper()}**  ",
        f"**Solver:** `{solution['solver']}`  ",
        f"**Objective:** `{_fmt(solution['objective'])}`",
        "",
        "> This result is produced from a small deterministic synthetic instance. It demonstrates decision logic and audit controls; it is not a production operating instruction.",
        "",
        "## Decision context",
        "",
        case["decision_context"],
        "",
        "## Recommended decision",
        "",
        "```json",
        __import__("json").dumps(solution["decision"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Audit gates",
        "",
        "| Gate | Result |",
        "|---|---:|",
    ]
    for gate, passed in audit["gates"].items():
        lines.append(f"| `{gate}` | {'PASS' if passed else 'FAIL'} |")
    lines.extend(["", "## Baseline comparison", ""])
    if audit["baseline"] is None:
        lines.append("No baseline decision was supplied.")
    else:
        lines.append(f"- Baseline objective: `{_fmt(audit['baseline']['objective'])}`")
        lines.append(f"- Improvement in the preferred direction: `{_fmt(audit['baseline']['improvement'])}`")
    lines.extend([
        "",
        "## Stress and sensitivity",
        "",
        f"- Stress tests: `{sensitivity['stress_test_count']}`",
        f"- All stress tests feasible: `{sensitivity['all_stress_tests_feasible']}`",
        f"- Decision stability ratio: `{sensitivity['decision_stability_ratio']:.1%}`",
        f"- Worst objective degradation: `{_fmt(sensitivity['worst_objective_degradation'])}`",
        "",
        "| Stress | Status | Objective | Decision changed |",
        "|---|---|---:|---:|",
    ])
    for item in sensitivity["results"]:
        lines.append(f"| {item['name']} | {item['status']} | {_fmt(item.get('objective', '—'))} | {item.get('decision_changed', True)} |")
    lines.extend(["", "## Implementation gate", ""])
    lines.append(f"- Owner: `{decision.get('implementation_owner')}`")
    lines.append(f"- Human approval required: `{decision['approval_required']}`")
    if decision["hard_failures"]:
        lines.append("- Hard failures: " + ", ".join(f"`{item}`" for item in decision["hard_failures"]))
    if decision["conditions"]:
        lines.append("- Conditions: " + ", ".join(f"`{item}`" for item in decision["conditions"]))
    lines.append(f"- Rollback trigger: {decision['rollback_trigger']}")
    if decision["monitoring_kpis"]:
        lines.append("- Monitoring KPIs: " + ", ".join(decision["monitoring_kpis"]))
    if decision.get("known_limitations"):
        lines.append("- Known model limitations: " + ", ".join(decision["known_limitations"]))
    lines.extend([
        "",
        "## Interpretation boundary",
        "",
        "An exact reference solution proves optimality only for the stated small synthetic instance and model contract. It does not prove that the model includes every real constraint, that input data are current, or that the recommendation should be executed without operational ownership and approval.",
        "",
    ])
    return "\n".join(lines)


def render_case_html(case: dict[str, Any], solution: dict[str, Any], audit: dict[str, Any], sensitivity: dict[str, Any], decision: dict[str, Any]) -> str:
    gates = "".join(f"<tr><td>{html.escape(gate)}</td><td>{'PASS' if passed else 'FAIL'}</td></tr>" for gate, passed in audit["gates"].items())
    stresses = "".join(
        "<tr>"
        f"<td>{html.escape(item['name'])}</td>"
        f"<td>{html.escape(item['status'])}</td>"
        f"<td>{html.escape(_fmt(item.get('objective', '—')))}</td>"
        f"<td>{html.escape(str(item.get('decision_changed', True)))}</td>"
        "</tr>"
        for item in sensitivity["results"]
    )
    decision_json = html.escape(__import__("json").dumps(solution["decision"], ensure_ascii=False, indent=2, sort_keys=True))
    conditions = "".join(f"<li>{html.escape(item)}</li>" for item in decision["conditions"]) or "<li>None</li>"
    failures = "".join(f"<li>{html.escape(item)}</li>" for item in decision["hard_failures"]) or "<li>None</li>"
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(case['title'])}</title>
<style>
:root{{font-family:Inter,ui-sans-serif,system-ui,sans-serif;color:#172033;background:#f3f6fa}}body{{margin:0}}main{{max-width:1100px;margin:auto;padding:32px 18px 60px}}.card{{background:white;border:1px solid #dce3ed;border-radius:14px;padding:22px;margin-bottom:18px;box-shadow:0 8px 24px rgba(20,35,60,.05)}}h1{{margin:0 0 8px}}.status{{font-size:26px;font-weight:800}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px;margin-top:16px}}.metric{{background:#f6f8fb;border-radius:10px;padding:12px}}.metric b{{display:block;font-size:20px}}table{{width:100%;border-collapse:collapse}}th,td{{padding:9px;border-bottom:1px solid #e5eaf1;text-align:left}}pre{{overflow:auto;background:#101826;color:#e8eef7;padding:16px;border-radius:10px}}.note{{color:#59667a}}@media(max-width:700px){{table{{display:block;overflow-x:auto}}}}
</style></head><body><main>
<section class="card"><h1>{html.escape(case['title'])}</h1><div class="status">{html.escape(decision['status'].upper())}</div><p>{html.escape(case['decision_context'])}</p><div class="grid"><div class="metric">Model<b>{html.escape(case['case_type'])}</b></div><div class="metric">Objective<b>{html.escape(_fmt(solution['objective']))}</b></div><div class="metric">Solver<b>{html.escape(solution['solver'])}</b></div><div class="metric">Stability<b>{sensitivity['decision_stability_ratio']:.1%}</b></div></div></section>
<section class="card"><h2>Decision</h2><pre>{decision_json}</pre></section>
<section class="card"><h2>Audit gates</h2><table><thead><tr><th>Gate</th><th>Result</th></tr></thead><tbody>{gates}</tbody></table></section>
<section class="card"><h2>Stress tests</h2><table><thead><tr><th>Stress</th><th>Status</th><th>Objective</th><th>Decision changed</th></tr></thead><tbody>{stresses}</tbody></table></section>
<section class="card"><h2>Implementation</h2><p><b>Owner:</b> {html.escape(str(decision.get('implementation_owner')))}</p><h3>Hard failures</h3><ul>{failures}</ul><h3>Conditions</h3><ul>{conditions}</ul><p><b>Rollback trigger:</b> {html.escape(decision['rollback_trigger'])}</p></section>
<section class="card note"><h2>Boundary</h2><p>An exact result applies only to this versioned synthetic model. It does not establish that a real operating system includes every constraint or that execution is authorized.</p></section>
</main></body></html>"""


def render_suite_markdown(summary: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Operations Optimization Casebook — Reference Suite",
        "",
        f"**Overall result:** {'PASS' if summary['passed'] else 'FAIL'}  ",
        f"**Cases:** `{summary['case_count']}`  ",
        f"**Recommended / Conditional / Hold:** `{summary['recommended_count']} / {summary['conditional_count']} / {summary['hold_count']}`",
        "",
        "> All examples are deterministic and synthetic. The suite validates algorithms, audit gates, reports, and evidence integrity; it does not authorize real operational changes.",
        "",
        "| Case | Type | Objective | Status | Improvement | Stability |",
        "|---|---|---:|---|---:|---:|",
    ]
    for row in rows:
        lines.append(f"| `{row['case_id']}` | `{row['case_type']}` | {_fmt(row['objective'])} | {row['decision_status']} | {_fmt(row.get('improvement', '—'))} | {row['decision_stability_ratio']:.1%} |")
    lines.extend([
        "",
        "## Portfolio interpretation",
        "",
        "A mathematically optimal solution can still be conditional or held when evidence, stress performance, service thresholds, ownership, or approval requirements are incomplete. The casebook intentionally keeps optimization quality separate from implementation authorization.",
        "",
    ])
    return "\n".join(lines)


def render_suite_html(summary: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    body = "".join(
        "<tr>"
        f"<td>{html.escape(row['case_id'])}</td><td>{html.escape(row['case_type'])}</td>"
        f"<td>{html.escape(_fmt(row['objective']))}</td><td>{html.escape(row['decision_status'])}</td>"
        f"<td>{html.escape(_fmt(row.get('improvement', '—')))}</td><td>{row['decision_stability_ratio']:.1%}</td>"
        "</tr>"
        for row in rows
    )
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Operations Optimization Casebook</title><style>:root{{font-family:Inter,system-ui,sans-serif;background:#f3f6fa;color:#182235}}body{{margin:0}}main{{max-width:1120px;margin:auto;padding:32px 18px}}section{{background:white;border:1px solid #dce3ed;border-radius:14px;padding:22px;margin-bottom:18px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px}}.metric{{background:#f6f8fb;padding:14px;border-radius:10px}}.metric b{{display:block;font-size:24px}}table{{width:100%;border-collapse:collapse}}th,td{{padding:10px;border-bottom:1px solid #e5eaf1;text-align:left}}@media(max-width:700px){{table{{display:block;overflow-x:auto}}}}</style></head><body><main><section><h1>Operations Optimization Casebook</h1><p>Auditable exact reference models, stress tests, and implementation gates.</p><div class="grid"><div class="metric">Cases<b>{summary['case_count']}</b></div><div class="metric">Recommended<b>{summary['recommended_count']}</b></div><div class="metric">Conditional<b>{summary['conditional_count']}</b></div><div class="metric">Hold<b>{summary['hold_count']}</b></div></div></section><section><table><thead><tr><th>Case</th><th>Type</th><th>Objective</th><th>Status</th><th>Improvement</th><th>Stability</th></tr></thead><tbody>{body}</tbody></table></section><section><h2>Boundary</h2><p>All inputs are synthetic. A solved model is not an execution approval and does not prove that every real-world constraint has been represented.</p></section></main></body></html>"""
