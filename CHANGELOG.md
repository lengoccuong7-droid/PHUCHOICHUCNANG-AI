# CHANGELOG 2.1
- Module hóa Tab 1–5 theo cấu trúc package, giữ mã giao diện của bản 2.0.
- Tách `clinical_engine`, `diagnostic_audit`, `storage` vào `core/` và `database/`.
- Bổ sung API đọc chi tiết lần khám và truy vấn chuỗi lần khám.
- Bổ sung Tab 6 theo dõi tiến triển từ lịch sử đã lưu.
- Không tự chuyển “chưa làm” thành “âm tính”; không tự tính phần trăm tiến triển khi thiếu thang đo lặp lại.


## Cập nhật giao diện theo yêu cầu
- Tờ giấy trắng tổng hợp dữ kiện được đồng bộ lại mỗi lần nhập/sửa trường dữ liệu trong Tab 3.
- Tab 3 hiển thị thông tin hành chính gọn: Họ tên, Năm sinh và Nghề nghiệp; không bắt buộc số điện thoại để lưu lần khám.
- Số điện thoại nếu có từ hồ sơ Tab 1 vẫn được giữ; nếu không có, hệ thống tạo mã nội bộ không hiển thị cho người dùng để liên kết lịch sử.
- Chuyển điều hướng 6 chức năng sang Sidebar, luôn sẵn để chuyển tab nhanh khi cuộn trang.
- Tab 6 tra cứu theo mã hồ sơ nội bộ, nên theo dõi được cả bệnh nhân không cung cấp số điện thoại.
