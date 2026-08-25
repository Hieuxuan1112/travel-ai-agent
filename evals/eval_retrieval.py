"""Do chat luong TIM KIEM: vector-only vs BM25-only vs hybrid.

Khong goi LLM - chi do tang truy hoi, nen chay nhanh va gan nhu mien phi
(chi ton mot lan embedding cho moi cau hoi).

Chay:  venv\\Scripts\\python.exe evals\\eval_retrieval.py
Ket qua ghi ra evals/retrieval_comparison.md

## Cach lam nhan (doc ky truoc khi tin con so)

Khong co bo du lieu gan nhan san cho 92 chunk nay, nen dung NHAN YEU:
mot chunk duoc coi la LIEN QUAN neu no chua tu khoa moc cua cau hoi.

Han che phai noi ro:
  - Nhan yeu, khong phai nguoi danh gia -> con so chi de SO SANH ba cach voi
    nhau, khong phai diem tuyet doi.
  - Neu cau hoi chua san tu khoa moc thi BM25 duoc loi the mien phi. Vi vay
    mot NUA bo cau hoi duoi day duoc dien dat VONG (paraphrase) - khong chua
    tu khoa - de vector co dat dung cua no.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import main_02_02 as lab  # noqa: E402
from retrieval import HybridRetriever  # noqa: E402

# (cau hoi, tu khoa moc, cau hoi co chua tu khoa khong)
GOLDEN = [
    # -- dien dat VONG: khong chua tu khoa -> loi the cho vector -------------
    ("where can I ride waves on a board", "surf", False),
    ("an outdoor theatre carved into a cliff", "Minack", False),
    ("a quiet place by the sea to swim", "beach", False),
    ("how do I travel there without a car", "train", False),
    ("celebration at the end of the growing season", "harvest", False),
    ("small settlement where boats bring in the catch", "fishing", False),
    # -- ten rieng / tu khoa chinh xac -> loi the cho BM25 -------------------
    ("Penzance", "Penzance", True),
    ("Newquay", "Newquay", True),
    ("Falmouth", "Falmouth", True),
    ("Tamar Valley", "Tamar", True),
    ("St Ives", "St Ives", True),
    ("Minack Theatre", "Minack", True),
]

K_VALUES = (1, 3, 5)


def is_relevant(text: str, keyword: str) -> bool:
    return keyword.lower() in text.lower()


def recall_at_k(retriever: HybridRetriever, mode: str, k: int, subset=None) -> float:
    """Ti le cau hoi co IT NHAT MOT ket qua lien quan trong top-k."""
    rows = subset if subset is not None else GOLDEN
    hits = 0
    for question, keyword, _ in rows:
        if mode == "vector":
            ids = retriever.vector_ids(question, k=k)
        elif mode == "bm25":
            ids = retriever.bm25_ids(question, k=k)
        else:
            ids = [i for i, _, _ in retriever.search(question, k=k)]

        texts = [retriever._by_id[i][0] for i in ids if i in retriever._by_id]
        if any(is_relevant(t, keyword) for t in texts):
            hits += 1
    return hits / len(rows)


def main() -> None:
    retriever = HybridRetriever(lab.get_travel_info_vectorstore())
    print(f"Kho: {len(retriever.ids)} chunk | bo cau hoi: {len(GOLDEN)}\n")

    paraphrase = [r for r in GOLDEN if not r[2]]
    literal = [r for r in GOLDEN if r[2]]
    modes = ("vector", "bm25", "hybrid")

    table = {m: {k: recall_at_k(retriever, m, k) for k in K_VALUES} for m in modes}
    split = {
        m: {
            "paraphrase": recall_at_k(retriever, m, 5, paraphrase),
            "literal": recall_at_k(retriever, m, 5, literal),
        }
        for m in modes
    }

    for mode in modes:
        line = "  ".join(f"recall@{k} {table[mode][k]:.0%}" for k in K_VALUES)
        print(f"{mode:8} {line}")

    lines = [
        "# So sanh cach tim kiem",
        "",
        f"{len(retriever.ids)} chunk Wikivoyage - {len(GOLDEN)} cau hoi - "
        "nhan yeu (chunk chua tu khoa moc = lien quan).",
        "Sinh boi `evals/eval_retrieval.py`. Khong goi LLM.",
        "",
        "| Cach tim | recall@1 | recall@3 | recall@5 |",
        "| --- | :-: | :-: | :-: |",
    ]
    names = {"vector": "Vector only (truoc)", "bm25": "BM25 only",
             "hybrid": "**Hybrid (RRF)** (sau)"}
    for mode in modes:
        cells = " | ".join(f"{table[mode][k]:.0%}" for k in K_VALUES)
        lines.append(f"| {names[mode]} | {cells} |")

    lines += [
        "",
        "## Tach theo kieu cau hoi (recall@5)",
        "",
        "| Cach tim | Cau dien dat vong | Ten rieng / tu khoa |",
        "| --- | :-: | :-: |",
    ]
    for mode in modes:
        lines.append(
            f"| {names[mode]} | {split[mode]['paraphrase']:.0%} "
            f"| {split[mode]['literal']:.0%} |"
        )

    # Ket luan TU SO LIEU, khong viet san. Neu hybrid khong hon thi phai noi that.
    best_single = {k: max(table["vector"][k], table["bm25"][k]) for k in K_VALUES}
    wins = [k for k in K_VALUES if table["hybrid"][k] > best_single[k]]
    ties = [k for k in K_VALUES if table["hybrid"][k] == best_single[k]]

    lines += [
        "",
        "## Doc bang the nao",
        "",
        f"- Vector manh o cau **dien dat vong** ({split['vector']['paraphrase']:.0%}) "
        "vi no hieu nghia chu khong doi trung chu.",
        f"- BM25 manh o **ten rieng** ({split['bm25']['literal']:.0%}) "
        "vi no khop chinh xac chuoi ky tu.",
        "",
        "### Ket luan",
        "",
    ]
    if wins:
        lines.append(
            f"Hybrid tot hon cach don le tot nhat o recall@{', recall@'.join(map(str, wins))}."
        )
    else:
        lines += [
            "**Hybrid KHONG cai thien gi tren kho nay.** Vector don thuan da dat "
            f"recall@1 {table['vector'][1]:.0%} va recall@3 {table['vector'][3]:.0%}; "
            f"hybrid duoc {table['hybrid'][1]:.0%} va {table['hybrid'][3]:.0%}.",
            "",
            "Ly do: kho chi co "
            f"{len(retriever.ids)} chunk va bo cau hoi de - vector da cham tran, "
            "khong con cho de cai thien. Tron them BM25 chi lam mot vai ket qua tot "
            "bi day xuong. Hybrid chi thang khi kho lon, nhieu tai lieu gan giong "
            "nhau, va co ma so / ten rieng hiem ma embedding khong nam duoc.",
            "",
            "**Quyet dinh ky thuat:** giu code hybrid nhung de MAC DINH TAT "
            "(`RETRIEVAL_MODE=vector`). Them phuc tap ma khong do duoc loi ich la "
            "cai gia phai tra vo ich. Kho lon len thi bat lai va do lai.",
        ]
    if ties and not wins:
        lines.append("")
        lines.append(
            f"(Hybrid ngang bang o recall@{', recall@'.join(map(str, ties))}.)"
        )

    lines += [
        "",
        "**Han che cua phep do:** nhan la nhan yeu (chunk chua tu khoa moc), khong "
        "phai nguoi danh gia. Con so de so ba cach voi nhau, khong phai diem tuyet doi.",
    ]

    out = Path(__file__).parent / "retrieval_comparison.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n-> {out}")


if __name__ == "__main__":
    main()
