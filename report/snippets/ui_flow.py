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
