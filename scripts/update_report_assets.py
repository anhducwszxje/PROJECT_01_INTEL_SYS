"""Refresh measured report tables, figures and notebook excerpts from artifacts."""
import json
import shutil
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import nbformat
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts"
REPORT = ROOT / "report"
TABLES = REPORT / "tables"
IMAGES = REPORT / "images"
TABLES.mkdir(exist_ok=True)
IMAGES.mkdir(exist_ok=True)
import sys
sys.path.insert(0, str(ROOT))
from diabetes_agent.models import plot_test_curves
plot_test_curves()


def escape(value):
    return str(value).replace("_", r"\_").replace("%", r"\%")


def table(name, caption, header, rows, columns):
    content = [r"\begin{table}[H]\centering\small", r"\caption{" + caption + "}",
               r"\begin{tabular}{@{}" + columns + r"@{}}\toprule",
               " & ".join(header) + r" \\\midrule"]
    content += [" & ".join(escape(x) for x in row) + r" \\" for row in rows]
    content += [r"\bottomrule\end{tabular}", r"\end{table}"]
    (TABLES / (name + ".tex")).write_text("\n".join(content), encoding="utf-8")


frame = pd.read_csv(ROOT / "data/classification.csv")
table("splits", "Phân bố tập nghiên cứu được sử dụng thực tế.",
      ["Tập", "Số dòng", "Nhãn 1", "Tỷ lệ nhãn 1"],
      [(s, len(g), int(g.target.sum()), f"{g.target.mean()*100:.2f}\\%")
       for s, g in frame.groupby("split", sort=False)], "lrrr")
# Percent cells are escaped by table(); use ordinary numbers in tables instead.
p = TABLES / "splits.tex"
p.write_text(p.read_text(encoding="utf-8").replace(r"\\%", r"\%"), encoding="utf-8")
for split in ("test", "validation"):
    data = pd.read_csv(OUT / f"metrics_{split}.csv")
    table("model_" + split, f"Chỉ số trên {split}; ngưỡng được chọn bằng F1 validation.",
          ["Model", "AUC", "AP", "F1", "Precision", "Recall", "Brier"],
          [[r.model] + [f"{getattr(r, k):.4f}" for k in ("roc_auc", "average_precision", "f1", "precision", "recall", "brier")]
           for r in data.itertuples()], "lrrrrrr")
data = pd.read_csv(OUT / "metrics_test.csv")
table("confusion", "Ngưỡng đã khóa và số lượng dự đoán trên test.",
      ["Model", "Ngưỡng", "TN", "FP", "FN", "TP", "Specificity"],
      [[r.model, f"{r.threshold:.3f}", r.tn, r.fp, r.fn, r.tp, f"{r.specificity:.4f}"] for r in data.itertuples()], "lrrrrrr")
rl = pd.read_csv(OUT / "rl_summary.csv")
table("rl", "Reward mỗi ngày trong simulator; std giữa năm giá trị trung bình theo seed train.",
      ["Policy", "Reward trung bình", "Độ lệch chuẩn"],
      [[r.policy, f"{r.mean:.4f}", f"{r.std:.4f}"] for r in rl.itertuples()], "lrr")
evals = pd.read_csv(OUT / "system_evaluation.csv")
table("system", "Các kịch bản chức năng được chạy ở phiên bản bàn giao.",
      ["Kịch bản", "Trạng thái mong đợi", "Đạt", "Thông điệp"],
      [[r.case, r.expected, "Có" if r.passed else "Không", r.messages] for r in evals.itertuples()], "llcr")
retrieval = pd.read_csv(OUT / "retrieval_evaluation.csv")
table("retrieval", "Đánh giá truy xuất trên 24 câu hỏi của bộ thực nghiệm.",
      ["Cấu hình", "Hit@1", "Hit@3", "MRR"],
      [["TF-IDF + graph" if graph else "TF-IDF", *[f"{g[c].mean():.4f}" for c in ("hit_at_1", "hit_at_3", "reciprocal_rank")]]
       for graph, g in retrieval.groupby("graph")], "lrrr")
docs = json.loads((ROOT / "data/knowledge.json").read_text(encoding="utf-8"))
table("knowledge", "Danh mục 12 ghi chú có liên kết tới bảy trang nguồn.",
      ["ID", "Chủ đề", "Nguồn"],
      [[d["id"], d["title"], "CDC" if "CDC" in d["source_title"] else "NIDDK"] for d in docs], "lll")
for name in ("classification.png", "training.png", "rl.png"):
    shutil.copy2(OUT / "figures" / name, IMAGES / name)

# Explicit graph figure: label only the concepts, not invented patient entities.
graph = json.loads((ROOT / "data/graph.json").read_text(encoding="utf-8"))
positions = {"diabetes": (.10,.60), "types": (.10,.91), "tests": (.36,.80),
 "fasting": (.64,.94), "a1c": (.64,.72), "a1c_limits": (.91,.72),
 "care": (.36,.35), "journal": (.64,.47), "activity": (.64,.22),
 "nutrition": (.10,.06), "carbs": (.36,.06), "hypoglycemia": (.90,.22)}
fig, ax = plt.subplots(figsize=(9,4.5))
for edge in graph["relations"]:
    start, end = positions[edge["source"]], positions[edge["target"]]
    ax.annotate("", xy=end, xytext=start, arrowprops={"arrowstyle": "->", "color": "#668487", "lw": 1.5,
                "shrinkA": 38, "shrinkB": 44})
    ax.text((start[0]+end[0])/2, (start[1]+end[1])/2 + .035,
            edge["type"], fontsize=11, color="#49676a", ha="center")
for name, (x,y) in positions.items():
    ax.text(x,y,name,ha="center",va="center",fontsize=14,
            bbox={"boxstyle":"round,pad=.5", "fc":"#ecf6f5", "ec":"#20716f", "lw":1.2})
ax.set(xlim=(-.03,1.04),ylim=(-.04,1.04)); ax.axis("off")
fig.tight_layout(); fig.savefig(OUT / "figures/knowledge_graph.png", dpi=180); plt.close(fig)
shutil.copy2(OUT / "figures/knowledge_graph.png", IMAGES / "knowledge_graph.png")


def cellshot(notebook_name, source_fragment, filename):
    book = nbformat.read(ROOT / "notebooks" / notebook_name, as_version=4)
    cell = next(c for c in book.cells if c.cell_type == "code" and source_fragment in c.source)
    output_text = []
    for output in cell.outputs:
        if output.output_type == "stream":
            output_text.append(output.text)
        elif output.output_type in ("execute_result", "display_data") and "text/plain" in output.data:
            output_text.append(output.data["text/plain"])
    # Preserve measured values; line wrapping changes presentation only.
    text = "In [" + str(cell.execution_count) + "]\n" + cell.source + "\n\nOutput\n" + "\n".join(output_text)
    lines = []
    for line in text.splitlines():
        lines.extend(textwrap.wrap(line, width=84, replace_whitespace=False, drop_whitespace=False) or [""])
    font_path = Path("C:/Windows/Fonts/consola.ttf")
    if not font_path.exists():
        font_path = Path("C:/Windows/Fonts/cour.ttf")
    font = ImageFont.truetype(str(font_path), 23)
    width, line_height = 1260, 32
    image = Image.new("RGB", (width, 62+len(lines)*line_height), "#f7f8fa")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((1,1,width-2,image.height-2), radius=10, outline="#cbd4db", width=2)
    for i,line in enumerate(lines):
        color = "#185b77" if line.startswith(("#", "In [", "Output")) else "#172a3a"
        draw.text((25,24+i*line_height),line,font=font,fill=color)
    image.save(IMAGES / filename)


cellshot("01_Du_lieu_va_huan_luyen_MLP.ipynb", "test_metrics, manifest = train_all()", "cell_train.png")
cellshot("02_Tri_thuc_va_Graph_Retrieval.ipynb", 'query = "HbA1c', "cell_retrieval.png")
cellshot("03_Q_learning_nhac_nhat_ky.ipynb", 'q = np.load', "cell_rl.png")
cellshot("04_Tich_hop_Multi_Agent_va_Demo.ipynb", 'urgent = system.run', "cell_system.png")
print("Updated measured tables, charts, graph and four notebook excerpts.")
