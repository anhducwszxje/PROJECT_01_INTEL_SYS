"""One-time packaging of the existing research subset and authored knowledge notes.

Run only inside the original INTEL_SYS workspace. The delivery already contains
the generated CSV/JSON files, so recipients do not need this preparation step.
"""
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
source = ROOT.parent / "Diabetes_MultiAgent" / "data" / "ml"
if not (DATA / "classification.csv").exists():
    shutil.copy2(source / "classification.csv", DATA / "classification.csv")
card = json.loads((source.parent.parent / "artifacts/ml/data_card.json").read_text(encoding="utf-8"))["classification"]
card.update(study_sha256=hashlib.sha256((DATA / "classification.csv").read_bytes()).hexdigest(),
            prepared_at="2026-11-05", license="CC BY 4.0 (UCI metadata)",
            split_origin="Reuse frozen 24,000-row study subset from Diabetes_MultiAgent; group by identical 21-feature vector, seeds 42/43.",
            note="Target is the binary column supplied by UCI, not a clinical type-2 diagnosis. Source landing-page narrative and metadata contain inconsistencies; this project documents the actual CSV schema.")
(DATA / "provenance.json").write_text(json.dumps(card, ensure_ascii=False, indent=2), encoding="utf-8")

sources = {
 "basic": ("NIDDK What Is Diabetes", "https://www.niddk.nih.gov/health-information/diabetes/overview/what-is-diabetes"),
 "test": ("NIDDK Diabetes Tests and Diagnosis", "https://www.niddk.nih.gov/health-information/diabetes/overview/tests-diagnosis"),
 "a1c": ("NIDDK The A1C Test and Diabetes", "https://www.niddk.nih.gov/health-information/diagnostic-tests/a1c-test"),
 "low": ("CDC Treatment of Low Blood Sugar", "https://www.cdc.gov/diabetes/treatment/treatment-low-blood-sugar-hypoglycemia.html"),
 "log": ("NIDDK Managing Diabetes", "https://www.niddk.nih.gov/health-information/diabetes/overview/managing-diabetes"),
 "food": ("CDC Diabetes Meal Planning", "https://www.cdc.gov/diabetes/healthy-eating/diabetes-meal-planning.html"),
 "move": ("CDC Get Active", "https://www.cdc.gov/diabetes/living-with/physical-activity.html"),
}
# Concise Vietnamese paraphrases, not copied passages or individualized advice.
notes = [
 ("D01", "Tiểu đường và insulin", "basic", ["diabetes"], ["tiểu đường là gì", "insulin", "đái tháo đường"],
  "Tiểu đường liên quan đến glucose máu cao và khả năng tạo hoặc sử dụng insulin."),
 ("D02", "Các loại tiểu đường", "basic", ["types"], ["type 1", "type 2", "thai kỳ", "phân biệt"],
  "Type 1, type 2 và tiểu đường thai kỳ có cơ chế và hoàn cảnh khác nhau."),
 ("D03", "Xét nghiệm và xác nhận", "test", ["tests"], ["xét nghiệm", "chẩn đoán", "xác nhận"],
  "Chẩn đoán dựa vào xét nghiệm phù hợp và đánh giá của nhân viên y tế; thường cần xác nhận lại."),
 ("D04", "Glucose lúc đói", "test", ["fasting"], ["lúc đói", "nhịn ăn", "tám giờ", "8 giờ"],
  "Xét nghiệm glucose lúc đói cần nhịn ăn ít nhất tám giờ theo hướng dẫn xét nghiệm. Phải phân biệt số đo lúc đói với số đo ở thời điểm bất kỳ."),
 ("D05", "Đường huyết thấp", "low", ["hypoglycemia"], ["hạ đường huyết", "đường huyết thấp", "70 mg", "run tay"],
  "Theo CDC, glucose dưới 70 mg/dL được coi là thấp và cần xử trí kịp thời. Nếu không tỉnh táo hoặc không tự xử trí được, cần trợ giúp y tế khẩn cấp."),
 ("D06", "HbA1c phản ánh thời gian dài", "a1c", ["a1c"], ["hba1c", "a1c", "ba tháng", "trung bình"],
  "HbA1c phản ánh đường huyết trung bình khoảng ba tháng, khác số đo tức thời. Cần đọc kết quả cùng bối cảnh và hướng dẫn chuyên môn."),
 ("D07", "Giới hạn của HbA1c", "a1c", ["a1c_limits"], ["thiếu máu", "hemoglobin", "sai lệch hba1c"],
  "Một số tình trạng ảnh hưởng hồng cầu hoặc hemoglobin có thể làm HbA1c kém tin cậy. Khi kết quả không phù hợp, cần trao đổi với nhân viên y tế."),
 ("D08", "Nhật ký theo dõi", "log", ["journal"], ["nhật ký", "ghi chép", "ghi nhận", "theo dõi"],
  "Theo dõi và trao đổi kết quả với nhóm chăm sóc giúp quản lý bệnh. Project gợi ý ghi giá trị, thời gian, đơn vị và bối cảnh; lịch đo cần thống nhất với nhân viên y tế."),
 ("D09", "Mục tiêu và thuốc", "log", ["care"], ["mục tiêu", "thuốc", "kế hoạch chăm sóc"],
  "Mục tiêu theo dõi và kế hoạch chăm sóc cần phù hợp từng người. Trao đổi với nhóm chăm sóc về thuốc và khó khăn."),
 ("D10", "Ăn uống và khẩu phần", "food", ["nutrition"], ["ăn uống", "dinh dưỡng", "đĩa ăn", "khẩu phần"],
  "Lựa chọn thực phẩm và khẩu phần cần phù hợp mục tiêu, thói quen và thuốc đang dùng. Có thể tìm hiểu phương pháp đĩa ăn cùng chuyên viên dinh dưỡng."),
 ("D11", "Carbohydrate", "food", ["carbs"], ["carbohydrate", "carb", "tinh bột", "đếm carb"],
  "Carbohydrate ảnh hưởng đường huyết; tốc độ thay đổi còn phụ thuộc thực phẩm ăn kèm."),
 ("D12", "Vận động", "move", ["activity"], ["vận động", "đi bộ", "tập luyện", "thể dục"],
  "Vận động đều đặn hỗ trợ quản lý đường huyết. Bắt đầu phù hợp khả năng và hỏi nhân viên y tế về hoạt động hoặc giới hạn cần lưu ý."),
]
docs = [{"id": i, "title": t, "concepts": c, "keywords": k, "content": text,
         "source_title": sources[s][0], "source_url": sources[s][1], "checked_at": "2026-11-05"}
        for i, t, s, c, k, text in notes]
concepts = [{"id": c, "aliases": k} for _, _, _, cs, k, _ in notes for c in cs]
relations = [("diabetes", "tests", "assessed_by"), ("tests", "fasting", "includes"),
             ("tests", "a1c", "includes"), ("a1c", "a1c_limits", "has_limitation"),
             ("diabetes", "care", "managed_with"), ("care", "journal", "uses"),
             ("nutrition", "carbs", "includes"), ("care", "activity", "includes")]
graph = {"concepts": concepts, "relations": [{"source": s, "target": t, "type": r} for s,t,r in relations],
         "evidence_edges": [{"source": d["id"], "target": c, "type": "explains"} for d in docs for c in d["concepts"]]}
for name, obj in [("knowledge.json", docs), ("graph.json", graph)]:
    (DATA / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

# Evaluation questions are authored scenarios, not external patient questions.
questions = [
 ("Tiểu đường là gì và insulin có vai trò gì?", "D01"), ("Tìm hiểu khái niệm đái tháo đường", "D01"),
 ("Phân biệt type 1 type 2 và thai kỳ", "D02"), ("Có những loại tiểu đường nào?", "D02"),
 ("Cần xét nghiệm để xác nhận chẩn đoán không?", "D03"), ("Điểm mô hình thay được xét nghiệm không?", "D03"),
 ("Nhịn ăn bao lâu trước xét nghiệm lúc đói?", "D04"), ("Glucose lúc đói khác số đo bất kỳ thế nào?", "D04"),
 ("Hạ đường huyết là gì?", "D05"), ("Đường huyết thấp dưới 70 mg có đáng lưu ý?", "D05"),
 ("HbA1c phản ánh mấy tháng?", "D06"), ("A1C có phải số đo tức thời không?", "D06"),
 ("Thiếu máu ảnh hưởng kết quả ra sao?", "D07"), ("Hemoglobin làm sai lệch HbA1c không?", "D07"),
 ("Nhật ký cần ghi những gì?", "D08"), ("Lợi ích của ghi chép theo dõi?", "D08"),
 ("Mục tiêu và kế hoạch chăm sóc có giống mọi người?", "D09"), ("Trao đổi về thuốc với ai?", "D09"),
 ("Ăn uống và khẩu phần nên lưu ý gì?", "D10"), ("Phương pháp đĩa ăn là gì?", "D10"),
 ("Tinh bột tác động thế nào?", "D11"), ("Carbohydrate ảnh hưởng đường huyết không?", "D11"),
 ("Vận động có giúp quản lý bệnh không?", "D12"), ("Tập luyện và đi bộ cần lưu ý gì?", "D12"),
]
(DATA / "retrieval_cases.json").write_text(json.dumps([{"query": q, "expected_id": i} for q,i in questions], ensure_ascii=False, indent=2), encoding="utf-8")
cypher = ["// Optional export only. The local demo does not require Neo4j."]
for c in concepts:
    cypher.append(f"MERGE (:Concept {{id: '{c['id']}'}});")
for s, t, r in relations:
    cypher.append(f"MATCH (a:Concept {{id:'{s}'}}), (b:Concept {{id:'{t}'}}) MERGE (a)-[:{r.upper()}]->(b);")
(DATA / "concept_graph.cypher").write_text("\n".join(cypher), encoding="utf-8")
print("Prepared frozen dataset, 12 knowledge notes, graph and 24 authored retrieval cases.")
