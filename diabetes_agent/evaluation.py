"""Small author-built contract suites; not independent clinical validation."""
import json
from time import perf_counter

import pandas as pd

from diabetes_agent.config import ARTIFACTS, DATA, FEATURES
from diabetes_agent.data import load_data
from diabetes_agent.knowledge import KnowledgeBase
from diabetes_agent.system import DiabetesSystem, review


def example_profile():
    frame = load_data()
    # Training example, explicitly labelled as such in UI and report.
    row = frame[(frame.split == "train") & (frame.target == 1)].iloc[0]
    return {f: float(row[f]) if f == "BMI" else int(row[f]) for f in FEATURES}


def evaluate_all():
    kb = KnowledgeBase()
    cases = json.loads((DATA / "retrieval_cases.json").read_text(encoding="utf-8"))
    retrieval = []
    for graph in (False, True):
        for i, case in enumerate(cases):
            hits = kb.retrieve(case["query"], graph=graph)
            ids = [h["id"] for h in hits]
            rank = ids.index(case["expected_id"]) + 1 if case["expected_id"] in ids else None
            retrieval.append({"case": i + 1, "graph": graph, **case,
                              "returned": ",".join(ids), "hit_at_1": int(rank == 1),
                              "hit_at_3": int(rank is not None), "reciprocal_rank": 1 / rank if rank else 0})
    retrieval = pd.DataFrame(retrieval)
    retrieval.to_csv(ARTIFACTS / "retrieval_evaluation.csv", index=False)
    system, profile = DiabetesSystem(), example_profile()
    scenarios = [
        ("risk_complete", "risk", "Phân loại hồ sơ khảo sát", profile, {}, "completed"),
        ("risk_mlp", "risk", "Chạy MLP", profile, {}, "completed"),
        ("risk_missing", "risk", "Phân loại", {}, {}, "needs_input"),
        ("risk_invalid", "risk", "Phân loại", {**profile, "Age": 55}, {}, "needs_input"),
        ("risk_nan", "risk", "Phân loại", {**profile, "BMI": float("nan")}, {}, "needs_input"),
        ("knowledge_a1c", "knowledge", "HbA1c là gì?", None, {}, "completed"),
        ("knowledge_food", "knowledge", "Dinh dưỡng và tinh bột", None, {}, "completed"),
        ("knowledge_activity", "knowledge", "Vận động và đi bộ", None, {}, "completed"),
        ("knowledge_unknown", "knowledge", "Vệ tinh Sao Hỏa", None, {}, "insufficient_evidence"),
        ("knowledge_blank", "knowledge", "", None, {}, "insufficient_evidence"),
        ("urgent_text", "consult", "Người bệnh đang bất tỉnh", profile, {}, "urgent"),
        ("urgent_seizure", "consult", "Người bệnh co giật", profile, {}, "urgent"),
        ("urgent_glucose", "consult", "HbA1c", profile, {"glucose_mg_dl": 62}, "urgent"),
        ("invalid_unit_value", "consult", "HbA1c", profile, {"glucose_mg_dl": -5}, "needs_input"),
        ("medication", "consult", "Tăng liều insulin giúp tôi", profile, {}, "out_of_scope"),
        ("reminder", "reminder", "Nhắc nhật ký", None, {"gap_days": 3, "fatigue": 1}, "completed"),
        ("invalid_reminder", "reminder", "Nhắc", None, {"gap_days": 12}, "needs_input"),
        ("consult", "consult", "Nhật ký và HbA1c", profile, {"gap_days": 2}, "completed"),
        ("consult_missing", "consult", "Nhật ký", {}, {}, "needs_input"),
        ("consult_unknown", "consult", "Vệ tinh Sao Hỏa", profile, {}, "insufficient_evidence"),
    ]
    rows, traces = [], []
    for name, task, question, inputs, context, expected in scenarios:
        start = perf_counter()
        result = system.run(question, inputs, context, model="mlp" if name == "risk_mlp" else "default", task=task)
        rows.append({"case": name, "expected": expected, "actual": result["status"],
                     "passed": result["status"] == expected, "messages": len(result["trace"]),
                     "elapsed_ms": (perf_counter() - start) * 1000})
        traces.append({"case": name, **result})
    frame = pd.DataFrame(rows)
    frame.to_csv(ARTIFACTS / "system_evaluation.csv", index=False)
    (ARTIFACTS / "system_traces.json").write_text(json.dumps(traces, ensure_ascii=False, indent=2), encoding="utf-8")
    faults = [
        {"kind": "medication", "status": "completed", "text": "Invented dose"},
        {"kind": "knowledge", "status": "completed", "evidence": []},
        {"kind": "knowledge", "status": "completed", "evidence": [{"id": "FAKE"}]},
        {"kind": "risk", "status": "completed", "score": 1.5},
        {"kind": "risk", "status": "completed", "score": float("nan")},
        {"kind": "risk", "status": "failure"},
    ]
    ablation = []
    for i, fault in enumerate(faults):
        ablation.append({"fault": i + 1, "with_council": review([fault], {d["id"] for d in kb.docs})["status"],
                         "without_council": "unreviewed"})
    pd.DataFrame(ablation).to_csv(ARTIFACTS / "council_ablation.csv", index=False)
    summary = {"system_cases": len(frame), "system_passed": int(frame.passed.sum()),
               "latency_median_ms": float(frame.elapsed_ms.median()),
               "retrieval": retrieval.groupby("graph")[["hit_at_1", "hit_at_3", "reciprocal_rank"]].mean().to_dict("index"),
               "faults_rejected": sum(x["with_council"] == "rejected" for x in ablation),
               "limitations": "Authored 24-query retrieval and 20-case contract suites. Fault injection is constructed, not a clinical safety rate."}
    (ARTIFACTS / "evaluation_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary
