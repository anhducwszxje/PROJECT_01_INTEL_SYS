"""Package the independent project, excluding caches and optional local audit."""
import hashlib
import json
import zipfile
from pathlib import Path

import nbformat

ROOT = Path(__file__).resolve().parents[1]
excluded = {".git", ".venv", "__pycache__", ".pytest_cache", ".ipynb_checkpoints", "build"}
output = ROOT.parent / "PROJECT_01_Ban_Giao.zip"
books = sorted((ROOT / "notebooks").glob("*.ipynb"))
assert len(books) == 4
for path in books:
    book = nbformat.read(path, as_version=4)
    code = [c for c in book.cells if c.cell_type == "code"]
    assert all(c.execution_count is not None for c in code), path.name
    assert not any(o.output_type == "error" for c in code for o in c.outputs), path.name
assert (ROOT / "report/project01_CT_02_ducba.165.pdf").is_file()
files = [p for p in ROOT.rglob("*") if p.is_file() and not set(p.relative_to(ROOT).parts) & excluded
         and p.name not in {"demo_audit.sqlite3", "DELIVERY_MANIFEST.json"}]
manifest = {"files": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in sorted(files)},
            "notes": "Four executed notebooks, source, public study data, trained artifacts and PDF/LaTeX. Excludes environments, caches, build intermediates and optional private audit."}
manifest_path = ROOT / "DELIVERY_MANIFEST.json"
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
    for path in [*files, manifest_path]:
        archive.write(path, "PROJECT_01/" + path.relative_to(ROOT).as_posix())
with zipfile.ZipFile(output) as archive:
    assert archive.testzip() is None
print(json.dumps({"zip": str(output), "files": len(files) + 1,
                  "bytes": output.stat().st_size, "sha256": hashlib.sha256(output.read_bytes()).hexdigest()}, indent=2))
