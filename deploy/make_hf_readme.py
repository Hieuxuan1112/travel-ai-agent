"""Sinh README.md cho Hugging Face Space.

HF doc cau hinh Space tu phan YAML dau file README.md. Nhung neu de YAML do trong
README tren GitHub thi GitHub se render no thanh mot cai bang xau ngay dau trang.

Giai phap: giu README tren nhanh main sach, va chi chen YAML o nhanh rieng danh
cho deploy. Script nay lam viec chen do. Xem docs/DEPLOY_HF.md de biet quy trinh.

Chay:  venv\\Scripts\\python.exe deploy\\make_hf_readme.py
"""

import pathlib

FRONTMATTER = """---
title: Cornwall Travel Agent
emoji: 🏖️
colorFrom: blue
colorTo: green
sdk: docker
app_port: 8000
pinned: false
short_description: A ReAct agent that combines RAG travel search with live weather
---

"""

readme = pathlib.Path(__file__).resolve().parents[1] / "README.md"
content = readme.read_text(encoding="utf-8")

# Neu da co frontmatter (chay script hai lan) thi cat bo cai cu di roi chen lai.
if content.startswith("---\n"):
    end = content.find("\n---\n", 4)
    content = content[end + 5 :].lstrip("\n")

readme.write_text(FRONTMATTER + content, encoding="utf-8")
print("Da chen frontmatter cua Hugging Face vao README.md")
print("Nho: chi commit thay doi nay tren nhanh hf-space, KHONG phai main.")
