# Dữ liệu và mã hóa

`classification.csv`: mẫu phân tầng 24.000 dòng lấy từ CSV UCI CDC Diabetes Health Indicators (nguồn 253.680 dòng, 21 input). Kế thừa nguyên mẫu/split nghiên cứu từ `Diabetes_MultiAgent`; project mới fit model riêng. `provenance.json` giữ URL, checksum nguồn và checksum mẫu. Không cần tải dữ liệu lại để chạy. Nguồn: https://archive.ics.uci.edu/dataset/891/cdc+diabetes+health+indicators (CC BY 4.0 theo metadata UCI).

Target là `Diabetes_binary` của CSV nguồn, đổi tên thành `target`: 0 không có nhãn, 1 tiền tiểu đường/tiểu đường theo mã nguồn. Không suy ra type 2, chẩn đoán hiện tại hay bệnh trong tương lai. Trang giới thiệu UCI có mô tả tổng quát chưa nhất quán với bảng metadata; schema trong gói lấy theo CSV thực tế, không dùng con số 35 đặc trưng ở phần văn bản giới thiệu.

Split cố định: train 16.787, validation 3.601, test 3.612. Các dòng có cùng vector 21 đặc trưng được gom cùng split. Không có ID người bệnh đủ để khẳng định tách hoàn toàn theo người; `row_id` chỉ là chỉ số dòng nguồn. Đây là khảo sát Mỹ và chưa được thẩm định ở Việt Nam.

| Trường | Ý nghĩa và mã |
|---|---|
| HighBP, HighChol | Được thông báo huyết áp/cholesterol cao; 0 không, 1 có |
| CholCheck | Kiểm tra cholesterol trong 5 năm; 0/1 |
| BMI | BMI kg/m²; khoảng quan sát/kiểm tra 12–98 |
| Smoker | Từng hút ít nhất 100 điếu; 0/1 |
| Stroke, HeartDiseaseorAttack | Tiền sử đột quỵ, bệnh mạch vành/nhồi máu; 0/1 |
| PhysActivity | Hoạt động thể chất trong 30 ngày ngoài công việc; 0/1 |
| Fruits, Veggies | Ăn trái cây/rau ít nhất một lần mỗi ngày; 0/1 |
| HvyAlcoholConsump | Uống nhiều rượu theo mã khảo sát; 0/1 |
| AnyHealthcare | Có bảo hiểm/chăm sóc sức khỏe theo khảo sát; 0/1 |
| NoDocbcCost | Không đi khám vì chi phí trong 12 tháng; 0/1 |
| GenHlth | Tự đánh giá sức khỏe 1 rất tốt đến 5 rất kém |
| MentHlth, PhysHlth | Số ngày sức khỏe tinh thần/thể chất kém trong 30 ngày; 0–30 |
| DiffWalk | Khó đi bộ/leo cầu thang; 0/1 |
| Sex | Mã giới tính nhị phân khảo sát: 0 nữ, 1 nam; giới hạn của dữ liệu gốc |
| Age | Mã 1: 18–24; 2: 25–29; …; 12: 75–79; 13: từ 80 tuổi |
| Education | 1 chưa đi học/mẫu giáo; 2 lớp 1–8; 3 lớp 9–11; 4 tốt nghiệp phổ thông; 5 học cao đẳng/đại học chưa tốt nghiệp; 6 tốt nghiệp đại học |
| Income | 1 dưới $10k; 2 $10–15k; 3 $15–20k; 4 $20–25k; 5 $25–35k; 6 $35–50k; 7 $50–75k; 8 từ $75k mỗi năm |

Các mô tả mã theo schema UCI/BRFSS, dùng để giải thích input nghiên cứu; không yêu cầu người dùng Việt Nam tự quy đổi thu nhập thành một hồ sơ lâm sàng. `target`, `row_id`, `group`, `split` không là đặc trưng.

`knowledge.json`: 12 ghi chú tiếng Việt biên soạn, 7 nguồn NIDDK/CDC, kiểm tra ngày 05/11/2026. Không phải dữ liệu bệnh nhân. `graph.json`: 12 khái niệm, 8 quan hệ có hướng và 12 cạnh bằng chứng. `retrieval_cases.json`: 24 câu do tác giả viết, không độc lập với người xây KB. `concept_graph.cypher`: xuất khái niệm/cạnh tùy chọn; chưa kiểm thử trên Neo4j server.
