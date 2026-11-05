"""Local Diabetes Agent dashboard; inference uses saved project artifacts."""
import json
from html import escape

import pandas as pd
import streamlit as st

from diabetes_agent.config import ARTIFACTS, ROOT
from diabetes_agent.evaluation import example_profile
from diabetes_agent.system import DiabetesSystem

st.set_page_config(page_title="Diabetes Agent", page_icon="💧", layout="wide")
st.markdown(f"<style>{(ROOT / 'assets/demo.css').read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

MODEL_NAMES = {"default": "Tự động chọn", "mlp": "MLP · PyTorch", "random_forest": "Random Forest",
               "logistic": "Logistic Regression", "dummy": "Dummy · đối chứng"}
TASK_NAMES = {"consult": "Phân tích tổng hợp", "risk": "Phân loại hồ sơ", "knowledge": "Tra cứu tri thức", "reminder": "Nhắc nhật ký"}
AGENTS = [("Coordinator", "Điều phối", "01"), ("Intake", "Tiếp nhận", "02"),
          ("Risk", "Dự đoán", "03"), ("Knowledge", "Tri thức", "04"),
          ("Reminder", "Nhắc việc", "05"), ("Council", "Kiểm tra", "06"), ("Advisor", "Tổng hợp", "07")]


@st.cache_resource
def load_system():
    return DiabetesSystem()


@st.cache_data
def load_dashboard():
    return (pd.read_csv(ARTIFACTS / "metrics_test.csv"),
            pd.read_csv(ARTIFACTS / "rl_summary.csv"),
            pd.read_csv(ARTIFACTS / "training_history.csv"), example_profile())


if not (ARTIFACTS / "model_manifest.json").exists() or not (ARTIFACTS / "q_table.npy").exists():
    st.error("Chưa có mô hình. Chạy python scripts/run_experiments.py để khởi tạo.")
    st.stop()
system = load_system()
metrics, rl_metrics, history, sample_profile = load_dashboard()
default_model = system.risk.manifest["default_model"]
current_metrics = metrics[metrics.model == default_model].iloc[0]
defaults = {"task": "consult", "model": "default", "question": "HbA1c phản ánh điều gì và cần ghi nhật ký thế nào?",
            "profile_mode": "Hồ sơ mẫu", "profile_json": json.dumps(sample_profile, indent=2),
            "gap": 2, "fatigue": 0, "use_glucose": False, "glucose": 110.0}
for key, value in defaults.items():
    st.session_state.setdefault(key, value)


def run_preset(task):
    questions = {"consult": "HbA1c phản ánh điều gì và cần ghi nhật ký thế nào?",
                 "knowledge": "HbA1c và thiếu máu có liên quan thế nào?", "reminder": "Nhắc tôi ghi nhật ký đường huyết"}
    st.session_state.update(task=task, question=questions[task], profile_mode="Hồ sơ mẫu", use_glucose=False)
    st.session_state.result = system.run(questions[task], sample_profile,
        {"gap_days": st.session_state.gap, "fatigue": st.session_state.fatigue},
        model=st.session_state.model, task=task)


def render_flow(result):
    responses = {m["sender"]: m for m in (result or {}).get("trace", []) if m["performative"] != "REQUEST"}
    tiles = []
    for name, label, number in AGENTS:
        status = responses.get(name, {}).get("status")
        if name == "Coordinator" and result:
            status = result["status"]
        state = "done" if status in ("completed", "approved") else "attention" if status else "idle"
        note = "Hoàn tất" if state == "done" else "Cần chú ý" if state == "attention" else "Sẵn sàng"
        tiles.append(f'<div class="agent-node {state}"><span class="agent-number">{number}</span>'
                     f'<strong>{label}</strong><small>{name}</small><span class="agent-state"><i></i>{note}</span></div>')
    st.markdown('<div class="agent-flow">' + "".join(tiles) + '</div>', unsafe_allow_html=True)


def render_risk(proposal):
    score, threshold = proposal["score"], proposal["threshold"]
    label = "Nhóm 1 · Tiền tiểu đường / tiểu đường" if proposal["positive"] else "Nhóm 0 · Không có nhãn tiểu đường"
    tone = "amber" if proposal["positive"] else "teal"
    st.markdown(f'''<div class="risk-card {tone}">
        <div class="score-ring" style="--angle:{score * 360:.2f}deg"><div><strong>{score:.3f}</strong><span>ĐIỂM MÔ HÌNH</span></div></div>
        <div class="risk-copy"><span class="eyebrow">KẾT QUẢ PHÂN LOẠI</span><h3>{label}</h3>
        <p>{escape(MODEL_NAMES[proposal['model']])}</p><div class="threshold">Ngưỡng phân loại <strong>{threshold:.3f}</strong></div></div>
        </div>''', unsafe_allow_html=True)


def render_evidence(docs):
    for doc in docs:
        with st.container(border=True):
            st.markdown(f'<div class="evidence-heading"><span>{escape(doc["id"])}</span><strong>{escape(doc["title"])}</strong></div>', unsafe_allow_html=True)
            st.write(doc["content"])
            st.markdown(f'[{doc["source_title"]} ↗]({doc["source_url"]})')


st.markdown('''<div class="hero"><div class="hero-copy"><div class="hero-kicker"><span class="brand-mark">✚</span> DIABETES AGENT <span class="live-badge"><i></i> LOCAL LIVE</span></div>
    <h1>Một góc nhìn rõ hơn<br>về sức khỏe của bạn<span>.</span></h1>
    <p>Phân tích hồ sơ, kết nối tri thức và theo dõi từng bước của hệ đa tác tử.</p>
    <div class="hero-tags"><span>Machine Learning</span><span>Knowledge Graph</span><span>Q-learning</span></div></div>
    <div class="hero-art" aria-hidden="true"><div class="orbit orbit-one"></div><div class="orbit orbit-two"></div>
    <div class="pulse-core"><svg viewBox="0 0 100 112"><path d="M50 5C39 24 15 49 15 72a35 35 0 0 0 70 0C85 49 61 24 50 5Z" fill="currentColor"/><path d="M24 70h14l8-16 11 31 9-15h12" fill="none" stroke="white" stroke-width="4" stroke-linejoin="round"/></svg></div>
    <span class="orbit-chip chip-one">✦ Tri thức</span><span class="orbit-chip chip-two">↗ Dự đoán</span><span class="orbit-chip chip-three">✓ Đồng hành</span></div></div>''', unsafe_allow_html=True)

for col, label, value, detail in zip(st.columns(4),
    ["HỒ SƠ DỮ LIỆU", "VAI TRÒ TÁC TỬ", "ROC AUC", "KHO TRI THỨC"],
    ["24.000", "07", f"{current_metrics.roc_auc:.3f}", "12"],
    ["21 chỉ báo sức khỏe", "Phối hợp trong một luồng", MODEL_NAMES[default_model], "Ghi chú từ 7 nguồn"]):
    with col:
        st.markdown(f'<div class="stat-card"><span>{label}</span><strong>{value}</strong><small>{detail}</small></div>', unsafe_allow_html=True)

consult, knowledge_tab, benchmark, guide = st.tabs(["Hội chẩn demo", "Tri thức và đồ thị", "Thực nghiệm", "Hướng dẫn"])
with consult:
    st.markdown('<div class="section-heading"><div><span class="eyebrow">KHỞI ĐỘNG NHANH</span><h2>Bạn muốn khám phá điều gì?</h2></div><span class="section-note">Chọn một kịch bản để chạy ngay</span></div>', unsafe_allow_html=True)
    for col, task, title in zip(st.columns(3), ["consult", "knowledge", "reminder"],
                               ["◈  Phân tích hồ sơ", "✦  Tìm hiểu HbA1c", "◷  Nhắc ghi nhật ký"]):
        col.button(title, key="scenario_" + task, on_click=run_preset, args=(task,), width="stretch")
    render_flow(st.session_state.get("result"))
    left, right = st.columns([.9, 1.5], gap="large")
    with left:
        with st.container(border=True, key="input_panel"):
            st.markdown('<span class="eyebrow">THIẾT LẬP PHIÊN</span><h3>Hồ sơ & câu hỏi</h3>', unsafe_allow_html=True)
            st.selectbox("Tác vụ", list(TASK_NAMES), format_func=TASK_NAMES.get, key="task")
            st.selectbox("Mô hình phân loại", list(MODEL_NAMES), format_func=MODEL_NAMES.get, key="model")
            st.text_area("Câu hỏi", key="question", height=105)
            st.segmented_control("Nguồn hồ sơ", ["Hồ sơ mẫu", "Nhập JSON"], key="profile_mode", required=True)
            profile = sample_profile
            if st.session_state.profile_mode == "Nhập JSON":
                st.text_area("21 chỉ báo sức khỏe", key="profile_json", height=235)
                try:
                    profile = json.loads(st.session_state.profile_json)
                    if not isinstance(profile, dict):
                        raise ValueError("Hồ sơ cần là một JSON object.")
                except (json.JSONDecodeError, ValueError) as exc:
                    st.error(str(exc)); profile = {}
            else:
                st.markdown(f'<div class="profile-preview"><span>HỒ SƠ CDC</span><div><strong>BMI {profile["BMI"]:g}</strong><span>Nhóm tuổi {profile["Age"]}</span><span>{"Có" if profile["HighBP"] else "Không"} tăng huyết áp</span></div></div>', unsafe_allow_html=True)
                with st.expander("Xem 21 chỉ báo"):
                    st.json(profile)
                    st.caption("Age: mã nhóm tuổi 1–13. Sex: 0 nữ, 1 nam.")
            with st.expander("Nhật ký & số đo", expanded=st.session_state.task == "reminder"):
                st.slider("Số ngày chưa ghi", 0, 3, key="gap")
                st.selectbox("Mệt vì thông báo", [0, 1], format_func=lambda v: "Có" if v else "Không", key="fatigue")
                st.checkbox("Thêm số đo glucose", key="use_glucose")
                st.number_input("Glucose · mg/dL", 10., 1000., key="glucose", disabled=not st.session_state.use_glucose)
            save = st.checkbox("Lưu lịch sử phiên", value=False)
            if st.button("Bắt đầu phân tích", type="primary", key="run_agent", width="stretch", icon=":material/arrow_forward:"):
                context = {"gap_days": st.session_state.gap, "fatigue": st.session_state.fatigue}
                if st.session_state.use_glucose:
                    context["glucose_mg_dl"] = st.session_state.glucose
                with st.spinner("Các tác tử đang xử lý yêu cầu…"):
                    result = system.run(st.session_state.question, profile, context,
                                        model=st.session_state.model, task=st.session_state.task)
                if save:
                    system.save_audit(result, ARTIFACTS / "demo_audit.sqlite3")
                st.session_state.result = result
                st.rerun()
    with right:
        result = st.session_state.get("result")
        if result is None:
            st.markdown('''<div class="empty-state"><div class="empty-symbol">✦</div><span class="eyebrow">KHÔNG GIAN PHÂN TÍCH</span>
                <h2>Sẵn sàng cho phiên đầu tiên</h2><p>Chọn kịch bản bên trên hoặc nhập câu hỏi.<br>Các tác tử sẽ kết nối dữ liệu và tri thức ngay tại đây.</p>
                <div class="empty-steps"><span>01 · Tiếp nhận</span><b>→</b><span>02 · Phân tích</span><b>→</b><span>03 · Tổng hợp</span></div></div>''', unsafe_allow_html=True)
        else:
            replies = [m for m in result["trace"] if m["performative"] != "REQUEST"]
            elapsed = sum(m.get("elapsed_ms", 0) for m in replies)
            status_names = {"completed": "Đã hoàn tất", "urgent": "Cần xử trí ngay", "needs_input": "Cần thêm thông tin",
                            "insufficient_evidence": "Chưa tìm thấy tri thức", "rejected": "Cần kiểm tra lại",
                            "out_of_scope": "Chuyển hỗ trợ chuyên môn", "failure": "Chưa hoàn tất"}
            tone = "" if result["status"] == "completed" else "attention"
            st.markdown(f'<div class="result-top"><span class="result-status {tone}">● {status_names[result["status"]]}</span><span>{len(replies)} tác tử phản hồi · {elapsed:.0f} ms</span></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="question-echo">“{escape(result["question"])}”</div>', unsafe_allow_html=True)
            if not result["proposals"] or result["status"] in ("rejected", "failure"):
                st.warning(result["text"])
            for proposal in ([] if result["status"] in ("rejected", "failure") else result["proposals"]):
                if proposal["kind"] == "risk":
                    if proposal["status"] == "completed":
                        render_risk(proposal)
                    else:
                        st.info(proposal.get("error", "Bổ sung các trường: " + ", ".join(proposal.get("missing", []))))
                elif proposal["kind"] == "knowledge":
                    st.markdown("#### Tri thức dành cho câu hỏi của bạn")
                    if proposal["evidence"]:
                        render_evidence(proposal["evidence"])
                    else:
                        st.info(proposal["text"])
                elif proposal["kind"] == "reminder":
                    st.markdown(f'<div class="reminder-card"><span class="reminder-icon">◷</span><div><span class="eyebrow">NHẬT KÝ CỦA BẠN</span><strong>{escape(proposal.get("text", proposal.get("error", "Cần thêm thông tin")))}</strong></div></div>', unsafe_allow_html=True)
            if result.get("safety", {}).get("source_ids"):
                render_evidence([d for d in system.kb.docs if d["id"] in result["safety"]["source_ids"]])
            with st.expander("Chi tiết phối hợp tác tử"):
                st.dataframe(pd.DataFrame(result["trace"]), hide_index=True, width="stretch")
                st.json(result)
            with st.expander("Xem bản tổng hợp"):
                st.write(result["text"])
            st.download_button("Tải kết quả phiên", json.dumps(result, ensure_ascii=False, indent=2),
                               "diabetes_trace.json", "application/json", icon=":material/download:")

with knowledge_tab:
    st.markdown('<span class="eyebrow">KHÁM PHÁ TRI THỨC</span><h2>Tìm câu trả lời, kết nối khái niệm</h2>', unsafe_allow_html=True)
    query = st.text_input("Bạn muốn tìm hiểu điều gì?", "HbA1c và thiếu máu", placeholder="HbA1c, dinh dưỡng, vận động…")
    evidence_col, graph_col = st.columns([1.1, 1], gap="large")
    with evidence_col:
        hits = system.kb.retrieve(query)
        if hits:
            render_evidence(hits)
        else:
            st.info("Chưa tìm thấy nội dung phù hợp. Thử một chủ đề khác.")
    with graph_col:
        with st.container(border=True):
            st.markdown("#### Bản đồ khái niệm")
            st.image(str(ARTIFACTS / "figures/knowledge_graph.png"), width="stretch")
            with st.expander("Khái niệm và quan hệ"):
                st.dataframe(pd.DataFrame(system.kb.graph["relations"]), hide_index=True, width="stretch")

with benchmark:
    st.markdown('<span class="eyebrow">MODEL INSIGHTS</span><h2>Hiệu năng mô hình, nhìn từ dữ liệu</h2>', unsafe_allow_html=True)
    classification_col, reminder_col = st.columns(2, gap="large")
    with classification_col:
        with st.container(border=True):
            st.markdown("#### So sánh mô hình phân loại")
            measure = st.segmented_control("Chỉ số", ["ROC AUC", "Average Precision", "F1"], default="ROC AUC", required=True)
            column = {"ROC AUC": "roc_auc", "Average Precision": "average_precision", "F1": "f1"}[measure]
            comparison = metrics.assign(model=metrics.model.map(MODEL_NAMES)).set_index("model")
            st.bar_chart(comparison[[column]], color="#367be6", height=260, horizontal=True)
            st.caption("Mô hình mặc định · " + MODEL_NAMES[default_model])
    with reminder_col:
        with st.container(border=True):
            st.markdown("#### Chính sách nhắc nhật ký")
            st.bar_chart(rl_metrics.set_index("policy")[["mean"]], color="#12a698", height=260, horizontal=True)
            st.caption("Reward trung bình mỗi ngày · môi trường mô phỏng")
    with st.expander("Bảng chỉ số đầy đủ & đường cong đánh giá"):
        st.dataframe(metrics.round(4), hide_index=True, width="stretch")
        st.image(str(ARTIFACTS / "figures/classification.png"))
        st.image(str(ARTIFACTS / "figures/rl.png"))
    with st.expander("Quá trình huấn luyện MLP"):
        st.line_chart(history.set_index("epoch")[["train_loss", "validation_loss"]], color=["#367be6", "#12a698"], height=280)

with guide:
    st.markdown('<span class="eyebrow">BẮT ĐẦU TRONG VÀI BƯỚC</span><h2>Từ notebook đến phiên phân tích</h2>', unsafe_allow_html=True)
    for col, title, text in zip(st.columns(3), ["01 · Mở hệ thống", "02 · Chọn kịch bản", "03 · Khám phá kết quả"],
        ["Khởi chạy ứng dụng và mở địa chỉ local bên dưới.", "Dùng hồ sơ mẫu hoặc nhập 21 chỉ báo, chọn tác vụ và đặt câu hỏi.", "Xem dự đoán, tri thức, hành động nhắc việc và tải vết xử lý."]):
        with col:
            with st.container(border=True):
                st.markdown("#### " + title); st.write(text)
    st.code("python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8521", language="powershell")
    st.markdown("Mở **http://127.0.0.1:8521** · Dừng bằng **Ctrl+C**.")
    with st.expander("Notebook & các lệnh tái lập"):
        st.write("01 · Dữ liệu và MLP → 02 · Tri thức và đồ thị → 03 · Q-learning → 04 · Tích hợp hệ đa tác tử")
        st.code("python scripts/run_experiments.py\npython scripts/execute_notebooks.py\npython -m pytest -q", language="powershell")

st.markdown('<div class="app-footer"><strong>DIABETES AGENT</strong><span>PROJECT 01 · PTIT</span><span>Bùi Anh Đức · B23DCCN165</span></div>', unsafe_allow_html=True)

