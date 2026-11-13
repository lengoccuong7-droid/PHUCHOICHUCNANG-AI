# PHCN AI 2.1 – Modular build, giữ luồng Tab 1–5 của 2.0 và bổ sung Tab 6
import streamlit as st
from database.storage import init_db
from modules.tab1_hoso import render as render_tab1
from modules.tab2_trithuc import render as render_tab2
from modules.tab3_kham import render as render_tab3
from modules.tab4_phcn import render as render_tab4
from modules.tab5_doi_soat import render as render_tab5
from modules.tab6_theo_doi import render as render_tab6

st.set_page_config(page_title="PHCN AI 2.1", page_icon="🩺", layout="wide", initial_sidebar_state="expanded")
init_db()
st.markdown("""<style>
.grid-card-box{background:#fff;border-radius:16px;padding:14px 8px;text-align:center;box-shadow:0 3px 8px rgba(0,0,0,.06);border:1px solid #eaeaea;margin-bottom:12px}
.icon-circle-btn{width:50px;height:50px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:24px;margin:0 auto 8px;color:white;box-shadow:0 2px 5px rgba(0,0,0,.1)}
.scrollable-feed{max-height:850px;overflow-y:auto;padding-right:12px}
</style>""", unsafe_allow_html=True)

def main():
    st.title("🩺 PHCN AI 2.1 – Trợ lý Phục hồi Chức năng & Lâm sàng")
    st.caption("Kiến trúc module hóa · phân tích offline · dữ liệu SQLite cục bộ · đối soát hai chiều · theo dõi tiến triển")

    # Điều hướng cố định trong sidebar để không phải cuộn lên đầu trang.
    pages = {
        "👤 Hồ sơ & Lịch sử": render_tab1,
        "📚 Cẩm nang Tri thức": render_tab2,
        "🩺 Khám Lâm sàng": render_tab3,
        "🏋️‍♂️ Kho Bài tập PHCN": render_tab4,
        "🔎 Đối soát chẩn đoán": render_tab5,
        "📈 Theo dõi tiến triển": render_tab6,
    }
    with st.sidebar:
        st.title("PHCN AI")
        st.caption("Điều hướng nhanh")
        selected_page = st.radio(
            "Chọn chức năng", list(pages.keys()), key="main_navigation",
            label_visibility="collapsed"
        )
        st.divider()
        patient = st.session_state.get("current_patient", {})
        st.caption("BỆNH NHÂN ĐANG CHỌN")
        st.write(patient.get("name") or "Chưa chọn bệnh nhân")
        if patient.get("age"):
            st.caption(f"Năm sinh: {patient.get('age')}")
        if patient.get("job"):
            st.caption(f"Nghề nghiệp: {patient.get('job')}")
    pages[selected_page]()

if __name__ == "__main__":
    main()
