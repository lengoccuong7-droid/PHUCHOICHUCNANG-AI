"""Giao diện Tab 3 – trích nguyên luồng chức năng từ PHCN AI 2.0."""
import streamlit as st
from core.knowledge_loader import load_knowledge
import json, hashlib
from core.clinical_engine import analyze_case, render_report
from database.storage import save_visit


def render():
    if "exam_active_region" not in st.session_state:
        st.session_state.exam_active_region = None

    regions = [
        ("Cột sống cổ", "🦴", "C1-C7 và hội chứng chèn ép", "linear-gradient(135deg, #ff6b6b, #ee5253)"),
        ("Cột sống thắt lưng", "🩻", "Thoát vị đĩa đệm, đau thần kinh tọa", "linear-gradient(135deg, #10ac84, #1dd1a1)"),
        ("Khớp vai", "🦾", "Chóp xoay & đông cứng khớp vai", "linear-gradient(135deg, #5f27cd, #341f97)"),
        ("Khuỷu tay", "💪", "Viêm lồi cầu, hội chứng ống khuỷu", "linear-gradient(135deg, #ff9f43, #ee5253)"),
        ("Cổ tay – bàn tay", "✋", "Hội chứng ống cổ tay, De Quervain", "linear-gradient(135deg, #48dbfb, #0abde3)"),
        ("Khớp háng", "🦿", "Thoái hóa & kẹp háng FAI", "linear-gradient(135deg, #f39c12, #e67e22)"),
        ("Khớp gối", "🦵", "ACL, sụn chêm & thoái hóa gối", "linear-gradient(135deg, #2e86de, #222f3e)"),
        ("Cổ chân – bàn chân", "🦶", "Bong gân & viêm cân gan chân", "linear-gradient(135deg, #ee5253, #ff6b6b)"),
        ("Thần kinh & Khác", "🧠", "Đột quỵ, phục hồi chức năng thần kinh", "linear-gradient(135deg, #0abde3, #2e86de)")
    ]

    if st.session_state.exam_active_region is None:
        st.subheader("🎯 Chọn Vùng Thăm Khám Lâm Sàng")
        st.markdown("Chọn vùng cơ thể bên dưới để mở phiếu thăm khám chuyên sâu độc lập:")

        cols_r = st.columns(2)
        for idx, item in enumerate(regions):
            title, icon, desc, color = item
            with cols_r[idx % 2]:
                st.markdown(f"""
                    <div class="grid-card-box">
                        <div class="icon-circle-btn" style="background: {color};">
                            {icon}
                        </div>
                        <div style="font-weight: 700; font-size: 12px; color: #1f2937; min-height: 35px; display: flex; align-items: center; justify-content: center;">{title}</div>
                    </div>
                """, unsafe_allow_html=True)
                if st.button("🩺 Bắt đầu khám", use_container_width=True, key=f"open_exam_{idx}"):
                    st.session_state.exam_active_region = title
                    st.rerun()
    else:
        current_reg = st.session_state.exam_active_region

        c_top1, c_top2 = st.columns([1, 4])
        with c_top1:
            if st.button("⬅️ Quay lại", type="secondary"):
                st.session_state.exam_active_region = None
                st.rerun()
        with c_top2:
            st.subheader(f"📋 PHIẾU KHÁM: {current_reg.upper()}")

        st.markdown("---")

        active_patient = st.session_state.get("current_patient", {"name": "", "phone": "", "age": 1990, "job": ""})
        if active_patient.get("name"):
            st.info(f"🔗 Hồ sơ đang liên kết: **{active_patient.get('name')}** · Năm sinh: **{active_patient.get('age') or 'Chưa nhập'}**")

        # Khung cuộn dọc toàn bộ nội dung khám
        st.markdown('<div class="scrollable-feed">', unsafe_allow_html=True)

        p_name = st.text_input("Họ tên bệnh nhân", value=active_patient.get("name", ""), key="rt_p_name")
        birth_default = int(active_patient.get("age") or 1990)
        p_birth_year = st.number_input("Năm sinh", min_value=1900, max_value=2026, value=birth_default, step=1, key="rt_p_birth_year")
        p_job = st.text_input("Nghề nghiệp", value=active_patient.get("job", ""), key="rt_p_job")
        ly_do = st.text_input("🏥 Lý do vào viện / Than phiền chính", key="rt_ly_do")
        tien_su = st.text_area("📜 Tiền sử bệnh (Bản thân / Chấn thương)", key="rt_tien_su")

        # QUY TRÌNH SOCRATES GẠCH ĐẦU DÒNG TỪNG MỤC - GÕ TỰ DO
        with st.expander("🩺 Bệnh sử chi tiết (Quy trình SOCRATES chuẩn y khoa)", expanded=True):
            st.caption("Khai thác triệu chứng theo quy trình SOCRATES (nhập tự do từng mục):")
            soc_s = st.text_input("• **S (Site) – Vị trí đau:**", placeholder="Ví dụ: Đau khu trú mặt trước trong gối trái...", key="rt_soc_s")
            soc_o = st.text_input("• **O (Onset) – Hoàn cảnh khởi phát:**", placeholder="Ví dụ: Đột ngột sau khi vặn xoắn gối lúc đá bóng...", key="rt_soc_o")
            soc_c = st.text_input("• **C (Character) – Tính chất đau:**", placeholder="Ví dụ: Đau nhói, âm ỉ, có tiếng lạo xạo...", key="rt_soc_c")
            soc_r = st.text_input("• **R (Radiation) – Hướng lan:**", placeholder="Ví dụ: Không lan, hoặc lan xuống cẳng chân...", key="rt_soc_r")
            soc_a = st.text_input("• **A (Associations) – Triệu chứng đi kèm:**", placeholder="Ví dụ: Sưng nề, khóa khớp, tê bì...", key="rt_soc_a")
            soc_t = st.text_input("• **T (Time/Course) – Diễn tiến thời gian:**", placeholder="Ví dụ: Tăng dần khi leo cầu thang, nghỉ bớt đau...", key="rt_soc_t")
        
            col_nrs1, col_nrs2 = st.columns([1, 2])
            with col_nrs1:
                nrs = st.selectbox("• **S (Severity) – Mức độ NRS (0-10):**", [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10], key="rt_nrs")
            with col_nrs2:
                nrs_note = st.text_input("• **Ghi chú mức độ đau:**", placeholder="Ví dụ: Đau tăng nhiều về chiều...", key="rt_nrs_note")

        with st.expander("🔍 Khám thực thể chuẩn y khoa (Nhìn – Sờ – Đo ROM)", expanded=True):
            inspect = st.text_area("👁️ NHÌN (Inspection) - Biến dạng, sưng nề, teo cơ", key="rt_inspect")
            palp = st.text_area("✋ SỜ (Palpation) - Điểm đau chói, nhiệt độ, trương lực", key="rt_palp")
            rom_meas = st.text_area("📏 ĐO / GÕ (ROM & Phản xạ) - Tầm vận động, lực cơ MMT", key="rt_rom")

        with st.expander("🖼️ Hình ảnh Lâm sàng & Cận lâm sàng (X-quang / MRI)", expanded=False):
            uploaded_image = st.file_uploader("📤 Tải ảnh X-quang / MRI:", type=["png", "jpg", "jpeg"], key="rt_uploaded_img")
            if uploaded_image is not None:
                st.image(uploaded_image, caption="🖼️ Hình ảnh lâm sàng", use_container_width=True)

        # CSDL 3 - 4 NGHIỆM PHÁP ĐẶC HIỆU CHUYÊN SÂU THEO VÙNG
        specific_tests_db = load_knowledge("clinical_tests/region_tests.json")

        active_tests = specific_tests_db.get(current_reg, [
            ("Test đặc hiệu 1", "Đánh giá tổn thương cấu trúc", "Thực hiện kỹ thuật chuẩn."),
            ("Test đặc hiệu 2", "Kiểm tra độ vững", "Thực hiện theo quy trình lâm sàng."),
            ("Test đặc hiệu 3", "Đánh giá chức năng", "Thực hiện theo hướng dẫn."),
            ("Test đặc hiệu 4", "Kiểm tra bổ trợ", "Thực hiện kỹ thuật lâm sàng.")
        ])
    
        with st.expander(f"🧬 Nghiệm pháp đặc hiệu ({current_reg}) - Đủ 4 Test", expanded=True):
            test_results = {}
            for t_idx, (t_name, t_use, t_tech) in enumerate(active_tests):
                st.markdown(f"**🔹 {t_idx+1}. {t_name}**")
                st.caption(f"• **Công dụng:** {t_use}  \n• **Kỹ thuật:** {t_tech}")
                res = st.radio(f"Kết quả {t_name}:", ["Chưa làm / Âm tính (-)", "Dương tính (+)"], horizontal=True, key=f"ex_t_res_{t_idx}")
                test_results[t_name] = res
                st.markdown("---")

        with st.expander("🚩 Cờ đỏ an toàn lâm sàng (Red Flags)", expanded=False):
            rf_1 = st.checkbox("Hội chứng đuôi ngựa / Rối loạn cơ tròn", key="rt_rf1")
            rf_2 = st.checkbox("Sụt cân nhanh / Tiền sử ung thư", key="rt_rf2")
            rf_3 = st.checkbox("Sốt cao, sưng nóng đỏ đau cấp tính", key="rt_rf3")

        # TỜ GIẤY TRẮNG REAL-TIME TỰ ĐỘNG CẬP NHẬT TỪNG GIÂY
        st.markdown("---")
        st.markdown("### 📄 Tờ Giấy Trắng Tổng Hợp & Phân Tích AI (Real-time)")
    
        pos_tests_list = [t for t, res in test_results.items() if res == "Dương tính (+)"]
        summary_text = f"""[BỆNH ÁN PHCN CHUYÊN SÂU]
    - Vùng khám: {current_reg}
    - Bệnh nhân: {p_name if p_name else '---'}
    - Năm sinh: {p_birth_year if p_birth_year else '---'}
    - Nghề nghiệp: {p_job if p_job else '---'}
    - Lý do vào viện: {ly_do if ly_do else '---'}
    - Tiền sử: {tien_su if tien_su else '---'}
    [BỆNH SỬ (SOCRATES)]
    - Site (Vị trí): {soc_s if soc_s else '---'}
    - Onset (Khởi phát): {soc_o if soc_o else '---'}
    - Character (Tính chất): {soc_c if soc_c else '---'}
    - Radiation (Hướng lan): {soc_r if soc_r else '---'}
    - Associations (Triệu chứng kèm): {soc_a if soc_a else '---'}
    - Time (Diễn tiến): {soc_t if soc_t else '---'}
    - Severity (Mức độ đau): {nrs}/10
    ----------------------------------------
    [KHÁM THỰC THỂ]
    - Nhìn: {inspect if inspect else '---'}
    - Sờ: {palp if palp else '---'}
    - ROM: {rom_meas if rom_meas else '---'}
    - Test đặc hiệu (+): {', '.join(pos_tests_list) if pos_tests_list else 'Không có'}
    - Cờ đỏ: {'Có dấu hiệu nguy cơ' if (rf_1 or rf_2 or rf_3) else 'Không phát hiện'}"""

        # Đồng bộ giá trị trước khi tạo widget: mỗi lần người dùng nhập/sửa dữ kiện,
        # Streamlit rerun và tờ tổng hợp nhận ngay nội dung mới nhất.
        st.session_state["quick_copy_box"] = summary_text
        with st.container(border=True):
            st.text_area("📄 Tờ giấy trắng – tự cập nhật theo dữ kiện vừa nhập:", key="quick_copy_box", height=300)

        # ENGINE SUY LUẬN CÓ ĐỐI SOÁT NGƯỢC
        case_payload = {
            "region": current_reg, "reason": ly_do, "history": tien_su,
            "site": soc_s, "onset": soc_o, "character": soc_c,
            "radiation": soc_r, "associations": soc_a, "course": soc_t,
            "nrs": nrs, "inspection": inspect, "palpation": palp,
            "rom_mmt": rom_meas, "tests": test_results,
            "red_flags": {
                "Rối loạn cơ tròn / nghi hội chứng đuôi ngựa": rf_1,
                "Tiền sử ung thư / sụt cân nhanh": rf_2,
                "Sốt cao / sưng nóng đỏ đau cấp tính": rf_3,
            }
        }
        case_signature = hashlib.sha256(json.dumps(case_payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
        # Tab 5 reads this live snapshot. Streamlit evaluates all tab bodies on rerun.
        st.session_state["phcn_current_payload"] = case_payload
        st.session_state["phcn_current_signature"] = case_signature
        if st.button("🚀 Chạy Phân Tích AI Y Khoa Chuyên Sâu", type="primary", use_container_width=True):
            st.session_state["phcn_last_payload"] = case_payload
            st.session_state["phcn_last_signature"] = case_signature
            st.session_state["phcn_last_analysis"] = analyze_case(case_payload)
            st.session_state["phcn_last_report"] = render_report(st.session_state["phcn_last_analysis"])

        analysis_is_current = (st.session_state.get("phcn_last_signature") == case_signature)
        if st.session_state.get("phcn_last_analysis") and analysis_is_current:
            result = st.session_state["phcn_last_analysis"]
            st.markdown("---")
            st.markdown("#### 🤖 KẾT QUẢ PHÂN TÍCH & ĐỐI SOÁT LÂM SÀNG")
            if result["red_flags"]:
                st.error("🚩 Có dấu hiệu cảnh báo: " + "; ".join(result["red_flags"]))
            else:
                st.warning("Lưu ý: chưa ghi nhận cờ đỏ trong các mục đã nhập không đồng nghĩa đã loại trừ bệnh lý nghiêm trọng.")
            st.markdown("**1. Giả thuyết / định hướng cần kiểm chứng**")
            for item in result["hypotheses"]: st.markdown(f"- {item}")
            st.markdown("**2. Đối soát ngược – dữ kiện ủng hộ**")
            for item in result["supporting"]: st.markdown(f"- {item}")
            st.markdown("**3. Đối soát ngược – dữ kiện chống lại / mâu thuẫn**")
            for item in result["opposing"]: st.markdown(f"- {item}")
            st.markdown("**4. Dữ liệu chưa rõ / cần bổ sung**")
            for item in result["unresolved"]: st.markdown(f"- {item}")
            st.markdown("**5. Thông tin còn thiếu**")
            for item in result["missing"]: st.markdown(f"- {item}")
            st.markdown("**6. Mức độ tin cậy**")
            st.info(result["confidence"])
            st.caption("Engine offline dựa trên quy tắc minh bạch; chưa phải mô hình AI đã được thẩm định lâm sàng. Không dùng một test đơn lẻ để xác nhận hoặc loại trừ bệnh.")
            st.text_area("Báo cáo phân tích – sao chép để hội chẩn", value=st.session_state["phcn_last_report"], height=360, key="phcn_report_copy")

        st.markdown("---")
        col_b1, col_b2, col_b3 = st.columns(3)
        with col_b1:
            if st.button("🤖 Hỏi ChatGPT", use_container_width=True):
                st.info("💡 Mẹo: Copy nội dung bệnh án ở trên và dán vào ChatGPT kèm câu lệnh: 'Đóng vai bác sĩ PHCN, hãy biện luận chẩn đoán ca bệnh này'.")
        with col_b2:
            if st.button("✨ Hỏi Gemini", use_container_width=True):
                st.success("💡 Mẹo: Dùng nội dung bệnh án này để trao đổi trực tiếp với trợ lý Gemini nhận phác đồ điều trị.")
        with col_b3:
            if st.button("💾 Lưu hồ sơ", type="primary", use_container_width=True):
                if not p_name.strip():
                    st.warning("⚠️ Vui lòng nhập họ tên bệnh nhân!")
                elif not st.session_state.get("phcn_last_analysis") or st.session_state.get("phcn_last_signature") != case_signature:
                    st.warning("Dữ liệu đã thay đổi sau lần phân tích gần nhất. Vui lòng phân tích lại trước khi lưu để tránh lưu kết quả cũ.")
                else:
                    try:
                        visit_id = save_visit(
                            {"name": p_name.strip(), "phone": active_patient.get("phone", ""), "age": int(p_birth_year), "job": p_job.strip()},
                            current_reg, st.session_state["phcn_last_payload"], summary_text,
                            st.session_state["phcn_last_analysis"], st.session_state["phcn_last_report"])
                        st.session_state.current_patient = {**active_patient, "name": p_name.strip(), "age": int(p_birth_year), "job": p_job.strip()}
                        st.success(f"Đã lưu lần khám #{visit_id} cho {p_name} vào SQLite cục bộ.")
                    except Exception as exc:
                        st.error(f"Không thể lưu hồ sơ: {exc}")

        st.markdown('</div>', unsafe_allow_html=True)
