# Hướng dẫn chạy Project01

## 1 Chuẩn bị

Windows 64-bit, Python 3.11, khoảng 3 GB dung lượng trống cho thư viện và tối thiểu 4 GB RAM (8 GB thuận tiện hơn). Internet chỉ cần để cài thư viện. Không cần GPU, OpenAI key hoặc Neo4j. Các thông số dung lượng/RAM là ước lượng cài đặt, không phải benchmark tài nguyên.

Giải nén toàn bộ gói vào một thư mục có quyền ghi, ví dụ `D:\HocTap\PROJECT_01`. Không chạy app trực tiếp trong ZIP.

## 2 Cài bằng PowerShell hoặc Anaconda Prompt

Chuyển vào thư mục chứa `app.py`, tạo Python 3.11 riêng rồi cài theo README. PowerShell không cần activate venv; gọi thẳng `.\.venv\Scripts\python.exe`. Điều này tránh lỗi ExecutionPolicy của `Activate.ps1`.

Với Anaconda:

```bat
conda create -n project01 python=3.11 -y
conda activate project01
cd /d "D:\HocTap\PROJECT_01"
python -m pip install torch==2.15.0 --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r requirements.txt
python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8521 --browser.gatherUsageStats false
```

Lần kiểm tra tác giả dùng Python 3.11.9 CPU và phiên bản trực tiếp ghi trong `requirements.txt` / `artifacts/environment.txt`. Môi trường cài mới trên máy khác chưa được kiểm tra; nếu đổi phiên bản sklearn/torch, nên train lại từ CSV bằng script để tránh lỗi nạp model.

## 3 Mở giao diện

Truy cập http://127.0.0.1:8521. Mặc định chỉ bind localhost. Tab Hội chẩn demo có bốn tác vụ; tab Tri thức cho xem nguồn/cạnh; tab Thực nghiệm chứa metrics/ROC/RL; tab Hướng dẫn nhắc lại lệnh.

Để nhập hồ sơ riêng, mở mục 21 trường khảo sát, bỏ chọn mẫu và sửa JSON. Giữ đủ 21 trường; Age là mã nhóm tuổi, không nhập tuổi 55 vào trường đó. Model không nhận glucose. Checkbox glucose bổ sung chỉ điều khiển luật cảnh báo, đơn vị mg/dL.

Không chọn lưu audit nếu chỉ trình diễn. Nếu chọn, SQLite local chứa câu hỏi/kết quả/trace; không có chức năng đăng nhập hay bảo vệ hồ sơ bệnh nhân thật.

## 4 Đọc và chạy notebook

Chạy `python -m notebook` trong cùng môi trường. Mở lần lượt 01–04. Chọn đúng kernel Python 3.11; xem dòng Python/Project trong cell đầu. Bấm Run All và lưu notebook sau khi kết thúc. Mỗi notebook đi từ mục tiêu, lý thuyết ngắn, code thật tới output và giới hạn.

Hoặc chạy `python scripts/execute_notebooks.py`: script dùng đúng interpreter hiện tại cho cả bốn kernel. Kết quả thực thi nằm trong `artifacts/notebook_execution.json`. Lượt đã kiểm tra có 26/26 code cell chạy thành công. Không chạy `build_notebooks.py` sau khi Run All nếu muốn giữ output; script đó chỉ tái tạo phần source notebook và xóa output hiện có.

## 5 Huấn luyện và kiểm thử

```bat
python scripts/run_experiments.py
python scripts/execute_notebooks.py
python -m pytest -q --junitxml=artifacts/test-results.xml
```

Train ghi đè artifact do Project01 sinh ra. Không thay split hoặc sửa test để tăng điểm. MLP fit BCE trên train, chọn epoch bằng validation; model/ngưỡng chọn validation trước khi xem test. Mọi model cùng tập dữ liệu. RL có seed train riêng và seed eval tách biệt.

## 6 Xử lý lỗi thường gặp

| Triệu chứng | Cách xử lý |
|---|---|
| Không có lệnh py | Dùng Anaconda hoặc cài Python launcher; không trộn Python của nhiều môi trường |
| ModuleNotFoundError | Dùng `python -m pip install -r requirements.txt` bằng đúng Python chạy app |
| Lỗi nạp joblib/torch | Kiểm tra phiên bản; tạo môi trường theo requirements hoặc huấn luyện lại |
| Port 8521 đã dùng | Chọn `--server.port 8522` rồi mở đúng URL mới |
| Thiếu model_manifest hoặc q_table | Chạy `python scripts/run_experiments.py` trước |
| Checksum dữ liệu thay đổi | Khôi phục CSV từ gói; không tự sửa provenance để bỏ qua kiểm tra |
| Notebook chạy sai thư mục | Khởi động Jupyter trong PROJECT_01 hoặc thư mục notebooks của nó |
| App chưa cập nhật model sau train | Dừng app bằng Ctrl+C và mở lại để xóa cache model |

## 7 Báo cáo

Mở `report/project01_CT_02_ducba.165.pdf`. Source LaTeX ở cùng thư mục. Nếu sửa nội dung, đọc `report/README.md` để build lại. PDF chứa số liệu của lần chạy đã bàn giao; khi thay model, cần cập nhật bảng/hình và biên dịch lại báo cáo.
