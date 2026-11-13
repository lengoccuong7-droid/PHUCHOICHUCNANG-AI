"""Giao diện Tab 5 – trích nguyên luồng chức năng từ PHCN AI 2.0."""
import streamlit as st
from core.diagnostic_audit import run_bidirectional_audit, render_audit_report


def render():
    st.subheader("🔎 Đối soát chẩn đoán hai chiều tự động")
    st.caption("Tab này tự đọc dữ liệu từ Tab 3. Không cần nhập lại và không có nút kiểm chứng thủ công.")

    last_analysis = st.session_state.get("phcn_last_analysis")
    last_payload = st.session_state.get("phcn_last_payload")
    last_signature = st.session_state.get("phcn_last_signature")
    current_signature = st.session_state.get("phcn_current_signature")
    current_payload = st.session_state.get("phcn_current_payload")

    if not last_analysis or not last_payload:
        st.info("Chưa có kết quả khám. Vào Tab 3, chọn vùng khám, nhập dữ liệu và chạy phân tích. Tab 5 sẽ tự động đối soát sau đó.")
    elif not current_payload or not current_signature:
        st.warning("Chưa có ảnh chụp dữ liệu khám hiện hành để xác nhận kết quả. Quay lại Tab 3 và mở phiếu khám đang thực hiện.")
    elif last_signature != current_signature:
        st.error("Dữ liệu Tab 3 đã thay đổi sau lần phân tích gần nhất. Kết quả cũ không được dùng để đối soát. Hãy chạy phân tích lại ở Tab 3.")
        st.caption("Cơ chế này ngăn Tab 5 hiển thị kết luận dựa trên dữ liệu cũ.")
    else:
        audit = run_bidirectional_audit(current_payload, last_analysis)
        audit_report = render_audit_report(audit)
        st.session_state["phcn_last_audit"] = audit
        st.session_state["phcn_last_audit_report"] = audit_report

        if audit["red_flags"]:
            st.error("🚩 Có cảnh báo an toàn từ Tab 3: " + "; ".join(audit["red_flags"]))
        st.warning("**Kết quả kiểm soát:** " + audit["overall"])

        st.markdown("### 1. Chiều thuận – hình thành giả thuyết từ dữ liệu")
        st.markdown("Các giả thuyết dưới đây chỉ được đưa lên khi có ít nhất một dữ kiện gợi ý trong ghi chép. Đây không phải bảng xếp hạng xác suất.")
        if audit["forward"]:
            for item in audit["forward"]:
                with st.container(border=True):
                    st.markdown(f"**{item['name']}**")
                    st.caption(item["status"])
                    st.markdown("**Dữ kiện gợi ý:** " + ("; ".join(item["supporting"]) or "Chưa ghi nhận"))
                    st.markdown("**Điểm chưa tương hợp:** " + ("; ".join(item["opposing"]) or "Chưa ghi nhận rõ"))
        else:
            st.info("Chưa có kiểu hình nào đủ dữ kiện gợi ý để hình thành giả thuyết cụ thể. Không tự suy đoán khi dữ liệu chưa đủ.")

        st.markdown("### 2. Chiều ngược – kiểm tra từng giả thuyết")
        st.caption("Mỗi giả thuyết được kiểm tra lại bằng các dấu hiệu kỳ vọng. Dữ kiện không được ghi nhận được xem là 'chưa biết', không tự động xem là âm tính.")
        if audit["reverse"]:
            for item in audit["reverse"]:
                with st.expander(f"{item['name']} · {item['status']}", expanded=bool(item["supporting"] or item["opposing"])):
                    st.markdown("**Ủng hộ:**")
                    for value in item["supporting"] or ["Chưa tìm thấy dữ kiện ủng hộ trong phần ghi chép."]:
                        st.markdown(f"- {value}")
                    st.markdown("**Chống lại / chưa tương hợp:**")
                    for value in item["opposing"] or ["Chưa ghi nhận dữ kiện chống lại rõ ràng."]:
                        st.markdown(f"- {value}")
                    st.markdown("**Dấu hiệu kỳ vọng chưa có thông tin (không đồng nghĩa âm tính):**")
                    for value in item["unverified_features"] or ["Không còn mục chưa xác minh trong nhóm dấu hiệu này."]:
                        st.markdown(f"- {value}")
                    st.markdown("**Khám / đánh giá bổ sung nên cân nhắc:**")
                    for value in item["recommended_checks"] or ["Không có mục bổ sung từ bộ quy tắc hiện tại."]:
                        st.markdown(f"- {value}")
                    st.info("Lưu ý chuyên môn: " + item["caution"])
        else:
            st.info("Vùng khám này chưa có bộ giả thuyết chuyên biệt trong phiên bản hiện tại. Hệ thống không tự mở rộng kết luận ngoài phạm vi đã lập trình.")

        st.markdown("### 3. Mâu thuẫn và giới hạn dữ liệu")
        if audit["contradictions"]:
            for item in audit["contradictions"]:
                st.warning(item)
        else:
            st.success("Chưa phát hiện mâu thuẫn tự động từ các trường dữ liệu được kiểm tra. Điều này không chứng minh chẩn đoán là đúng.")

        st.markdown("### 4. Báo cáo đối soát có thể sao chép")
        if st.session_state.get("phcn_audit_report_signature") != last_signature:
            st.session_state["phcn_audit_report_copy"] = audit_report
            st.session_state["phcn_audit_report_signature"] = last_signature
        st.text_area("Báo cáo Tab 5", height=460, key="phcn_audit_report_copy")
        st.caption("Báo cáo được tạo tự động từ dữ liệu Tab 3 hiện hành. Nếu sửa dữ liệu, cần phân tích lại để tạo báo cáo mới.")

        with st.expander("Giới hạn và nguyên tắc an toàn", expanded=False):
            for item in audit["limitations"]:
                st.markdown(f"- {item}")
