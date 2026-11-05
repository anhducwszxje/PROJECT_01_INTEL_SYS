"""Streamlit local demo; all model and policy training happens outside requests."""
import json

import pandas as pd
import streamlit as st

from diabetes_agent.config import ARTIFACTS, DISCLAIMER
from diabetes_agent.evaluation import example_profile
from diabetes_agent.system import DiabetesSystem

st.set_page_config(page_title="Diabetes Agent | Project01", page_icon="🩺", layout="wide")
st.markdown("""<style>
.stApp {background:#f5f8fa} .block-container {padding-top:2rem;max-width:1350px}
h1,h2,h3 {color:#114b50} div[data-testid="stMetric"] {background:white;padding:1rem;border-radius:12px;border:1px solid #dce8e8}
div.stButton > button[kind="primary"] {background:#146c70;border:0}
</style>""", unsafe_allow_html=True)
st.caption("PTIT · PROJECT 01 · BÙI ANH ĐỨC · B23DCCN165")
st.title("Diabetes Agent")
st.write("Phân loại hồ sơ khảo sát, tra cứu tri thức có nguồn và quan sát các tác tử phối hợp.")
st.info(DISCLAIMER)


@st.cache_resource
def load_system():
    return DiabetesSystem()


if not (ARTIFACTS / "model_manifest.json").exists() or not (ARTIFACTS / "q_table.npy").exists():
    st.error("Chưa có artifact. Chạy: python scripts/run_experiments.py")
    st.stop()
system = load_system()
metrics = pd.read_csv(ARTIFACTS / "metrics_test.csv")
default = system.risk.manifest["default_model"]
selected = metrics[metrics.model == default].iloc[0]
cols = st.columns(4)
for col, label, value in zip(cols, ["Hồ sơ nghiên cứu", "Tác tử và điều phối", "ROC AUC test mặc định", "Tri thức · 7 nguồn"],
                             ["24.000", "7 vai trò", f"{selected.roc_auc:.3f}", "12 ghi chú"]):
    col.metric(label, value)
consult, evidence_tab, benchmark, guide = st.tabs(["Hội chẩn demo", "Tri thức và đồ thị", "Thực nghiệm", "Hướng dẫn"])
with consult:
    left, right = st.columns([.9, 1.1], gap="large")
    with left:
        st.subheader("1. Đầu vào")
        labels = {"Hội chẩn tổng hợp": "consult", "Chỉ hỏi tri thức": "knowledge", "Chỉ phân loại hồ sơ": "risk", "Chỉ nhắc nhật ký": "reminder"}
        task_label = st.selectbox("Tác vụ", list(labels))
        model = st.selectbox("Mô hình phân loại", ["default", "mlp", "logistic", "random_forest", "dummy"])
        question = st.text_area("Câu hỏi", "HbA1c phản ánh điều gì và cần ghi nhật ký thế nào?", height=95)
        use_profile = st.checkbox("Dùng hồ sơ mẫu từ tập train", value=True)
        profile = example_profile() if use_profile else {}
        with st.expander("21 trường khảo sát CDC", expanded=False):
            st.caption("Mẫu minh họa từ tập train, không dùng để chứng minh chất lượng dự đoán. Age là nhóm tuổi 1–13; Sex: 0 nữ, 1 nam theo mã dữ liệu. Xem data/README.md để biết toàn bộ mã.")
            profile_text = st.text_area("Hồ sơ JSON (bỏ chọn mẫu để nhập riêng)",
                json.dumps(example_profile(), indent=2), height=330)
            if not use_profile:
                try:
                    profile = json.loads(profile_text)
                    if not isinstance(profile, dict):
                        raise ValueError("Cần JSON object")
                except (json.JSONDecodeError, ValueError) as exc:
                    st.error(str(exc)); profile = {}
        a, b = st.columns(2)
        gap = a.slider("Số ngày chưa ghi (mô phỏng)", 0, 3, 2)
        fatigue = b.selectbox("Mệt vì thông báo (mô phỏng)", [0, 1])
        use_glucose = st.checkbox("Thêm số đo glucose cho luật cảnh báo")
        glucose = st.number_input("Glucose mg/dL", 10., 1000., 110., disabled=not use_glucose)
        st.caption("Glucose không phải đặc trưng của mô hình CDC. Nếu có dấu hiệu khẩn cấp, cần hỗ trợ y tế ngay.")
        save = st.checkbox("Lưu câu hỏi và kết quả vào SQLite local", value=False)
        if st.button("Chạy Diabetes Agent", type="primary", use_container_width=True):
            context = {"gap_days": gap, "fatigue": fatigue}
            if use_glucose:
                context["glucose_mg_dl"] = glucose
            result = system.run(question, profile, context, model=model, task=labels[task_label])
            if save:
                system.save_audit(result, ARTIFACTS / "demo_audit.sqlite3")
            st.session_state.result = result
    with right:
        st.subheader("2. Kết quả và thông điệp")
        if "result" not in st.session_state:
            st.write("Chọn tác vụ rồi bấm **Chạy Diabetes Agent**. Mỗi lần chạy hiển thị kết quả, nguồn và thông điệp của từng tác tử.")
            st.markdown("**Các tình huống nên thử**\n\n- Hội chẩn với hồ sơ mẫu và câu hỏi HbA1c.\n- Chỉ hỏi tri thức: “Vận động có ích gì?”\n- Nhập Age = 55 để xem kiểm tra mã khảo sát.\n- Nhập glucose = 62 mg/dL để xem nhánh cảnh báo.")
        else:
            r = st.session_state.result
            st.caption("Trạng thái: " + r["status"] + " · " + r["run_id"][:8])
            st.write(r["text"])
            source_docs = {d["id"]: d for p in r["proposals"] for d in p.get("evidence", [])}
            if r.get("safety", {}).get("source_ids"):
                source_docs.update({d["id"]: d for d in system.kb.docs if d["id"] in r["safety"]["source_ids"]})
            for d in source_docs.values():
                st.markdown(f"[{d['id']} · {d['source_title']}]({d['source_url']})")
            st.markdown("**Thông điệp giữa các tác tử**")
            st.dataframe(pd.DataFrame(r["trace"]), hide_index=True, use_container_width=True)
            with st.expander("Kết quả có cấu trúc và kiểm tra của Council"):
                st.json(r)
            st.download_button("Tải trace JSON", json.dumps(r, ensure_ascii=False, indent=2), "diabetes_trace.json", "application/json")
with evidence_tab:
    st.subheader("Truy xuất tri thức local")
    query = st.text_input("Từ khóa tra cứu", "HbA1c và thiếu máu")
    for d in system.kb.retrieve(query):
        with st.container(border=True):
            st.markdown(f"**{d['id']} · {d['title']}**")
            st.write(d["content"])
            st.markdown(f"[Nguồn: {d['source_title']}]({d['source_url']}) · Điểm truy xuất {d['score']:.3f}")
            st.caption("Khái niệm khớp: " + ", ".join(d["matched_concepts"]))
    st.caption("TF-IDF kết hợp liên kết khái niệm một bước; câu trả lời trích xuất theo mẫu. Không gọi LLM, không cần Neo4j đang chạy.")
    if (ARTIFACTS / "figures" / "knowledge_graph.png").exists():
        st.image(str(ARTIFACTS / "figures" / "knowledge_graph.png"))
    st.dataframe(pd.DataFrame(system.kb.graph["relations"]), hide_index=True)
with benchmark:
    st.subheader("Kết quả trên test đã khóa")
    st.caption("Mô hình mặc định chọn bằng Average Precision trên validation: " + default + ". Ngưỡng từng model chọn bằng F1 validation. Điểm score chưa được hiệu chỉnh cho quần thể Việt Nam.")
    st.dataframe(metrics, hide_index=True, use_container_width=True)
    st.image(str(ARTIFACTS / "figures" / "classification.png"))
    st.subheader("Q-learning nhắc nhật ký")
    st.image(str(ARTIFACTS / "figures" / "rl.png"))
    st.dataframe(pd.read_csv(ARTIFACTS / "rl_summary.csv"), hide_index=True)
    st.warning("Reward và phản ứng người dùng được mô phỏng. Kết quả không đo hiệu quả điều trị.")
    st.subheader("Kiểm tra hệ thống")
    st.dataframe(pd.read_csv(ARTIFACTS / "system_evaluation.csv"), hide_index=True)
with guide:
    st.subheader("Chạy và tái lập")
    st.code("python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8521\npython scripts/run_experiments.py\npython scripts/execute_notebooks.py\npython -m pytest -q", language="powershell")
    st.write("Notebook: 01 dữ liệu và MLP; 02 tri thức và đồ thị; 03 Q-learning; 04 tích hợp và đánh giá. Đọc README.md và docs/HUONG_DAN_CHAY.md trước khi chạy lại.")
    st.write("Mô hình suy luận từ artifacts/models. CSV/JSON tri thức và mô hình đã có trong gói; sau khi cài thư viện, demo không cần Internet hoặc API key.")
