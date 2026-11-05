"""Bounded in-process message protocol, independent review and SQLite audit."""
import json
import math
import sqlite3
import uuid
from datetime import datetime, timezone
from time import perf_counter

import numpy as np

from diabetes_agent.config import ARTIFACTS, BOUNDS, DISCLAIMER, FEATURES
from diabetes_agent.knowledge import KnowledgeBase, normalize
from diabetes_agent.models import RiskModel
from diabetes_agent.rl import ACTIONS


def validate_profile(profile):
    missing = [f for f in FEATURES if f not in profile]
    if missing:
        return {"status": "needs_input", "missing": missing}
    for name in FEATURES:
        value = profile[name]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            return {"status": "needs_input", "error": f"{name}: cần giá trị số hữu hạn."}
        low, high = BOUNDS[name]
        if value < low or value > high or (name != "BMI" and value != int(value)):
            return {"status": "needs_input", "error": f"{name}: cần mã hợp lệ trong [{low}, {high}]."}
    return {"status": "completed"}


def safety_check(question, context):
    q = normalize(question)
    if any(w in q for w in ("bat tinh", "co giat", "kho tho nang", "khong tinh tao")):
        return {"status": "urgent", "text": "Dấu hiệu bạn mô tả có thể nguy hiểm. Cần trợ giúp y tế khẩn cấp ngay; không chờ kết quả mô hình."}
    glucose = context.get("glucose_mg_dl")
    if glucose is not None:
        if isinstance(glucose, bool) or not isinstance(glucose, (int, float)) or not math.isfinite(glucose) or not 10 <= glucose <= 1000:
            return {"status": "needs_input", "text": "Glucose cần là số hữu hạn trong 10–1000 mg/dL. Kiểm tra đơn vị nhập."}
        if glucose < 70:
            return {"status": "urgent", "text": "Số đo dưới 70 mg/dL cần được xử trí kịp thời theo hướng dẫn của nhóm chăm sóc. Liên hệ hỗ trợ y tế; nếu không tỉnh táo hoặc không thể tự xử trí, cần trợ giúp khẩn cấp.", "source_ids": ["D05"]}
    if any(w in q for w in ("ke don", "lieu insulin", "tang lieu", "giam lieu", "ngung thuoc", "doi thuoc", "uong thuoc gi")):
        return {"status": "out_of_scope", "text": "Hệ thống không kê đơn hoặc điều chỉnh thuốc. Hãy trao đổi với nhân viên y tế."}
    return {"status": "completed"}


def review(proposals, valid_source_ids):
    """Council checks contracts, not clinical truth. It may veto a specialist."""
    reasons = []
    for item in proposals:
        if item.get("kind") == "medication":
            reasons.append("Không cho phép đề xuất thuốc hoặc liều điều trị.")
        if item.get("status") == "failure":
            reasons.append("Một tác tử không thực hiện được nhiệm vụ.")
        if item.get("kind") == "knowledge":
            evidence = item.get("evidence", [])
            if item.get("status") == "completed" and not evidence:
                reasons.append("Kết luận tri thức không có bằng chứng.")
            if any(d.get("id") not in valid_source_ids for d in evidence):
                reasons.append("Bằng chứng chứa mã nguồn không hợp lệ.")
        if item.get("kind") == "risk" and "score" in item:
            if not math.isfinite(item["score"]) or not 0 <= item["score"] <= 1:
                reasons.append("Điểm mô hình không hợp lệ.")
    return {"status": "approved" if not reasons else "rejected", "reasons": reasons}


class MessageBus:
    def __init__(self, handlers):
        self.handlers, self.trace = handlers, []

    def send(self, sender, receiver, task, payload):
        self.trace.append({"sender": sender, "receiver": receiver, "performative": "REQUEST", "task": task})
        start = perf_counter()
        try:
            result = self.handlers[receiver](payload)
        except Exception as exc:
            result = {"status": "failure", "error": f"{type(exc).__name__}: {exc}"}
        self.trace.append({"sender": receiver, "receiver": sender,
                           "performative": "FAILURE" if result.get("status") == "failure" else "INFORM",
                           "task": task, "status": result.get("status", "completed"),
                           "elapsed_ms": round((perf_counter() - start) * 1000, 3)})
        return result


class DiabetesSystem:
    def __init__(self, audit_path=None):
        self.risk, self.kb = RiskModel(), KnowledgeBase()
        self.q = np.load(ARTIFACTS / "q_table.npy")
        self.audit_path = audit_path

    def reminder(self, payload):
        gap, fatigue = payload.get("gap_days", 0), payload.get("fatigue", 0)
        if type(gap) is not int or not 0 <= gap <= 3 or type(fatigue) is not int or fatigue not in (0, 1):
            return {"status": "needs_input", "kind": "reminder", "error": "gap_days cần 0–3, fatigue cần 0 hoặc 1."}
        state = gap * 2 + fatigue
        action = int(self.q[state].argmax())
        return {"status": "completed", "kind": "reminder", "state": state,
                "action": action, "text": ACTIONS[action], "q_values": self.q[state].tolist(),
                "meaning": "Chính sách nhắc nhật ký trong mô phỏng, không phải can thiệp điều trị."}

    def risk_task(self, payload):
        check = validate_profile(payload["profile"])
        if check["status"] != "completed":
            return {"kind": "risk", **check}
        return {"kind": "risk", "status": "completed",
                **self.risk.predict(payload["profile"], payload.get("model", "default"))}

    def run(self, question, profile=None, context=None, model="default", task="consult"):
        if task not in ("consult", "knowledge", "risk", "reminder"):
            raise ValueError("Unknown task")
        context = context or {}
        handlers = {
            "Intake": lambda p: safety_check(p["question"], p["context"]),
            "Risk": self.risk_task,
            "Knowledge": lambda p: {"kind": "knowledge", **self.kb.answer(p["question"])},
            "Reminder": self.reminder,
            "Council": lambda p: review(p["proposals"], {d["id"] for d in self.kb.docs}),
            "Advisor": lambda p: {"status": "completed", "text": self.compose(p["proposals"])},
        }
        bus, proposals = MessageBus(handlers), []
        safety = bus.send("Coordinator", "Intake", "CHECK_SCOPE", {"question": question, "context": context})
        if safety["status"] != "completed":
            result = {"status": safety["status"], "text": safety.get("text", safety.get("error", "Lỗi tiếp nhận")),
                      "safety": safety, "proposals": [], "review": None}
        else:
            if task in ("consult", "risk"):
                proposals.append(bus.send("Coordinator", "Risk", "PREDICT_LABEL", {"profile": profile or {}, "model": model}))
            if task in ("consult", "knowledge"):
                proposals.append(bus.send("Coordinator", "Knowledge", "RETRIEVE", {"question": question}))
            if task in ("consult", "reminder"):
                proposals.append(bus.send("Coordinator", "Reminder", "PROPOSE_REMINDER", context))
            council = bus.send("Coordinator", "Council", "VERIFY", {"proposals": proposals})
            if council["status"] != "approved":
                result = {"status": "rejected", "text": "Chưa thể tổng hợp: " + "; ".join(council["reasons"]),
                          "proposals": proposals, "review": council}
            else:
                advice = bus.send("Coordinator", "Advisor", "SUMMARIZE", {"proposals": proposals})
                statuses = {p.get("status") for p in proposals}
                result = {"status": "needs_input" if "needs_input" in statuses else
                          ("insufficient_evidence" if "insufficient_evidence" in statuses else "completed"),
                          "text": advice.get("text", advice.get("error", "Không thể tổng hợp")),
                          "proposals": proposals, "review": council}
                if advice["status"] == "failure":
                    result["status"] = "failure"
        result.update(run_id=str(uuid.uuid4()), question=question, trace=bus.trace, disclaimer=DISCLAIMER)
        if self.audit_path:
            self.save_audit(result)
        return result

    @staticmethod
    def compose(proposals):
        paragraphs = []
        for p in proposals:
            if p["kind"] == "risk":
                if p["status"] == "needs_input":
                    paragraphs.append("Chưa chạy dự đoán: " + p.get("error", "thiếu " + ", ".join(p.get("missing", []))))
                elif p["status"] == "completed":
                    label = "nhãn 1" if p["positive"] else "nhãn 0"
                    paragraphs.append(f"Mô hình {p['model']}: điểm {p['score']:.3f}, ngưỡng {p['threshold']:.3f}, dự đoán {label}. " + p["meaning"])
            elif p["kind"] == "knowledge":
                paragraphs.append(p["text"])
            elif p["kind"] == "reminder":
                paragraphs.append("Nhắc việc mô phỏng: " + p.get("text", p.get("error", "Thiếu thông tin")))
        paragraphs.append("Bạn có thể mang thông tin và câu hỏi tới nhân viên y tế để được đánh giá phù hợp. " + DISCLAIMER)
        return "\n\n".join(paragraphs)

    def save_audit(self, result, path=None):
        # No profile is persisted. Audit question/answer may still contain user-entered text.
        with sqlite3.connect(path or self.audit_path) as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS runs (run_id TEXT PRIMARY KEY, created_at TEXT, result_json TEXT)")
            conn.execute("INSERT INTO runs VALUES (?, ?, ?)", (result["run_id"],
                         datetime.now(timezone.utc).isoformat(), json.dumps(result, ensure_ascii=False)))
