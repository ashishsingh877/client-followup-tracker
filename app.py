"""
Client Follow-Up Tracker  ·  Streamlit + SQLite
Run:  streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import database as db

# ─── PAGE CONFIG ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Client Follow-Up Tracker",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

db.init_db()

# ─── CONSTANTS ──────────────────────────────────────────────────────────────
ENGAGEMENT_STAGES = [
    "Lead Identified",
    "Pre-Scoping Questionnaire Sent",
    "Approach Note Shared",
    "Proposal Sent",
    "Negotiation",
    "Won",
    "Lost",
]

CLIENT_STATUSES   = ["Active", "On Hold", "Closed", "Prospect"]
ENGAGEMENT_TYPES  = [
    "Advisory", "Audit", "Consulting", "Tax", "Legal",
    "Financial Planning", "Technology", "Other"
]

STAGE_COLORS = {
    "Lead Identified":                    "#64748b",
    "Pre-Scoping Questionnaire Sent":     "#3b82f6",
    "Approach Note Shared":               "#8b5cf6",
    "Proposal Sent":                      "#f59e0b",
    "Negotiation":                        "#ef4444",
    "Won":                                "#10b981",
    "Lost":                               "#6b7280",
}

# ─── GLOBAL CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&family=Playfair+Display:wght@700&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* ── DARK BACKGROUND ── */
.stApp {
    background: #0d1117;
    color: #e2e8f0;
}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f1923 0%, #0d1117 100%);
    border-right: 1px solid #1e2d3d;
}
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stRadio label {
    color: #94a3b8 !important;
}

/* ── METRIC CARDS ── */
.metric-card {
    background: linear-gradient(135deg, #141e2e 0%, #1a2540 100%);
    border: 1px solid #1e3a5f;
    border-radius: 16px;
    padding: 24px 28px;
    margin-bottom: 4px;
    position: relative;
    overflow: hidden;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(59,130,246,0.15);
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: var(--accent, #3b82f6);
    border-radius: 16px 16px 0 0;
}
.metric-label {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: #64748b;
    margin-bottom: 8px;
}
.metric-value {
    font-size: 36px;
    font-weight: 700;
    color: #f1f5f9;
    line-height: 1;
    font-family: 'DM Mono', monospace;
}
.metric-sub {
    font-size: 12px;
    color: #475569;
    margin-top: 6px;
}

/* ── PAGE TITLE ── */
.page-title {
    font-family: 'Playfair Display', serif;
    font-size: 32px;
    font-weight: 700;
    color: #f1f5f9;
    margin-bottom: 4px;
}
.page-subtitle {
    font-size: 14px;
    color: #64748b;
    margin-bottom: 32px;
}

/* ── REMINDER POPUP ── */
.reminder-box {
    background: linear-gradient(135deg, #1c1a2e, #221a38);
    border: 2px solid #7c3aed;
    border-radius: 16px;
    padding: 24px 28px;
    margin-bottom: 20px;
    box-shadow: 0 0 40px rgba(124,58,237,0.3);
    animation: pulse-glow 2s infinite;
}
@keyframes pulse-glow {
    0%, 100% { box-shadow: 0 0 20px rgba(124,58,237,0.2); }
    50%       { box-shadow: 0 0 40px rgba(124,58,237,0.5); }
}
.reminder-title {
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #a78bfa;
    margin-bottom: 8px;
}
.reminder-client {
    font-size: 22px;
    font-weight: 600;
    color: #f1f5f9;
    margin-bottom: 6px;
}
.reminder-task {
    font-size: 15px;
    color: #cbd5e1;
    margin-bottom: 16px;
    padding: 12px 16px;
    background: rgba(255,255,255,0.04);
    border-radius: 8px;
    border-left: 3px solid #7c3aed;
}
.reminder-time {
    font-size: 12px;
    color: #94a3b8;
    font-family: 'DM Mono', monospace;
}

/* ── STAGE BADGE ── */
.stage-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.5px;
}

/* ── CLIENT CARD ── */
.client-row {
    background: #141e2e;
    border: 1px solid #1e3a5f;
    border-radius: 12px;
    padding: 18px 22px;
    margin-bottom: 10px;
    transition: border-color 0.2s, background 0.2s;
    cursor: pointer;
}
.client-row:hover {
    border-color: #3b82f6;
    background: #172034;
}

/* ── INPUTS ── */
.stTextInput input, .stTextArea textarea, .stSelectbox select {
    background: #141e2e !important;
    border: 1px solid #1e3a5f !important;
    color: #e2e8f0 !important;
    border-radius: 8px !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.15) !important;
}

/* ── BUTTONS ── */
.stButton button {
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: 0.3px !important;
    border-radius: 8px !important;
    transition: all 0.2s !important;
}
.stButton button:hover {
    transform: translateY(-1px) !important;
}

/* ── SECTION HEADER ── */
.section-header {
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #3b82f6;
    padding-bottom: 10px;
    border-bottom: 1px solid #1e3a5f;
    margin-bottom: 20px;
    margin-top: 10px;
}

/* ── TABLE ── */
.stDataFrame { border-radius: 12px; overflow: hidden; }

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {
    background: #141e2e;
    border-radius: 10px;
    padding: 4px;
    gap: 2px;
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    color: #64748b;
    border-radius: 8px;
    font-weight: 500;
}
.stTabs [aria-selected="true"] {
    background: #1e3a5f !important;
    color: #60a5fa !important;
}

/* ── DIVIDER ── */
hr { border-color: #1e3a5f; }

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0d1117; }
::-webkit-scrollbar-thumb { background: #1e3a5f; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #2d4a6e; }
</style>
""", unsafe_allow_html=True)


# ─── SESSION STATE ───────────────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"
if "selected_client_id" not in st.session_state:
    st.session_state.selected_client_id = None
if "dismissed_reminders" not in st.session_state:
    st.session_state.dismissed_reminders = set()
if "edit_client_id" not in st.session_state:
    st.session_state.edit_client_id = None


def nav_to(page, client_id=None):
    st.session_state.page = page
    if client_id is not None:
        st.session_state.selected_client_id = client_id
    st.rerun()


# ─── SIDEBAR ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
        <div style='padding: 20px 0 24px; text-align:center;'>
            <div style='font-family: Playfair Display, serif; font-size:22px;
                        font-weight:700; color:#60a5fa; letter-spacing:1px;'>
                ◈ ClientTrack
            </div>
            <div style='font-size:11px; color:#475569; margin-top:4px;
                        letter-spacing:2px; text-transform:uppercase;'>
                Follow-Up Manager
            </div>
        </div>
    """, unsafe_allow_html=True)

    pages = {
        "Dashboard":         "📊",
        "Client Pipeline":   "👥",
        "Add Client":        "➕",
        "Follow-Ups":        "🔔",
    }

    for pg, icon in pages.items():
        is_active = st.session_state.page == pg
        style = (
            "background:#1e3a5f; color:#60a5fa; border-left:3px solid #3b82f6;"
            if is_active else
            "color:#94a3b8;"
        )
        if st.button(
            f"{icon}  {pg}",
            key=f"nav_{pg}",
            use_container_width=True,
            type="secondary",
        ):
            nav_to(pg)

    # ── Quick stats in sidebar ──
    st.markdown("<hr style='border-color:#1e2d3d; margin:20px 0;'>", unsafe_allow_html=True)
    stats = db.get_dashboard_stats()
    st.markdown(f"""
        <div style='padding:0 8px;'>
            <div style='font-size:11px; color:#475569; letter-spacing:1.5px;
                        text-transform:uppercase; margin-bottom:12px;'>Quick Stats</div>
            <div style='display:flex; justify-content:space-between; margin-bottom:8px;'>
                <span style='font-size:13px; color:#64748b;'>Total Clients</span>
                <span style='font-size:13px; font-weight:700; color:#e2e8f0;
                             font-family:DM Mono,monospace;'>{stats['total_clients']}</span>
            </div>
            <div style='display:flex; justify-content:space-between; margin-bottom:8px;'>
                <span style='font-size:13px; color:#64748b;'>Pending Tasks</span>
                <span style='font-size:13px; font-weight:700;
                             color:{"#ef4444" if stats["pending_followups"]>0 else "#10b981"};
                             font-family:DM Mono,monospace;'>{stats['pending_followups']}</span>
            </div>
            <div style='display:flex; justify-content:space-between;'>
                <span style='font-size:13px; color:#64748b;'>Won</span>
                <span style='font-size:13px; font-weight:700; color:#10b981;
                             font-family:DM Mono,monospace;'>{stats['won_clients']}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div style='position:absolute; bottom:20px; left:20px; right:20px;
                    font-size:10px; color:#334155; text-align:center;'>
            {datetime.now().strftime('%A, %d %b %Y  %H:%M')}
        </div>
    """, unsafe_allow_html=True)


# ─── REMINDER POPUPS (checked on every page load) ────────────────────────────
def show_reminders():
    due = db.get_due_followups()
    pending = [r for r in due if r["followup_id"] not in st.session_state.dismissed_reminders]

    for reminder in pending:
        fid = reminder["followup_id"]
        db.mark_followup_shown(fid)

        with st.container():
            st.markdown(f"""
                <div class='reminder-box'>
                    <div class='reminder-title'>⏰ Action Required · Follow-Up Reminder</div>
                    <div class='reminder-client'>📁 {reminder['client_name']}</div>
                    <div class='reminder-task'>{reminder['task_description']}</div>
                    <div class='reminder-time'>
                        Scheduled: {reminder['followup_datetime']} &nbsp;|&nbsp;
                        Reminded {reminder['reminder_count']} time(s)
                    </div>
                </div>
            """, unsafe_allow_html=True)

            c1, c2, c3 = st.columns([1, 1, 4])
            with c1:
                if st.button("✅ Yes, Done!", key=f"done_{fid}", type="primary"):
                    db.complete_followup(fid)
                    st.session_state.dismissed_reminders.add(fid)
                    st.success(f"✓ Task completed for {reminder['client_name']}!")
                    st.rerun()
            with c2:
                if st.button("⏳ Snooze 1h", key=f"snooze_{fid}"):
                    st.session_state.dismissed_reminders.add(fid)
                    st.info("Reminder snoozed for 1 hour.")
                    st.rerun()
            with c3:
                if st.button("✕ Dismiss", key=f"dismiss_{fid}"):
                    st.session_state.dismissed_reminders.add(fid)
                    st.rerun()

        st.markdown("---")


# ─── HELPERS ─────────────────────────────────────────────────────────────────
def stage_badge(stage):
    color = STAGE_COLORS.get(stage, "#64748b")
    return f"""<span style='background:{color}22; color:{color};
        border:1px solid {color}55; padding:3px 10px;
        border-radius:20px; font-size:11px; font-weight:600;'>{stage}</span>"""


def status_badge(status):
    colors = {"Active": "#10b981", "On Hold": "#f59e0b",
               "Closed": "#64748b", "Prospect": "#3b82f6"}
    c = colors.get(status, "#64748b")
    return f"""<span style='background:{c}22; color:{c}; border:1px solid {c}55;
        padding:3px 10px; border-radius:20px; font-size:11px; font-weight:600;'>{status}</span>"""


def fmt_date(d):
    return d if d else "—"


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
def page_dashboard():
    show_reminders()

    st.markdown("<div class='page-title'>Dashboard</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-subtitle'>Your client engagement pipeline at a glance</div>",
                unsafe_allow_html=True)

    stats = db.get_dashboard_stats()

    # ── Metric cards ──
    c1, c2, c3, c4, c5 = st.columns(5)
    cards = [
        (c1, "Total Clients",    stats["total_clients"],     "#3b82f6", "All time"),
        (c2, "Active",           stats["active_clients"],    "#10b981", "Currently engaged"),
        (c3, "Pending Tasks",    stats["pending_followups"], "#f59e0b", "Awaiting action"),
        (c4, "Overdue",          stats["overdue_followups"], "#ef4444", "Past due date"),
        (c5, "Won",              stats["won_clients"],       "#a78bfa", "Closed successfully"),
    ]
    for col, label, val, accent, sub in cards:
        with col:
            st.markdown(f"""
                <div class='metric-card' style='--accent:{accent}'>
                    <div class='metric-label'>{label}</div>
                    <div class='metric-value'>{val}</div>
                    <div class='metric-sub'>{sub}</div>
                </div>
            """, unsafe_allow_html=True)

    fee_fmt = f"₹{stats['total_fees']:,.0f}" if stats['total_fees'] else "—"
    st.markdown(f"""
        <div style='background: linear-gradient(90deg,#0f2744,#162040);
                    border:1px solid #1e3a5f; border-radius:12px; padding:16px 24px;
                    margin:12px 0 28px; display:flex; align-items:center; gap:16px;'>
            <span style='font-size:22px;'>💼</span>
            <span style='color:#94a3b8; font-size:14px;'>Total Pipeline Value (Active Clients):</span>
            <span style='font-size:22px; font-weight:700; color:#60a5fa;
                         font-family:DM Mono,monospace;'>{fee_fmt}</span>
        </div>
    """, unsafe_allow_html=True)

    # ── Charts ──
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown("<div class='section-header'>Pipeline Stage Distribution</div>",
                    unsafe_allow_html=True)
        if stats["stage_distribution"]:
            df_stage = pd.DataFrame(stats["stage_distribution"])
            colors = [STAGE_COLORS.get(s, "#64748b") for s in df_stage["engagement_stage"]]
            fig = px.bar(
                df_stage, x="engagement_stage", y="cnt",
                color="engagement_stage",
                color_discrete_sequence=colors,
                labels={"cnt": "Clients", "engagement_stage": "Stage"},
            )
            fig.update_layout(
                plot_bgcolor="#141e2e", paper_bgcolor="#141e2e",
                font_color="#94a3b8", showlegend=False,
                margin=dict(l=0, r=0, t=10, b=0),
                xaxis=dict(showgrid=False, tickfont=dict(size=10)),
                yaxis=dict(gridcolor="#1e3a5f", tickfont=dict(size=11)),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No client data yet.")

    with col_right:
        st.markdown("<div class='section-header'>Status Breakdown</div>",
                    unsafe_allow_html=True)
        clients = db.get_all_clients()
        if clients:
            status_counts = {}
            for c in clients:
                s = c.get("client_status", "Unknown")
                status_counts[s] = status_counts.get(s, 0) + 1
            df_status = pd.DataFrame(list(status_counts.items()),
                                     columns=["Status", "Count"])
            fig2 = px.pie(
                df_status, names="Status", values="Count",
                color_discrete_sequence=["#3b82f6", "#10b981", "#f59e0b", "#64748b"],
                hole=0.6,
            )
            fig2.update_layout(
                plot_bgcolor="#141e2e", paper_bgcolor="#141e2e",
                font_color="#94a3b8", showlegend=True,
                legend=dict(font=dict(size=12, color="#94a3b8")),
                margin=dict(l=0, r=0, t=10, b=0),
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No clients yet.")

    # ── Upcoming follow-ups ──
    st.markdown("<div class='section-header'>Upcoming Follow-Ups (Next 7 Days)</div>",
                unsafe_allow_html=True)
    all_fu = db.get_followups()
    now = datetime.now()
    upcoming = [
        f for f in all_fu
        if f["status"] == "Pending"
        and now <= datetime.strptime(f["followup_datetime"], "%Y-%m-%d %H:%M")
                   <= now + timedelta(days=7)
    ]

    if upcoming:
        for fu in upcoming[:5]:
            due_dt = datetime.strptime(fu["followup_datetime"], "%Y-%m-%d %H:%M")
            delta  = due_dt - now
            hrs    = int(delta.total_seconds() / 3600)
            urgency_color = "#ef4444" if hrs < 2 else "#f59e0b" if hrs < 24 else "#3b82f6"
            st.markdown(f"""
                <div style='background:#141e2e; border:1px solid #1e3a5f; border-radius:10px;
                            padding:14px 18px; margin-bottom:8px; display:flex;
                            align-items:center; gap:16px;'>
                    <div style='width:48px; height:48px; border-radius:50%;
                                background:{urgency_color}22; border:2px solid {urgency_color};
                                display:flex; align-items:center; justify-content:center;
                                font-size:18px; flex-shrink:0;'>🔔</div>
                    <div style='flex:1;'>
                        <div style='font-weight:600; color:#e2e8f0; font-size:14px;'>
                            {fu['client_name']}</div>
                        <div style='font-size:12px; color:#94a3b8; margin-top:2px;'>
                            {fu['task_description'][:80]}{'...' if len(fu['task_description'])>80 else ''}</div>
                    </div>
                    <div style='text-align:right;'>
                        <div style='font-family:DM Mono,monospace; font-size:12px; color:{urgency_color};'>
                            {fu['followup_datetime']}</div>
                        <div style='font-size:11px; color:#475569; margin-top:2px;'>
                            in {hrs}h</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div style='background:#141e2e; border:1px solid #1e3a5f; border-radius:10px;
                        padding:20px; text-align:center; color:#475569;'>
                ✓ No follow-ups in the next 7 days
            </div>
        """, unsafe_allow_html=True)

    # ── Recent clients ──
    st.markdown("<div class='section-header'>Recent Clients</div>",
                unsafe_allow_html=True)
    recent = db.get_all_clients()[:5]
    if recent:
        for cl in recent:
            col_n, col_t, col_s, col_st, col_btn = st.columns([3, 2, 2, 2, 1])
            with col_n:
                st.markdown(f"**{cl['client_name']}**")
                st.caption(cl.get("email") or "—")
            with col_t:
                st.write(cl.get("engagement_type") or "—")
            with col_s:
                st.markdown(stage_badge(cl.get("engagement_stage", "—")),
                            unsafe_allow_html=True)
            with col_st:
                st.markdown(status_badge(cl.get("client_status", "—")),
                            unsafe_allow_html=True)
            with col_btn:
                if st.button("View", key=f"dash_view_{cl['client_id']}"):
                    nav_to("Client Detail", cl["client_id"])
    else:
        st.info("No clients yet. Add your first client!")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: CLIENT PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════
def page_pipeline():
    show_reminders()

    st.markdown("<div class='page-title'>Client Pipeline</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-subtitle'>All potential clients and their engagement status</div>",
                unsafe_allow_html=True)

    # ── Search & Filter ──
    col_s, col_f1, col_f2, col_add = st.columns([3, 2, 2, 1])
    with col_s:
        search = st.text_input("🔍  Search by name, email or phone", placeholder="Type to search…")
    with col_f1:
        filter_stage = st.selectbox("Filter Stage", ["All"] + ENGAGEMENT_STAGES)
    with col_f2:
        filter_status = st.selectbox("Filter Status", ["All"] + CLIENT_STATUSES)
    with col_add:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("＋ Add Client", use_container_width=True, type="primary"):
            nav_to("Add Client")

    # ── Fetch data ──
    if search:
        clients = db.search_clients(search)
    else:
        clients = db.get_all_clients()

    if filter_stage != "All":
        clients = [c for c in clients if c.get("engagement_stage") == filter_stage]
    if filter_status != "All":
        clients = [c for c in clients if c.get("client_status") == filter_status]

    st.markdown(f"<div style='font-size:13px; color:#475569; margin-bottom:16px;'>"
                f"Showing {len(clients)} client(s)</div>", unsafe_allow_html=True)

    if not clients:
        st.markdown("""
            <div style='background:#141e2e; border:1px dashed #1e3a5f; border-radius:12px;
                        padding:40px; text-align:center; color:#475569;'>
                <div style='font-size:32px; margin-bottom:12px;'>👥</div>
                <div style='font-size:16px;'>No clients found</div>
                <div style='font-size:13px; margin-top:6px;'>Try a different search or add a new client</div>
            </div>
        """, unsafe_allow_html=True)
        return

    # ── Column headers ──
    st.markdown("""
        <div style='display:grid; grid-template-columns:2fr 1.5fr 1fr 1.5fr 2fr 1.2fr 1.2fr 1.2fr 0.8fr;
                    padding:8px 18px; font-size:10px; font-weight:700; letter-spacing:1.5px;
                    text-transform:uppercase; color:#475569; margin-bottom:4px;
                    border-bottom:1px solid #1e2d3d;'>
            <span>Client</span><span>Engagement Type</span><span>Fee</span>
            <span>Stage</span><span>Status</span>
            <span>Pre-Scope</span><span>Approach</span><span>Proposal</span>
            <span>Actions</span>
        </div>
    """, unsafe_allow_html=True)

    for cl in clients:
        cid = cl["client_id"]
        c1, c2, c3, c4, c5, c6, c7, c8, c9 = st.columns([2, 1.5, 1, 1.5, 2, 1.2, 1.2, 1.2, 0.8])

        with c1:
            st.markdown(f"**{cl['client_name']}**")
            st.caption(cl.get("email") or cl.get("phone") or "—")
        with c2:
            st.write(cl.get("engagement_type") or "—")
        with c3:
            fee = cl.get("estimated_fee")
            st.write(f"₹{fee:,.0f}" if fee else "—")
        with c4:
            st.markdown(stage_badge(cl.get("engagement_stage", "—")),
                        unsafe_allow_html=True)
        with c5:
            st.markdown(status_badge(cl.get("client_status", "—")),
                        unsafe_allow_html=True)
        with c6:
            st.caption(fmt_date(cl.get("questionnaire_sent_date")))
        with c7:
            st.caption(fmt_date(cl.get("approach_note_sent_date")))
        with c8:
            st.caption(fmt_date(cl.get("proposal_sent_date")))
        with c9:
            if st.button("→", key=f"view_{cid}", help="View Details"):
                nav_to("Client Detail", cid)

        st.markdown("<hr style='border-color:#1a2535; margin:4px 0;'>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: ADD / EDIT CLIENT
# ═══════════════════════════════════════════════════════════════════════════════
def page_add_client():
    is_edit = st.session_state.edit_client_id is not None
    existing = db.get_client(st.session_state.edit_client_id) if is_edit else None

    title = f"Edit Client — {existing['client_name']}" if is_edit else "Add New Client"
    st.markdown(f"<div class='page-title'>{title}</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='page-subtitle'>Fill in the client details below</div>",
        unsafe_allow_html=True,
    )

    def v(key, default=""):
        return existing.get(key, default) if existing else default

    with st.form("client_form", clear_on_submit=False):
        st.markdown("<div class='section-header'>Basic Information</div>",
                    unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            name  = st.text_input("Client Name *", value=v("client_name"))
            email = st.text_input("Email", value=v("email"))
            phone = st.text_input("Phone", value=v("phone"))
        with col2:
            eng_type = st.selectbox("Engagement Type",
                                     ENGAGEMENT_TYPES,
                                     index=ENGAGEMENT_TYPES.index(v("engagement_type"))
                                     if v("engagement_type") in ENGAGEMENT_TYPES else 0)
            fee      = st.number_input("Estimated Fee (₹)",
                                        min_value=0.0, step=1000.0,
                                        value=float(v("estimated_fee") or 0))
            status   = st.selectbox("Client Status",
                                     CLIENT_STATUSES,
                                     index=CLIENT_STATUSES.index(v("client_status"))
                                     if v("client_status") in CLIENT_STATUSES else 0)
            stage    = st.selectbox("Engagement Stage",
                                     ENGAGEMENT_STAGES,
                                     index=ENGAGEMENT_STAGES.index(v("engagement_stage"))
                                     if v("engagement_stage") in ENGAGEMENT_STAGES else 0)

        st.markdown("<div class='section-header'>Key Dates</div>",
                    unsafe_allow_html=True)
        dc1, dc2, dc3 = st.columns(3)
        with dc1:
            q_date = st.date_input("Pre-Scoping Questionnaire Sent",
                                    value=_parse_date(v("questionnaire_sent_date")),
                                    key="q_date")
        with dc2:
            a_date = st.date_input("Approach Note Sent",
                                    value=_parse_date(v("approach_note_sent_date")),
                                    key="a_date")
        with dc3:
            p_date = st.date_input("Proposal Sent",
                                    value=_parse_date(v("proposal_sent_date")),
                                    key="p_date")

        st.markdown("<div class='section-header'>Notes</div>",
                    unsafe_allow_html=True)
        cn1, cn2 = st.columns(2)
        with cn1:
            curr_notes = st.text_area("Current Stage Notes", value=v("current_stage_notes"),
                                       height=120)
        with cn2:
            next_notes = st.text_area("Next Step Notes", value=v("next_step_notes"),
                                       height=120)

        st.markdown("<br>", unsafe_allow_html=True)
        b1, b2, _ = st.columns([1, 1, 4])
        with b1:
            submitted = st.form_submit_button(
                "💾  Save Client" if is_edit else "➕  Add Client",
                type="primary", use_container_width=True
            )
        with b2:
            cancelled = st.form_submit_button("Cancel", use_container_width=True)

    if submitted:
        if not name.strip():
            st.error("Client Name is required.")
            return
        q_str = q_date.strftime("%Y-%m-%d") if q_date else None
        a_str = a_date.strftime("%Y-%m-%d") if a_date else None
        p_str = p_date.strftime("%Y-%m-%d") if p_date else None

        if is_edit:
            db.update_client(existing["client_id"], name, email, phone,
                              eng_type, fee, status, stage)
            db.update_engagement_dates(existing["client_id"], q_str, a_str, p_str)
            db.update_notes(existing["client_id"], curr_notes, next_notes)
            st.success(f"✓ Client '{name}' updated successfully!")
            st.session_state.edit_client_id = None
        else:
            cid = db.add_client(name, email, phone, eng_type, fee, status, stage)
            db.update_engagement_dates(cid, q_str, a_str, p_str)
            db.update_notes(cid, curr_notes, next_notes)
            st.success(f"✓ Client '{name}' added successfully!")

        import time; time.sleep(0.8)
        nav_to("Client Pipeline")

    if cancelled:
        st.session_state.edit_client_id = None
        nav_to("Client Pipeline")


def _parse_date(val):
    if not val:
        return None
    try:
        return datetime.strptime(val, "%Y-%m-%d").date()
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: CLIENT DETAIL
# ═══════════════════════════════════════════════════════════════════════════════
def page_client_detail():
    show_reminders()

    cid = st.session_state.selected_client_id
    if not cid:
        st.error("No client selected.")
        return

    cl = db.get_client(cid)
    if not cl:
        st.error("Client not found.")
        return

    # ── Back button ──
    if st.button("← Back to Pipeline"):
        nav_to("Client Pipeline")

    st.markdown(f"<div class='page-title'>{cl['client_name']}</div>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='page-subtitle'>"
        f"{stage_badge(cl.get('engagement_stage','—'))} &nbsp; "
        f"{status_badge(cl.get('client_status','—'))}"
        f"</div>",
        unsafe_allow_html=True,
    )

    col_act1, col_act2, _ = st.columns([1, 1, 6])
    with col_act1:
        if st.button("✏️  Edit Client", type="primary"):
            st.session_state.edit_client_id = cid
            nav_to("Add Client")
    with col_act2:
        if st.button("🗑️  Delete", type="secondary"):
            db.delete_client(cid)
            st.success("Client deleted.")
            import time; time.sleep(0.5)
            nav_to("Client Pipeline")

    st.markdown("<br>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["📋 Overview", "📅 Timeline & Notes", "🔔 Follow-Ups"])

    # ── TAB 1: Overview ──
    with tab1:
        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown("<div class='section-header'>Contact Information</div>",
                        unsafe_allow_html=True)
            _detail_row("📧 Email",   cl.get("email") or "—")
            _detail_row("📱 Phone",   cl.get("phone") or "—")
            _detail_row("📅 Added",   cl.get("created_date", "—")[:10])

        with col_r:
            st.markdown("<div class='section-header'>Engagement Details</div>",
                        unsafe_allow_html=True)
            _detail_row("Type",       cl.get("engagement_type") or "—")
            fee = cl.get("estimated_fee")
            _detail_row("Est. Fee",   f"₹{fee:,.0f}" if fee else "—")
            _detail_row("Stage",      cl.get("engagement_stage") or "—")
            _detail_row("Status",     cl.get("client_status") or "—")

    # ── TAB 2: Timeline ──
    with tab2:
        st.markdown("<div class='section-header'>Engagement Timeline</div>",
                    unsafe_allow_html=True)

        milestones = [
            ("📋 Pre-Scoping Questionnaire", cl.get("questionnaire_sent_date")),
            ("📝 Approach Note",             cl.get("approach_note_sent_date")),
            ("📄 Proposal",                  cl.get("proposal_sent_date")),
        ]
        for label, date in milestones:
            done = bool(date)
            color = "#10b981" if done else "#1e3a5f"
            text_color = "#e2e8f0" if done else "#475569"
            st.markdown(f"""
                <div style='display:flex; align-items:center; gap:16px; padding:12px 0;
                            border-bottom:1px solid #1a2535;'>
                    <div style='width:36px; height:36px; border-radius:50%;
                                background:{color}22; border:2px solid {color};
                                display:flex; align-items:center; justify-content:center;
                                font-size:16px;'>{'✓' if done else '○'}</div>
                    <div>
                        <div style='font-weight:600; color:{text_color};'>{label}</div>
                        <div style='font-size:12px; color:#64748b; font-family:DM Mono,monospace;'>
                            {date if date else 'Not yet sent'}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<div class='section-header' style='margin-top:24px;'>Notes</div>",
                    unsafe_allow_html=True)
        n1, n2 = st.columns(2)
        with n1:
            st.markdown("**Current Stage Notes**")
            st.markdown(f"""
                <div style='background:#141e2e; border:1px solid #1e3a5f; border-radius:10px;
                            padding:14px; min-height:100px; font-size:14px; color:#cbd5e1;'>
                    {cl.get('current_stage_notes') or '<span style="color:#475569;">No notes yet</span>'}
                </div>
            """, unsafe_allow_html=True)
        with n2:
            st.markdown("**Next Step Notes**")
            st.markdown(f"""
                <div style='background:#141e2e; border:1px solid #1e3a5f; border-radius:10px;
                            padding:14px; min-height:100px; font-size:14px; color:#cbd5e1;'>
                    {cl.get('next_step_notes') or '<span style="color:#475569;">No notes yet</span>'}
                </div>
            """, unsafe_allow_html=True)

    # ── TAB 3: Follow-Ups ──
    with tab3:
        st.markdown("<div class='section-header'>Schedule New Follow-Up</div>",
                    unsafe_allow_html=True)
        with st.form(f"fu_form_{cid}"):
            fu_task = st.text_area("Task Description *", placeholder="e.g. Follow up on proposal discussion…")
            fc1, fc2 = st.columns(2)
            with fc1:
                fu_date = st.date_input("Follow-Up Date", min_value=datetime.today().date())
            with fc2:
                fu_time = st.time_input("Follow-Up Time", value=datetime.now().replace(
                    hour=10, minute=0, second=0, microsecond=0).time())
            if st.form_submit_button("➕ Schedule Reminder", type="primary"):
                if fu_task.strip():
                    dt_str = f"{fu_date} {fu_time.strftime('%H:%M')}"
                    db.add_followup(cid, fu_task, dt_str)
                    st.success(f"✓ Reminder scheduled for {dt_str}")
                    st.rerun()
                else:
                    st.error("Task description required.")

        st.markdown("<div class='section-header' style='margin-top:24px;'>Follow-Up History</div>",
                    unsafe_allow_html=True)
        followups = db.get_followups(cid)
        if followups:
            for fu in followups:
                _render_followup_row(fu)
        else:
            st.info("No follow-ups scheduled yet.")


def _detail_row(label, value):
    st.markdown(f"""
        <div style='display:flex; justify-content:space-between; padding:10px 0;
                    border-bottom:1px solid #1a2535;'>
            <span style='font-size:13px; color:#64748b;'>{label}</span>
            <span style='font-size:13px; color:#e2e8f0; font-weight:500;'>{value}</span>
        </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: FOLLOW-UPS
# ═══════════════════════════════════════════════════════════════════════════════
def page_followups():
    show_reminders()

    st.markdown("<div class='page-title'>Follow-Up Manager</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-subtitle'>Track and manage all pending client actions</div>",
                unsafe_allow_html=True)

    # ── Quick add ──
    with st.expander("➕ Schedule New Follow-Up", expanded=False):
        clients = db.get_all_clients()
        if not clients:
            st.info("Add a client first.")
        else:
            with st.form("global_fu_form"):
                client_opts = {c["client_name"]: c["client_id"] for c in clients}
                sel_name  = st.selectbox("Select Client", list(client_opts.keys()))
                fu_task   = st.text_area("Task Description *")
                fc1, fc2  = st.columns(2)
                with fc1:
                    fu_date = st.date_input("Date", min_value=datetime.today().date())
                with fc2:
                    fu_time = st.time_input("Time", value=datetime.now().replace(
                        hour=10, minute=0, second=0, microsecond=0).time())
                if st.form_submit_button("Schedule", type="primary"):
                    if fu_task.strip():
                        dt_str = f"{fu_date} {fu_time.strftime('%H:%M')}"
                        db.add_followup(client_opts[sel_name], fu_task, dt_str)
                        st.success("✓ Follow-up scheduled!")
                        st.rerun()
                    else:
                        st.error("Task description required.")

    # ── Tabs: Pending / Completed / Overdue ──
    all_fu = db.get_followups()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    pending   = [f for f in all_fu if f["status"] == "Pending"
                 and f["followup_datetime"] >= now_str]
    overdue   = [f for f in all_fu if f["status"] == "Pending"
                 and f["followup_datetime"] < now_str]
    completed = [f for f in all_fu if f["status"] == "Completed"]

    tab_p, tab_o, tab_c = st.tabs([
        f"⏳ Pending ({len(pending)})",
        f"🚨 Overdue ({len(overdue)})",
        f"✅ Completed ({len(completed)})",
    ])

    with tab_p:
        if pending:
            for fu in pending:
                _render_followup_row(fu, show_client=True)
        else:
            _empty_state("No pending follow-ups", "✓")

    with tab_o:
        if overdue:
            for fu in overdue:
                _render_followup_row(fu, show_client=True, is_overdue=True)
        else:
            _empty_state("No overdue follow-ups", "🎉")

    with tab_c:
        if completed:
            for fu in completed:
                _render_followup_row(fu, show_client=True, read_only=True)
        else:
            _empty_state("No completed follow-ups yet", "📋")


def _render_followup_row(fu, show_client=False, is_overdue=False, read_only=False):
    fid        = fu["followup_id"]
    border_col = "#ef4444" if is_overdue else "#1e3a5f"
    status_col = "#10b981" if fu["status"] == "Completed" else (
                 "#ef4444" if is_overdue else "#f59e0b")
    icon       = "✅" if fu["status"] == "Completed" else ("🚨" if is_overdue else "⏳")

    client_label = f"**{fu.get('client_name', '')}** · " if show_client else ""

    col_info, col_act = st.columns([5, 2])
    with col_info:
        st.markdown(f"""
            <div style='background:#141e2e; border:1px solid {border_col};
                        border-radius:10px; padding:14px 18px; margin-bottom:6px;'>
                <div style='font-size:12px; color:#64748b; margin-bottom:4px;'>
                    {icon} &nbsp; {client_label}
                    <span style='font-family:DM Mono,monospace; color:{status_col};'>
                        {fu['followup_datetime']}</span>
                    {'&nbsp; <span style="color:#ef4444; font-size:11px;">OVERDUE</span>' if is_overdue else ''}
                </div>
                <div style='font-size:14px; color:#e2e8f0;'>{fu['task_description']}</div>
                <div style='font-size:11px; color:#475569; margin-top:6px;'>
                    Status: {fu['status']} &nbsp;|&nbsp; Reminders sent: {fu.get('reminder_count',0)}
                    {f" | Completed: {fu['completed_time'][:16]}" if fu.get('completed_time') else ''}
                </div>
            </div>
        """, unsafe_allow_html=True)

    with col_act:
        if not read_only:
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ Done", key=f"fd_{fid}", use_container_width=True, type="primary"):
                    db.complete_followup(fid)
                    st.rerun()
            with c2:
                if st.button("🗑️", key=f"fdel_{fid}", use_container_width=True):
                    db.delete_followup(fid)
                    st.rerun()

            # Reschedule
            with st.expander("🔄 Reschedule", expanded=False):
                new_date = st.date_input("New Date", key=f"nd_{fid}",
                                          min_value=datetime.today().date())
                new_time = st.time_input("New Time", key=f"nt_{fid}",
                                          value=datetime.now().replace(
                                              hour=10, minute=0, second=0, microsecond=0).time())
                if st.button("Confirm Reschedule", key=f"rs_{fid}"):
                    db.reschedule_followup(fid, f"{new_date} {new_time.strftime('%H:%M')}")
                    st.success("Rescheduled!")
                    st.rerun()


def _empty_state(msg, icon="📋"):
    st.markdown(f"""
        <div style='background:#141e2e; border:1px dashed #1e3a5f; border-radius:12px;
                    padding:40px; text-align:center; color:#475569; margin:16px 0;'>
            <div style='font-size:32px; margin-bottom:12px;'>{icon}</div>
            <div style='font-size:15px;'>{msg}</div>
        </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# ROUTER
# ═══════════════════════════════════════════════════════════════════════════════
page = st.session_state.page

if page == "Dashboard":
    page_dashboard()
elif page == "Client Pipeline":
    page_pipeline()
elif page == "Add Client":
    page_add_client()
elif page == "Client Detail":
    page_client_detail()
elif page == "Follow-Ups":
    page_followups()
else:
    page_dashboard()
