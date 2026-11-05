# Kịch bản demo khoảng 8 phút

1. **Giới thiệu 30 giây.** Nêu ba kỹ thuật chính: supervised learning, truy xuất tri thức, Q-learning nhắc nhật ký. Phạm vi là project học tập, không chẩn đoán.
2. **Luồng đầy đủ 90 giây.** Hội chẩn tổng hợp, hồ sơ mẫu train, câu hỏi HbA1c/nhật ký, gap 2. Bấm Chạy. Chỉ score/ngưỡng/nhãn, đoạn có ID nguồn, policy nhắc và bảng 12 thông điệp.
3. **MLP 60 giây.** Chọn model mlp, tác vụ chỉ phân loại và chạy. Giải thích MLP vẫn được cung cấp dù mặc định Random Forest do validation chọn. Mở notebook 01, chỉ kiến trúc, output train, loss và test.
4. **Tri thức 60 giây.** Tab Tri thức, hỏi HbA1c và thiếu máu. Chỉ URL NIDDK, lexical score, khái niệm và cạnh. Nêu trích xuất theo mẫu, không có LLM sinh tự do.
5. **Thiếu dữ liệu 45 giây.** Chỉ phân loại, bỏ mẫu, sửa JSON thành `{"BMI":26}`. Hệ thống liệt kê trường thiếu thay vì bù số hoặc vẫn dự đoán.
6. **Cảnh báo 45 giây.** Bật số đo glucose, nhập 62 mg/dL rồi chạy. Trace dừng sau Intake, có nguồn D05; mô hình không được gọi. Tắt số đo sau khi trình diễn.
7. **RL 60 giây.** Tab Thực nghiệm, mở biểu đồ và bảng RL. Nêu rõ Q-learning chưa vượt fixed trong cấu hình này. Notebook 03 cho xem reward công thức tự đặt, Q-table và 5 seed.
8. **Council và kết thúc 90 giây.** Notebook 04 inject thuốc/ID giả; xem veto, 20 kịch bản, 6 lỗi inject. Chỉ đường dẫn source và lệnh pytest. Nêu giới hạn: bộ câu tự xây, dữ liệu Mỹ, chưa clinical validation, chưa chứng minh MAS hơn single.

Nếu mất Internet, các bước trên vẫn chạy sau khi cài thư viện. Tránh dùng dữ liệu thật hoặc mở dữ liệu riêng của người khác khi bảo vệ.
