# Đọc notebook Project01

Các notebook đã thực thi và lưu output trong file. Không cần Run All chỉ để đọc. Khi muốn chạy lại, cài requirements và dùng đúng môi trường Python 3.11 như hướng dẫn ở README gốc.

| Thứ tự | Notebook | Nội dung | Code cell |
|---|---|---|---:|
| 01 | `01_Du_lieu_va_huan_luyen_MLP.ipynb` | Nguồn/split, SQLite, train MLP và baseline, validation/test, nạp model | 7 |
| 02 | `02_Tri_thuc_va_Graph_Retrieval.ipynb` | KB, cạnh khái niệm, retrieval, nguồn và 24 query tự xây | 6 |
| 03 | `03_Q_learning_nhac_nhat_ky.ipynb` | MDP giả lập, Q-learning 5 seed, đối chứng, Q-table | 5 |
| 04 | `04_Tich_hop_Multi_Agent_va_Demo.ipynb` | Hội chẩn, 12 thông điệp, thiếu dữ liệu, urgent, veto và đánh giá | 8 |

Source thuật toán được dùng chung trong `diabetes_agent/`; cell train thực sự gọi fit và xuất artifact. Notebook giữ giải thích, thứ tự thao tác, số liệu và hình để người đọc theo dõi. Lệnh `python scripts/execute_notebooks.py` chạy toàn bộ bằng đúng interpreter gọi script, tách tiến trình từng notebook để quản lý kernel trên Windows.

Không chạy `scripts/build_notebooks.py` nếu chỉ muốn xem/chạy notebook, vì script bảo trì này tái tạo source và xóa output cũ. Sau khi thay mã mô hình, chạy 01 rồi 04; sau khi thay RL, chạy 03 rồi 04. Đổi KB cần chạy 02 và 04. Nếu muốn tạo lại đầy đủ gói kết quả, chạy tuần tự 01–04.
