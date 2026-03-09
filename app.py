import streamlit as st
import json
import os
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

def now_ist():
    """Current datetime in IST (no tzinfo attached, for naive comparisons)."""
    return datetime.now(IST).replace(tzinfo=None)

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ClientTrack",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Persistent storage helpers ────────────────────────────────────────────────
DATA_FILE = "clienttrack_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"clients": [], "followups": []}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)

# ── Session state bootstrap ───────────────────────────────────────────────────
if "data" not in st.session_state:
    st.session_state.data = load_data()
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

data = st.session_state.data

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebar"] { background: #0e1117; }
.ct-logo { font-size:28px; font-weight:800; color:#7c6af7; margin-bottom:2px; }
.ct-sub  { font-size:11px; letter-spacing:3px; color:#555; margin-bottom:18px; }
.stat-row { display:flex; justify-content:space-between; font-size:13px;
            color:#aaa; padding:4px 0; border-bottom:1px solid #1e2130; }
.stat-val  { font-weight:700; color:#e2e8f0; }
.stat-val.red { color:#f87171; }
.stat-val.grn { color:#34d399; }
.fu-card { background:#161b2e; border:1px solid #2a2f45; border-radius:10px;
           padding:14px 16px; margin-bottom:10px; }
.fu-card-header { font-size:13px; font-weight:700; margin-bottom:6px; }
.fu-desc  { font-size:14px; color:#e2e8f0; margin-bottom:4px; }
.fu-meta  { font-size:11px; color:#475569; margin-top:6px; }
.section-title { font-size:22px; font-weight:700; color:#e2e8f0; margin-bottom:16px; }
.cl-card { background:#161b2e; border:1px solid #2a2f45; border-radius:10px;
           padding:14px 16px; margin-bottom:10px; }
.cl-name { font-size:16px; font-weight:700; color:#7c6af7; }
.cl-info { font-size:12px; color:#6b7280; margin-top:4px; }
</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
def now_str():
    return now_ist().strftime("%Y-%m-%d %H:%M")

def _is_overdue(fu):
    try:
        return (fu["status"] == "Pending" and
                datetime.strptime(fu["datetime"], "%Y-%m-%d %H:%M") < now_ist())
    except Exception:
        return False

def _time_options():
    return [f"{h:02d}:{m:02d}" for h in range(24) for m in (0, 30)]

def pending_count():
    now = now_ist()
    return sum(1 for f in data["followups"]
               if f["status"] == "Pending"
               and datetime.strptime(f["datetime"], "%Y-%m-%d %H:%M") >= now)

def overdue_count():
    now = now_ist()
    return sum(1 for f in data["followups"]
               if f["status"] == "Pending"
               and datetime.strptime(f["datetime"], "%Y-%m-%d %H:%M") < now)

def completed_count():
    return sum(1 for f in data["followups"] if f["status"] == "Completed")

def won_count():
    return sum(1 for c in data["clients"] if c.get("stage") == "Won")

# ── Follow-up card renderer (FIXED: no raw HTML shown) ───────────────────────
def render_followup_card(fu, idx):
    status       = fu["status"]
    client       = fu.get("client", "Unknown")
    dt_str       = fu["datetime"]
    desc         = fu.get("description", "")
    reminders    = fu.get("reminders_sent", 0)
    completed_at = fu.get("completed_at", "")

    if status == "Completed":
        icon, hdr_color = "✅", "#34d399"
    elif _is_overdue(fu):
        icon, hdr_color = "🚨", "#f87171"
    else:
        icon, hdr_color = "⏳", "#a78bfa"

    meta_parts = [f"Status: {status}", f"Reminders sent: {reminders}"]
    if completed_at:
        meta_parts.append(f"Completed: {completed_at}")
    meta_html = " &nbsp;|&nbsp; ".join(meta_parts)

    desc_html = (desc if desc
                 else '<em style="color:#475569;">No description</em>')

    col_card, col_actions = st.columns([3, 1])

    with col_card:
        # ✅ FIX: build the full HTML string first, then pass once to st.markdown
        card_html = f"""
        <div class="fu-card">
            <div class="fu-card-header" style="color:{hdr_color};">
                {icon} &nbsp;<strong>{client}</strong> · {dt_str}
            </div>
            <div class="fu-desc">{desc_html}</div>
            <div class="fu-meta">{meta_html}</div>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)

    with col_actions:
        st.write("")
        if status != "Completed":
            if st.button("✅ Done", key=f"done_{idx}", type="primary",
                         use_container_width=True):
                data["followups"][idx]["status"] = "Completed"
                data["followups"][idx]["completed_at"] = now_str()
                save_data(data)
                st.rerun()

        if st.button("🗑️", key=f"del_{idx}", use_container_width=True):
            data["followups"].pop(idx)
            save_data(data)
            st.rerun()

        if status != "Completed":
            with st.expander("▶ 📅 Reschedule"):
                new_date = st.date_input("New date", key=f"rdate_{idx}",
                                         value=date.today() + timedelta(days=1))
                time_opts = _time_options()
                new_time = st.selectbox("New time", options=time_opts,
                                        key=f"rtime_{idx}")
                if st.button("Confirm", key=f"rconf_{idx}"):
                    data["followups"][idx]["datetime"] = f"{new_date} {new_time}"
                    save_data(data)
                    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown('<div class="ct-logo">◈ ClientTrack</div>', unsafe_allow_html=True)
    st.markdown('<div class="ct-sub">FOLLOW-UP MANAGER</div>', unsafe_allow_html=True)

    nav_items = [("📊", "Dashboard"), ("👥", "Client Pipeline"),
                 ("➕", "Add Client"), ("🔔", "Follow-Ups")]
    for icon, pg in nav_items:
        btn_type = "primary" if st.session_state.page == pg else "secondary"
        if st.button(f"{icon}  {pg}", key=f"nav_{pg}",
                     use_container_width=True, type=btn_type):
            st.session_state.page = pg
            st.rerun()

    st.markdown("---")
    st.markdown("**QUICK STATS**")

    pc  = pending_count() + overdue_count()
    wc  = won_count()
    tot = len(data["clients"])
    red = "red" if pc > 0 else ""

    st.markdown(f"""
    <div class="stat-row">
        <span>Total Clients</span><span class="stat-val">{tot}</span>
    </div>
    <div class="stat-row">
        <span>Pending Tasks</span><span class="stat-val {red}">{pc}</span>
    </div>
    <div class="stat-row">
        <span>Won</span><span class="stat-val grn">{wc}</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        f"<div style='font-size:10px;color:#374151;margin-top:8px;'>"
        f"{now_ist().strftime('%A, %d %b %Y %H:%M')}</div>",
        unsafe_allow_html=True,
    )

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Dashboard
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.page == "Dashboard":
    st.markdown('<div class="section-title">📊 Dashboard</div>',
                unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Clients", len(data["clients"]))
    c2.metric("Pending",       pending_count())
    c3.metric("Overdue",       overdue_count())
    c4.metric("Completed",     completed_count())

    st.markdown("---")
    now = now_ist()

    st.markdown("### Upcoming Follow-Ups")
    upcoming = sorted(
        [f for f in data["followups"]
         if f["status"] == "Pending"
         and datetime.strptime(f["datetime"], "%Y-%m-%d %H:%M") >= now],
        key=lambda x: x["datetime"],
    )
    if not upcoming:
        st.info("No upcoming follow-ups. Schedule one in the Follow-Ups section!")
    else:
        for fu in upcoming[:5]:
            render_followup_card(fu, data["followups"].index(fu))

    st.markdown("### Overdue")
    overdue = [f for f in data["followups"]
               if f["status"] == "Pending"
               and datetime.strptime(f["datetime"], "%Y-%m-%d %H:%M") < now]
    if overdue:
        for fu in overdue:
            render_followup_card(fu, data["followups"].index(fu))
    else:
        st.success("No overdue follow-ups! 🎉")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Client Pipeline
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "Client Pipeline":
    st.markdown('<div class="section-title">👥 Client Pipeline</div>',
                unsafe_allow_html=True)

    stages = ["Lead", "Contacted", "Proposal", "Negotiation", "Won", "Lost"]
    sel_stage = st.selectbox("Filter by stage", ["All"] + stages)

    clients_to_show = (data["clients"] if sel_stage == "All"
                       else [c for c in data["clients"] if c.get("stage") == sel_stage])

    if not clients_to_show:
        st.info("No clients found. Add one via the 'Add Client' page.")
    else:
        for client in clients_to_show:
            orig_idx = data["clients"].index(client)
            col_card, col_act = st.columns([4, 1])
            with col_card:
                stage_color = {"Won": "#34d399", "Lost": "#f87171"}.get(
                    client.get("stage", ""), "#7c6af7")
                notes_html = (
                    f'<div class="cl-info" style="margin-top:6px;">📝 {client["notes"]}</div>'
                    if client.get("notes") else ""
                )
                st.markdown(f"""
                <div class="cl-card">
                    <div class="cl-name">{client['name']}</div>
                    <div class="cl-info">📧 {client.get('email','')} &nbsp; 📞 {client.get('phone','')}</div>
                    <div class="cl-info">🏢 {client.get('company','')}</div>
                    <span style="display:inline-block;font-size:11px;padding:2px 8px;
                                 border-radius:12px;background:#1a1f35;color:{stage_color};
                                 margin-top:6px;">{client.get('stage','Lead')}</span>
                    {notes_html}
                </div>
                """, unsafe_allow_html=True)
            with col_act:
                st.write("")
                new_stage = st.selectbox("Stage", stages,
                                         index=stages.index(client.get("stage", "Lead")),
                                         key=f"stage_{orig_idx}")
                if st.button("Update", key=f"upd_{orig_idx}", use_container_width=True):
                    data["clients"][orig_idx]["stage"] = new_stage
                    save_data(data)
                    st.rerun()
                if st.button("🗑️ Remove", key=f"remc_{orig_idx}", use_container_width=True):
                    data["clients"].pop(orig_idx)
                    save_data(data)
                    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Add Client
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "Add Client":
    st.markdown('<div class="section-title">➕ Add New Client</div>',
                unsafe_allow_html=True)

    with st.form("add_client_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name    = st.text_input("Full Name *")
            email   = st.text_input("Email")
            company = st.text_input("Company")
        with col2:
            phone = st.text_input("Phone")
            stage = st.selectbox("Pipeline Stage",
                                 ["Lead", "Contacted", "Proposal",
                                  "Negotiation", "Won", "Lost"])
        notes = st.text_area("Notes")

        if st.form_submit_button("Add Client", type="primary"):
            if not name.strip():
                st.error("Name is required.")
            else:
                data["clients"].append({
                    "name":       name.strip(),
                    "email":      email.strip(),
                    "phone":      phone.strip(),
                    "company":    company.strip(),
                    "stage":      stage,
                    "notes":      notes.strip(),
                    "created_at": now_str(),
                })
                save_data(data)
                st.success(f"✅ Client '{name}' added successfully!")
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Follow-Ups
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "Follow-Ups":
    st.markdown('<div class="section-title">🔔 Follow-Ups</div>',
                unsafe_allow_html=True)

    with st.expander("➕ Schedule a New Follow-Up", expanded=True):
        client_names = [c["name"] for c in data["clients"]]
        if not client_names:
            st.warning("Add a client first before scheduling follow-ups.")
        else:
            sel_client  = st.selectbox("Client", client_names)
            description = st.text_area("Description / Notes")
            col_d, col_t = st.columns(2)
            with col_d:
                fu_date = st.date_input("Date", value=date.today())
            with col_t:
                time_opts = _time_options()
                fu_time   = st.selectbox(
                    "Time", options=time_opts,
                    index=time_opts.index("09:00") if "09:00" in time_opts else 0,
                )

            if st.button("Schedule", type="primary"):
                dt_str = f"{fu_date} {fu_time}"
                data["followups"].append({
                    "client":          sel_client,
                    "description":     description.strip(),
                    "datetime":        dt_str,
                    "status":          "Pending",
                    "reminders_sent":  0,
                    "created_at":      now_str(),
                })
                save_data(data)
                st.success(f"✅ Follow-up scheduled for {sel_client} on {dt_str}")
                st.rerun()

    st.markdown("---")

    now = now_ist()

    pending_fus   = [(i, f) for i, f in enumerate(data["followups"])
                     if f["status"] == "Pending"
                     and datetime.strptime(f["datetime"], "%Y-%m-%d %H:%M") >= now]
    overdue_fus   = [(i, f) for i, f in enumerate(data["followups"])
                     if f["status"] == "Pending"
                     and datetime.strptime(f["datetime"], "%Y-%m-%d %H:%M") < now]
    completed_fus = [(i, f) for i, f in enumerate(data["followups"])
                     if f["status"] == "Completed"]

    tab_p, tab_o, tab_c = st.tabs([
        f"⏳ Pending ({len(pending_fus)})",
        f"🚨 Overdue ({len(overdue_fus)})",
        f"✅ Completed ({len(completed_fus)})",
    ])

    with tab_p:
        if not pending_fus:
            st.info("No pending follow-ups.")
        else:
            for idx, fu in pending_fus:
                render_followup_card(fu, idx)

    with tab_o:
        if not overdue_fus:
            st.success("No overdue follow-ups! 🎉")
        else:
            for idx, fu in overdue_fus:
                render_followup_card(fu, idx)

    with tab_c:
        if not completed_fus:
            st.info("No completed follow-ups yet.")
        else:
            for idx, fu in completed_fus:
                render_followup_card(fu, idx)
