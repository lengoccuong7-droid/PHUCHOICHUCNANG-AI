"""Tab 5 độc lập: nhập dữ liệu thô, biên tập bảng, lưu và xuất CSV/XLSX.
Không đọc/ghi session dữ liệu lâm sàng hoặc dữ liệu của các tab khác.
"""
from __future__ import annotations

import csv
import io
import re
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "tab5_workspace"
ALLOWED_EXTENSIONS = {"csv", "txt", "tsv", "xlsx", "xls"}


def _clean_name(name: str) -> str:
    name = Path(str(name)).name.strip()
    name = re.sub(r"[^\w .()\-]+", "_", name, flags=re.UNICODE)
    name = re.sub(r"\s+", "_", name).strip("._")
    if not name:
        raise ValueError("Tên tệp không hợp lệ.")
    return name


def _unique_columns(columns):
    seen, result = {}, []
    for i, col in enumerate(columns, 1):
        name = str(col).strip() or f"Cột_{i}"
        n = seen.get(name, 0)
        seen[name] = n + 1
        result.append(name if n == 0 else f"{name}_{n+1}")
    return result


def detect_delimiter(text: str) -> str:
    lines = [line for line in text.splitlines() if line.strip()]
    sample = "\n".join(lines[:30])[:16000]
    if not sample:
        raise ValueError("Chưa có dữ liệu.")
    try:
        return csv.Sniffer().sniff(sample, delimiters="\t,;| ").delimiter
    except csv.Error:
        candidates = ["\t", "|", ";", ","]
        counts = {d: sum(line.count(d) for line in lines[:30]) for d in candidates}
        best = max(counts, key=counts.get)
        return best if counts[best] else "whitespace"


def parse_raw_text(raw_text: str, delimiter: str = "Tự nhận diện", first_row_header: bool = True) -> pd.DataFrame:
    if not isinstance(raw_text, str) or not raw_text.strip():
        raise ValueError("Ô văn bản thô đang trống.")
    sep = detect_delimiter(raw_text) if delimiter == "Tự nhận diện" else delimiter
    if sep == "whitespace":
        frame = pd.read_csv(io.StringIO(raw_text.strip()), sep=r"\s+", header=0 if first_row_header else None, engine="python", dtype=object, keep_default_na=False)
    else:
        frame = pd.read_csv(io.StringIO(raw_text.strip()), sep=sep, header=0 if first_row_header else None, engine="python", dtype=object, keep_default_na=False)
    if frame.shape[1] == 0:
        raise ValueError("Không nhận diện được cột. Hãy kiểm tra dữ liệu hoặc dấu phân cách.")
    if not first_row_header:
        frame.columns = [f"Cột_{i+1}" for i in range(len(frame.columns))]
    frame.columns = _unique_columns(frame.columns)
    return frame.fillna("")


def read_uploaded(uploaded) -> pd.DataFrame:
    name = uploaded.name.lower()
    ext = name.rsplit(".", 1)[-1] if "." in name else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError("Định dạng hỗ trợ: TXT, CSV, TSV, XLS và XLSX.")
    raw = uploaded.getvalue()
    if ext in {"xlsx", "xls"}:
        df = pd.read_excel(io.BytesIO(raw), dtype=object)
    else:
        decoded = None
        for enc in ("utf-8-sig", "utf-8", "cp1258", "cp1252", "latin1"):
            try:
                decoded = raw.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        if decoded is None:
            raise ValueError("Không giải mã được tệp văn bản. Hãy lưu lại dưới dạng UTF-8.")
        df = parse_raw_text(decoded)
    if df is None or len(df.columns) == 0:
        raise ValueError("Tệp không có bảng dữ liệu hợp lệ.")
    df.columns = _unique_columns(df.columns)
    return df.fillna("")


def _saved_path(filename: str) -> Path:
    safe = _clean_name(filename)
    path = (DATA_DIR / safe).resolve()
    if path.parent != DATA_DIR.resolve():
        raise ValueError("Đường dẫn không hợp lệ.")
    return path


def saved_files():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return sorted(p.name for p in DATA_DIR.iterdir() if p.is_file() and p.suffix.lower() in {".csv", ".xlsx"} and ".backup" not in p.name)


def load_saved(filename: str) -> pd.DataFrame:
    path = _saved_path(filename)
    if not path.exists():
        raise FileNotFoundError(filename)
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path, dtype=object, keep_default_na=False, encoding="utf-8-sig")
    return pd.read_excel(path, dtype=object).fillna("")


def save_table(df: pd.DataFrame, filename: str, overwrite: bool = False) -> tuple[Path, Path | None]:
    if df is None or len(df.columns) == 0:
        raise ValueError("Bảng chưa có cột dữ liệu.")
    name = _clean_name(filename)
    ext = Path(name).suffix.lower()
    if ext not in {".csv", ".xlsx"}:
        name += ".xlsx"
    path = _saved_path(name)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    backup = None
    if path.exists():
        if not overwrite:
            raise FileExistsError(f"{path.name} đã tồn tại. Chọn ghi đè hoặc đổi tên.")
        backup = path.with_name(f"{path.stem}.backup_{datetime.now():%Y%m%d_%H%M%S}{path.suffix}")
        shutil.copy2(path, backup)
    temp = path.with_name(path.stem + ".tmp" + path.suffix)
    try:
        if path.suffix.lower() == ".csv":
            df.to_csv(temp, index=False, encoding="utf-8-sig")
        else:
            df.to_excel(temp, index=False, engine="openpyxl")
        temp.replace(path)
    except Exception:
        if temp.exists():
            temp.unlink()
        raise
    return path, backup


def csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8-sig")


def excel_bytes(df: pd.DataFrame) -> bytes:
    bio = io.BytesIO()
    with pd.ExcelWriter(bio, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Du_lieu")
    return bio.getvalue()


def render():
    st.subheader("📊 Tab 5 – Nhập và xử lý dữ liệu thô")
    st.caption("Phân hệ độc lập. Dữ liệu tại đây không đưa vào hồ sơ, khám lâm sàng, phân tích hoặc theo dõi ở các tab khác.")

    if "tab5_df" not in st.session_state:
        st.session_state.tab5_df = pd.DataFrame()
    if "tab5_source_name" not in st.session_state:
        st.session_state.tab5_source_name = ""
    if "tab5_editor_version" not in st.session_state:
        st.session_state.tab5_editor_version = 0

    with st.expander("1. Nhập dữ liệu", expanded=True):
        uploaded = st.file_uploader("Tải tệp từ thiết bị", type=sorted(ALLOWED_EXTENSIONS), key="tab5_upload")
        if uploaded is not None and st.button("Đọc tệp vào bảng", key="tab5_read_upload"):
            try:
                st.session_state.tab5_df = read_uploaded(uploaded)
                st.session_state.tab5_editor_version += 1
                st.session_state.tab5_source_name = Path(uploaded.name).stem
                st.success(f"Đã đọc {len(st.session_state.tab5_df)} dòng × {len(st.session_state.tab5_df.columns)} cột.")
            except Exception as exc:
                st.error(f"Không đọc được tệp: {exc}")

        raw = st.text_area("Hoặc dán văn bản thô (từ Excel, Word, web, email hoặc tệp TXT)", height=180, key="tab5_raw_text", placeholder="Dán dữ liệu vào đây. Có thể phân tách bằng Tab, dấu phẩy, chấm phẩy hoặc dấu |.")
        c1, c2, c3 = st.columns([1.3, 1, 1])
        delimiter = c1.selectbox("Dấu phân cách", ["Tự nhận diện", "\t", ",", ";", "|", "whitespace"], key="tab5_delimiter", format_func=lambda x: {"\t":"Tab", "whitespace":"Khoảng trắng"}.get(x, x))
        header = c2.checkbox("Dòng đầu là tiêu đề", value=True, key="tab5_header")
        if c3.button("Tách thành bảng", type="primary", key="tab5_parse"):
            try:
                st.session_state.tab5_df = parse_raw_text(raw, delimiter, header)
                st.session_state.tab5_editor_version += 1
                st.session_state.tab5_source_name = "Du_lieu_nhap"
                st.success(f"Đã tách thành {len(st.session_state.tab5_df)} dòng × {len(st.session_state.tab5_df.columns)} cột.")
            except Exception as exc:
                st.error(f"Không tách được dữ liệu: {exc}")

    df = st.session_state.tab5_df.copy()
    if df.empty and len(df.columns) == 0:
        st.info("Chưa có bảng dữ liệu. Hãy dán văn bản hoặc tải tệp ở phần trên.")
    else:
        st.markdown("### 2. Chỉnh sửa bảng")
        st.caption("Có thể sửa trực tiếp từng ô. Dùng nút thêm/xóa dòng, thêm/xóa cột và đổi tên cột bên dưới.")
        edited = st.data_editor(df, key=f"tab5_data_editor_{st.session_state.tab5_editor_version}", num_rows="dynamic", use_container_width=True, hide_index=True)
        st.session_state.tab5_df = edited.copy()

        a, b, c = st.columns(3)
        with a:
            if st.button("＋ Thêm cột", key="tab5_add_col"):
                new_name = f"Cột_{len(st.session_state.tab5_df.columns)+1}"
                while new_name in st.session_state.tab5_df.columns:
                    new_name += "_moi"
                st.session_state.tab5_df[new_name] = ""
                st.session_state.tab5_editor_version += 1
                st.rerun()
        with b:
            if st.button("－ Xóa cột cuối", key="tab5_drop_col", disabled=len(st.session_state.tab5_df.columns) == 0):
                st.session_state.tab5_df = st.session_state.tab5_df.iloc[:, :-1]
                st.session_state.tab5_editor_version += 1
                st.rerun()
        with c:
            st.metric("Kích thước bảng", f"{len(st.session_state.tab5_df)} × {len(st.session_state.tab5_df.columns)}")

        with st.expander("Đổi tên cột / xóa cột bất kỳ", expanded=False):
            current_cols = list(st.session_state.tab5_df.columns)
            for idx, old in enumerate(current_cols):
                x1, x2 = st.columns([3, 1])
                new = x1.text_input(f"Tên cột {idx+1}", value=str(old), key=f"tab5_rename_{idx}")
                if x2.button("Đổi tên", key=f"tab5_rename_btn_{idx}"):
                    new = new.strip()
                    if not new:
                        st.warning("Tên cột không được để trống.")
                    elif new != old and new in st.session_state.tab5_df.columns:
                        st.warning("Tên cột đã tồn tại.")
                    else:
                        st.session_state.tab5_df = st.session_state.tab5_df.rename(columns={old:new})
                        st.session_state.tab5_editor_version += 1
                        st.rerun()
            if current_cols:
                drop = st.selectbox("Chọn cột cần xóa", current_cols, key="tab5_choose_drop")
                if st.button("Xóa cột đã chọn", key="tab5_drop_selected"):
                    st.session_state.tab5_df = st.session_state.tab5_df.drop(columns=[drop])
                    st.session_state.tab5_editor_version += 1
                    st.rerun()

        st.markdown("### 3. Lưu và cập nhật tệp")
        existing = saved_files()
        left, right = st.columns(2)
        with left:
            filename = st.text_input("Tên tệp lưu", value=st.session_state.tab5_source_name or "Du_lieu_moi", key="tab5_save_name", help="Lưu dạng .xlsx hoặc .csv; nếu không ghi phần mở rộng sẽ mặc định .xlsx.")
            overwrite = st.checkbox("Cho phép ghi đè tệp cùng tên (tự tạo bản sao lưu)", value=False, key="tab5_overwrite")
            if st.button("Lưu bảng", type="primary", key="tab5_save"):
                try:
                    path, backup = save_table(st.session_state.tab5_df, filename, overwrite)
                    st.success(f"Đã lưu: {path.name}")
                    if backup:
                        st.caption(f"Bản sao lưu trước khi ghi đè: {backup.name}")
                except Exception as exc:
                    st.error(f"Không lưu được: {exc}")
        with right:
            st.write("**Mở và cập nhật tệp đã lưu**")
            if existing:
                selected = st.selectbox("Chọn tệp trong kho Tab 5", existing, key="tab5_existing_file")
                q1, q2 = st.columns(2)
                if q1.button("Mở tệp", key="tab5_load_saved"):
                    try:
                        st.session_state.tab5_df = load_saved(selected)
                        st.session_state.tab5_editor_version += 1
                        st.session_state.tab5_source_name = Path(selected).stem
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Không mở được: {exc}")
                if q2.button("Ghi đè tệp đã chọn", key="tab5_overwrite_selected"):
                    try:
                        path, backup = save_table(st.session_state.tab5_df, selected, overwrite=True)
                        st.success(f"Đã cập nhật {path.name}; bản cũ được sao lưu.")
                        if backup:
                            st.caption(f"Bản sao lưu: {backup.name}")
                    except Exception as exc:
                        st.error(f"Không cập nhật được: {exc}")
            else:
                st.caption("Chưa có tệp nào được lưu trong kho riêng của Tab 5.")

        st.markdown("### 4. Xuất dữ liệu")
        e1, e2 = st.columns(2)
        base = _clean_name(st.session_state.tab5_source_name or "Du_lieu")
        with e1:
            st.download_button("⬇ Xuất CSV", data=csv_bytes(st.session_state.tab5_df), file_name=Path(base).stem + ".csv", mime="text/csv", key="tab5_export_csv", use_container_width=True)
        with e2:
            try:
                xlsx_data = excel_bytes(st.session_state.tab5_df)
                st.download_button("⬇ Xuất Excel", data=xlsx_data, file_name=Path(base).stem + ".xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="tab5_export_xlsx", use_container_width=True)
            except Exception as exc:
                st.error(f"Không tạo được Excel: {exc}")
