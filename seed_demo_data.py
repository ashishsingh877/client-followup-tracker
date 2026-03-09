"""
Run this once to populate sample data for testing:
    python seed_demo_data.py
"""
import database as db
from datetime import datetime, timedelta

db.init_db()

clients = [
    ("ABC Pharma Ltd",       "raj.mehta@abcpharma.com",  "+91 98001 11222",
     "Advisory",        850000, "Active",    "Proposal Sent"),
    ("Horizon Infra Pvt",    "cfo@horizoninfra.in",      "+91 98002 22333",
     "Tax",             420000, "Active",    "Negotiation"),
    ("Synapse Tech",         "accounts@synapsetech.io",  "+91 98003 33444",
     "Consulting",     1200000, "Active",    "Approach Note Shared"),
    ("GreenLeaf Foods",      "finance@greenleaf.com",    "+91 98004 44555",
     "Audit",           650000, "Prospect",  "Pre-Scoping Questionnaire Sent"),
    ("Meridian Capital",     "ops@meridiancap.com",      "+91 98005 55666",
     "Financial Planning", 950000, "Active", "Won"),
    ("NovaBuild Constructions","ceo@novabuild.in",       "+91 98006 66777",
     "Legal",           380000, "On Hold",   "Lead Identified"),
]

now = datetime.now()

for name, email, phone, eng, fee, status, stage in clients:
    cid = db.add_client(name, email, phone, eng, fee, status, stage)
    db.update_engagement_dates(
        cid,
        (now - timedelta(days=20)).strftime("%Y-%m-%d"),
        (now - timedelta(days=12)).strftime("%Y-%m-%d") if stage not in ["Lead Identified","Pre-Scoping Questionnaire Sent"] else None,
        (now - timedelta(days=5)).strftime("%Y-%m-%d")  if stage in ["Proposal Sent","Negotiation","Won"] else None,
    )
    db.update_notes(
        cid,
        f"Currently in {stage} phase. Client is engaged and responsive.",
        "Schedule a follow-up call to discuss next steps and timeline.",
    )

# Add some follow-ups (one overdue, one upcoming)
clients_list = db.get_all_clients()
if len(clients_list) >= 2:
    # Overdue reminder
    db.add_followup(
        clients_list[0]["client_id"],
        "Follow up on proposal discussion — confirm budget approval",
        (now - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M"),
    )
    # Upcoming reminder
    db.add_followup(
        clients_list[1]["client_id"],
        "Call CFO to discuss tax planning scope and engagement letter",
        (now + timedelta(hours=3)).strftime("%Y-%m-%d %H:%M"),
    )
    # Completed
    fu_id = db.add_followup(
        clients_list[2]["client_id"],
        "Send approach note draft for review",
        (now - timedelta(days=2)).strftime("%Y-%m-%d %H:%M"),
    )
    db.complete_followup(fu_id)

print("✓ Demo data loaded! Run: streamlit run app.py")
