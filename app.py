import streamlit as st
import json, os, re
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

def now_ist():
    return datetime.now(IST).replace(tzinfo=None)

def now_str():
    return now_ist().strftime("%Y-%m-%d %H:%M")

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="ClientTrack", page_icon="◈",
                   layout="wide", initial_sidebar_state="expanded")

# ── Options ───────────────────────────────────────────────────────────────────
ENGAGEMENT_TYPES = [
    "", "Gap Assessment", "DPDPA End-to-End Compliance",
    "Unified Privacy Framework", "ISO27701 Implementation",
    "(PMO) Support", "DPDPA Review Program",
    "Quick Diagnostic", "Privacy Maturity Assessment",
]
ENGAGEMENT_STAGES = [
    "", "Initial Call/Discussion", "Pre-Scoping Sent", "Pre-Scoping Awaited",
    "Pre-Scoping Received", "Approach Note sent", "Costing", "Proposal sent",
    "Presentation", "Consultant Interview - In progress",
    "Negotiation", "Active Client", "Inactive Client", "On Hold",
]
CLIENT_STATUSES = ["Active", "Inactive", "On Hold"]
PIPELINE_STAGES  = ["Lead","Contacted","Proposal","Negotiation","Won","Lost"]

# ── Persistent storage ────────────────────────────────────────────────────────
DATA_FILE = "clienttrack_data.json"

EMPTY_CLIENT_TEMPLATE = {
    "name":"","email":"","phone":"","company":"","client_status":"Active",
    "stage":"Lead","engagement_type":"","estimated_fee":"","engagement_stage":"",
    "pre_scoping_date":"","approach_note_date":"","proposal_date":"",
    "current_notes":"","next_steps":"","created_at":"",
}

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            d = json.load(f)
        for c in d.get("clients", []):
            for k, v in EMPTY_CLIENT_TEMPLATE.items():
                c.setdefault(k, v)
        return d
    return {"clients": [], "followups": []}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)

# ── Session state ─────────────────────────────────────────────────────────────
if "data"          not in st.session_state: st.session_state.data = load_data()
if "page"          not in st.session_state: st.session_state.page = "Dashboard"
if "edit_client"   not in st.session_state: st.session_state.edit_client = None
if "show_add_form" not in st.session_state: st.session_state.show_add_form = False

data = st.session_state.data

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebar"] { background:#0e1117; }
.ct-logo{font-size:26px;font-weight:800;color:#7c6af7;margin-bottom:2px;}
.ct-sub{font-size:10px;letter-spacing:3px;color:#555;margin-bottom:18px;}
.stat-row{display:flex;justify-content:space-between;font-size:13px;color:#aaa;padding:4px 0;border-bottom:1px solid #1e2130;}
.stat-val{font-weight:700;color:#e2e8f0;}
.stat-val.red{color:#f87171;}
.stat-val.grn{color:#34d399;}
.section-title{font-size:22px;font-weight:700;color:#e2e8f0;margin-bottom:16px;}
.metric-card{background:#161b2e;border:1px solid #2a2f45;border-radius:12px;padding:18px 20px;text-align:center;}
.metric-val{font-size:32px;font-weight:800;color:#7c6af7;}
.metric-lbl{font-size:12px;color:#6b7280;margin-top:4px;}
.pill{display:inline-block;padding:2px 10px;border-radius:20px;font-size:11px;font-weight:600;}
.pill-active{background:#14532d;color:#4ade80;}
.pill-hold{background:#713f12;color:#fbbf24;}
.pill-inactive{background:#1f2937;color:#9ca3af;}
.cl-card{background:#161b2e;border:1px solid #2a2f45;border-radius:10px;padding:14px 16px;margin-bottom:10px;}
.cl-name{font-size:15px;font-weight:700;color:#a78bfa;}
.cl-row{font-size:12px;color:#6b7280;margin-top:3px;}
.cl-stage-badge{display:inline-block;font-size:11px;padding:2px 8px;border-radius:12px;background:#1a1f35;color:#7c6af7;margin-top:5px;}
.fu-card{background:#161b2e;border:1px solid #2a2f45;border-radius:10px;padding:14px 16px;margin-bottom:10px;}
.fu-hdr{font-size:13px;font-weight:700;margin-bottom:6px;}
.fu-desc{font-size:14px;color:#e2e8f0;}
.fu-meta{font-size:11px;color:#475569;margin-top:6px;}
.notes-box{background:#0e1117;border:1px solid #2a2f45;border-radius:8px;padding:10px 12px;font-size:12px;color:#9ca3af;line-height:1.6;margin-top:4px;}
div[data-testid="stHorizontalBlock"] > div { align-items: flex-start !important; }
</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
def status_pill(s):
    cls = {"Active":"pill-active","On Hold":"pill-hold","Inactive":"pill-inactive"}.get(s,"pill-inactive")
    return f'<span class="pill {cls}">{s}</span>'

def _is_overdue(fu):
    try:
        return (fu["status"]=="Pending" and
                datetime.strptime(fu["datetime"],"%Y-%m-%d %H:%M") < now_ist())
    except: return False

def _time_options():
    return [f"{h:02d}:{m:02d}" for h in range(24) for m in (0,30)]

def pending_count():
    now=now_ist()
    return sum(1 for f in data["followups"]
               if f["status"]=="Pending" and datetime.strptime(f["datetime"],"%Y-%m-%d %H:%M")>=now)

def overdue_count():
    now=now_ist()
    return sum(1 for f in data["followups"]
               if f["status"]=="Pending" and datetime.strptime(f["datetime"],"%Y-%m-%d %H:%M")<now)

def completed_count():
    return sum(1 for f in data["followups"] if f["status"]=="Completed")

def active_count():  return sum(1 for c in data["clients"] if c.get("client_status")=="Active")
def onhold_count():  return sum(1 for c in data["clients"] if c.get("client_status")=="On Hold")
def won_count():     return sum(1 for c in data["clients"] if c.get("stage")=="Won")

def stage_counts():
    counts = {}
    for c in data["clients"]:
        s = c.get("engagement_stage","") or "—"
        counts[s] = counts.get(s,0)+1
    return counts

# ── Follow-up card ────────────────────────────────────────────────────────────
def render_followup_card(fu, idx):
    status       = fu["status"]
    client       = fu.get("client","Unknown")
    dt_str       = fu["datetime"]
    desc         = fu.get("description","")
    reminders    = fu.get("reminders_sent",0)
    completed_at = fu.get("completed_at","")
    if status=="Completed":   icon,hdr="#34d399","✅"
    elif _is_overdue(fu):     icon,hdr="#f87171","🚨"
    else:                     icon,hdr="#a78bfa","⏳"
    meta=f"Status: {status} &nbsp;|&nbsp; Reminders sent: {reminders}"
    if completed_at: meta+=f" &nbsp;|&nbsp; Completed: {completed_at}"
    desc_html=desc if desc else '<em style="color:#475569;">No description</em>'
    col_card,col_act=st.columns([3,1])
    with col_card:
        st.markdown(f"""
        <div class="fu-card">
            <div class="fu-hdr" style="color:{icon};">{hdr} &nbsp;<strong>{client}</strong> · {dt_str}</div>
            <div class="fu-desc">{desc_html}</div>
            <div class="fu-meta">{meta}</div>
        </div>""",unsafe_allow_html=True)
    with col_act:
        st.write("")
        if status!="Completed":
            if st.button("✅ Done",key=f"done_{idx}",type="primary",use_container_width=True):
                data["followups"][idx]["status"]="Completed"
                data["followups"][idx]["completed_at"]=now_str()
                save_data(data); st.rerun()
        if st.button("🗑️",key=f"del_{idx}",use_container_width=True):
            data["followups"].pop(idx); save_data(data); st.rerun()
        if status!="Completed":
            with st.expander("📅 Reschedule"):
                nd=st.date_input("Date",key=f"rd_{idx}",value=date.today()+timedelta(days=1))
                nt=st.selectbox("Time",_time_options(),key=f"rt_{idx}")
                if st.button("Confirm",key=f"rc_{idx}"):
                    data["followups"][idx]["datetime"]=f"{nd} {nt}"
                    save_data(data); st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown('<div class="ct-logo">◈ ClientTrack</div>',unsafe_allow_html=True)
    st.markdown('<div class="ct-sub">FOLLOW-UP MANAGER</div>',unsafe_allow_html=True)
    for icon,pg in [("📊","Dashboard"),("📋","Pipeline Tracker"),("➕","Add Client"),("🔔","Follow-Ups")]:
        t="primary" if st.session_state.page==pg else "secondary"
        if st.button(f"{icon}  {pg}",key=f"nav_{pg}",use_container_width=True,type=t):
            st.session_state.page=pg; st.rerun()
    st.markdown("---")
    st.markdown("**QUICK STATS**")
    pc=pending_count()+overdue_count(); wc=won_count(); tot=len(data["clients"])
    ac=active_count(); hc=onhold_count()
    red="red" if pc>0 else ""
    st.markdown(f"""
    <div class="stat-row"><span>Total Clients</span><span class="stat-val">{tot}</span></div>
    <div class="stat-row"><span>Active</span><span class="stat-val grn">{ac}</span></div>
    <div class="stat-row"><span>On Hold</span><span class="stat-val" style="color:#fbbf24;">{hc}</span></div>
    <div class="stat-row"><span>Pending Tasks</span><span class="stat-val {red}">{pc}</span></div>
    <div class="stat-row"><span>Won</span><span class="stat-val grn">{wc}</span></div>
    """,unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:10px;color:#374151;margin-top:8px;'>{now_ist().strftime('%A, %d %b %Y %H:%M')}</div>",unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Dashboard
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.page=="Dashboard":
    st.markdown('<div class="section-title">📊 Dashboard</div>',unsafe_allow_html=True)

    # ── Metric tiles ──────────────────────────────────────────────────────────
    cols=st.columns(5)
    metrics=[
        ("Total Clients",len(data["clients"]),"#7c6af7"),
        ("Active",active_count(),"#34d399"),
        ("On Hold",onhold_count(),"#fbbf24"),
        ("Pending Follow-Ups",pending_count()+overdue_count(),"#f87171"),
        ("Completed",completed_count(),"#60a5fa"),
    ]
    for col,(lbl,val,color) in zip(cols,metrics):
        col.markdown(f"""
        <div class="metric-card">
            <div class="metric-val" style="color:{color};">{val}</div>
            <div class="metric-lbl">{lbl}</div>
        </div>""",unsafe_allow_html=True)

    st.markdown("<br>",unsafe_allow_html=True)

    # ── Stage distribution ────────────────────────────────────────────────────
    col_left,col_right=st.columns([1,1])

    with col_left:
        st.markdown("#### 📌 Clients by Engagement Stage")
        sc=stage_counts()
        for stage,count in sorted(sc.items(),key=lambda x:-x[1]):
            pct=int(count/max(len(data["clients"]),1)*100)
            bar_color="#7c6af7" if stage!="—" else "#374151"
            st.markdown(f"""
            <div style="margin-bottom:8px;">
              <div style="display:flex;justify-content:space-between;font-size:12px;color:#9ca3af;">
                <span>{stage}</span><span style="color:#e2e8f0;font-weight:700;">{count}</span>
              </div>
              <div style="background:#1e2130;border-radius:4px;height:6px;margin-top:3px;">
                <div style="width:{pct}%;background:{bar_color};height:6px;border-radius:4px;"></div>
              </div>
            </div>""",unsafe_allow_html=True)

    with col_right:
        st.markdown("#### 💰 Top Proposals by Value")
        fee_clients=[c for c in data["clients"] if c.get("estimated_fee","").strip()]
        fee_clients.sort(key=lambda x: int(re.sub(r"[^\d]","",x["estimated_fee"]) or "0"),reverse=True)
        if not fee_clients:
            st.info("No fee data yet.")
        else:
            for c in fee_clients[:8]:
                fee=c.get("estimated_fee","")
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;align-items:center;
                            padding:7px 10px;background:#161b2e;border-radius:8px;margin-bottom:5px;">
                  <span style="font-size:13px;color:#e2e8f0;">{c['name']}</span>
                  <span style="font-size:13px;font-weight:700;color:#34d399;">₹{fee}</span>
                </div>""",unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 🔔 Upcoming Follow-Ups")
    now=now_ist()
    upcoming=sorted([f for f in data["followups"]
                     if f["status"]=="Pending"
                     and datetime.strptime(f["datetime"],"%Y-%m-%d %H:%M")>=now],
                    key=lambda x:x["datetime"])
    if not upcoming:
        st.info("No upcoming follow-ups.")
    else:
        for fu in upcoming[:4]:
            render_followup_card(fu,data["followups"].index(fu))

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Pipeline Tracker  (main Excel-mirror view)
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page=="Pipeline Tracker":
    st.markdown('<div class="section-title">📋 Pipeline Tracker</div>',unsafe_allow_html=True)

    # ── Filters ───────────────────────────────────────────────────────────────
    fc1,fc2,fc3=st.columns(3)
    with fc1:
        f_status=st.selectbox("Filter: Client Status",["All"]+CLIENT_STATUSES)
    with fc2:
        f_stage=st.selectbox("Filter: Engagement Stage",["All"]+[s for s in ENGAGEMENT_STAGES if s])
    with fc3:
        f_eng=st.selectbox("Filter: Engagement Type",["All"]+[e for e in ENGAGEMENT_TYPES if e])

    clients_shown=data["clients"]
    if f_status!="All": clients_shown=[c for c in clients_shown if c.get("client_status")==f_status]
    if f_stage!="All":  clients_shown=[c for c in clients_shown if c.get("engagement_stage")==f_stage]
    if f_eng!="All":    clients_shown=[c for c in clients_shown if c.get("engagement_type")==f_eng]

    st.markdown(f"<div style='font-size:12px;color:#6b7280;margin-bottom:10px;'>{len(clients_shown)} client(s) shown</div>",unsafe_allow_html=True)

    # ── Table header ──────────────────────────────────────────────────────────
    hcols=st.columns([2,2,1.2,1,2,1.8,1.8,1.8])
    headers=["Client Name","Engagement Type","Est. Fee","Status","Eng. Stage","Pre-Scoping Date","Approach Note Date","Proposal Date"]
    for h,col in zip(headers,hcols):
        col.markdown(f"<div style='font-size:11px;font-weight:700;color:#7c6af7;padding:4px 0;border-bottom:1px solid #2a2f45;'>{h}</div>",unsafe_allow_html=True)

    st.markdown("<div style='height:4px'></div>",unsafe_allow_html=True)

    # ── Rows ──────────────────────────────────────────────────────────────────
    for client in clients_shown:
        orig_idx=data["clients"].index(client)
        rcols=st.columns([2,2,1.2,1,2,1.8,1.8,1.8])

        with rcols[0]:
            st.markdown(f"<div style='font-size:13px;font-weight:600;color:#e2e8f0;padding:6px 0;'>{client['name']}</div>",unsafe_allow_html=True)
        with rcols[1]:
            st.markdown(f"<div style='font-size:12px;color:#9ca3af;padding:6px 0;'>{client.get('engagement_type','')}</div>",unsafe_allow_html=True)
        with rcols[2]:
            fee=client.get('estimated_fee','')
            fee_color="#f87171" if fee else "#374151"
            st.markdown(f"<div style='font-size:12px;color:{fee_color};padding:6px 0;font-weight:600;'>{'₹'+fee if fee else '—'}</div>",unsafe_allow_html=True)
        with rcols[3]:
            st.markdown(f"<div style='padding:6px 0;'>{status_pill(client.get('client_status','Active'))}</div>",unsafe_allow_html=True)
        with rcols[4]:
            es=client.get('engagement_stage','') or '—'
            es_color={"Negotiation":"#fbbf24","Proposal sent":"#60a5fa","Costing":"#f87171","Presentation":"#a78bfa"}.get(es,"#9ca3af")
            st.markdown(f"<div style='font-size:12px;color:{es_color};padding:6px 0;'>{es}</div>",unsafe_allow_html=True)
        with rcols[5]:
            st.markdown(f"<div style='font-size:11px;color:#6b7280;padding:6px 0;'>{client.get('pre_scoping_date','') or '—'}</div>",unsafe_allow_html=True)
        with rcols[6]:
            st.markdown(f"<div style='font-size:11px;color:#6b7280;padding:6px 0;'>{client.get('approach_note_date','') or '—'}</div>",unsafe_allow_html=True)
        with rcols[7]:
            st.markdown(f"<div style='font-size:11px;color:#6b7280;padding:6px 0;'>{client.get('proposal_date','') or '—'}</div>",unsafe_allow_html=True)

        # Notes + Edit expandable row
        with st.expander(f"📝 Notes & Edit — {client['name']}"):
            n1,n2=st.columns(2)
            with n1:
                st.markdown("**Current Stage Notes**")
                st.markdown(f"<div class='notes-box'>{client.get('current_notes','') or '—'}</div>",unsafe_allow_html=True)
            with n2:
                st.markdown("**Next Step Notes**")
                st.markdown(f"<div class='notes-box'>{client.get('next_steps','') or '—'}</div>",unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("**✏️ Quick Edit**")
            e1,e2,e3=st.columns(3)
            with e1:
                new_status=st.selectbox("Client Status",CLIENT_STATUSES,
                                        index=CLIENT_STATUSES.index(client.get("client_status","Active")),
                                        key=f"es_{orig_idx}")
                new_eng_type=st.selectbox("Engagement Type",ENGAGEMENT_TYPES,
                                          index=ENGAGEMENT_TYPES.index(client.get("engagement_type","")) if client.get("engagement_type","") in ENGAGEMENT_TYPES else 0,
                                          key=f"et_{orig_idx}")
            with e2:
                new_stage=st.selectbox("Engagement Stage",ENGAGEMENT_STAGES,
                                       index=ENGAGEMENT_STAGES.index(client.get("engagement_stage","")) if client.get("engagement_stage","") in ENGAGEMENT_STAGES else 0,
                                       key=f"esg_{orig_idx}")
                new_fee=st.text_input("Estimated Fee",value=client.get("estimated_fee",""),key=f"ef_{orig_idx}")
            with e3:
                new_pre=st.text_input("Pre-Scoping Date",value=client.get("pre_scoping_date",""),key=f"ep_{orig_idx}")
                new_an=st.text_input("Approach Note Date",value=client.get("approach_note_date",""),key=f"ea_{orig_idx}")
                new_prop=st.text_input("Proposal Date",value=client.get("proposal_date",""),key=f"epr_{orig_idx}")

            new_cur=st.text_area("Current Stage Notes",value=client.get("current_notes",""),key=f"ecn_{orig_idx}",height=80)
            new_nxt=st.text_area("Next Step Notes",value=client.get("next_steps",""),key=f"ens_{orig_idx}",height=80)

            bc1,bc2=st.columns([1,5])
            with bc1:
                if st.button("💾 Save",key=f"save_{orig_idx}",type="primary"):
                    data["clients"][orig_idx].update({
                        "client_status":new_status,"engagement_type":new_eng_type,
                        "engagement_stage":new_stage,"estimated_fee":new_fee,
                        "pre_scoping_date":new_pre,"approach_note_date":new_an,
                        "proposal_date":new_prop,"current_notes":new_cur,"next_steps":new_nxt,
                    })
                    save_data(data); st.success("Saved!"); st.rerun()
            with bc2:
                if st.button("🗑️ Delete Client",key=f"deld_{orig_idx}"):
                    data["clients"].pop(orig_idx); save_data(data); st.rerun()

        st.markdown("<div style='height:2px;background:#1e2130;margin:2px 0;'></div>",unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Add Client
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page=="Add Client":
    st.markdown('<div class="section-title">➕ Add New Client</div>',unsafe_allow_html=True)

    with st.form("add_client_form",clear_on_submit=True):
        st.markdown("#### 🏢 Basic Info")
        c1,c2,c3=st.columns(3)
        with c1:
            name    =st.text_input("Client / Company Name *")
            email   =st.text_input("Email")
        with c2:
            phone   =st.text_input("Phone")
            company =st.text_input("Company Full Name")
        with c3:
            client_status=st.selectbox("Client Status",CLIENT_STATUSES)
            pipeline_stage=st.selectbox("Pipeline Stage",PIPELINE_STAGES)

        st.markdown("#### 📑 Engagement Details")
        e1,e2,e3=st.columns(3)
        with e1:
            eng_type =st.selectbox("Engagement Type",ENGAGEMENT_TYPES)
            est_fee  =st.text_input("Estimated Fee (e.g. 52,33,641/-)")
        with e2:
            eng_stage    =st.selectbox("Engagement Stage",ENGAGEMENT_STAGES)
            pre_scoping  =st.text_input("Pre-Scoping Date")
        with e3:
            approach_date=st.text_input("Approach Note Date")
            proposal_date=st.text_input("Proposal Sent Date")

        st.markdown("#### 📝 Notes")
        n1,n2=st.columns(2)
        with n1: cur_notes=st.text_area("Current Stage Notes",height=100)
        with n2: nxt_notes=st.text_area("Next Step Notes",height=100)

        if st.form_submit_button("➕ Add Client",type="primary"):
            if not name.strip():
                st.error("Client name is required.")
            else:
                data["clients"].append({
                    "name":name.strip(),"email":email.strip(),"phone":phone.strip(),
                    "company":company.strip(),"client_status":client_status,
                    "stage":pipeline_stage,"engagement_type":eng_type,
                    "estimated_fee":est_fee.strip(),"engagement_stage":eng_stage,
                    "pre_scoping_date":pre_scoping.strip(),
                    "approach_note_date":approach_date.strip(),
                    "proposal_date":proposal_date.strip(),
                    "current_notes":cur_notes.strip(),"next_steps":nxt_notes.strip(),
                    "created_at":now_str(),
                })
                save_data(data)
                st.success(f"✅ Client '{name}' added!")
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Follow-Ups
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page=="Follow-Ups":
    st.markdown('<div class="section-title">🔔 Follow-Ups</div>',unsafe_allow_html=True)

    with st.expander("➕ Schedule a New Follow-Up",expanded=True):
        client_names=[c["name"] for c in data["clients"]]
        if not client_names:
            st.warning("Add a client first.")
        else:
            sel_client =st.selectbox("Client",client_names)
            description=st.text_area("Description / Notes")
            cd,ct=st.columns(2)
            with cd: fu_date=st.date_input("Date",value=date.today())
            with ct:
                topts=_time_options()
                fu_time=st.selectbox("Time",topts,index=topts.index("09:00") if "09:00" in topts else 0)
            if st.button("Schedule",type="primary"):
                dt_str=f"{fu_date} {fu_time}"
                data["followups"].append({
                    "client":sel_client,"description":description.strip(),
                    "datetime":dt_str,"status":"Pending","reminders_sent":0,"created_at":now_str(),
                })
                save_data(data); st.success(f"✅ Scheduled for {sel_client} on {dt_str}"); st.rerun()

    st.markdown("---")
    now=now_ist()
    pf=[(i,f) for i,f in enumerate(data["followups"]) if f["status"]=="Pending" and datetime.strptime(f["datetime"],"%Y-%m-%d %H:%M")>=now]
    of=[(i,f) for i,f in enumerate(data["followups"]) if f["status"]=="Pending" and datetime.strptime(f["datetime"],"%Y-%m-%d %H:%M")<now]
    cf=[(i,f) for i,f in enumerate(data["followups"]) if f["status"]=="Completed"]

    tp,to,tc=st.tabs([f"⏳ Pending ({len(pf)})",f"🚨 Overdue ({len(of)})",f"✅ Completed ({len(cf)})"])
    with tp:
        [render_followup_card(fu,idx) for idx,fu in pf] if pf else st.info("No pending follow-ups.")
    with to:
        [render_followup_card(fu,idx) for idx,fu in of] if of else st.success("No overdue! 🎉")
    with tc:
        [render_followup_card(fu,idx) for idx,fu in cf] if cf else st.info("No completed yet.")
