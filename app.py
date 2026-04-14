#!/usr/bin/env python3
“””
L&P SMT Organizer - Flask App
Run: python app.py
Open browser: http://localhost:5000
“””

from flask import Flask, request, jsonify
import sqlite3, json, os, datetime

app = Flask(**name**)
DB = os.path.join(os.path.dirname(**file**), “smt.db”)

# ─── Database setup ────────────────────────────────────────────────────────────

def get_db():
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
return conn

def init_db():
conn = get_db()
c = conn.cursor()
c.executescript(”””
CREATE TABLE IF NOT EXISTS reels (
id TEXT PRIMARY KEY,
barcode TEXT UNIQUE NOT NULL,
part TEXT NOT NULL,
pkg TEXT,
qty INTEGER DEFAULT 0,
loc TEXT,
status TEXT DEFAULT ‘In Stock’
);
CREATE TABLE IF NOT EXISTS feeders (
id TEXT PRIMARY KEY,
slot INTEGER,
machine TEXT,
type TEXT,
loaded_reel TEXT,
status TEXT DEFAULT ‘Available’
);
CREATE TABLE IF NOT EXISTS activity (
id INTEGER PRIMARY KEY AUTOINCREMENT,
action TEXT,
ref TEXT,
detail TEXT,
icon TEXT,
created_at TEXT
);
“””)
# Seed data if empty
c.execute(“SELECT COUNT(*) FROM reels”)
if c.fetchone()[0] == 0:
reels = [
(“REL-2024-00146”,“REL-2024-00146”,“STM32F103C8T6”,“QFP”,0,“C2-001”,“Empty”),
(“REL-2024-00147”,“REL-2024-00147”,“RC0402FR-071KL”,“0402”,8500,“A2-B08”,“In Stock”),
(“REL-2024-00142”,“REL-2024-00142”,“RC0805FR-0710KL”,“0805”,4500,“A3-B12”,“In Stock”),
(“REL-2024-00143”,“REL-2024-00143”,“CL10B104KB8NNNL”,“0402”,180,“A3-B13”,“Low Stock”),
(“REL-2024-00144”,“REL-2024-00144”,“GRM188R71C104KA01D”,“0603”,3200,“A4-C01”,“In Use”),
(“REL-2024-00145”,“REL-2024-00145”,“BAT54S-7-F”,“SOT23”,2800,“B1-A05”,“In Stock”),
]
c.executemany(“INSERT INTO reels VALUES (?,?,?,?,?,?,?)”, reels)
feeders = [
(“F-001”,1,“Line 1 - Juki RS-1”,“8mm”,None,“Available”),
(“F-002”,2,“Line 1 - Juki RS-1”,“8mm”,None,“Available”),
(“F-003”,3,“Line 1 - Juki RS-1”,“8mm”,“GRM188R71C104KA01D”,“Loaded”),
(“F-004”,5,“Line 2 - Samsung CP45”,“12mm”,None,“Maintenance”),
(“F-005”,8,“Line 2 - Samsung CP45”,“24mm”,None,“Available”),
]
c.executemany(“INSERT INTO feeders VALUES (?,?,?,?,?,?)”, feeders)
logs = [
(“Locate”,“REL-2024-00142”,“LED activated for location A3-B12”,“💡”),
(“Locate”,“F-004”,“Located feeder for maintenance check”,“💡”),
(“Assign Feeder”,“REL-2024-00144”,“Assigned to feeder F-003”,“🔗”),
]
for l in logs:
c.execute(“INSERT INTO activity (action,ref,detail,icon,created_at) VALUES (?,?,?,?,?)”,
(*l, datetime.datetime.now().strftime(”%b %d, %H:%M”)))
conn.commit()
conn.close()

# ─── API Routes ────────────────────────────────────────────────────────────────

@app.route(”/api/reels”, methods=[“GET”])
def get_reels():
conn = get_db()
rows = conn.execute(“SELECT * FROM reels ORDER BY id”).fetchall()
conn.close()
return jsonify([dict(r) for r in rows])

@app.route(”/api/reels”, methods=[“POST”])
def add_reel():
d = request.json
conn = get_db()
try:
conn.execute(“INSERT INTO reels VALUES (?,?,?,?,?,?,?)”,
(d[“barcode”],d[“barcode”],d[“part”],d.get(“pkg”,””),int(d.get(“qty”,0)),d.get(“loc”,””),d.get(“status”,“In Stock”)))
conn.execute(“INSERT INTO activity (action,ref,detail,icon,created_at) VALUES (?,?,?,?,?)”,
(“Add Reel”,d[“barcode”],f”Added {d[‘part’]} at {d.get(‘loc’,’’)}”,“➕”,datetime.datetime.now().strftime(”%b %d, %H:%M”)))
conn.commit()
conn.close()
return jsonify({“ok”: True})
except Exception as e:
conn.close()
return jsonify({“ok”: False, “error”: str(e)}), 400

@app.route(”/api/reels/<reel_id>”, methods=[“PUT”])
def update_reel(reel_id):
d = request.json
conn = get_db()
conn.execute(“UPDATE reels SET part=?,pkg=?,qty=?,loc=?,status=? WHERE id=?”,
(d[“part”],d.get(“pkg”,””),int(d.get(“qty”,0)),d.get(“loc”,””),d.get(“status”,“In Stock”),reel_id))
conn.execute(“INSERT INTO activity (action,ref,detail,icon,created_at) VALUES (?,?,?,?,?)”,
(“Edit Reel”,reel_id,f”Updated {d[‘part’]}”,“✏️”,datetime.datetime.now().strftime(”%b %d, %H:%M”)))
conn.commit()
conn.close()
return jsonify({“ok”: True})

@app.route(”/api/reels/<reel_id>”, methods=[“DELETE”])
def delete_reel(reel_id):
conn = get_db()
conn.execute(“DELETE FROM reels WHERE id=?”, (reel_id,))
conn.commit()
conn.close()
return jsonify({“ok”: True})

@app.route(”/api/feeders”, methods=[“GET”])
def get_feeders():
conn = get_db()
rows = conn.execute(“SELECT * FROM feeders ORDER BY slot”).fetchall()
conn.close()
return jsonify([dict(r) for r in rows])

@app.route(”/api/feeders”, methods=[“POST”])
def add_feeder():
d = request.json
conn = get_db()
try:
conn.execute(“INSERT INTO feeders VALUES (?,?,?,?,?,?)”,
(d[“id”],int(d.get(“slot”,0)),d.get(“machine”,””),d.get(“type”,“8mm”),None,d.get(“status”,“Available”)))
conn.execute(“INSERT INTO activity (action,ref,detail,icon,created_at) VALUES (?,?,?,?,?)”,
(“Add Feeder”,d[“id”],f”Registered feeder {d[‘id’]} on {d.get(‘machine’,’’)}”,“➕”,datetime.datetime.now().strftime(”%b %d, %H:%M”)))
conn.commit()
conn.close()
return jsonify({“ok”: True})
except Exception as e:
conn.close()
return jsonify({“ok”: False, “error”: str(e)}), 400

@app.route(”/api/feeders/<feeder_id>”, methods=[“PUT”])
def update_feeder(feeder_id):
d = request.json
conn = get_db()
conn.execute(“UPDATE feeders SET slot=?,machine=?,type=?,loaded_reel=?,status=? WHERE id=?”,
(int(d.get(“slot”,0)),d.get(“machine”,””),d.get(“type”,“8mm”),d.get(“loaded_reel”),d.get(“status”,“Available”),feeder_id))
conn.commit()
conn.close()
return jsonify({“ok”: True})

@app.route(”/api/feeders/<feeder_id>”, methods=[“DELETE”])
def delete_feeder(feeder_id):
conn = get_db()
conn.execute(“DELETE FROM feeders WHERE id=?”, (feeder_id,))
conn.commit()
conn.close()
return jsonify({“ok”: True})

@app.route(”/api/scan”, methods=[“POST”])
def scan():
code = request.json.get(“code”,””).strip()
conn = get_db()
reel = conn.execute(“SELECT * FROM reels WHERE barcode=? OR id=? OR part LIKE ?”,
(code,code,f”%{code}%”)).fetchone()
if reel:
conn.execute(“INSERT INTO activity (action,ref,detail,icon,created_at) VALUES (?,?,?,?,?)”,
(“Locate”,reel[“id”],f”LED activated for location {reel[‘loc’]}”,“💡”,datetime.datetime.now().strftime(”%b %d, %H:%M”)))
conn.commit()
conn.close()
return jsonify({“found”: True, “type”: “reel”, “item”: dict(reel)})
feeder = conn.execute(“SELECT * FROM feeders WHERE id LIKE ?”, (f”%{code}%”,)).fetchone()
if feeder:
conn.execute(“INSERT INTO activity (action,ref,detail,icon,created_at) VALUES (?,?,?,?,?)”,
(“Locate”,feeder[“id”],f”Located feeder {feeder[‘id’]}”,“💡”,datetime.datetime.now().strftime(”%b %d, %H:%M”)))
conn.commit()
conn.close()
return jsonify({“found”: True, “type”: “feeder”, “item”: dict(feeder)})
conn.close()
return jsonify({“found”: False})

@app.route(”/api/activity”, methods=[“GET”])
def get_activity():
conn = get_db()
rows = conn.execute(“SELECT * FROM activity ORDER BY id DESC LIMIT 100”).fetchall()
conn.close()
return jsonify([dict(r) for r in rows])

@app.route(”/api/log”, methods=[“POST”])
def add_log():
d = request.json
conn = get_db()
conn.execute(“INSERT INTO activity (action,ref,detail,icon,created_at) VALUES (?,?,?,?,?)”,
(d.get(“action”,””),d.get(“ref”,””),d.get(“detail”,””),d.get(“icon”,“💡”),datetime.datetime.now().strftime(”%b %d, %H:%M”)))
conn.commit()
conn.close()
return jsonify({“ok”: True})

# ─── Main HTML page ────────────────────────────────────────────────────────────

@app.route(”/”)
def index():
return “””<!DOCTYPE html>

<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>L&P SMT Organizer</title>
<style>
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:system-ui,-apple-system,sans-serif;background:#f8fafc;color:#334155;display:flex;height:100vh;overflow:hidden;}
::-webkit-scrollbar{width:5px;height:5px;}::-webkit-scrollbar-thumb{background:#cbd5e1;border-radius:3px;}
input,select,textarea{font-family:inherit;}
input:focus,select:focus{border-color:#93c5fd!important;outline:none;box-shadow:0 0 0 3px #dbeafe;}
button{cursor:pointer;font-family:inherit;}
button:hover{opacity:0.85;}

/* Sidebar */
#sidebar{width:220px;background:#fff;border-right:1px solid #e2e8f0;display:flex;flex-direction:column;flex-shrink:0;padding:0 10px;}
.logo{padding:18px 8px 16px;border-bottom:1px solid #f1f5f9;display:flex;align-items:center;gap:10px;}
.logo-icon{width:30px;height:30px;border-radius:8px;background:linear-gradient(135deg,#2563eb,#7c3aed);display:flex;align-items:center;justify-content:center;font-size:15px;flex-shrink:0;}
.logo-text{font-size:13px;font-weight:700;color:#0f172a;line-height:1.2;}
.logo-sub{font-size:11px;color:#94a3b8;}
nav{padding:10px 0;flex:1;}
.nav-btn{display:flex;align-items:center;gap:10px;padding:9px 12px;border-radius:8px;width:100%;border:none;background:transparent;font-size:14px;font-weight:500;color:#475569;transition:all 0.15s;text-align:left;}
.nav-btn.active{color:#2563eb;background:#eff6ff;}
.nav-btn:hover:not(.active){background:#f8fafc;}
.led-status{padding:12px 8px;border-top:1px solid #f1f5f9;}
.led-box{display:flex;align-items:center;gap:8px;padding:8px 10px;border-radius:8px;background:#f8fafc;border:1px solid #e2e8f0;transition:all 0.3s;}
.led-box.active{background:#fefce8;border-color:#fde68a;}
.led-label{font-size:11px;font-weight:600;color:#475569;}
.led-box.active .led-label{color:#92400e;}
.led-sub{font-size:10px;color:#94a3b8;}
.led-box.active .led-sub{color:#b45309;}

/* Main */
#main{flex:1;overflow-y:auto;padding:24px;}
.page{display:none;}.page.active{display:block;}
h1{font-size:22px;font-weight:700;color:#0f172a;}
.page-sub{font-size:13px;color:#64748b;margin-top:4px;margin-bottom:20px;}

/* Cards */
.card{background:#fff;border-radius:12px;border:1px solid #e2e8f0;padding:20px;box-shadow:0 1px 4px rgba(0,0,0,0.05);margin-bottom:16px;}

/* Stat grid */
.stat-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:24px;}
.stat-card{background:#fff;border-radius:12px;border:1px solid #e2e8f0;padding:20px;display:flex;align-items:flex-start;justify-content:space-between;box-shadow:0 1px 4px rgba(0,0,0,0.05);}
.stat-label{font-size:11px;font-weight:600;color:#64748b;letter-spacing:.05em;margin-bottom:6px;}
.stat-value{font-size:28px;font-weight:700;color:#0f172a;line-height:1;}
.stat-sub{font-size:12px;color:#94a3b8;margin-top:4px;}
.stat-icon{width:36px;height:36px;border-radius:9px;display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0;}

/* Two col */
.two-col{display:grid;grid-template-columns:1fr 1fr;gap:16px;}

/* Table */
.tbl-wrap{overflow-x:auto;}
table{width:100%;border-collapse:collapse;}
th{font-size:11px;font-weight:600;color:#64748b;text-transform:uppercase;letter-spacing:.05em;padding:10px 14px;border-bottom:1px solid #f1f5f9;white-space:nowrap;text-align:left;}
td{font-size:13px;color:#334155;padding:11px 14px;border-bottom:1px solid #f8fafc;}
tr:hover td{background:#fafafa;}

/* Badges */
.badge{display:inline-flex;align-items:center;gap:5px;padding:3px 10px;border-radius:20px;font-size:12px;font-weight:500;white-space:nowrap;border:1px solid transparent;}
.badge-dot{width:6px;height:6px;border-radius:50%;flex-shrink:0;}
.badge-instock{background:#f0fdf4;color:#16a34a;border-color:#bbf7d0;}
.badge-instock .badge-dot{background:#16a34a;}
.badge-lowstock{background:#fffbeb;color:#d97706;border-color:#fde68a;}
.badge-lowstock .badge-dot{background:#d97706;}
.badge-inuse{background:#eff6ff;color:#2563eb;border-color:#bfdbfe;}
.badge-inuse .badge-dot{background:#2563eb;}
.badge-empty{background:#fef2f2;color:#dc2626;border-color:#fecaca;}
.badge-empty .badge-dot{background:#dc2626;}
.badge-available{background:#f0fdf4;color:#16a34a;border-color:#bbf7d0;}
.badge-available .badge-dot{background:#16a34a;}
.badge-loaded{background:#eff6ff;color:#2563eb;border-color:#bfdbfe;}
.badge-loaded .badge-dot{background:#2563eb;}
.badge-maintenance{background:#fffbeb;color:#d97706;border-color:#fde68a;}
.badge-maintenance .badge-dot{background:#d97706;}

/* Buttons */
.btn-primary{padding:8px 16px;background:#2563eb;color:#fff;border:none;border-radius:8px;font-size:13px;font-weight:600;display:inline-flex;align-items:center;gap:6px;}
.btn-ghost{padding:6px 10px;background:transparent;color:#64748b;border:1px solid #e2e8f0;border-radius:6px;font-size:12px;display:inline-flex;align-items:center;gap:4px;}
.btn-danger{padding:6px 10px;background:transparent;color:#ef4444;border:1px solid #fecaca;border-radius:6px;font-size:12px;}
.page-header{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:20px;}

/* Search bar */
.search-wrap{display:flex;align-items:center;gap:8px;padding:8px 12px;border:1px solid #e2e8f0;border-radius:8px;background:#f8fafc;margin-bottom:14px;}
.search-wrap input{border:none;background:transparent;font-size:13px;color:#334155;width:280px;outline:none;}

/* Scanner */
.scan-row{display:flex;gap:10px;margin-bottom:8px;}
.scan-input-wrap{flex:1;display:flex;align-items:center;gap:10px;padding:10px 14px;border:2px solid #3b82f6;border-radius:8px;background:#fff;}
.scan-input-wrap input{border:none;outline:none;font-size:14px;color:#334155;width:100%;}
.scan-hint{font-size:12px;color:#94a3b8;margin-bottom:0;}
.scan-result{margin-top:16px;}
.result-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:14px;}
.result-field label{font-size:11px;color:#94a3b8;font-weight:500;}
.result-field div{font-size:13px;color:#0f172a;font-weight:500;}
.led-activated{margin-top:14px;padding:12px 14px;background:#fefce8;border-radius:8px;border:1px solid #fde68a;display:flex;align-items:center;gap:10px;}
.led-activated-title{font-size:13px;font-weight:600;color:#92400e;}
.led-activated-sub{font-size:12px;color:#b45309;}
.quick-chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px;}
.chip{padding:4px 12px;border-radius:20px;border:1px solid #e2e8f0;background:#f8fafc;font-size:12px;color:#334155;font-family:monospace;}

/* Layout */
.section-header{display:flex;align-items:center;gap:12px;margin-bottom:14px;}
.section-tag{padding:3px 12px;border-radius:6px;background:#eff6ff;border:1px solid #bfdbfe;font-size:13px;font-weight:700;color:#2563eb;}
.progress-bar-wrap{flex:1;height:4px;background:#f1f5f9;border-radius:2px;overflow:hidden;}
.progress-bar{height:100%;background:linear-gradient(90deg,#3b82f6,#8b5cf6);border-radius:2px;transition:width 0.4s;}
.slot-row{display:flex;gap:5px;margin-bottom:5px;overflow-x:auto;padding-bottom:2px;}
.slot{width:44px;height:48px;border-radius:6px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;cursor:default;transition:all 0.2s;flex-shrink:0;border:1.5px solid #e2e8f0;background:#f8fafc;}
.slot.has-reel{cursor:pointer;}
.slot.glowing{border:2px solid #fbbf24!important;background:linear-gradient(135deg,#fef9c3,#fde68a)!important;box-shadow:0 0 0 3px #fde047,0 0 16px #fbbf2488!important;transform:scale(1.08);animation:slotGlow 0.7s ease-in-out infinite alternate;}
.slot-led{width:6px;height:6px;border-radius:50%;background:#e2e8f0;}
.slot.has-reel .slot-led{background:#16a34a;}
.slot.glowing .slot-led{background:#fff!important;}
.slot-num{font-size:9px;font-weight:700;color:#94a3b8;line-height:1;}
.slot.has-reel .slot-num{color:#334155;}
.slot.glowing .slot-num{color:#92400e!important;}
.slot-pkg{font-size:7px;color:#94a3b8;max-width:40px;overflow:hidden;white-space:nowrap;text-overflow:ellipsis;text-align:center;}
.slot.has-reel .slot-pkg{color:#64748b;}
.slot.glowing .slot-pkg{color:#78350f!important;}
.layout-legend{display:flex;gap:14px;align-items:center;font-size:12px;color:#64748b;}
.legend-dot{width:10px;height:10px;border-radius:50%;}

/* Activity */
.act-row{display:flex;align-items:flex-start;gap:14px;padding:14px 0;border-bottom:1px solid #f1f5f9;}
.act-icon{width:32px;height:32px;border-radius:8px;background:#f8fafc;border:1px solid #e2e8f0;display:flex;align-items:center;justify-content:center;font-size:14px;flex-shrink:0;}
.act-body{flex:1;min-width:0;}
.act-tags{display:flex;align-items:center;gap:8px;margin-bottom:2px;}
.act-action{padding:2px 8px;border-radius:4px;background:#eff6ff;color:#2563eb;font-size:11px;font-weight:600;}
.act-ref{font-size:12px;font-weight:600;color:#334155;font-family:monospace;}
.act-detail{font-size:13px;color:#64748b;}
.act-time{font-size:11px;color:#94a3b8;white-space:nowrap;}

/* Modal */
.modal-overlay{position:fixed;inset:0;background:rgba(0,0,0,0.4);z-index:500;display:flex;align-items:center;justify-content:center;}
.modal{background:#fff;border-radius:12px;padding:24px;width:480px;max-width:90vw;box-shadow:0 20px 60px rgba(0,0,0,0.2);animation:modalIn 0.2s ease;}
.modal-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;}
.modal-title{font-size:16px;font-weight:600;color:#0f172a;}
.modal-close{border:none;background:none;font-size:20px;color:#94a3b8;line-height:1;}
.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;}
.form-grid .full{grid-column:1/-1;}
.form-group label{display:block;font-size:12px;font-weight:500;color:#64748b;margin-bottom:4px;}
.form-group input,.form-group select{width:100%;padding:8px 12px;border:1px solid #e2e8f0;border-radius:6px;font-size:13px;color:#0f172a;background:#fff;}
.modal-footer{display:flex;justify-content:flex-end;gap:10px;margin-top:20px;}

/* Toast */
#toast{position:fixed;top:16px;left:50%;transform:translateX(-50%);z-index:9999;padding:10px 20px;border-radius:8px;font-size:13px;font-weight:500;display:none;align-items:center;gap:8px;box-shadow:0 4px 20px rgba(0,0,0,0.12);animation:toastIn 0.2s ease;}
#toast.ok{background:#f0fdf4;color:#15803d;border:1px solid #86efac;}
#toast.err{background:#fef2f2;color:#dc2626;border:1px solid #fca5a5;}

@keyframes slotGlow{from{box-shadow:0 0 0 3px #fde047,0 0 12px #fbbf2488;}to{box-shadow:0 0 0 5px #fde047,0 0 28px #fbbf24bb;}}
@keyframes modalIn{from{opacity:0;transform:scale(0.96);}to{opacity:1;transform:scale(1);}}
@keyframes toastIn{from{opacity:0;transform:translateX(-50%) translateY(-8px);}to{opacity:1;transform:translateX(-50%) translateY(0);}}
@keyframes ledBlink{0%,100%{opacity:1;}50%{opacity:0.3;}}
</style>

</head>
<body>

<!-- SIDEBAR -->

<div id="sidebar">
<div class="logo">
<div class="logo-icon">⚡</div>
<div><div class="logo-text">L&P SMT</div><div class="logo-sub">Organizer</div></div>
</div>
<nav>
<button class="nav-btn active" onclick="showPage('dashboard',this)">⊞ &nbsp;Dashboard</button>
<button class="nav-btn" onclick="showPage('reels',this)">◎ &nbsp;Reels</button>
<button class="nav-btn" onclick="showPage('feeders',this)">≡ &nbsp;Feeders</button>
<button class="nav-btn" onclick="showPage('scanner',this)">▣ &nbsp;Barcode Scanner</button>
<button class="nav-btn" onclick="showPage('layout',this)">⌗ &nbsp;Machine Layout</button>
<button class="nav-btn" onclick="showPage('log',this)">☰ &nbsp;Activity Log</button>
</nav>
<div class="led-status">
<div class="led-box" id="led-box">
<span id="led-icon">💡</span>
<div><div class="led-label">LED Controller</div><div class="led-sub" id="led-sub">Idle</div></div>
</div>
</div>
</div>

<!-- MAIN -->

<div id="main">

<!-- DASHBOARD -->

<div class="page active" id="page-dashboard">
<h1>Dashboard</h1>
<p class="page-sub">L&amp;P SMT Reel &amp; Feeder Organizer</p>
<div class="stat-grid" id="stat-grid"></div>
<div class="two-col">
<div class="card">
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
<h3 style="font-size:15px;font-weight:600;color:#0f172a;">Recent Reels</h3>
<button class="btn-ghost" onclick="showPage('reels',document.querySelectorAll('.nav-btn')[1])">View all →</button>
</div>
<div id="dash-reels"></div>
</div>
<div class="card">
<div style="display:flex;align-items:center;gap:6px;margin-bottom:14px;">
<span style="color:#d97706;">⚠</span>
<h3 style="font-size:15px;font-weight:600;color:#0f172a;">Alerts</h3>
</div>
<div id="dash-alerts"></div>
</div>
</div>
</div>

<!-- REELS -->

<div class="page" id="page-reels">
<div class="page-header">
<div><h1>Reels</h1><p class="page-sub" id="reels-sub"></p></div>
<button class="btn-primary" onclick="openModal('add-reel')">+ Add Reel</button>
</div>
<div class="card">
<div class="search-wrap">
<span style="color:#94a3b8;">🔍</span>
<input id="reel-search" placeholder="Search by barcode, part, location..." oninput="renderReels()"/>
</div>
<div class="tbl-wrap">
<table><thead><tr>
<th>LED</th><th>Barcode</th><th>Part Number</th><th>Pkg</th><th>Qty</th><th>Location</th><th>Status</th><th>Actions</th>
</tr></thead><tbody id="reels-tbody"></tbody></table>
</div>
</div>
</div>

<!-- FEEDERS -->

<div class="page" id="page-feeders">
<div class="page-header">
<div><h1>Feeders</h1><p class="page-sub" id="feeders-sub"></p></div>
<button class="btn-primary" onclick="openModal('add-feeder')">+ Add Feeder</button>
</div>
<div class="card">
<div class="search-wrap">
<span style="color:#94a3b8;">🔍</span>
<input id="feeder-search" placeholder="Search feeders..." oninput="renderFeeders()"/>
</div>
<div class="tbl-wrap">
<table><thead><tr>
<th>LED</th><th>Feeder ID</th><th>Slot</th><th>Machine</th><th>Type</th><th>Loaded Reel</th><th>Status</th><th>Actions</th>
</tr></thead><tbody id="feeders-tbody"></tbody></table>
</div>
</div>
</div>

<!-- SCANNER -->

<div class="page" id="page-scanner">
<h1>Barcode Scanner</h1>
<p class="page-sub">Scan a reel or feeder barcode to find and manage it</p>
<div class="card">
<div class="scan-row">
<div class="scan-input-wrap">
<span style="font-size:18px;">▣</span>
<input id="scan-input" placeholder="Scan or type barcode..." onkeydown="if(event.key==='Enter')doScan()"/>
</div>
<button class="btn-primary" onclick="doScan()">🔍 Find</button>
</div>
<p class="scan-hint">• Ready to scan — point barcode scanner at this field</p>
</div>
<div id="scan-result"></div>
<div class="card">
<div style="font-size:12px;font-weight:600;color:#64748b;margin-bottom:10px;">Quick test barcodes</div>
<div class="quick-chips" id="quick-chips"></div>
</div>
</div>

<!-- LAYOUT -->

<div class="page" id="page-layout">
<div class="page-header">
<div>
<h1>Machine Layout</h1>
<p class="page-sub" id="layout-sub"></p>
</div>
<div class="layout-legend">
<div style="display:flex;align-items:center;gap:5px;"><div class="legend-dot" style="background:#16a34a;"></div>In Stock</div>
<div style="display:flex;align-items:center;gap:5px;"><div class="legend-dot" style="background:#d97706;"></div>Low Stock</div>
<div style="display:flex;align-items:center;gap:5px;"><div class="legend-dot" style="background:#2563eb;"></div>In Use</div>
<div style="display:flex;align-items:center;gap:5px;"><div class="legend-dot" style="background:#dc2626;"></div>Empty</div>
<div style="display:flex;align-items:center;gap:5px;">💡 Active LED</div>
</div>
</div>
<div id="layout-grid"></div>
</div>

<!-- LOG -->

<div class="page" id="page-log">
<h1>Activity Log</h1>
<p class="page-sub">Recent scan and action history</p>
<div class="card" id="act-log"></div>
</div>

</div>

<!-- TOAST -->

<div id="toast"></div>

<!-- MODALS -->

<div id="modal-overlay" class="modal-overlay" style="display:none;" onclick="closeModal()">
<div class="modal" onclick="event.stopPropagation()">
<div class="modal-header">
<div class="modal-title" id="modal-title"></div>
<button class="modal-close" onclick="closeModal()">×</button>
</div>
<div id="modal-body"></div>
</div>
</div>

<script>
// ── State ──────────────────────────────────────────────────────────────────
let reels = [], feeders = [], glowId = null, glowTimer = null;
const SECTIONS = ['A','B','C','D'];
const SLOTS = 32;

// ── API helpers ────────────────────────────────────────────────────────────
async function api(path, method='GET', body=null){
 const opts = {method, headers:{'Content-Type':'application/json'}};
 if(body) opts.body = JSON.stringify(body);
 const r = await fetch(path, opts);
 return r.json();
}

// ── Toast ──────────────────────────────────────────────────────────────────
function toast(msg, type='ok'){
 const t = document.getElementById('toast');
 t.textContent = (type==='ok'?'✓ ':'✗ ') + msg;
 t.className = type; t.style.display='flex';
 setTimeout(()=>t.style.display='none', 3500);
}

// ── LED ────────────────────────────────────────────────────────────────────
function activateLED(reel){
 if(glowTimer) clearTimeout(glowTimer);
 glowId = reel.id;
 const box = document.getElementById('led-box');
 const sub = document.getElementById('led-sub');
 box.classList.add('active');
 sub.textContent = 'Active: ' + reel.loc;
 sub.style.animation = 'ledBlink 1s infinite';
 renderLayout();
 glowTimer = setTimeout(()=>{
   glowId = null;
   box.classList.remove('active');
   sub.textContent = 'Idle';
   sub.style.animation = 'none';
   renderLayout();
 }, 9000);
 api('/api/log','POST',{action:'Locate',ref:reel.id,detail:'LED activated for location '+reel.loc,icon:'💡'});
}

// ── Badge ──────────────────────────────────────────────────────────────────
function badge(status){
 const map = {'In Stock':'instock','Low Stock':'lowstock','In Use':'inuse','Empty':'empty','Available':'available','Loaded':'loaded','Maintenance':'maintenance'};
 const cls = map[status]||'instock';
 return `<span class="badge badge-${cls}"><span class="badge-dot"></span>${status}</span>`;
}

// ── Nav ────────────────────────────────────────────────────────────────────
function showPage(id, btn){
 document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
 document.querySelectorAll('.nav-btn').forEach(b=>b.classList.remove('active'));
 document.getElementById('page-'+id).classList.add('active');
 if(btn) btn.classList.add('active');
 if(id==='dashboard') renderDashboard();
 if(id==='reels') renderReels();
 if(id==='feeders') renderFeeders();
 if(id==='layout') renderLayout();
 if(id==='log') renderLog();
 if(id==='scanner'){
   renderQuickChips();
   setTimeout(()=>document.getElementById('scan-input').focus(),100);
 }
}

// ── Dashboard ─────────────────────────────────────────────────────────────
async function renderDashboard(){
 reels = await api('/api/reels');
 feeders = await api('/api/feeders');
 const lowStock = reels.filter(r=>r.status==='Low Stock');
 const empty = reels.filter(r=>r.status==='Empty');
 const avail = feeders.filter(f=>f.status==='Available');
 const stats = [
   {label:'TOTAL REELS', value:reels.length, sub:reels.filter(r=>r.status==='In Use').length+' in use', icon:'◎', bg:'#eff6ff'},
   {label:'FEEDERS', value:feeders.length, sub:avail.length+' available', icon:'≡', bg:'#f5f3ff'},
   {label:'LOW STOCK', value:lowStock.length, sub:'Need attention', icon:'⚠', bg:'#fffbeb'},
   {label:'ACTIVE LEDS', value:glowId?1:0, sub:glowId?'Currently locating':'All idle', icon:'💡', bg:glowId?'#fefce8':'#f8fafc'},
 ];
 document.getElementById('stat-grid').innerHTML = stats.map(s=>`
<div class="stat-card">
<div>
<div class="stat-label">${s.label}</div>
<div class="stat-value">${s.value}</div>
<div class="stat-sub">${s.sub}</div>
</div>
<div class="stat-icon" style="background:${s.bg}">${s.icon}</div>
</div>`).join('');

 document.getElementById('dash-reels').innerHTML = reels.slice(0,5).map(r=>`
<div style="display:flex;align-items:center;justify-content:space-between;padding:8px 0;border-bottom:1px solid #f8fafc;">
<div>
<div style="font-size:13px;font-weight:500;color:#0f172a;">${r.part}</div>
<div style="font-size:11px;color:#94a3b8;">${r.id}</div>
</div>
<div style="display:flex;align-items:center;gap:8px;">
<span style="font-size:12px;color:#64748b;">Qty: ${Number(r.qty).toLocaleString()}</span>
       ${badge(r.status)}
</div>
</div>`).join('');

 const alerts = [...empty,...lowStock];
 document.getElementById('dash-alerts').innerHTML = alerts.length===0
   ? '<div style="text-align:center;padding:20px 0;color:#94a3b8;font-size:13px;">✓ No alerts</div>'
   : alerts.map(r=>`
<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid #f8fafc;">
<div>
<div style="font-size:13px;font-weight:500;color:#0f172a;">${r.part}</div>
<div style="font-size:11px;color:#94a3b8;">${r.status==='Empty'?'Empty reel':r.qty+' remaining'}</div>
</div>
       ${badge(r.status)}
</div>`).join('');
}

// ── Reels ──────────────────────────────────────────────────────────────────
async function renderReels(){
 reels = await api('/api/reels');
 document.getElementById('reels-sub').textContent = reels.length + ' total reels';
 const q = document.getElementById('reel-search').value.toLowerCase();
 const filtered = reels.filter(r=>!q||r.barcode.toLowerCase().includes(q)||r.part.toLowerCase().includes(q)||r.loc.toLowerCase().includes(q));
 document.getElementById('reels-tbody').innerHTML = filtered.map(r=>`
<tr style="background:${glowId===r.id?'#fefce8':'transparent'}">
<td><button onclick="activateLED(${JSON.stringify(r).replace(/"/g,'&quot;')})" style="border:none;background:none;font-size:18px;cursor:pointer;" title="Activate LED">${glowId===r.id?'💡':'🔦'}</button></td>
<td style="font-family:monospace;font-size:12px;">${r.barcode}</td>
<td style="font-weight:500;">${r.part}</td>
<td>${r.pkg}</td>
<td style="color:${r.qty==0?'#ef4444':r.qty<500?'#d97706':'#334155'}">${Number(r.qty).toLocaleString()}</td>
<td style="font-family:monospace;font-size:12px;">${r.loc}</td>
<td>${badge(r.status)}</td>
<td>
<div style="display:flex;gap:6px;">
<button class="btn-ghost" onclick='openEditReel(${JSON.stringify(r)})'>✏</button>
<button class="btn-danger" onclick="deleteReel('${r.id}')">🗑</button>
</div>
</td>
</tr>`).join('');
}

async function deleteReel(id){
 if(!confirm('Delete this reel?')) return;
 await api('/api/reels/'+id,'DELETE');
 toast('Reel removed');
 renderReels();
 renderDashboard();
}

// ── Feeders ────────────────────────────────────────────────────────────────
async function renderFeeders(){
 feeders = await api('/api/feeders');
 document.getElementById('feeders-sub').textContent = feeders.length + ' total feeders';
 const q = document.getElementById('feeder-search').value.toLowerCase();
 const filtered = feeders.filter(f=>!q||f.id.toLowerCase().includes(q)||f.machine.toLowerCase().includes(q));
 document.getElementById('feeders-tbody').innerHTML = filtered.map(f=>`
<tr>
<td><button onclick="locateFeeder('${f.id}')" style="border:none;background:none;font-size:18px;cursor:pointer;" title="Locate feeder">🔦</button></td>
<td style="font-family:monospace;font-weight:600;">${f.id}</td>
<td>${f.slot}</td>
<td>${f.machine}</td>
<td>${f.type}</td>
<td style="font-family:monospace;font-size:12px;color:${f.loaded_reel?'#334155':'#94a3b8'}">${f.loaded_reel||'–'}</td>
<td>${badge(f.status)}</td>
<td>
<div style="display:flex;gap:6px;">
<button class="btn-ghost" onclick='openEditFeeder(${JSON.stringify(f)})'>✏</button>
<button class="btn-danger" onclick="deleteFeeder('${f.id}')">🗑</button>
</div>
</td>
</tr>`).join('');
}

async function locateFeeder(id){
 const f = feeders.find(x=>x.id===id);
 if(f && f.loaded_reel){
   const r = reels.find(x=>x.part===f.loaded_reel);
   if(r){ activateLED(r); return; }
 }
 toast('Feeder '+id+' — no reel loaded');
 api('/api/log','POST',{action:'Locate',ref:id,detail:'Located feeder '+id,icon:'💡'});
}

async function deleteFeeder(id){
 if(!confirm('Delete this feeder?')) return;
 await api('/api/feeders/'+id,'DELETE');
 toast('Feeder removed');
 renderFeeders();
}

// ── Scanner ────────────────────────────────────────────────────────────────
async function doScan(){
 const code = document.getElementById('scan-input').value.trim();
 if(!code) return;
 const res = await api('/api/scan','POST',{code});
 document.getElementById('scan-input').value='';
 const el = document.getElementById('scan-result');
 if(!res.found){
   el.innerHTML=`<div class="card"><div style="text-align:center;padding:20px 0;"><div style="font-size:32px;margin-bottom:8px;">✗</div><div style="font-size:15px;font-weight:600;color:#dc2626;">Not Found</div><div style="font-size:13px;color:#94a3b8;">No reel or feeder matches "${code}"</div></div></div>`;
   return;
 }
 if(res.type==='reel'){
   const r=res.item;
   activateLED(r);
   reels = await api('/api/reels');
   el.innerHTML=`<div class="card">
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
<h3 style="font-size:15px;font-weight:600;">Reel Found</h3>${badge(r.status)}
</div>
<div class="result-grid">
<div class="result-field"><label>Barcode</label><div style="font-family:monospace">${r.barcode}</div></div>
<div class="result-field"><label>Part Number</label><div>${r.part}</div></div>
<div class="result-field"><label>Package</label><div>${r.pkg}</div></div>
<div class="result-field"><label>Quantity</label><div>${Number(r.qty).toLocaleString()}</div></div>
<div class="result-field"><label>Location</label><div style="font-family:monospace">${r.loc}</div></div>
</div>
<div class="led-activated">
       💡 <div><div class="led-activated-title">LED Activated</div><div class="led-activated-sub">Location ${r.loc} is now glowing on the machine layout</div></div>
</div>
</div>`;
   toast('Found: '+r.part+' → '+r.loc);
 } else {
   const f=res.item;
   el.innerHTML=`<div class="card">
<h3 style="font-size:15px;font-weight:600;margin-bottom:14px;">Feeder Found</h3>
<div class="result-grid">
<div class="result-field"><label>Feeder ID</label><div>${f.id}</div></div>
<div class="result-field"><label>Machine</label><div>${f.machine}</div></div>
<div class="result-field"><label>Slot</label><div>${f.slot}</div></div>
<div class="result-field"><label>Type</label><div>${f.type}</div></div>
<div class="result-field"><label>Loaded Reel</label><div>${f.loaded_reel||'None'}</div></div>
<div class="result-field"><label>Status</label><div>${badge(f.status)}</div></div>
</div>
</div>`;
   toast('Feeder found: '+f.id);
 }
}

function renderQuickChips(){
 document.getElementById('quick-chips').innerHTML = reels.map(r=>
   `<button class="chip" onclick="document.getElementById('scan-input').value='${r.barcode}';doScan();">${r.barcode}</button>`
 ).join('');
}

// ── Layout ─────────────────────────────────────────────────────────────────
function reelToGridPos(reel){
 const sec = reel.loc.charAt(0);
 const m = reel.loc.match(/(\d+)/);
 const slot = m ? Math.min(parseInt(m[1]),SLOTS) : 1;
 return {section:sec, slot};
}

async function renderLayout(){
 if(!reels.length) reels = await api('/api/reels');
 const SCOLS = {'In Stock':'#16a34a','Low Stock':'#d97706','In Use':'#2563eb','Empty':'#dc2626'};
 const SBGS  = {'In Stock':'#f0fdf4','Low Stock':'#fffbeb','In Use':'#eff6ff','Empty':'#fef2f2'};
 document.getElementById('layout-sub').textContent = `4 sections × ${SLOTS} slots — ${reels.length} reels loaded, ${feeders.length} feeders assigned`;

 const gridData = {};
 SECTIONS.forEach(s=>{gridData[s]={};});
 reels.forEach(r=>{
   const {section,slot} = reelToGridPos(r);
   if(gridData[section]) gridData[section][slot]=r;
 });

 document.getElementById('layout-grid').innerHTML = SECTIONS.map(sec=>{
   const secReels = reels.filter(r=>reelToGridPos(r).section===sec);
   const pct = Math.round((secReels.length/SLOTS)*100);
   const rows = [
     Array.from({length:16},(_,i)=>i+1),
     Array.from({length:16},(_,i)=>i+17)
   ];
   return `<div class="card">
<div class="section-header">
<span class="section-tag">Section ${sec}</span>
<span style="font-size:12px;color:#64748b;">${secReels.length}/${SLOTS} slots loaded</span>
<div class="progress-bar-wrap"><div class="progress-bar" style="width:${pct}%"></div></div>
<span style="font-size:11px;color:#94a3b8;">${pct}%</span>
</div>
     ${rows.map(row=>`
<div class="slot-row">
         ${row.map(n=>{
           const r=gridData[sec]?.[n];
           const glow=r&&glowId===r.id;
           const sc=r?SCOLS[r.status]:'#94a3b8';
           const sbg=r?SBGS[r.status]:'#f8fafc';
           return `<div class="slot${r?' has-reel':''}${glow?' glowing':''}"
             style="${r?`border-color:${sc}44;background:${sbg};`:''}"
             title="${r?r.part+' ('+r.barcode+')':'Slot '+n+' – Empty'}"
             onclick="${r?`activateLEDById('${r.id}')`:''}"
>
<div class="slot-led" style="${r?`background:${sc};`:''} ${glow?'background:#fff!important;':''}""></div>
<div class="slot-num" style="${r?`color:${sc};`:''}">${String(n).padStart(2,'0')}</div>
             ${r?`<div class="slot-pkg">${r.pkg}</div>`:''}
</div>`;
         }).join('')}
</div>`).join('')}
</div>`;
 }).join('');
}

function activateLEDById(id){
 const r = reels.find(x=>x.id===id);
 if(r) activateLED(r);
}

// ── Log ────────────────────────────────────────────────────────────────────
async function renderLog(){
 const logs = await api('/api/activity');
 document.getElementById('act-log').innerHTML = logs.length===0
   ? '<div style="text-align:center;padding:40px 0;color:#94a3b8;font-size:13px;">No activity yet</div>'
   : logs.map(l=>`
<div class="act-row">
<div class="act-icon">${l.icon||'💡'}</div>
<div class="act-body">
<div class="act-tags">
<span class="act-action">${l.action}</span>
<span class="act-ref">${l.ref}</span>
</div>
<div class="act-detail">${l.detail}</div>
</div>
<div class="act-time">${l.created_at}</div>
</div>`).join('');
}

// ── Modals ─────────────────────────────────────────────────────────────────
function openModal(type){
 document.getElementById('modal-overlay').style.display='flex';
 if(type==='add-reel'){
   document.getElementById('modal-title').textContent='Add New Reel';
   document.getElementById('modal-body').innerHTML=`
<div class="form-grid">
<div class="form-group full"><label>Barcode *</label><input id="f-barcode" placeholder="REL-2024-00150"/></div>
<div class="form-group full"><label>Part Number *</label><input id="f-part" placeholder="RC0402FR-071KL"/></div>
<div class="form-group"><label>Package</label>
<select id="f-pkg"><option>0402</option><option>0603</option><option>0805</option><option>1206</option><option>SOT23</option><option>QFP</option><option>SOIC8</option></select>
</div>
<div class="form-group"><label>Quantity *</label><input id="f-qty" type="number" placeholder="5000"/></div>
<div class="form-group"><label>Location *</label><input id="f-loc" placeholder="A2-B08"/></div>
<div class="form-group"><label>Status</label>
<select id="f-status"><option>In Stock</option><option>Low Stock</option><option>In Use</option><option>Empty</option></select>
</div>
</div>
<div class="modal-footer">
<button class="btn-ghost" onclick="closeModal()">Cancel</button>
<button class="btn-primary" onclick="submitAddReel()">Add Reel</button>
</div>`;
 } else if(type==='add-feeder'){
   document.getElementById('modal-title').textContent='Add New Feeder';
   document.getElementById('modal-body').innerHTML=`
<div class="form-grid">
<div class="form-group"><label>Feeder ID *</label><input id="ff-id" placeholder="F-006"/></div>
<div class="form-group"><label>Slot *</label><input id="ff-slot" type="number" placeholder="10"/></div>
<div class="form-group full"><label>Machine *</label><input id="ff-machine" placeholder="Line 1 - Juki RS-1"/></div>
<div class="form-group"><label>Tape Type</label>
<select id="ff-type"><option>8mm</option><option>12mm</option><option>16mm</option><option>24mm</option></select>
</div>
<div class="form-group"><label>Status</label>
<select id="ff-status"><option>Available</option><option>Loaded</option><option>Maintenance</option></select>
</div>
</div>
<div class="modal-footer">
<button class="btn-ghost" onclick="closeModal()">Cancel</button>
<button class="btn-primary" onclick="submitAddFeeder()">Add Feeder</button>
</div>`;
 }
}

function openEditReel(r){
 document.getElementById('modal-overlay').style.display='flex';
 document.getElementById('modal-title').textContent='Edit Reel';
 document.getElementById('modal-body').innerHTML=`
<div class="form-grid">
<div class="form-group full"><label>Barcode</label><input id="ef-barcode" value="${r.barcode}" readonly style="background:#f8fafc;"/></div>
<div class="form-group full"><label>Part Number</label><input id="ef-part" value="${r.part}"/></div>
<div class="form-group"><label>Package</label><input id="ef-pkg" value="${r.pkg}"/></div>
<div class="form-group"><label>Quantity</label><input id="ef-qty" type="number" value="${r.qty}"/></div>
<div class="form-group"><label>Location</label><input id="ef-loc" value="${r.loc}"/></div>
<div class="form-group"><label>Status</label>
<select id="ef-status">
         ${['In Stock','Low Stock','In Use','Empty'].map(s=>`<option${s===r.status?' selected':''}>${s}</option>`).join('')}
</select>
</div>
</div>
<div class="modal-footer">
<button class="btn-ghost" onclick="closeModal()">Cancel</button>
<button class="btn-primary" onclick="submitEditReel('${r.id}')">Save Changes</button>
</div>`;
}

function openEditFeeder(f){
 document.getElementById('modal-overlay').style.display='flex';
 document.getElementById('modal-title').textContent='Edit Feeder';
 document.getElementById('modal-body').innerHTML=`
<div class="form-grid">
<div class="form-group"><label>Feeder ID</label><input id="eff-id" value="${f.id}" readonly style="background:#f8fafc;"/></div>
<div class="form-group"><label>Slot</label><input id="eff-slot" type="number" value="${f.slot}"/></div>
<div class="form-group full"><label>Machine</label><input id="eff-machine" value="${f.machine}"/></div>
<div class="form-group"><label>Tape Type</label><input id="eff-type" value="${f.type}"/></div>
<div class="form-group"><label>Loaded Reel</label><input id="eff-loaded" value="${f.loaded_reel||''}"/></div>
<div class="form-group"><label>Status</label>
<select id="eff-status">
         ${['Available','Loaded','Maintenance'].map(s=>`<option${s===f.status?' selected':''}>${s}</option>`).join('')}
</select>
</div>
</div>
<div class="modal-footer">
<button class="btn-ghost" onclick="closeModal()">Cancel</button>
<button class="btn-primary" onclick="submitEditFeeder('${f.id}')">Save Changes</button>
</div>`;
}

function closeModal(){ document.getElementById('modal-overlay').style.display='none'; }

async function submitAddReel(){
 const data={barcode:document.getElementById('f-barcode').value,part:document.getElementById('f-part').value,pkg:document.getElementById('f-pkg').value,qty:document.getElementById('f-qty').value,loc:document.getElementById('f-loc').value,status:document.getElementById('f-status').value};
 if(!data.barcode||!data.part||!data.qty||!data.loc){toast('Fill all required fields','err');return;}
 const res=await api('/api/reels','POST',data);
 if(!res.ok){toast(res.error||'Error','err');return;}
 toast('Reel added');closeModal();reels=await api('/api/reels');renderReels();renderDashboard();
}

async function submitAddFeeder(){
 const data={id:document.getElementById('ff-id').value,slot:document.getElementById('ff-slot').value,machine:document.getElementById('ff-machine').value,type:document.getElementById('ff-type').value,status:document.getElementById('ff-status').value};
 if(!data.id||!data.slot||!data.machine){toast('Fill all required fields','err');return;}
 const res=await api('/api/feeders','POST',data);
 if(!res.ok){toast(res.error||'Error','err');return;}
 toast('Feeder added');closeModal();feeders=await api('/api/feeders');renderFeeders();
}

async function submitEditReel(id){
 const data={part:document.getElementById('ef-part').value,pkg:document.getElementById('ef-pkg').value,qty:document.getElementById('ef-qty').value,loc:document.getElementById('ef-loc').value,status:document.getElementById('ef-status').value};
 await api('/api/reels/'+id,'PUT',data);
 toast('Reel updated');closeModal();reels=await api('/api/reels');renderReels();renderDashboard();renderLayout();
}

async function submitEditFeeder(id){
 const data={slot:document.getElementById('eff-slot').value,machine:document.getElementById('eff-machine').value,type:document.getElementById('eff-type').value,loaded_reel:document.getElementById('eff-loaded').value||null,status:document.getElementById('eff-status').value};
 await api('/api/feeders/'+id,'PUT',data);
 toast('Feeder updated');closeModal();feeders=await api('/api/feeders');renderFeeders();
}

// ── Init ───────────────────────────────────────────────────────────────────
(async()=>{
 reels = await api('/api/reels');
 feeders = await api('/api/feeders');
 renderDashboard();
})();
</script>

</body>
</html>"""

# ─── Run ───────────────────────────────────────────────────────────────────────

if **name** == “**main**”:
init_db()
print(”\n✅  L&P SMT Organizer is running!”)
print(“📡  Open your browser at: http://localhost:5000”)
print(“🌐  Or from another device: http://172.16.100.4:5000”)
print(”    Press CTRL+C to stop\n”)
app.run(host=“0.0.0.0”, port=5000, debug=False)
