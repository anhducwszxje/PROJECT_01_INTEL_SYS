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
