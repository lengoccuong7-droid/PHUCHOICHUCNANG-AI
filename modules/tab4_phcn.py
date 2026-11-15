"""Tab 4 – Thư viện bài tập PHCN: 9 nhóm, 63 bài, 315 biến thể."""
import streamlit as st
from core.knowledge_loader import load_knowledge

def render():
    catalog = load_knowledge("rehabilitation/exercise_catalog.json")
    legacy = load_knowledge("rehabilitation/exercise_library.json")
    legacy_details = load_knowledge("rehabilitation/exercise_details.json")
    st.subheader("🏋️ Kho bài tập Phục hồi chức năng")
    st.caption("9 nhóm chức năng · 7 bài mỗi nhóm · 5 biến thể mỗi bài · có liên kết bệnh lý")
    st.warning("Đây là thư viện tham khảo, không tự động thay thế lượng giá hoặc chỉ định. Sau phẫu thuật/gãy xương phải tuân thủ giới hạn ROM và mức chịu lực do bác sĩ điều trị quy định. Các bài tập nuốt, trẻ nhỏ và thần kinh cần chuyên viên phù hợp hướng dẫn trực tiếp.")
    pathology_options = ["Không lọc bệnh lý"] + list(catalog.get("pathology_mapping", {}).keys())
    pathology = st.selectbox("Lọc theo bệnh lý / tình trạng", pathology_options, key="exercise_pathology_filter")
    allowed = catalog["pathology_mapping"].get(pathology, []) if pathology != "Không lọc bệnh lý" else [g["key"] for g in catalog["groups"]]
    groups = [g for g in catalog["groups"] if g["key"] in allowed]
    group_titles = {g["title"]:g for g in groups}
    selected_group_title = st.selectbox("Nhóm mục tiêu phục hồi", list(group_titles), key="exercise_group_filter")
    group = group_titles[selected_group_title]
    ex_map = {e["name"]:e for e in group["exercises"]}
    selected_ex = st.selectbox("Chọn bài tập", list(ex_map), key="exercise_item_filter")
    ex = ex_map[selected_ex]
    st.markdown(f"### {ex['name']}")
    st.markdown("**Công dụng / mục tiêu**")
    st.write(ex["purpose"])
    st.markdown("**Kỹ thuật cơ bản**")
    st.write(ex["technique"])
    st.markdown("**Lỗi thường gặp**")
    st.write(ex["common_errors"])
    st.markdown("### 5 biến thể dụng cụ và cách tập")
    for i,v in enumerate(ex["variants"],1):
        with st.expander(f"Biến thể {i}: {v['equipment']} · {v['level']}", expanded=(i==1)):
            st.markdown("**Tên biến thể**")
            st.write(v["name"])
            st.markdown("**Công dụng**")
            st.write(v["purpose"])
            st.markdown("**Dụng cụ và kỹ thuật**")
            st.write(v["technique"])
            st.markdown("**Liều lượng**")
            st.info(v["dose"])
            st.markdown("**An toàn**")
            st.warning(v["safety"])
    # Keep disease-specific legacy content available for specialized conditions not represented by general movement groups.
    if pathology in legacy:
        with st.expander("Bài tập chuyên biệt theo bệnh lý (thư viện hiện có)", expanded=False):
            st.caption("Một số can thiệp chuyên biệt không thể thay thế bằng biến thể dụng cụ của bài tập vận động thông thường.")
            items=legacy.get(pathology,[])
            guides=legacy_details.get(pathology,[])
            for idx,item in enumerate(items):
                guide=guides[idx] if idx<len(guides) else {}
                with st.expander(item, expanded=False):
                    st.write("**Công dụng:**",guide.get("purpose","Cần lượng giá để xác định mục tiêu."))
                    st.write("**Kỹ thuật:**",guide.get("technique",item))
                    st.write("**Tư thế:**",guide.get("position","Theo hướng dẫn chuyên môn."))
                    st.info(guide.get("dose","Liều lượng cá thể hóa."))
                    st.warning(guide.get("safety","Chỉ thực hiện khi được chuyên viên phù hợp hướng dẫn."))
