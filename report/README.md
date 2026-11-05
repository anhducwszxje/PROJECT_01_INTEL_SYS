# Báo cáo Project01

Bản đọc: `project01_CT_02_ducba.165.pdf`. Source chính: `main.tex`; các phần nội dung chia file cùng thư mục. Style kế thừa Agent02, nội dung và số liệu riêng của Project01.

Báo cáo có chương mã nguồn với 14 đoạn trích và giải thích, cùng chương giao diện demo gồm bốn ảnh chụp. Các đoạn mã giữ tên tệp và số dòng gốc; bảng đối chiếu và SHA256 nằm trong `snippets/manifest.json`.

Để cập nhật bảng/đồ thị theo artifact và trích lại code, chạy từ thư mục PROJECT_01:

```powershell
python scripts/update_report_assets.py
python scripts/export_report_code.py
```

Sau đó đối chiếu các nhận xét định lượng trong `results.tex`, `learning.tex`, `demo.tex`. Script không tự thay diễn giải hoặc chụp lại giao diện. Ảnh demo nằm trong `images/demo_*.jpg`.

Biên dịch bằng MiKTeX hoặc TeX Live có XeLaTeX và font Times New Roman (nếu thiếu, source fallback TeX Gyre Termes). Từ thư mục report:

```powershell
New-Item -ItemType Directory -Force build | Out-Null
xelatex -interaction=nonstopmode -halt-on-error -output-directory=build main.tex
xelatex -interaction=nonstopmode -halt-on-error -output-directory=build main.tex
Copy-Item build/main.pdf project01_CT_02_ducba.165.pdf -Force
```

Trong Anaconda Prompt/CMD, dùng `mkdir build` nếu chưa có và `copy /Y build\main.pdf project01_CT_02_ducba.165.pdf` ở bước cuối. Có thể đưa toàn bộ thư mục report lên Overleaf và chọn XeLaTeX; chưa kiểm thử trực tiếp Overleaf. Không chỉ đưa riêng main.tex vì còn cần nội dung, bảng và hình.

Sau khi sửa, kiểm tra PDF ở từng trang: bìa, mục lục, bảng, mã, ảnh demo, tham chiếu và trang trắng. Bản bàn giao đã được biên dịch và render để kiểm tra trực quan.
