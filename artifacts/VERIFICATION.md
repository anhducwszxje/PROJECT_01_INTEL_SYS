# Kiểm tra bản bàn giao

Ngày hoàn thiện: 06/11/2026 (Asia/Saigon). Kiểm tra bằng Python 3.11.9 CPU trên Windows; các nguồn tri thức được kiểm tra ngày 05/11/2026.

- Bốn notebook đã thực thi, 26/26 code cell có execution count, không có error output. Xem `notebook_execution.json` và output ngay trong ipynb.
- 28 kiểm thử pytest, gồm Streamlit AppTest mở giao diện và bấm chạy hội chẩn. Chi tiết trong `test-results.xml`.
- 20/20 kịch bản hệ thống đạt trạng thái mong đợi. Xem `system_evaluation.csv` và `system_traces.json`.
- Council bác 6/6 proposal lỗi do tác giả inject. Đây là kiểm tra chức năng veto, không phải tỷ lệ an toàn lâm sàng.
- 24/24 câu truy xuất tìm đúng ID đầu tiên trong bộ tự xây ở cả hai cấu hình. Chưa có bằng chứng graph cải thiện điểm trên bộ này.
- Trình duyệt local đã kiểm tra hội chẩn có nguồn/trace, tab tri thức và nhánh urgent. Ảnh chụp trong `report/images/demo_*.jpg`.
- Báo cáo biên dịch bằng XeLaTeX, render PNG bằng Poppler và kiểm tra toàn bộ trang. Bản giao không có trang chỉ dồn vài dòng lẻ, tham chiếu chưa giải quyết hoặc text tràn lề.

Kết quả model/test lấy từ `metrics_test.csv`; model mặc định Random Forest chọn theo AP validation. MLP ROC AUC khoảng 0,8168. Không thay mặc định dựa trên test.

Q-learning mean reward/day khoảng 0,2703; fixed khoảng 0,2868. Không tuyên bố RL tốt nhất. Reward là giả định của simulator; std giữa seed train của fixed bằng 0 do tái dùng cùng bộ eval, không phải rollout không biến thiên.

Package bao gồm dữ liệu và mô hình để inference không cần Internet sau khi cài thư viện. Không đóng gói `.venv`, cache, build tạm hoặc database audit tùy chọn. Phiên bản trực tiếp nằm trong requirements; bản cài mới trên máy khác chưa được xác nhận.
