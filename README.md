# 📊 Client Follow-Up Tracker

A professional Streamlit application for tracking potential clients, engagement stages, and automated follow-up reminders.

---

## 🚀 Quick Start

### 1. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the application
```bash
streamlit run app.py
```

The app opens at **http://localhost:8501**

---

## ✨ Features

### 📋 Dashboard
- Summary metrics: total clients, active, pending tasks, overdue, won
- Pipeline value (total estimated fees)
- Stage distribution bar chart
- Status breakdown donut chart
- Upcoming follow-ups for next 7 days

### 👥 Client Pipeline
- Full table view with all fields:
  - Client Name, Engagement Type, Estimated Fee
  - Client Status, Engagement Stage
  - Pre-Scoping Date, Approach Note Date, Proposal Date
  - Current Notes, Next Step Notes
- Search by name, email, or phone
- Filter by stage and status
- Click **→** to open client detail page

### 📄 Client Detail Page
- Full client information
- Engagement timeline (visual checklist)
- Notes section
- Schedule follow-ups directly from the client page
- Edit / Delete client

### ➕ Add / Edit Client
- Complete form with all required fields
- Date pickers for key milestones
- Notes fields

### 🔔 Follow-Up Reminders
- Schedule reminders with date + time
- **Popup appears automatically** when reminder is due
- **YES = marks task complete**, database updated instantly
- **Snooze 1h** = reminder shown again after 1 hour
- Dismiss without action = shown again after 1 hour
- Tabs: Pending / Overdue / Completed
- Reschedule any reminder
- Reminder count tracking

---

## 🗄️ Database
SQLite database (`client_tracker.db`) created automatically on first run.

Tables:
- `clients` — core client info
- `engagement_stages` — milestone dates
- `notes` — current + next step notes
- `followups` — reminder tasks with status tracking

---

## 📦 Tech Stack
- **Frontend**: Streamlit
- **Database**: SQLite (built-in Python)
- **Charts**: Plotly
- **Data**: Pandas

---

## 💡 How Reminders Work

1. Add a follow-up with a date and time for any client
2. When that time arrives, a **glowing purple popup** appears at the top of every page
3. Click **✅ Yes, Done!** → task marked complete in database
4. Click **⏳ Snooze 1h** → reminder dismissed for 1 hour, then shown again
5. If you close the browser and come back after the due time → popup still appears
6. Overdue reminders reappear every hour until resolved

> **Tip**: Keep the Streamlit app open in your browser during the day for real-time reminders.
> For background notifications when the app isn't open, consider running the app on a server or adding MS Teams webhook integration.

---

## 🔮 Future Enhancements
- Microsoft Teams webhook notifications
- Email reminders via SMTP
- Export to Excel / CSV
- Multi-user support
- Mobile-friendly layout
