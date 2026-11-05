"""Maintain readable notebook sources; this script does not fabricate outputs."""
import sys
from pathlib import Path

import nbformat as nb

ROOT = Path(__file__).resolve().parents[1]
setup = '''# Chạy được khi kernel bắt đầu ở PROJECT_01 hoặc notebooks.
import sys
from pathlib import Path
ROOT = Path.cwd() if (Path.cwd() / "diabetes_agent").exists() else Path.cwd().parent
assert (ROOT / "diabetes_agent").exists(), "Mở notebook từ thư mục PROJECT_01"
sys.path.insert(0, str(ROOT))
import pandas as pd
from IPython.display import display, Image
from diabetes_agent.config import ARTIFACTS, DATA, FEATURES
print("Python:", sys.version.split()[0], "| Project:", ROOT.name)'''


def markdown(text):
    return nb.v4.new_markdown_cell(text)


def code(text):
    return nb.v4.new_code_cell(text)


def write(name, cells):
    book = nb.v4.new_notebook(cells=cells, metadata={"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.11"}})
    nb.write(book, ROOT / "notebooks" / name)


write("01_Du_lieu_va_huan_luyen_MLP.ipynb", [
 markdown("""# Project01 Dữ liệu và huấn luyện MLP

Notebook này đọc **24.000 dòng đã đóng gói**, kiểm tra chia tập, huấn luyện MLP PyTorch và ba đối chứng, chọn model/ngưỡng trên validation rồi đánh giá test.

**Cách chạy:** cài `requirements.txt`, chọn kernel Python 3.11 của môi trường đó, Run All. Không có cell tự cài thư viện. Các cell gọi mã thật trong `diabetes_agent/models.py`; source nằm cùng gói, không phụ thuộc workspace khác.

**Giới hạn:** nhãn khảo sát gộp theo UCI, không phải chẩn đoán type 2 hoặc dự báo bệnh tương lai. Dữ liệu được kế thừa từ tập nghiên cứu cũ trong workspace; model được huấn luyện mới cho Project01."""),
 code(setup),
 markdown("## 1 Kiểm tra nguồn và tính toàn vẹn\nSHA256 phải khớp provenance. Fingerprint của cùng vector đặc trưng không được xuất hiện ở hai split; đây không phải bảo đảm nhận dạng người tham gia khi thiếu ID người bệnh."),
 code('''import json
from diabetes_agent.data import load_data, build_database
frame = load_data()
display(frame.groupby("split").target.agg(["count", "mean"]))
print("Đặc trưng:", FEATURES)
display(frame[FEATURES + ["target", "split"]].head())
provenance = json.loads((DATA / "provenance.json").read_text(encoding="utf-8"))
print("Nguồn:", provenance["source"])
print("SHA256:", provenance["study_sha256"])'''),
 markdown("## 2 Tạo CSDL SQLite và kiểm tra phân bố\nCSDL được dựng lại từ CSV. Bảng chỉ lưu dữ liệu nghiên cứu công khai. Target, row_id, group và split không được đưa vào input model."),
 code('''display(build_database())
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(5, 3))
frame.groupby(["split", "target"]).size().unstack().plot.bar(ax=ax)
ax.set_ylabel("Số hồ sơ"); ax.set_title("Phân bố nhãn theo split")
plt.tight_layout(); display(fig); plt.close(fig)'''),
 markdown(r"""## 3 Mô hình và quy trình học

MLP: $21 \to 64 \to 32 \to 1$, ReLU, dropout 0.15, Adam learning rate 0.001, batch 256. Hàm loss là BCE với logit; không cân bằng lại nhãn nên không tuyên bố hiệu chỉnh về một dân số khác. Scaler chỉ fit train. Early stopping xem BCE validation, patience 10, tối đa 80 epoch. Hai mô hình đối chứng học là Logistic Regression và Random Forest; Dummy chỉ dùng tiên nghiệm train.

**Quy tắc khóa trước test:** chọn mặc định bằng Average Precision validation; mỗi ngưỡng tối ưu F1 trên validation. Test không được dùng để thay cấu hình. Một split/seed supervised chưa đủ để suy rộng kết quả."""),
 code('''# Xem trực tiếp kiến trúc thực thi, không phải pseudocode.
from diabetes_agent.models import architecture
print(architecture())'''),
 code('''# Fit thật, lưu weight/scaler, quyết định validation, rồi xuất test predictions.
from diabetes_agent.models import train_all
test_metrics, manifest = train_all()
display(pd.read_csv(ARTIFACTS / "metrics_validation.csv"))
print("Mặc định đã chọn bằng validation:", manifest["default_model"])
print("Epoch MLP được chọn:", manifest["best_epoch"])'''),
 markdown("## 4 Đọc output huấn luyện và test\nRecall và precision phải đọc cùng nhau. Tập mất cân bằng khiến accuracy dễ gây hiểu nhầm; Average Precision có đường chuẩn bằng tỷ lệ nhãn 1."),
 code('''display(test_metrics.round(4))
display(Image(filename=str(ARTIFACTS / "figures/training.png")))
display(Image(filename=str(ARTIFACTS / "figures/classification.png")))'''),
 markdown("## 5 Nạp model đã lưu và đối chiếu từng dòng\nDùng một dòng test để đối chiếu suy luận với prediction CSV, không dùng dòng đó để chọn lại model."),
 code('''from diabetes_agent.models import RiskModel
model = RiskModel()
stored = pd.read_csv(ARTIFACTS / "predictions_mlp.csv").iloc[0]
sample = frame[frame.row_id == stored.row_id].iloc[0]
prediction = model.predict(sample[FEATURES].to_dict(), "mlp")
print(prediction)
assert abs(prediction["score"] - stored.score) < 1e-6
print("PASS: nạp weight và suy luận khớp prediction đã xuất.")'''),
 markdown("**Tự đọc mã:** `data.py` bảo vệ nguồn/split; `models.py` chứa vòng mini-batch, early stopping và export. Báo cáo ghi số liệu lấy từ `artifacts/metrics_test.csv`; không lấy kết quả mẫu từ tài liệu tham khảo.")
])

write("02_Tri_thuc_va_Graph_Retrieval.ipynb", [
 markdown("# Project01 Tri thức và truy xuất đồ thị\n\nMục tiêu: theo dõi đường đi từ ghi chú có nguồn tới bằng chứng và câu trả lời. Đây là RAG theo kiểu trích xuất, không có LLM sinh tự do. Đồ thị local là JSON với cạnh tường minh; file Cypher chỉ là bản xuất tùy chọn."),
 code(setup),
 markdown("## 1 Kiểm tra cấu trúc kho tri thức\n12 ghi chú tiếng Việt biên soạn ngắn từ 7 trang NIDDK/CDC, có URL, ngày kiểm tra và ID. Đây không phải 12 tài liệu gốc đầy đủ hoặc kho hướng dẫn lâm sàng."),
 code('''from diabetes_agent.knowledge import KnowledgeBase
kb = KnowledgeBase()
display(pd.DataFrame(kb.docs)[["id", "title", "concepts", "source_title", "checked_at"]])
print("Số khái niệm:", len(kb.graph["concepts"]))
display(pd.DataFrame(kb.graph["relations"]))'''),
 markdown("## 2 Thuật toán truy xuất\nChuẩn hóa chữ thường, bỏ dấu; TF-IDF unigram/bigram và cosine similarity. Từ khóa alias xác định khái niệm, mở rộng cạnh có hướng một bước; ghi chú liên quan được cộng 0.12. Cần khớp alias hoặc ít nhất hai token ở tiêu đề/từ khóa để hạn chế kết quả do từ chức năng. Điểm cosine tối thiểu 0.10 khi không khớp trực tiếp. Các hằng số là lựa chọn cài đặt, chưa tối ưu trên dữ liệu độc lập."),
 code('''query = "HbA1c và thiếu máu"
hits = kb.retrieve(query)
display(pd.DataFrame(hits)[["id", "title", "lexical_score", "score", "matched_concepts"]])
print(kb.answer(query)["text"])
for item in hits:
    print(item["id"], item["source_url"])'''),
 markdown("## 3 Từ chối khi thiếu bằng chứng\nBộ lọc lexical không bảo đảm hiểu ngữ nghĩa; câu hỏi không có căn cứ phù hợp cần trả trạng thái riêng."),
 code('''unknown = kb.answer("Vệ tinh Sao Hỏa")
print(unknown)
assert unknown["status"] == "insufficient_evidence"
print([d["id"] for d in kb.retrieve("hba1c ba thang")])'''),
 markdown("## 4 Đối chiếu truy xuất có và không có đồ thị\n24 câu do tác giả soạn, mỗi ghi chú hai câu, một ID mục tiêu mỗi câu. Hit@k đo tìm đúng ID trong k kết quả. MRR là trung bình nghịch đảo thứ hạng. Bộ câu nhỏ và dùng cùng từ vựng kho tri thức nên không đại diện câu hỏi người bệnh ngoài thực tế."),
 code('''import json
cases = json.loads((DATA / "retrieval_cases.json").read_text(encoding="utf-8"))
rows = []
for use_graph in (False, True):
    for case in cases:
        ids = [d["id"] for d in kb.retrieve(case["query"], graph=use_graph)]
        rank = ids.index(case["expected_id"]) + 1 if case["expected_id"] in ids else None
        rows.append({"graph": use_graph, "query": case["query"], "hit1": rank == 1,
                     "hit3": rank is not None, "rr": 1/rank if rank else 0})
results = pd.DataFrame(rows)
display(results.groupby("graph")[["hit1", "hit3", "rr"]].mean())
display(results)'''),
 markdown("## 5 Xem phần mã chịu trách nhiệm truy xuất\nSử dụng chính class của demo. Council sẽ kiểm tra ID bằng chứng, nhưng ID hợp lệ không chứng minh đoạn trích đã trả lời đúng ý người hỏi."),
 code('''import inspect
print(inspect.getsource(KnowledgeBase.retrieve))
if (ARTIFACTS / "figures/knowledge_graph.png").exists():
    display(Image(filename=str(ARTIFACTS / "figures/knowledge_graph.png")))''')
])

write("03_Q_learning_nhac_nhat_ky.ipynb", [
 markdown("# Project01 Q-learning nhắc nhật ký\n\nMục tiêu: thực thi một tác tử học chính sách theo phần thưởng, đọc Q-table và so sánh đối chứng. RL chỉ nhắc ghi dữ liệu trong mô phỏng; không kê thuốc, không có outcome lâm sàng."),
 code(setup),
 markdown(r"""## 1 Định nghĩa môi trường

Trạng thái $s=2g+f$: số ngày chưa ghi $g\in\{0,1,2,3\}$ (3 nghĩa là từ 3 ngày), mệt vì thông báo $f\in\{0,1\}$. Ba hành động: không nhắc, nhắc nhật ký, gợi ý ghi chép ngắn. Phản ứng ghi nhật ký là Bernoulli với xác suất do tác giả đặt trong `transition`. Reward cộng điểm ghi nhận, trừ chi phí nhắc, ngày thiếu và mệt. Không sử dụng số liệu y khoa để suy ra hệ số này.

Q-learning: $Q(s,a)\leftarrow Q(s,a)+0.08[r+0.92\max_{a'}Q(s',a')-Q(s,a)]$. Đây là bài toán continuing; mỗi rollout cắt ở 28 ngày nhưng vẫn bootstrap ở ngày cuối."""),
 code('''import inspect
from diabetes_agent.rl import transition, train_q, run_experiment, ACTIONS
print(inspect.getsource(transition))
print("Hành động:", ACTIONS)'''),
 markdown("## 2 Huấn luyện và đánh giá thật\n5 seed train 42–46, mỗi seed 1.800 episode. Đánh giá greedy trên 200 seed 10000–10199. Các policy dùng cùng seed để so sánh; Q-table dùng trong demo luôn là seed 42 được quy định trước, không chọn seed tốt nhất."),
 code('''summary = run_experiment()
display(summary)
display(Image(filename=str(ARTIFACTS / "figures/rl.png")))'''),
 markdown("## 3 Đọc chính sách\nAction là argmax của Q cho trạng thái đang xét. Q-value là utility chiết khấu trong simulator, không có đơn vị xác suất hoặc đường huyết."),
 code('''import numpy as np
q = np.load(ARTIFACTS / "q_table.npy")
policy = pd.DataFrame(q, columns=ACTIONS)
policy.insert(0, "gap_days", np.arange(8)//2)
policy.insert(1, "fatigue", np.arange(8)%2)
policy["chosen_action"] = [ACTIONS[i] for i in q.argmax(axis=1)]
display(policy.round(3))'''),
 markdown("## 4 Kiểm tra tính tái lập\nChạy hai lượt seed giống nhau với ít episode để kiểm chứng cơ chế ngẫu nhiên. Đây không thay thế đánh giá hiệu quả trên người thật."),
 code('''qa, _ = train_q(seed=7, episodes=20)
qb, _ = train_q(seed=7, episodes=20)
assert np.array_equal(qa, qb)
print("PASS: cùng seed tạo cùng Q-table.")
detail = pd.read_csv(ARTIFACTS / "rl_evaluation.csv")
display(detail.groupby("policy")[["reward_per_day", "logging_rate", "reminder_rate"]].mean())'''),
 markdown("**Phân tích:** đọc bảng để kiểm tra Q-learning có vượt policy cố định không. Nếu không vượt, vẫn báo đúng kết quả; không thay reward để tạo ưu thế. Độ lệch chuẩn trong `rl_summary.csv` là giữa năm giá trị trung bình theo seed train; policy cố định có std này bằng 0 vì dùng lại cùng seed eval, không có nghĩa không có biến thiên giữa người dùng mô phỏng.")
])

write("04_Tich_hop_Multi_Agent_va_Demo.ipynb", [
 markdown("# Project01 Tích hợp hệ đa tác tử và demo\n\nMục tiêu: chạy toàn bộ hội chẩn, quan sát thông điệp, thử dữ liệu thiếu, nhánh cảnh báo và veto của Council. Cần chạy notebook 01 và 03 trước nếu không có artifact đi kèm."),
 code(setup),
 markdown("## 1 Khởi tạo hệ thống và hồ sơ minh họa\nCoordinator giao việc qua MessageBus trong cùng tiến trình. Sáu chuyên gia là Intake, Risk, Knowledge, Reminder, Council và Advisor. Đây là bảy vai trò tính cả điều phối, không phải bảy LLM độc lập."),
 code('''from diabetes_agent.system import DiabetesSystem, review
from diabetes_agent.evaluation import example_profile, evaluate_all
system = DiabetesSystem()
profile = example_profile()
print("Hồ sơ minh họa thuộc train, không phải kiểm định:")
display(pd.Series(profile))'''),
 markdown("## 2 Một lượt đầy đủ\nIntake kiểm tra phạm vi trước. Risk phân loại vector khảo sát; Knowledge tìm bằng chứng; Reminder chọn hành động; Council kiểm tra hợp đồng; Advisor ghép kết quả có nguồn."),
 code('''result = system.run("HbA1c phản ánh điều gì và ghi nhật ký ra sao?", profile,
                    context={"gap_days": 2, "fatigue": 0})
print(result["text"])
print("Trạng thái:", result["status"], "| Council:", result["review"])
display(pd.DataFrame(result["trace"]))
assert result["status"] == "completed" and len(result["trace"]) == 12'''),
 markdown("## 3 Dữ liệu thiếu không được tự điền\nModel cần đúng 21 trường. Yêu cầu bổ sung không có nghĩa đã đưa ra dự đoán từ hồ sơ hoàn chỉnh."),
 code('''incomplete = system.run("Phân loại", {"BMI": 26}, task="risk")
print(incomplete["status"])
print(incomplete["text"])
assert incomplete["status"] == "needs_input"'''),
 markdown("## 4 Nhánh khẩn cấp ưu tiên trước mô hình\nSố đo glucose không thuộc input CDC. Luật dưới 70 mg/dL có nguồn CDC và chỉ kích hoạt thông điệp cần xử trí/hỗ trợ, không chẩn đoán từ mô hình."),
 code('''urgent = system.run("Tôi hỏi về HbA1c", profile, context={"glucose_mg_dl": 62})
print(urgent["status"], urgent["text"])
display(pd.DataFrame(urgent["trace"]))
assert len(urgent["trace"]) == 2
assert not any(m["receiver"] == "Risk" for m in urgent["trace"])'''),
 markdown("## 5 Council từ chối đề xuất không đạt\nThử inject một đề xuất thuốc và một bằng chứng ID giả. Đây là kiểm tra phần mềm có chủ đích; không phải đo tỷ lệ sự cố lâm sàng."),
 code('''bad = [{"kind": "medication", "status": "completed"},
       {"kind": "knowledge", "status": "completed", "evidence": [{"id": "FAKE"}]}]
veto = review(bad, {d["id"] for d in system.kb.docs})
print(veto)
assert veto["status"] == "rejected"'''),
 markdown("## 6 Chạy bộ đánh giá và xem kết quả\n24 câu truy xuất, 20 kịch bản hệ thống và 6 lỗi inject đều do tác giả thiết kế. Phải phân biệt tỷ lệ đạt hợp đồng với chất lượng y khoa hoặc độ đúng hội thoại mở."),
 code('''summary = evaluate_all()
print(summary)
display(pd.read_csv(ARTIFACTS / "system_evaluation.csv"))
display(pd.read_csv(ARTIFACTS / "council_ablation.csv"))
assert summary["system_passed"] == summary["system_cases"]'''),
 markdown("## 7 Chạy giao diện local\nMở terminal tại PROJECT_01 và chạy lệnh dưới. Lệnh được in ra để tránh notebook giữ kernel vì server. Trong giao diện thử bốn tác vụ, đổi sang MLP, tải trace JSON và xem benchmark."),
 code('''print("python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8521")
print("Mở http://127.0.0.1:8521 | Dừng server bằng Ctrl+C")''')
])
print("Wrote four notebooks. Execute with scripts/execute_notebooks.py to produce outputs.")
