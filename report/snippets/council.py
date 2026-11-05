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
