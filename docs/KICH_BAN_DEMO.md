# Kịch bản demo khoảng 8 phút

1. **Giới thiệu 30 giây.** Mở dashboard, giới thiệu ba kỹ thuật chính: supervised learning, truy xuất tri thức và Q-learning nhắc nhật ký.
2. **Luồng đầy đủ 90 giây.** Bấm Phân tích hồ sơ để chạy ngay. Chỉ bảy thẻ tác tử, vòng score, ngưỡng/nhãn, các thẻ tri thức và nhắc việc. Mở Chi tiết phối hợp tác tử để xem 12 thông điệp.
3. **MLP 60 giây.** Chọn model mlp, tác vụ chỉ phân loại và chạy. Giải thích MLP vẫn được cung cấp dù mặc định Random Forest do validation chọn. Mở notebook 01, chỉ kiến trúc, output train, loss và test.
4. **Tri thức 60 giây.** Tab Tri thức và đồ thị, hỏi HbA1c và thiếu máu. Chỉ các thẻ nguồn NIDDK và bản đồ khái niệm bên cạnh.
5. **Thiếu dữ liệu 45 giây.** Chọn Phân loại hồ sơ, chọn Nhập JSON, sửa thành `{"BMI":26}` rồi bấm Bắt đầu phân tích. Hệ thống liệt kê trường cần bổ sung.
6. **Cảnh báo 45 giây.** Mở Nhật ký & số đo, bật Thêm số đo glucose, nhập 62 mg/dL rồi chạy. Thẻ Tiếp nhận chuyển trạng thái; trace dừng sau Intake và có nguồn D05. Tắt số đo sau khi trình diễn.
7. **RL 60 giây.** Tab Thực nghiệm, mở biểu đồ và bảng RL. Nêu rõ Q-learning chưa vượt fixed trong cấu hình này. Notebook 03 cho xem reward công thức tự đặt, Q-table và 5 seed.
8. **Council và kết thúc 90 giây.** Notebook 04 inject thuốc/ID giả; xem veto, 20 kịch bản, 6 lỗi inject. Chỉ đường dẫn source và lệnh pytest. Nêu giới hạn: bộ câu tự xây, dữ liệu Mỹ, chưa clinical validation, chưa chứng minh MAS hơn single.

Nếu mất Internet, các bước trên vẫn chạy sau khi cài thư viện. Tránh dùng dữ liệu thật hoặc mở dữ liệu riêng của người khác khi bảo vệ.
