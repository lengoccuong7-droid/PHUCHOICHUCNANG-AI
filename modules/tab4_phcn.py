"""Giao diện Tab 4 – trích nguyên luồng chức năng từ PHCN AI 2.0."""
import streamlit as st
from core.knowledge_loader import load_knowledge


def render():
    pathologies_m4 = load_knowledge("rehabilitation/exercise_library.json")

    st.warning("Lưu ý an toàn: bài tập trong thư viện là gợi ý tham khảo. Sau phẫu thuật, gãy xương hoặc có hạn chế chịu lực/tầm vận động, phải đối chiếu chỉ định phẫu thuật viên và lượng giá trực tiếp trước khi áp dụng.")

    if "selected_pathology_m4" not in st.session_state:
        st.session_state.selected_pathology_m4 = None

    if st.session_state.selected_pathology_m4 is None:
        st.markdown("### 🏋️‍♂️ Kho Bài Tập Phục Hồi Chức Năng Theo Bệnh Lý")
        st.caption("Chọn nhóm bệnh lý bên dưới để xem trọn bộ 7 bài tập chuyên sâu:")

        for path_key in pathologies_m4.keys():
            if st.button(f"📌 {path_key}", use_container_width=True, key=f"btn_m4_{path_key}"):
                st.session_state.selected_pathology_m4 = path_key
                st.rerun()
    else:
        c1, c2 = st.columns([4, 1])
        with c1:
            st.markdown(f"#### 🏥 Phác đồ: `{st.session_state.selected_pathology_m4}`")
        with c2:
            if st.button("⬅ Quay lại", use_container_width=True):
                st.session_state.selected_pathology_m4 = None
                st.rerun()

        st.markdown("---")
        st.markdown("##### 📋 Trọn bộ 7 bài tập phục hồi chức năng chuẩn hóa:")
    
        exercises = pathologies_m4[st.session_state.selected_pathology_m4]
        for exercise in exercises:
            with st.container(border=True):
                st.markdown(f"- {exercise}")
