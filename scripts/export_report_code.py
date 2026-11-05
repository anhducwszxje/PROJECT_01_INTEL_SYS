"""Extract the source ranges printed in the report without changing runtime code."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "report" / "snippets"
OUT.mkdir(exist_ok=True)
SPEC = {
    "data_check": ("diabetes_agent/data.py", "load_data", None),
    "architecture": ("diabetes_agent/models.py", "architecture", None),
    "train_setup": ("diabetes_agent/models.py", "train_all", (78, 88)),
    "train_loop": ("diabetes_agent/models.py", "train_all", (89, 113)),
    "threshold": ("diabetes_agent/models.py", "choose_threshold", None),
    "model_selection": ("diabetes_agent/models.py", "train_all", (133, 145)),
    "inference": ("diabetes_agent/models.py", "predict", None),
    "retrieval": ("diabetes_agent/knowledge.py", "retrieve", None),
    "q_learning": ("diabetes_agent/rl.py", "train_q", None),
    "message_bus": ("diabetes_agent/system.py", "send", None),
    "council": ("diabetes_agent/system.py", "review", None),
    "coordination": ("diabetes_agent/system.py", "run", (120, 141)),
    "ui_presets": ("app.py", "run_preset", None),
    "ui_flow": ("app.py", "render_flow", None),
}
manifest = {}
characters = set()
commands = []
for identifier, (relative, function, lines) in SPEC.items():
    source_path = ROOT / relative
    source = source_path.read_text(encoding="utf-8-sig")
    matches = [node for node in ast.walk(ast.parse(source))
               if isinstance(node, ast.FunctionDef) and node.name == function]
    assert len(matches) == 1, (relative, function)
    node = matches[0]
    first, last = lines or (node.lineno, node.end_lineno)
    assert node.lineno <= first <= last <= node.end_lineno
    selected = source.splitlines()[first - 1:last]
    code = "\n".join(selected) + "\n"
    (OUT / f"{identifier}.py").write_text(code, encoding="utf-8", newline="\n")
    characters.update(char for char in code if ord(char) > 127)
    nonempty = [line for line in selected if line.strip()]
    gobble = min(len(line) - len(line.lstrip()) for line in nonempty)
    manifest[identifier] = {"source": relative, "function": function,
        "first_line": first, "last_line": last, "gobble": gobble,
        "sha256": hashlib.sha256(code.encode("utf-8")).hexdigest()}
    commands.append(r"\expandafter\def\csname code@" + identifier + r"\endcsname#1{%" + "\n" +
        r"\par\noindent\begin{minipage}{\linewidth}" + "\n" +
        r"\noindent{\footnotesize\textit{Nguồn: }\path{" + relative + "}" +
        f", dòng {first}--{last}." + r"}\par\smallskip" + "\n" +
        r"\lstinputlisting[style=projectcode,firstnumber=" + str(first) +
        ",gobble=" + str(gobble) + r",caption={#1}]{snippets/" + identifier + ".py}" +
        "\n" + r"\end{minipage}\par}")

style = r'''\ifPDFTeX\else
\IfFontExistsTF{Consolas}{\setmonofont{Consolas}[Scale=MatchLowercase]}{\setmonofont{DejaVu Sans Mono}[Scale=MatchLowercase]}
\fi
\lstdefinestyle{projectcode}{style=mystyle,language=Python,
  basicstyle=\ttfamily\fontsize{9}{11}\selectfont,
  numberstyle=\ttfamily\fontsize{7}{9}\selectfont\color{codegray},
  columns=fullflexible,breaklines=true,breakatwhitespace=false,upquote=true,
  xleftmargin=15pt,xrightmargin=3pt,framexleftmargin=3pt,
  aboveskip=7pt,belowskip=10pt,captionpos=b}
'''
# Listings already registers Latin-1. Register the remaining Unicode letters
# so Vietnamese text is buffered in source order rather than emitted early.
style += r'''\ifPDFTeX\else
\makeatletter
\begingroup\catcode0=12\relax
\gdef\reportunicode{\lst@CCECUse\lst@ProcessLetter '''
style += "".join(char for char in sorted(characters) if ord(char) > 255)
style += r'''^^00}
\endgroup
\lst@AddToHook{SelectCharTable}{\reportunicode}
\makeatother
\fi
'''
style += r"\newcommand{\reportcode}[2]{\csname code@#1\endcsname{#2}}" + "\n"
style += "\n".join(commands) + "\n"
(ROOT / "report" / "code_setup.tex").write_text(style, encoding="utf-8")
(OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({key: f"{value['source']}:{value['first_line']}-{value['last_line']}"
                  for key, value in manifest.items()}, ensure_ascii=False, indent=2))
