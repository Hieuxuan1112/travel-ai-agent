"""Demo TUONG TAC: nhin tan mat vector search hoat dong the nao.

Chay tren CHINH kho du lieu that cua agent (92 chunk Wikivoyage trong Chroma),
khong phai vi du bia.

Ba che do:
  1. (mac dinh) Go cau hoi -> xem 5 doan gan nhat kem diem so
  2. --compare   -> so do gan cua hai cau bat ky (cosine similarity)
  3. --demo      -> chay san mot loat vi du cho thay diem manh/diem mu cua vector search

Chay:
  venv\\Scripts\\python.exe docs\\hoc\\demo_vector_search.py
  venv\\Scripts\\python.exe docs\\hoc\\demo_vector_search.py --compare
  venv\\Scripts\\python.exe docs\\hoc\\demo_vector_search.py --demo
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import main_02_02 as lab  # noqa: E402

BAR_WIDTH = 40


def bar(value: float, lo: float = 0.0, hi: float = 1.0) -> str:
    """Ve thanh do bang ky tu - de nhin bang mat thay ngay cai nao gan hon."""
    ratio = 0.0 if hi == lo else (value - lo) / (hi - lo)
    ratio = max(0.0, min(1.0, ratio))
    filled = int(ratio * BAR_WIDTH)
    return "#" * filled + "." * (BAR_WIDTH - filled)


def cosine(a: list[float], b: list[float]) -> float:
    """Cosine similarity tinh tay de thay ro cong thuc, khong giau trong thu vien.

    cos = (a . b) / (|a| * |b|)   -> 1 la cung huong, 0 la khong lien quan
    """
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    return dot / (norm_a * norm_b)


def show_results(store, query: str, k: int = 5) -> None:
    """Tim k doan gan nhat va in ra kem thanh do."""
    hits = store.similarity_search_with_score(query, k=k)
    if not hits:
        print("   (khong tim thay gi)")
        return

    print(f"\n   Cau hoi: {query!r}")
    print(f"   {'hang':<6}{'khoang cach':<14}trich doan")
    print("   " + "-" * 96)
    for rank, (doc, score) in enumerate(hits, start=1):
        # Chroma tra ve KHOANG CACH, khong phai do giong: SO CANG NHO CANG GAN.
        # Khong ve thanh do o day vi cac khoang cach thuong sat nhau (0.66 vs 0.71),
        # chuan hoa theo min-max se phong dai chenh lech va gay hieu nham.
        snippet = " ".join(doc.page_content.split())[:70]
        print(f"   {rank:<6}{score:<14.4f}{snippet}")
    spread = max(s for _, s in hits) - min(s for _, s in hits)
    print(f"   (chenh lech giua hang 1 va hang {len(hits)}: {spread:.4f})")


def mode_search(store) -> None:
    print("\n" + "=" * 104)
    print("  CHE DO TIM KIEM - go cau hoi bat ky, go 'exit' de thoat")
    print("=" * 104)
    print("  Goi y thu: beaches / surfing / castle / where can I eat / bai bien dep")

    while True:
        try:
            query = input("\n  > ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not query:
            continue
        if query.lower() in {"exit", "quit"}:
            break
        show_results(store, query)


def mode_compare() -> None:
    print("\n" + "=" * 104)
    print("  CHE DO SO SANH - nhap hai cau, xem chung gan nhau bao nhieu")
    print("=" * 104)
    print("  Thu: 'sandy beach' vs 'bai bien cat'")
    print("  Roi thu: 'sandy beach' vs 'bank interest rate'")

    while True:
        try:
            first = input("\n  Cau 1 (rong de thoat): ").strip()
            if not first:
                break
            second = input("  Cau 2: ").strip()
            if not second:
                break
        except (EOFError, KeyboardInterrupt):
            break

        vec_a = lab.embeddings.embed_query(first)
        vec_b = lab.embeddings.embed_query(second)
        score = cosine(vec_a, vec_b)

        print(f"\n  So chieu cua moi vector: {len(vec_a)}")
        print(f"  cosine similarity     : {score:.4f}")
        print(f"  {bar(score)}  (1.0 = trung y, 0.0 = khong lien quan)")
        verdict = "rat gan" if score > 0.8 else "kha gan" if score > 0.6 else "xa nhau"
        print(f"  Ket luan: {verdict}")


DEMO_CASES = [
    ("beaches", "Tim binh thuong - tu khoa co that trong tai lieu"),
    ("sandy shore for swimming", "KHONG dung chu 'beach' ma van ra dung - suc manh cua vector"),
    ("noi nao co bai bien dep", "Hoi bang TIENG VIET, tai lieu toan tieng Anh - van ra dung"),
    ("SKU-99321", "Ma so vo nghia - diem MU cua vector search, BM25 se lam tot hon"),
]


def mode_demo(store) -> None:
    print("\n" + "=" * 104)
    print("  CHE DO DEMO - bon vi du cho thay vector search manh va yeu o dau")
    print("=" * 104)
    for query, note in DEMO_CASES:
        print(f"\n  >>> {note}")
        show_results(store, query, k=3)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compare", action="store_true", help="so do gan cua hai cau")
    parser.add_argument("--demo", action="store_true", help="chay loat vi du dung san")
    args = parser.parse_args()

    if args.compare:
        mode_compare()
        return

    store = lab.get_travel_info_vectorstore()
    total = len(store.get(limit=100000)["ids"])
    print(f"\n  Kho du lieu: {total} chunk tu 4 trang Wikivoyage ve Cornwall")

    if args.demo:
        mode_demo(store)
    else:
        mode_search(store)


if __name__ == "__main__":
    main()
