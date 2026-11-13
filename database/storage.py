"""Lưu hồ sơ và lần khám cục bộ bằng SQLite. Không lưu ảnh tải lên."""
import sqlite3, json, uuid
from pathlib import Path
from datetime import datetime
DB_PATH = Path(__file__).resolve().parents[1] / "data" / "phcn_ai.db"

def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con=sqlite3.connect(DB_PATH)
    con.row_factory=sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    return con

def init_db():
    with connect() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, phone TEXT NOT NULL UNIQUE,
            birth_year INTEGER, job TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)""")
        con.execute("""CREATE TABLE IF NOT EXISTS visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT, patient_id INTEGER NOT NULL,
            region TEXT NOT NULL, input_json TEXT NOT NULL, summary_text TEXT,
            analysis_json TEXT, report_text TEXT, created_at TEXT NOT NULL,
            FOREIGN KEY(patient_id) REFERENCES patients(id))""")
        con.execute("CREATE INDEX IF NOT EXISTS idx_visits_patient ON visits(patient_id, created_at DESC)")

def save_visit(patient, region, payload, summary_text, analysis, report):
    now=datetime.now().isoformat(timespec="seconds")
    with connect() as con:
        phone = str(patient.get('phone') or '').strip()
        # Tab 3 cho phép lưu chỉ với họ tên + năm sinh. Nếu không có SĐT,
        # tạo mã nội bộ để đáp ứng ràng buộc UNIQUE/NOT NULL của DB cũ mà không
        # hiển thị mã này như số điện thoại cho người dùng.
        patient_key = phone or f"PHCN-{uuid.uuid4().hex}"
        row = con.execute("SELECT id FROM patients WHERE phone=?", (patient_key,)).fetchone()
        if row:
            pid=row['id']
            con.execute("UPDATE patients SET name=?, birth_year=?, job=?, updated_at=? WHERE id=?",
                        (patient.get('name',''), patient.get('age'), patient.get('job',''), now, pid))
        else:
            cur=con.execute("INSERT INTO patients(name,phone,birth_year,job,created_at,updated_at) VALUES(?,?,?,?,?,?)",
                (patient.get('name',''),patient_key,patient.get('age'),patient.get('job',''),now,now))
            pid=cur.lastrowid
        cur=con.execute("INSERT INTO visits(patient_id,region,input_json,summary_text,analysis_json,report_text,created_at) VALUES(?,?,?,?,?,?,?)",
            (pid,region,json.dumps(payload,ensure_ascii=False),summary_text,
             json.dumps(analysis,ensure_ascii=False),report,now))
        return cur.lastrowid

def list_visits(limit=100):
    with connect() as con:
        return con.execute("""SELECT v.id, p.id AS patient_id, p.name, p.birth_year,
            CASE WHEN p.phone LIKE 'PHCN-%' THEN '' ELSE p.phone END AS phone,
            v.region, v.created_at
            FROM visits v JOIN patients p ON p.id=v.patient_id
            ORDER BY v.created_at DESC LIMIT ?""",(limit,)).fetchall()


def get_visit_detail(visit_id):
    """Lấy đầy đủ dữ liệu một lần khám để xem lại; không sửa dữ liệu gốc."""
    with connect() as con:
        row = con.execute("""SELECT v.*, p.name, p.phone, p.birth_year, p.job
            FROM visits v JOIN patients p ON p.id=v.patient_id WHERE v.id=?""", (int(visit_id),)).fetchone()
        if not row:
            return None
        item = dict(row)
        for key in ("input_json", "analysis_json"):
            try: item[key.replace("_json", "")] = json.loads(item[key] or "{}")
            except (TypeError, ValueError): item[key.replace("_json", "")] = {}
        return item

def list_patient_visits(phone, limit=100):
    """Tương thích ngược: tra cứu theo số điện thoại như các bản trước."""
    with connect() as con:
        return con.execute("""SELECT v.id, v.region, v.created_at, v.summary_text, v.analysis_json, p.name, p.phone
            FROM visits v JOIN patients p ON p.id=v.patient_id
            WHERE p.phone=? ORDER BY v.created_at ASC LIMIT ?""", (str(phone).strip(), int(limit))).fetchall()

def list_patient_visits_by_id(patient_id, limit=100):
    """Tra cứu theo ID nội bộ, hỗ trợ hồ sơ không cung cấp số điện thoại."""
    with connect() as con:
        return con.execute("""SELECT v.id, v.region, v.created_at, v.summary_text,
            v.analysis_json, p.name, p.phone, p.birth_year
            FROM visits v JOIN patients p ON p.id=v.patient_id
            WHERE p.id=? ORDER BY v.created_at ASC LIMIT ?""", (int(patient_id), int(limit))).fetchall()
