"""Xuat so do do thi agent ra docs/graph.png + docs/graph.mmd (dung cho README).

Chay:  venv\\Scripts\\python.exe make_graph_image.py
"""

from pathlib import Path

from main_02_02 import travel_info_agent

DOCS = Path(__file__).parent / "docs"
DOCS.mkdir(exist_ok=True)

graph = travel_info_agent.get_graph()

(DOCS / "graph.mmd").write_text(graph.draw_mermaid(), encoding="utf-8")
print("wrote docs/graph.mmd")

try:
    (DOCS / "graph.png").write_bytes(graph.draw_mermaid_png())
    print("wrote docs/graph.png")
except Exception as exc:  # mermaid.ink can can mang
    print(f"PNG skipped ({exc}); the .mmd file is enough for the README.")
