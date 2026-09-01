# DSA & OOP — từ số 0 đến qua được vòng technical interview

> Hai chủ đề trong một file, vì trong phỏng vấn chúng đi cùng nhau: DSA để giải bài
> LeetCode, OOP để trả lời câu "thiết kế class thế nào".
>
> Phần OOP bám vào **code thật của bạn** — `ToolsExecutionNode` trong
> [`main_02_02.py`](../../main_02_02.py) là một ví dụ OOP đẹp mà bạn đã viết rồi.

**Mục lục**

**PHẦN A — DSA**
1. [Big-O: đo code nhanh chậm](#1-big-o-đo-code-nhanh-chậm)
2. [Array & String](#2-array--string)
3. [Hash map — vũ khí số 1](#3-hash-map--vũ-khí-số-1)
4. [Two pointers & Sliding window](#4-two-pointers--sliding-window)
5. [Stack & Queue](#5-stack--queue)
6. [Linked list](#6-linked-list)
7. [Cây và đệ quy](#7-cây-và-đệ-quy)
8. [BFS / DFS trên đồ thị](#8-bfs--dfs-trên-đồ-thị)
9. [Sắp xếp & tìm kiếm nhị phân](#9-sắp-xếp--tìm-kiếm-nhị-phân)
10. [Quy hoạch động — mức cơ bản](#10-quy-hoạch-động--mức-cơ-bản)
11. [Lộ trình 40 bài LeetCode](#11-lộ-trình-40-bài-leetcode)

**PHẦN B — OOP**
12. [Bốn tính chất, giải thích không thuộc lòng](#12-bốn-tính-chất-giải-thích-không-thuộc-lòng)
13. [OOP trong code bạn đã viết](#13-oop-trong-code-bạn-đã-viết)
14. [SOLID — chỉ 3 cái hay bị hỏi](#14-solid--chỉ-3-cái-hay-bị-hỏi)
15. [Design pattern bạn đã dùng](#15-design-pattern-bạn-đã-dùng)
16. [Tự kiểm tra](#16-tự-kiểm-tra)

---

# PHẦN A — DSA

## 1. Big-O: đo code nhanh chậm

Bạn không đo bằng giây — máy khác nhau cho số khác nhau. Bạn đo bằng **số phép tính tăng
thế nào khi dữ liệu to ra**.

```python
def tim(ds, x):          # ds có n phần tử
    for phan_tu in ds:   # chạy tối đa n lần
        if phan_tu == x:
            return True
    return False
```

n gấp đôi → số vòng lặp gấp đôi. Ta viết **O(n)**.

| Ký hiệu | Tên | n=1.000 thì khoảng | Ví dụ |
|---|---|---|---|
| O(1) | hằng số | 1 | `d[key]`, `arr[i]` |
| O(log n) | logarit | 10 | binary search |
| O(n) | tuyến tính | 1.000 | duyệt một vòng |
| O(n log n) | | 10.000 | `sorted()` |
| O(n²) | bậc hai | 1.000.000 | hai vòng lồng nhau |
| O(2ⁿ) | mũ | không tưởng | đệ quy không nhớ |

**Quy tắc đọc nhanh:** đếm số vòng `for` lồng nhau. Một vòng → O(n). Hai vòng lồng →
O(n²). Chia đôi mỗi bước → O(log n).

**Bỏ hằng số:** O(2n) viết là O(n). O(n² + n) viết là O(n²) — số hạng lớn nhất nuốt phần
còn lại.

**Space complexity** là bộ nhớ phụ bạn cấp thêm, đếm theo cùng cách. Tạo một `dict` chứa n
phần tử → O(n) bộ nhớ.

> **Trong phỏng vấn luôn nói cả hai:** *"Giải pháp này O(n) thời gian, O(n) bộ nhớ."*
> Người phỏng vấn chờ đúng câu đó. Không nói là mất điểm dù code đúng.

---

## 2. Array & String

Trong Python, `list` và `str` là hai thứ bạn dùng nhiều nhất.

```python
arr = [3, 1, 4, 1, 5]
arr[0]            # O(1)  — truy cập theo chỉ số
arr.append(9)     # O(1)  — thêm cuối
arr.insert(0, 9)  # O(n)  — thêm đầu, phải dịch mọi phần tử
arr.pop()         # O(1)  — xoá cuối
arr.pop(0)        # O(n)  — xoá đầu
x in arr          # O(n)  — phải duyệt
```

**Bẫy hay gặp:** `x in arr` là O(n), nhưng `x in tap_hop` (set) là O(1). Đổi `list` sang
`set` là cách tăng tốc phổ biến nhất trong LeetCode.

**String bất biến (immutable).** Nối chuỗi trong vòng lặp là O(n²):

```python
s = ""
for c in danh_sach:
    s += c          # ✗ mỗi lần tạo chuỗi MỚI, copy toàn bộ

s = "".join(danh_sach)   # ✓ O(n)
```

Kỹ thuật hay dùng:

```python
arr[::-1]                    # đảo ngược
arr[i:j]                     # cắt, O(j-i)
sorted(arr)                  # O(n log n), trả list mới
arr.sort()                   # sắp tại chỗ
enumerate(arr)               # vừa chỉ số vừa giá trị
zip(a, b)                    # ghép đôi hai list
```

---

## 3. Hash map — vũ khí số 1

**Nếu chỉ học được một cấu trúc, học cái này.** Khoảng một phần ba bài LeetCode dễ và
trung bình giải bằng dict.

Ý tưởng: đổi **tìm kiếm O(n)** thành **tra cứu O(1)** bằng cách trả giá bộ nhớ.

Bài kinh điển — **Two Sum**: cho mảng và số `target`, tìm 2 chỉ số cộng lại bằng target.

```python
# Cách ngây thơ: O(n²)
def two_sum_cham(nums, target):
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]

# Cách dùng dict: O(n) thời gian, O(n) bộ nhớ
def two_sum(nums, target):
    da_thay = {}                      # giá trị -> chỉ số
    for i, x in enumerate(nums):
        con_thieu = target - x
        if con_thieu in da_thay:      # O(1)
            return [da_thay[con_thieu], i]
        da_thay[x] = i
    return []
```

Ý tưởng cốt lõi: thay vì hỏi *"có cặp nào cộng bằng target không"*, ta hỏi *"số bù của số
hiện tại đã đi qua chưa"*. Một vòng duy nhất.

Ba biến thể phải thuộc:

```python
from collections import Counter, defaultdict

Counter("aabbbc")           # đếm tần suất: {'a':2,'b':3,'c':1}
d = defaultdict(list)       # dict tự tạo giá trị mặc định
d["x"].append(1)            # không cần kiểm tra key tồn tại

# Nhóm anagram: sắp chữ cái làm khoá
nhom = defaultdict(list)
for tu in ["eat", "tea", "tan"]:
    nhom["".join(sorted(tu))].append(tu)
```

---

## 4. Two pointers & Sliding window

### Two pointers — hai con trỏ

Dùng khi mảng **đã sắp xếp** hoặc khi cần so đầu với cuối.

```python
def la_palindrome(s):
    trai, phai = 0, len(s) - 1
    while trai < phai:
        if s[trai] != s[phai]:
            return False
        trai += 1
        phai -= 1
    return True
```

O(n) thời gian, **O(1) bộ nhớ** — không tạo chuỗi đảo ngược.

```python
# Tìm cặp có tổng = target trong mảng ĐÃ SẮP XẾP
def hai_so(nums, target):
    t, p = 0, len(nums) - 1
    while t < p:
        tong = nums[t] + nums[p]
        if tong == target: return [t, p]
        if tong < target:  t += 1      # cần lớn hơn -> đẩy trái
        else:              p -= 1      # cần nhỏ hơn -> kéo phải
```

### Sliding window — cửa sổ trượt

Dùng khi đề hỏi về **đoạn con liên tiếp**: dài nhất, tổng lớn nhất, chứa đủ ký tự...

```python
# Đoạn con dài nhất không có ký tự lặp
def do_dai_nhat(s):
    da_thay = {}       # ký tự -> vị trí cuối cùng
    trai = 0
    ket_qua = 0
    for phai, c in enumerate(s):
        if c in da_thay and da_thay[c] >= trai:
            trai = da_thay[c] + 1      # co cửa sổ lại
        da_thay[c] = phai
        ket_qua = max(ket_qua, phai - trai + 1)
    return ket_qua
```

Khuôn mẫu chung: **`phai` luôn tiến, `trai` chỉ tiến khi vi phạm điều kiện.** Mỗi phần tử
vào ra cửa sổ nhiều nhất một lần → O(n).

---

## 5. Stack & Queue

**Stack** — vào sau ra trước (LIFO). Python dùng luôn `list`:

```python
st = []
st.append(x)    # push
st.pop()        # pop
st[-1]          # peek
```

Bài kinh điển — **kiểm tra ngoặc hợp lệ**:

```python
def hop_le(s):
    cap = {')': '(', ']': '[', '}': '{'}
    st = []
    for c in s:
        if c in "([{":
            st.append(c)
        else:
            if not st or st.pop() != cap[c]:
                return False
    return not st          # còn thừa mở ngoặc -> sai
```

**Queue** — vào trước ra trước (FIFO). Đừng dùng `list.pop(0)` vì O(n):

```python
from collections import deque
q = deque()
q.append(x)      # vào cuối, O(1)
q.popleft()      # ra đầu, O(1)
```

---

## 6. Linked list

Ít gặp trong công việc thật nhưng **rất hay ra đề**.

```python
class Node:
    def __init__(self, val, next=None):
        self.val = val
        self.next = next
```

Kỹ thuật bắt buộc thuộc — **đảo danh sách**:

```python
def dao_nguoc(head):
    truoc = None
    hien_tai = head
    while hien_tai:
        ke_tiep = hien_tai.next    # nhớ trước khi mất
        hien_tai.next = truoc      # bẻ ngược mũi tên
        truoc = hien_tai           # dịch tới
        hien_tai = ke_tiep
    return truoc
```

Vẽ ra giấy 3 node rồi chạy tay một lần — hiểu ngay, học vẹt thì quên.

**Hai con trỏ nhanh/chậm** — tìm giữa danh sách hoặc phát hiện vòng lặp:

```python
def co_vong_lap(head):
    cham = nhanh = head
    while nhanh and nhanh.next:
        cham = cham.next            # 1 bước
        nhanh = nhanh.next.next     # 2 bước
        if cham is nhanh:           # gặp nhau -> có vòng
            return True
    return False
```

---

## 7. Cây và đệ quy

```python
class TreeNode:
    def __init__(self, val, left=None, right=None):
        self.val, self.left, self.right = val, left, right
```

**Đệ quy chỉ cần 2 phần:** trường hợp dừng, và bước thu nhỏ bài toán.

```python
def do_sau(root):
    if not root:                        # dừng
        return 0
    return 1 + max(do_sau(root.left), do_sau(root.right))   # thu nhỏ
```

Ba kiểu duyệt — khác nhau ở **chỗ đặt câu lệnh xử lý**:

```python
def truoc(n):   # preorder: gốc -> trái -> phải
    if not n: return
    print(n.val); truoc(n.left); truoc(n.right)

def giua(n):    # inorder: trái -> gốc -> phải
    if not n: return
    giua(n.left); print(n.val); giua(n.right)

def sau(n):     # postorder: trái -> phải -> gốc
    if not n: return
    sau(n.left); sau(n.right); print(n.val)
```

**Mẹo nhớ:** với **cây tìm kiếm nhị phân (BST)**, duyệt **inorder cho ra dãy tăng dần**.
Đây là câu hỏi mẹo rất hay gặp.

---

## 8. BFS / DFS trên đồ thị

Bạn đã quen khái niệm đồ thị rồi — agent LangGraph của bạn chính là một đồ thị.

**BFS (loang theo tầng)** — dùng queue, tìm **đường ngắn nhất**:

```python
from collections import deque

def bfs(do_thi, bat_dau):
    da_tham = {bat_dau}
    q = deque([bat_dau])
    while q:
        nut = q.popleft()
        for ke in do_thi[nut]:
            if ke not in da_tham:
                da_tham.add(ke)
                q.append(ke)
    return da_tham
```

**DFS (đi sâu)** — dùng stack hoặc đệ quy:

```python
def dfs(do_thi, nut, da_tham=None):
    if da_tham is None: da_tham = set()
    da_tham.add(nut)
    for ke in do_thi[nut]:
        if ke not in da_tham:
            dfs(do_thi, ke, da_tham)
    return da_tham
```

**Chọn cái nào:** đường ngắn nhất → BFS. Duyệt hết / tìm chu trình → DFS. Cả hai đều
O(V+E).

Dạng đề hay gặp: **đếm số đảo** trên lưới 2 chiều. Coi mỗi ô đất là một đỉnh, ô kề nhau là
cạnh, rồi đếm số lần khởi động BFS/DFS.

---

## 9. Sắp xếp & tìm kiếm nhị phân

```python
sorted(arr)                          # O(n log n)
sorted(ds, key=lambda x: x[1])       # theo trường
sorted(ds, key=lambda x: (-x.diem, x.ten))   # nhiều tiêu chí
```

**Binary search** — chỉ dùng được trên dữ liệu **đã sắp xếp**, O(log n):

```python
def tim_nhi_phan(arr, x):
    t, p = 0, len(arr) - 1
    while t <= p:
        giua = (t + p) // 2
        if arr[giua] == x: return giua
        if arr[giua] < x:  t = giua + 1
        else:              p = giua - 1
    return -1
```

Hai lỗi kinh điển: viết `while t < p` (bỏ sót phần tử cuối), và quên `+1`/`-1` (lặp vô
hạn). Chạy tay mảng 2 phần tử để kiểm.

Python có sẵn: `import bisect; bisect.bisect_left(arr, x)`.

---

## 10. Quy hoạch động — mức cơ bản

DP = **nhớ lại kết quả đã tính** để khỏi tính lại.

```python
# Fibonacci không nhớ: O(2^n) — n=40 đã đợi mỏi
def fib_cham(n):
    if n <= 1: return n
    return fib_cham(n-1) + fib_cham(n-2)

# Có nhớ (memoization): O(n)
def fib(n, nho={}):
    if n <= 1: return n
    if n in nho: return nho[n]
    nho[n] = fib(n-1, nho) + fib(n-2, nho)
    return nho[n]

# Bottom-up: O(n) thời gian, O(1) bộ nhớ
def fib_nhanh(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a
```

**Dấu hiệu nhận biết bài DP:** đề hỏi "có bao nhiêu cách", "lớn nhất/nhỏ nhất", và bài
toán con **lặp lại**. Ở mức fresher/junior, biết Fibonacci + Climbing Stairs + House
Robber là đủ.

---

## 11. Lộ trình 40 bài LeetCode

Làm theo thứ tự này. **Đừng nhảy cóc.** Mỗi bài: tự nghĩ 20 phút, bí thì xem lời giải,
rồi **đóng lại và viết lại từ đầu**.

**Tuần 1 — Array & Hash map (12 bài)**
Two Sum · Best Time to Buy and Sell Stock · Contains Duplicate · Valid Anagram ·
Group Anagrams · Top K Frequent Elements · Product of Array Except Self ·
Valid Palindrome · Two Sum II · 3Sum · Maximum Subarray · Merge Intervals

**Tuần 2 — Sliding window, Stack (8 bài)**
Longest Substring Without Repeating Characters · Longest Repeating Character Replacement ·
Minimum Window Substring · Valid Parentheses · Min Stack · Daily Temperatures ·
Generate Parentheses · Car Fleet

**Tuần 3 — Linked list, Tree (12 bài)**
Reverse Linked List · Merge Two Sorted Lists · Linked List Cycle · Remove Nth Node ·
Reorder List · Invert Binary Tree · Maximum Depth · Same Tree · Subtree of Another Tree ·
Lowest Common Ancestor of BST · Binary Tree Level Order Traversal · Validate BST

**Tuần 4 — Graph, Binary search, DP (8 bài)**
Number of Islands · Clone Graph · Course Schedule · Binary Search ·
Search in Rotated Sorted Array · Climbing Stairs · House Robber · Coin Change

**Cách luyện đúng:**
1. Đọc đề, nói to cách làm **trước khi** gõ code — phỏng vấn bắt bạn làm đúng vậy.
2. Nói Big-O trước khi viết.
3. Viết xong, tự nghĩ 2 test đặc biệt: mảng rỗng, một phần tử.
4. Bài nào sai quá 2 lần thì đánh dấu, tuần sau làm lại.

Cày 40 bài này qua được vòng technical của phần lớn công ty Việt Nam ở mức fresher/junior.

---

# PHẦN B — OOP

## 12. Bốn tính chất, giải thích không thuộc lòng

### Encapsulation (đóng gói)
Gói dữ liệu và hàm xử lý dữ liệu đó vào cùng một chỗ, và **giấu chi tiết bên trong**.

```python
class TaiKhoan:
    def __init__(self, so_du):
        self.__so_du = so_du          # hai gạch dưới = private

    def nap(self, tien):
        if tien <= 0:
            raise ValueError("Số tiền phải dương")
        self.__so_du += tien

    @property
    def so_du(self):                   # chỉ đọc, không sửa trực tiếp được
        return self.__so_du
```

Vì sao cần: nếu `so_du` là public, chỗ nào cũng gán bừa được `tk.so_du = -999`. Đóng gói
bắt mọi thay đổi đi qua `nap()`, nơi có kiểm tra.

### Abstraction (trừu tượng)
Chỉ lộ ra cái người dùng cần, giấu cách làm. Bạn gọi `tool.invoke(args)` mà không cần biết
bên trong nó gọi HTTP hay đọc file.

### Inheritance (kế thừa)
Class con lấy lại mọi thứ của class cha rồi thêm/sửa.

```python
class Tool:
    def invoke(self, args): raise NotImplementedError

class WeatherTool(Tool):
    def invoke(self, args): return goi_api_thoi_tiet(args["town"])
```

### Polymorphism (đa hình)
**Đây là cái quan trọng nhất và hay bị hỏi nhất.** Nhiều class khác nhau, cùng một cách
gọi.

```python
for tool in TOOLS:          # mỗi tool là class khác nhau
    tool.invoke(args)       # gọi giống hệt nhau
```

Code gọi **không cần biết** đang cầm tool nào. Thêm tool thứ ba không phải sửa vòng lặp.

> **Cách trả lời gây ấn tượng:** đừng đọc định nghĩa. Nói *"Trong agent của em, node chạy
> tool lặp qua danh sách tool và gọi `invoke` giống nhau cho mọi tool — đó là đa hình. Nhờ
> vậy thêm tool mới không phải sửa node."*

---

## 13. OOP trong code bạn đã viết

Bạn đã viết OOP tốt rồi mà có thể chưa gọi tên được. Đây là ví dụ thật:

```python
class ToolsExecutionNode:
    def __init__(self, tools: Sequence):
        self._tools_by_name = {t.name: t for t in tools}

    def __call__(self, state: dict):
        ...
        tool = self._tools_by_name[tool_call["name"]]
        result = tool.invoke(tool_args)
```

Đọc ra được bốn điều:

**1. Vì sao là class mà không phải hàm?** Vì nó cần **nhớ** `_tools_by_name`. Hàm thuần
không giữ được trạng thái giữa các lần gọi; muốn giữ thì phải dùng biến toàn cục (bẩn)
hoặc closure. Class là cách sạch.

**2. `__init__` làm gì?** Xây sẵn `dict` tra cứu **một lần** lúc khởi tạo. Nếu tra bằng
cách duyệt list mỗi lần gọi thì là O(n) mỗi tool; dựng dict trước thì O(1). Đây là **đánh
đổi bộ nhớ lấy tốc độ** — nối thẳng sang Phần A mục 3.

**3. `__call__` là gì?** Magic method cho phép gọi object như hàm:
`tools_execution_node(state)`. Nhờ vậy LangGraph — vốn chỉ cần "thứ gì gọi được" — nhận nó
như một node bình thường, không cần biết đó là class.

**4. `_tools_by_name` một gạch dưới** = quy ước "nội bộ, đừng đụng từ ngoài". Python không
chặn, nhưng người đọc hiểu ý.

> **Đây là câu trả lời vàng khi bị hỏi "em dùng OOP ở đâu":** không kể lý thuyết, mở đúng
> class này ra và giải thích bốn ý trên. Người phỏng vấn sẽ biết ngay bạn viết thật.

---

## 14. SOLID — chỉ 3 cái hay bị hỏi

**S — Single Responsibility.** Mỗi class làm một việc. Trong repo bạn:
`retrieval.py` lo tìm kiếm, `metrics.py` lo đo đạc, `persistence.py` lo lưu trữ. Sửa cách
đo không đụng tới tìm kiếm.

**O — Open/Closed.** Mở để mở rộng, đóng để sửa đổi. Thêm tool thứ ba vào `TOOLS` là agent
dùng được ngay — **không sửa** `ToolsExecutionNode`.

**D — Dependency Inversion.** Phụ thuộc vào trừu tượng, không vào cái cụ thể.

```python
def build_agent(checkpointer=None):
    return builder.compile(checkpointer=checkpointer)
```

`build_agent` không biết checkpointer là PostgreSQL, memory hay gì khác — nó nhận từ bên
ngoài. Nhờ vậy test chạy không cần database. **Đây gọi là dependency injection**, và bạn
đã làm rồi.

Hai cái còn lại (L — Liskov, I — Interface Segregation) ít hỏi ở mức fresher/junior.

---

## 15. Design pattern bạn đã dùng

**Adapter** — trong middleware e-Contract ở BestHR. Mỗi nhà cung cấp chữ ký số (FPT, VNPT)
có API khác nhau; bạn viết một lớp adapter cho mỗi bên, đưa về cùng một interface. Thêm
nhà cung cấp mới → viết adapter mới, không sửa lõi.

**Strategy** — `TOOLS` là một tập chiến lược; model chọn chiến lược nào lúc chạy.

**Factory** — `build_agent()` là hàm factory: nhận cấu hình, trả về object đã lắp ráp.

> Đừng học thuộc 23 pattern. Ba cái này bạn **đã dùng thật**, kể được thì hơn hẳn người
> đọc thuộc mà chưa viết bao giờ.

---

## 16. Tự kiểm tra

**DSA**
1. `x in list` và `x in set` khác nhau Big-O thế nào? Vì sao?
2. Viết Two Sum O(n) không nhìn tài liệu. Nói rõ time và space.
3. Vì sao nối chuỗi bằng `+=` trong vòng lặp là O(n²)?
4. Khi nào dùng BFS, khi nào DFS?
5. Duyệt inorder một BST cho ra thứ tự gì?
6. Viết đảo linked list. Vẽ 3 node ra giấy và chạy tay.
7. Sliding window: khi nào `trai` được phép tiến?
8. Hai lỗi kinh điển của binary search là gì?

**OOP**
9. Đa hình là gì? Lấy ví dụ từ chính code agent của bạn.
10. `ToolsExecutionNode` vì sao là class chứ không phải hàm?
11. `__call__` dùng để làm gì? Không có nó thì LangGraph có nhận node được không?
12. `build_agent(checkpointer=None)` minh hoạ nguyên tắc SOLID nào?
13. Kể một design pattern bạn đã dùng thật và giải thích vì sao dùng nó.

---

## 17. Tài liệu

- LeetCode theo chủ đề: https://neetcode.io/roadmap
- Big-O cheat sheet: https://www.bigocheatsheet.com/
- Python `collections`: https://docs.python.org/3/library/collections.html
- Code của bạn để đọc lại phần OOP: [`main_02_02.py`](../../main_02_02.py)
- Bài liên quan: [`HOC_LANGGRAPH.md`](HOC_LANGGRAPH.md) · [`HOC_SQL.md`](HOC_SQL.md)
