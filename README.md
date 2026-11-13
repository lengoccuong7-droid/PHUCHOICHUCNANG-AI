# PHCN AI 2.1 – Bản module hóa

## Điểm chính
- Tách giao diện thành `modules/tab1_hoso.py` đến `modules/tab6_theo_doi.py`.
- Đưa suy luận lâm sàng và đối soát vào `core/`.
- Đưa SQLite vào `database/storage.py`; giữ cấu trúc bảng `patients` và `visits` của bản 2.0 để tương thích dữ liệu.
- Tab 1–5 kế thừa trực tiếp luồng giao diện/chức năng từ PHCN AI 2.0; Tab 6 bổ sung xem dòng thời gian và mở lại báo cáo các lần khám.
- CSDL đặt tại `data/phcn_ai.db`; không xóa thư mục này khi cập nhật.

## Cấu trúc chính
- `app.py`: điều phối 6 tab.
- `modules/`: mỗi tab là một module giao diện độc lập.
- `core/`: engine phân tích, đối soát và bộ đọc dữ liệu tri thức.
- `knowledge/`: dữ liệu JSON tách khỏi mã giao diện (cẩm nang, nghiệm pháp, bài tập).
- `database/`: lưu trữ SQLite và truy vấn lịch sử.
- `tests/`: kiểm tra lưu/đọc SQLite, import module và tải dữ liệu JSON.

## Chạy ứng dụng
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Sao lưu và nâng cấp
Sao lưu nguyên thư mục `data/` trước khi thay phiên bản. Nếu đang dùng PHCN AI 2.0, hãy chép nguyên `data/phcn_ai.db` của bản cũ vào thư mục `data/` của bản 2.1 trước khi chạy. Cấu trúc hai bảng `patients` và `visits` được giữ nguyên. Không đưa dữ liệu định danh/sức khỏe thật lên nơi công khai.

## Lưu ý kiểm định
Động cơ là hệ luật/từ khóa offline, chưa được thẩm định lâm sàng. Kết quả hỗ trợ rà soát, không thay thế đánh giá chuyên môn. Trường test cũ gộp “Chưa làm / Âm tính” nên được xem là chưa xác định, không dùng để loại trừ bệnh. Tab 6 chỉ hiển thị các lần khám đã lưu; chưa tự tính mức cải thiện nếu không có thang đo lặp lại chuẩn hóa.


### Giao diện cập nhật
- Điều hướng chức năng nằm ở Sidebar bên trái.
- Tab 3 hiển thị Họ tên, Năm sinh và Nghề nghiệp tại phần thông tin bệnh nhân; số điện thoại không bắt buộc.
- Khung “Tờ giấy trắng” được cập nhật lại theo dữ kiện nhập vào sau mỗi lần Streamlit rerun.
- Hồ sơ không có số điện thoại được liên kết bằng mã nội bộ; mã này không hiển thị như số điện thoại.
