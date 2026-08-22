"""Demo TRUC QUAN cho bai giang HOC_TOAN_AI.md - moi con so deu tinh bang tay duoc.

Chi dung THU VIEN CHUAN cua Python (math, random, argparse). Khong cai gi them.
Bieu do ve bang ky tu ASCII de chay duoc tren moi terminal.

Sau phan, ung voi sau muc cua bai giang:
  1  cosine similarity giua cac vector 3 chieu
  2  attention: Q.K -> softmax -> tron V   (cau "con meo ngu")
  3  softmax doi hinh dang the nao khi temperature doi
  4  log-likelihood va perplexity cua mot cau 3 chu
  5  gradient descent hoi tu tung buoc, so 4 muc learning rate
  6  p95 vs trung binh tren du lieu lech duoi

Chay:
  venv\\Scripts\\python.exe docs\\hoc\\demo_toan_ai.py
  venv\\Scripts\\python.exe docs\\hoc\\demo_toan_ai.py --part 3
"""

import argparse
import math
import random

WIDTH = 78
BAR = 44


# --------------------------------------------------------------------------
# Tien ich chung
# --------------------------------------------------------------------------
def title(text: str) -> None:
    print()
    print("=" * WIDTH)
    print("  " + text)
    print("=" * WIDTH)


def step(text: str) -> None:
    print()
    print("--- " + text + " " + "-" * max(0, WIDTH - 5 - len(text)))


def bar(value: float, hi: float = 1.0, width: int = BAR) -> str:
    """Thanh ngang ty le voi value, de nhin bang mat thay ngay cai nao lon hon."""
    ratio = 0.0 if hi <= 0 else max(0.0, min(1.0, value / hi))
    filled = int(round(ratio * width))
    return "#" * filled + "." * (width - filled)


# --------------------------------------------------------------------------
# Cac phep toan - viet tay de nhin ro cong thuc, khong giau trong thu vien
# --------------------------------------------------------------------------
def dot(a, b):
    """a . b = a1*b1 + a2*b2 + ... -> MOT so."""
    return sum(x * y for x, y in zip(a, b, strict=True))


def norm(a):
    """||a|| = can bac hai cua tong binh phuong -> do dai mui ten."""
    return math.sqrt(sum(x * x for x in a))


def cosine(a, b):
    """cos = (a . b) / (||a|| * ||b||) -> chi do HUONG, bo qua DO DAI."""
    d = norm(a) * norm(b)
    return 0.0 if d == 0 else dot(a, b) / d


def softmax(z, temperature: float = 1.0):
    """e^(z_i/T) / tong e^(z_j/T). Tru max truoc khi mu de khong tran so."""
    scaled = [x / temperature for x in z]
    top = max(scaled)
    exps = [math.exp(x - top) for x in scaled]
    total = sum(exps)
    return [e / total for e in exps]


def percentile(values, k: float) -> float:
    """Nearest-rank: sap tang dan roi lay phan tu thu ceil(k/100 * n)."""
    s = sorted(values)
    n = len(s)
    idx = math.ceil(k / 100.0 * n)
    idx = max(1, min(n, idx))
    return s[idx - 1]


def median(values) -> float:
    s = sorted(values)
    n = len(s)
    mid = n // 2
    return s[mid] if n % 2 == 1 else (s[mid - 1] + s[mid]) / 2.0


def mean(values) -> float:
    return sum(values) / len(values)


# --------------------------------------------------------------------------
# PHAN 1 - Cosine similarity
# --------------------------------------------------------------------------
VECTORS = {
    "cho": [4, 3, 0],
    "meo": [3, 4, 0],
    "cun": [8, 6, 0],
    "o to": [0, 0, 5],
}


def part1() -> None:
    title("PHAN 1 - VECTOR, DOT PRODUCT, NORM, COSINE")
    print()
    print("  3 chieu y nghia: (1) nuoi trong nha  (2) la sinh vat  (3) la may moc")
    print()
    for name, v in VECTORS.items():
        print(f"    {name:<5} = {str(v):<12}  do dai ||v|| = {norm(v):.2f}")

    pairs = [("cho", "meo"), ("cho", "cun"), ("cho", "o to"), ("meo", "o to")]

    step("Tinh tung buoc")
    for a, b in pairs:
        va, vb = VECTORS[a], VECTORS[b]
        terms = " + ".join(f"{x}*{y}" for x, y in zip(va, vb, strict=True))
        print()
        print(f"  {a} vs {b}")
        print(f"    a . b   = {terms} = {dot(va, vb)}")
        print(f"    ||a||   = {norm(va):.2f}      ||b|| = {norm(vb):.2f}")
        print(f"    cosine  = {dot(va, vb)} / ({norm(va):.2f} * {norm(vb):.2f})"
              f" = {cosine(va, vb):.4f}")

    step("Nhin bang mat")
    print()
    for a, b in pairs:
        c = cosine(VECTORS[a], VECTORS[b])
        print("  {:<12} |{}| {:.3f}".format(a + " ~ " + b, bar(c), c))

    print()
    print("  DIEU CAN THAY:")
    print("    cho~cun cosine = 1.000 du dot product (50) LON HON cho~meo (24).")
    print("    Vi cun = 2 x cho: cung huong, chi dai gap doi -> cosine bo qua do dai.")
    print("    Neu xep hang bang dot product tho, ban se ket luan SAI.")


# --------------------------------------------------------------------------
# PHAN 2 - Attention
# --------------------------------------------------------------------------
def part2() -> None:
    title("PHAN 2 - ATTENTION: Q . K -> SOFTMAX -> TRON V")
    tokens = ["con", "meo", "ngu"]
    K = {"con": [1, 0], "meo": [2, 1], "ngu": [0, 1]}
    V = {"con": [1, 0, 0], "meo": [0, 2, 0], "ngu": [0, 0, 3]}
    q = [1, 1]
    d_k = len(q)

    print()
    print(f"  Cau: \"con meo ngu\". Dang tinh cho token \"ngu\", query q = {q}")
    print()
    print("    token   K (nhan dan)   V (noi dung)")
    for t in tokens:
        print(f"    {t:<7} {str(K[t]):<14} {str(V[t])}")

    step("Buoc 1: cham diem q . k voi tung token")
    scores = []
    print()
    for t in tokens:
        s = dot(q, K[t])
        scores.append(s)
        terms = " + ".join(f"{x}*{y}" for x, y in zip(q, K[t], strict=True))
        print(f"    q . k({t:<4}) = {terms} = {s}")
    print()
    print(f"    diem tho = {scores}")

    step("Buoc 2: softmax -> ty le chu y")
    weights = softmax(scores)
    print()
    for t, s, w in zip(tokens, scores, weights, strict=True):
        print(f"    {t:<5} diem {s:>2}  |{bar(w)}| {w * 100:5.1f}%")
    print()
    print(f"    tong ty le = {sum(weights):.4f}  (luon bang 1)")

    step("Buoc 3: tron V theo ty le do")
    out = [0.0] * len(V["con"])
    print()
    for t, w in zip(tokens, weights, strict=True):
        contrib = [w * x for x in V[t]]
        out = [o + c for o, c in zip(out, contrib, strict=True)]
        print("    {:.3f} x {:<10} = [{}]".format(
            w, str(V[t]), ", ".join(f"{c:.3f}" for c in contrib)))
    print("    " + "-" * 46)
    print("    ket qua cho \"ngu\"       = [{}]".format(
        ", ".join(f"{o:.3f}" for o in out)))
    print()
    print("    -> vector moi cua \"ngu\" da NGAM thong tin tu \"meo\" (78.7%).")

    step("Vi sao chia cho can(d_k)")
    scaled = [s / math.sqrt(d_k) for s in scores]
    w2 = softmax(scaled)
    print()
    print(f"    khong chia   : diem {scores} -> {[round(x, 3) for x in weights]}")
    print(f"    chia can({d_k}) : diem {[round(x, 2) for x in scaled]}"
          f" -> {[round(x, 3) for x in w2]}")
    print()
    print("    Chia lam phan bo MEM hon. Voi d_k = 64 hay 128 (thuc te), diem tho")
    print("    phinh rat to -> softmax bao hoa gan 0/1 -> gradient tat -> khong hoc duoc.")


# --------------------------------------------------------------------------
# PHAN 3 - Softmax va temperature
# --------------------------------------------------------------------------
def part3() -> None:
    title("PHAN 3 - SOFTMAX VA TEMPERATURE")
    z = [2.0, 1.0, 0.0]
    names = ["quan A", "quan B", "quan C"]

    print()
    print(f"  Diem tho (logits) = {z}")
    print("  Cong thuc: softmax(z)_i = e^(z_i / T) / tong e^(z_j / T)")

    step("T = 1.0, tinh tay tung buoc")
    exps = [math.exp(x) for x in z]
    total = sum(exps)
    print()
    for x, e in zip(z, exps, strict=True):
        print(f"    e^{x:<4} = {e:8.3f}")
    print(f"    tong   = {total:8.3f}")
    print()
    for n, e in zip(names, exps, strict=True):
        print(f"    {n} : {e:7.3f} / {total:.3f} = {e / total:.4f}")

    step("Temperature lam thay doi hinh dang phan bo the nao")
    for T in [0.2, 0.5, 1.0, 2.0, 5.0]:
        probs = softmax(z, T)
        tag = ""
        if T < 1.0:
            tag = "  <- gan nhu luon chon A (on dinh, lap lai duoc)"
        elif T > 1.0:
            tag = "  <- B va C cung hay duoc chon (sang tao, de bia)"
        else:
            tag = "  <- nguyen ban"
        print()
        print(f"  T = {T:<4}{tag}")
        for n, p in zip(names, probs, strict=True):
            print(f"    {n:<7} |{bar(p)}| {p * 100:6.2f}%")

    step("Hai truong hop cuc doan")
    print()
    for T in [0.01, 100.0]:
        probs = softmax(z, T)
        print(f"    T = {T:<7} -> {[round(p, 4) for p in probs]}")
    print()
    print("    T -> 0   : thanh argmax (greedy), chay lai cho ket qua y het")
    print("    T -> vo cung : deu nhau tuyet doi = boc ngau nhien, van ban thanh chao")

    step("Cong them cung mot so vao MOI logit thi sao?")
    print()
    print(f"    softmax([2, 1, 0])     = {[round(p, 4) for p in softmax(z)]}")
    print(f"    softmax([12, 11, 10])  = {[round(p, 4) for p in softmax([x + 10 for x in z])]}")
    print()
    print("    GIONG HET NHAU. Chi HIEU giua cac logit moi quan trong.")
    print("    Do la ly do code that tru max truoc khi mu (tranh tran so).")


# --------------------------------------------------------------------------
# PHAN 4 - Log-likelihood va perplexity
# --------------------------------------------------------------------------
def report_ppl(label, tokens, probs) -> float:
    prod = 1.0
    for p in probs:
        prod *= p
    logs = [math.log2(p) for p in probs]
    ll = sum(logs)
    ce = -ll / len(probs)
    ppl = 2 ** ce
    print()
    print(f"  {label}")
    for t, p, lg in zip(tokens, probs, logs, strict=True):
        print(f"    P({t:<22}) = {p:.4f}   log2 = {lg:7.3f}")
    print(f"    P(ca cau)          = {prod:.6f}")
    print(f"    log-likelihood     = {ll:.3f}  (cong cac log2)")
    print(f"    cross-entropy loss = {ce:.3f} bit/token  (doi dau, chia {len(probs)} token)")
    print(f"    perplexity         = 2^{ce:.3f} = {ppl:.3f}")
    return ppl


def part4() -> None:
    title("PHAN 4 - LOG-LIKELIHOOD VA PERPLEXITY")
    tokens = ["con", "meo | con", "ngu | con meo"]

    step("Model A - kha tot")
    ppl_a = report_ppl("cau: \"con meo ngu\"", tokens, [0.5, 0.25, 0.5])
    print()
    print(f"    Kiem tra cheo: PPL = (1/0.0625)^(1/3) = 16^(1/3) = {16 ** (1 / 3):.3f}  OK")

    step("Model B - te hon han tren cung cau do")
    ppl_b = report_ppl("cau: \"con meo ngu\"", tokens, [0.1, 0.05, 0.02])

    step("So sanh")
    print()
    print(f"    Model A: PPL = {ppl_a:6.2f}  |{bar(ppl_a, 60)}|")
    print(f"    Model B: PPL = {ppl_b:6.2f}  |{bar(ppl_b, 60)}|")
    print()
    print("    PPL = \"trung binh dang phan van giua bao nhieu lua chon\".")
    print("    Cang THAP cang tot. PPL = 1 la hoan hao; bang kich thuoc tu dien la doan mo.")
    print()
    print("    LUU Y: chi so sanh duoc khi CUNG tokenizer va CUNG tap test.")
    print("    Va PPL thap KHONG bao dam model huu ich hay noi that.")


# --------------------------------------------------------------------------
# PHAN 5 - Gradient descent
# --------------------------------------------------------------------------
def f(w):
    return (w - 3) ** 2


def grad(w):
    return 2 * (w - 3)


def axis_line(w, lo=-2.0, hi=8.0, width=52, target=3.0):
    """Ve mot truc ngang, danh dau vi tri w bang '*' va day bang '|'.

    w ra ngoai khung thi danh dau '<' hoac '>' o mep - de thay luc no bay di.
    """
    cells = ["."] * width

    def pos(x):
        r = (x - lo) / (hi - lo)
        return max(0, min(width - 1, int(round(r * (width - 1)))))

    cells[pos(target)] = "|"
    if w < lo:
        cells[0] = "<"
    elif w > hi:
        cells[width - 1] = ">"
    else:
        cells[pos(w)] = "*"
    return "".join(cells)


def part5() -> None:
    title("PHAN 5 - GRADIENT DESCENT VA LEARNING RATE")
    print()
    print("  Ham loss: f(w) = (w - 3)^2      dao ham: f'(w) = 2(w - 3)")
    print("  Day nam o w = 3. Bat dau tu w = 0.")
    print("  Quy tac cap nhat: w_moi = w_cu - lr * f'(w_cu)")

    step("lr = 0.1 - hoi tu dep, tung buoc")
    w = 0.0
    lr = 0.1
    print()
    print("   buoc      w      loss    f'(w)   buoc di   vi tri tren truc (| = day)")
    print("  " + "-" * 74)
    for i in range(12):
        g = grad(w)
        move = -lr * g
        print(f"   {i:>3}   {w:6.3f}  {f(w):7.3f}  {g:7.3f}  {move:+7.3f}   {axis_line(w)}")
        w = w + move
    print()
    print("    Buoc di TU DONG NGAN LAI khi gan day (vi gradient nho dan).")
    print("    Khong ai lap trinh dieu do - toan hoc tu lam.")

    step("Doi learning rate: chuyen gi xay ra")
    for lr in [0.01, 0.1, 0.5, 1.0, 1.1]:
        w = 0.0
        path = [w]
        blew_up = False
        for _ in range(30):
            w = w - lr * grad(w)
            if math.isnan(w) or abs(w) > 1e6:
                blew_up = True
                break
            path.append(w)

        last = path[-1]
        # Khoang cach toi day: dang XA DAN (no), GIU NGUYEN (dao dong) hay GAN LAI?
        d_last = abs(path[-1] - 3.0)
        d_prev = abs(path[-2] - 3.0)
        if blew_up or d_last > d_prev * 1.001:
            verdict = "NO (diverge) -> loss se thanh NaN"
        elif d_last < 1e-9:
            verdict = "hoi tu chinh xac"
        elif d_last < 0.5:
            verdict = "hoi tu"
        elif abs(d_last - d_prev) < 1e-9:
            verdict = "DAO DONG mai, khong bao gio xuong day"
        else:
            verdict = "cham qua, 30 buoc van chua toi"

        print()
        print(f"  lr = {lr:<5} sau 30 buoc: w = {last:>12.4f}   {verdict}")
        for i, p in enumerate(path[:6]):
            print(f"      buoc {i}  w = {p:>10.4f}  {axis_line(p)}")
        if len(path) > 6:
            print("      ...")

    step("Doc bang trieu chung nay khi di lam")
    print()
    print("    loss giam cuc cham           -> lr qua nho, tang len 3-10 lan")
    print("    loss nhay len xuong          -> lr hoi lon, giam + bat warmup")
    print("    loss thanh NaN sau vai buoc  -> lr qua lon, giam manh + gradient clipping")
    print()
    print("    Fine-tune LLM thuong dung lr ~ 1e-5 den 5e-5 (buoc rat be vi model DA")
    print("    o gan day roi - di manh la pha mat kien thuc cu).")


# --------------------------------------------------------------------------
# PHAN 6 - p95 vs trung binh
# --------------------------------------------------------------------------
def histogram(values, buckets, labels) -> None:
    counts = [0] * len(buckets)
    for v in values:
        for i, (lo, hi) in enumerate(buckets):
            if lo <= v < hi:
                counts[i] += 1
                break
    top = max(counts) if counts else 1
    for lbl, c in zip(labels, counts, strict=True):
        pct = 100.0 * c / len(values)
        print(f"    {lbl:<14} |{bar(c, top, 40)}| {c:>5} req ({pct:4.1f}%)")


def stats_block(values) -> None:
    print()
    print(f"    so mau            = {len(values)}")
    print(f"    TRUNG BINH (mean) = {mean(values):8.1f} ms")
    print(f"    trung vi   (p50)  = {median(values):8.1f} ms")
    print(f"    p90               = {percentile(values, 90):8.1f} ms")
    print(f"    p95               = {percentile(values, 95):8.1f} ms")
    print(f"    p99               = {percentile(values, 99):8.1f} ms")
    print(f"    nho nhat / lon nhat = {min(values):.1f} / {max(values):.1f} ms")


def part6() -> None:
    title("PHAN 6 - P95 VS TRUNG BINH TREN DU LIEU LECH")

    step("Vi du nho - tu tinh tay duoc")
    small = [100, 110, 120, 130, 140, 150, 160, 170, 180, 2000]
    print()
    print(f"    do tre 10 request (ms): {small}")
    stats_block(small)
    print()
    print("    Trung binh = 326 ms, nhung KHONG REQUEST NAO gan 326 ms.")
    print("    9/10 request duoi 180 ms, 1 request 2000 ms.")
    print("    Con so trung binh roi dung vao CHO TRONG giua hai cum.")

    step("Du lieu that hon - 1000 request mo phong")
    slow_rate = 0.08                         # 8% roi vao duong cham: retry, cold start, GC
    random.seed(42)
    data = []
    for _ in range(1000):
        if random.random() < slow_rate:
            v = random.gauss(1500, 400)      # duong cham
        else:
            v = random.gauss(120, 25)        # duong nhanh binh thuong
        data.append(max(20.0, v))
    print()
    print(f"    {slow_rate * 100:.0f}% request di duong cham (~1500 ms), con lai ~120 ms.")

    stats_block(data)

    print()
    print("    Phan bo (chu y DUOI DAI ben phai):")
    print()
    buckets = [(0, 100), (100, 150), (150, 200), (200, 400),
               (400, 1000), (1000, 1600), (1600, 10 ** 9)]
    labels = ["  < 100 ms", " 100-150 ms", " 150-200 ms", " 200-400 ms",
              " 400-1000 ms", "1000-1600 ms", "  > 1600 ms"]
    histogram(data, buckets, labels)

    m, p50, p95 = mean(data), median(data), percentile(data, 95)
    faster_than_mean = 100.0 * sum(1 for v in data if v < m) / len(data)
    print()
    print(f"    {faster_than_mean:.1f}% request NHANH HON muc trung binh ({m:.0f} ms).")
    print("    Trung binh bi keo len boi nhom cham - no khong mo ta ai ca.")

    step("Vi sao bao cao p95 chu khong bao cao trung binh")
    print()
    print(f"    trung binh {m:7.1f} ms  |{bar(m, p95)}|")
    print(f"    p50        {p50:7.1f} ms  |{bar(p50, p95)}|")
    print(f"    p95        {p95:7.1f} ms  |{bar(p95, p95)}|")
    print()
    print(f"    Trung binh {m:.0f} ms nghe on, nhung p95 = {p95:.0f} ms moi la thu")
    print("    ma cu 20 nguoi dung thi 1 nguoi phai chiu.")
    print()
    print("    1. User nho lan CHAM, khong nho lan trung binh.")
    print(f"    2. Mot trang goi 20 API, moi API cham {slow_rate * 100:.0f}% so lan:")
    at_least_one = (1 - (1 - slow_rate) ** 20) * 100
    print(f"       xac suat gap it nhat 1 lan cham = "
          f"1 - {1 - slow_rate:.2f}^20 = {at_least_one:.0f}%")
    print("       -> \"duoi nho\" hoa ra la DA SO phien.")
    print("    3. SLA viet bang phan vi: \"95% request duoi 500 ms\" moi kiem chung duoc.")
    print()
    print("    BAY: KHONG duoc lay trung binh cua cac p95 tu nhieu server!")
    print("         Phai gop du lieu tho (hoac histogram) roi tinh lai.")


# --------------------------------------------------------------------------
PARTS = {1: part1, 2: part2, 3: part3, 4: part4, 5: part5, 6: part6}


def main() -> None:
    ap = argparse.ArgumentParser(description="Demo toan cho AI Engineer")
    ap.add_argument("--part", type=int, choices=sorted(PARTS),
                    help="chi chay mot phan (1-6). Mac dinh: chay het.")
    args = ap.parse_args()

    parts = [args.part] if args.part else sorted(PARTS)
    for p in parts:
        PARTS[p]()

    print()
    print("=" * WIDTH)
    print("  Xong. Bai giang day du: docs/HOC_TOAN_AI.md")
    print("=" * WIDTH)


if __name__ == "__main__":
    main()
