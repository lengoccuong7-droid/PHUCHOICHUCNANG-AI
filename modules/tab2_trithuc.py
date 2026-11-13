"""Giao diện Tab 2 – trích nguyên luồng chức năng từ PHCN AI 2.0."""
import streamlit as st
from core.knowledge_loader import load_knowledge


def render():
    if "knowledge_active_cat" not in st.session_state:
        st.session_state.knowledge_active_cat = None

    knowledge_db = load_knowledge("clinical_manual.json")

    if st.session_state.knowledge_active_cat is None:
        st.markdown("### 📚 Cẩm Nang Tri Thức Y Chứng")
        st.caption("Chọn chuyên khoa bên dưới để tra cứu phác đồ và tài liệu lâm sàng chuẩn hóa:")

        cols = st.columns(2)
        for idx, (cat_name, data) in enumerate(knowledge_db.items()):
            with cols[idx % 2]:
                st.markdown(f"""
                    <div class="grid-card-box">
                        <div class="icon-circle-btn" style="background: {data['color']};">
                            {data['icon']}
                        </div>
                        <div style="font-weight: 700; font-size: 13px; color: #1f2937;">{cat_name}</div>
                    </div>
                """, unsafe_allow_html=True)
                if st.button("📖 Xem phác đồ", key=f"btn_k_{idx}", use_container_width=True):
                    st.session_state.knowledge_active_cat = cat_name
                    st.rerun()
    else:
        c1, c2 = st.columns([4, 1])
        with c1:
            st.markdown(f"#### 📖 Chuyên khoa: `{st.session_state.knowledge_active_cat}`")
        with c2:
            if st.button("⬅ Quay lại", use_container_width=True):
                st.session_state.knowledge_active_cat = None
                st.rerun()

        st.markdown("---")
        with st.container(border=True):
            st.markdown(knowledge_db[st.session_state.knowledge_active_cat]["content"])
