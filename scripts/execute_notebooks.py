"""Execute each notebook with this exact Python, preserving real outputs."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from time import perf_counter

import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]


def execute_one(path):
    start = perf_counter()
    with tempfile.TemporaryDirectory(prefix="project01_kernel_") as temporary:
        spec = Path(temporary) / "kernels" / "project01"
        spec.mkdir(parents=True)
        (spec / "kernel.json").write_text(json.dumps({"argv": [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"],
            "display_name": "Project01 Python", "language": "python"}), encoding="utf-8")
        os.environ["JUPYTER_PATH"] = temporary + os.pathsep + os.environ.get("JUPYTER_PATH", "")
        notebook = nbformat.read(path, as_version=4)
        # Let nbclient own the manager and its normal shutdown lifecycle.
        NotebookClient(notebook, timeout=900, kernel_name="project01",
                       resources={"metadata": {"path": str(ROOT)}}).execute()
        nbformat.write(notebook, path)
    code = [c for c in notebook.cells if c.cell_type == "code"]
    assert all(c.execution_count is not None for c in code)
    assert not any(o.output_type == "error" for c in code for o in c.outputs)
    return {"notebook": path.name, "code_cells": len(code), "executed_cells": len(code),
            "errors": 0, "seconds": round(perf_counter() - start, 2)}


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--one":
        print(json.dumps(execute_one(Path(sys.argv[2]))), flush=True)
    else:
        audit = []
        for path in sorted((ROOT / "notebooks").glob("*.ipynb")):
            # Separate processes isolate the ZeroMQ kernel lifecycle on Windows.
            result = subprocess.run([sys.executable, __file__, "--one", str(path)],
                                    check=True, capture_output=True, text=True, encoding="utf-8")
            record = json.loads(result.stdout.strip().splitlines()[-1])
            audit.append(record)
            print(json.dumps(record), flush=True)
        (ROOT / "artifacts/notebook_execution.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
