def run_preset(task):
    questions = {"consult": "HbA1c phản ánh điều gì và cần ghi nhật ký thế nào?",
                 "knowledge": "HbA1c và thiếu máu có liên quan thế nào?", "reminder": "Nhắc tôi ghi nhật ký đường huyết"}
    st.session_state.update(task=task, question=questions[task], profile_mode="Hồ sơ mẫu", use_glucose=False)
    st.session_state.result = system.run(questions[task], sample_profile,
        {"gap_days": st.session_state.gap, "fatigue": st.session_state.fatigue},
        model=st.session_state.model, task=task)
