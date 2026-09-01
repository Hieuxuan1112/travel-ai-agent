# Học CI/CD và deploy cloud qua chính project này

Bốn file: [`ci.yml`](../../.github/workflows/ci.yml), [`eval.yml`](../../.github/workflows/eval.yml),
[`cd.yml`](../../.github/workflows/cd.yml), [`Dockerfile`](../../Dockerfile).

Bài này viết sau khi deploy thật lên Azure — **đỏ 5 lần rồi mới xanh**. Mục 8 kể lại từng
lần, vì đó mới là phần đáng học: nhìn lỗi mà lần ra nguyên nhân.

---

## 1. CI và CD khác nhau chỗ nào

Hai chữ hay bị nói chung một hơi nhưng giải quyết hai nỗi lo khác nhau.

| | Trả lời câu hỏi | Chạy khi nào | File |
|---|---|---|---|
| **CI** (Continuous Integration) | *"Code này có hỏng gì không?"* | mỗi lần push | `ci.yml`, `eval.yml` |
| **CD** (Continuous Delivery) | *"Đưa nó tới tay người dùng"* | sau khi CI xanh | `cd.yml` |

CI là **cái lưới**: test, lint, type check. CD là **băng chuyền**: đóng gói, quét bảo mật,
đẩy lên registry, deploy.

Trong repo này CD **không chạy song song** với CI mà **móc vào sau**:

```yaml
on:
  workflow_run:
    workflows: ["CI"]
    types: [completed]
```

Vì sao quan trọng: nếu chạy song song, có lúc image hỏng vẫn được đẩy lên registry trong
khi test đang đỏ. Móc nối tiếp thì không image nào ra đời từ code chưa qua test.

---

## 2. Chuỗi giao hàng: code → image → quét → registry → cloud

```
git push
   │
   ├── CI ────────► test + lint              (~1 phút)
   ├── Eval gate ─► gọi LLM thật, chấm điểm  (~4 phút)
   │
   └── CI xanh ──► CD
                    ├── build image Docker
                    ├── Trivy quét          ← quét TRƯỚC khi đẩy
                    ├── đẩy lên ghcr.io
                    └── deploy Azure
                         └── curl /healthz  ← bắt buộc trả 200
```

Mỗi mũi tên là một chỗ có thể chặn. Đó là ý nghĩa của "pipeline": không phải để tự động cho
nhanh, mà để **không thứ gì hỏng lọt qua được**.

---

## 3. Trivy — quét lỗ hổng, và vì sao thứ tự quan trọng

Trivy đọc image, liệt kê thư viện bên trong, đối chiếu cơ sở dữ liệu lỗ hổng (CVE).

**Quét TRƯỚC khi đẩy, không phải sau.** Nghe hiển nhiên nhưng rất nhiều pipeline làm ngược:
đẩy lên rồi mới quét. Lúc đó image xấu đã nằm trên registry, ai đó có thể đã kéo về.

Cấu hình trong `cd.yml`:

```yaml
severity: CRITICAL
ignore-unfixed: true
exit-code: 1
```

`ignore-unfixed: true` là lựa chọn có chủ ý, và là câu hỏi phỏng vấn hay gặp.

| Nếu chặn mọi CRITICAL | Nếu chỉ chặn CRITICAL **có bản vá** |
|---|---|
| Đỏ vì lỗ hổng trong `libc` mà **chưa ai vá được** | Chỉ đỏ khi thật sự có việc để làm |
| Vài hôm là người ta quen mắt, bỏ qua màu đỏ | Đỏ nghĩa là "có bản vá, đi cập nhật đi" |
| **Cổng mất tác dụng vì bị nhờn** | Cổng giữ được uy tín |

Bài học tổng quát: **một cái cổng mà người ta học được cách phớt lờ thì tệ hơn không có cổng.**

---

## 4. Registry và tag: vì sao KHÔNG dùng `latest`

Image đẩy lên `ghcr.io` (GitHub Container Registry) với **hai** tag:

```
ghcr.io/hieuxuan1112/travel-ai-agent:latest
ghcr.io/hieuxuan1112/travel-ai-agent:70dc9eeda6a4740a5265528a399c776dca70499f
```

Cái thứ hai là **SHA của commit**. Deploy luôn dùng tag SHA, không dùng `latest`.

Lý do: `latest` là **con trỏ di động**. Hôm nay nó trỏ image A, mai trỏ image B. Khi
production hỏng và bạn hỏi "đang chạy code nào?", `latest` không trả lời được. Tag SHA truy
ngược thẳng về đúng một commit.

> **Quy tắc:** `latest` để cho người gõ tay thử nhanh. Máy móc thì luôn dùng tag bất biến.

---

## 5. OIDC keyless — phần đáng nói nhất khi phỏng vấn

### Cách cũ và vì sao nó tệ

Muốn GitHub Actions nói chuyện được với Azure, cách truyền thống là tạo một **service
principal** rồi nhét mật khẩu của nó vào GitHub Secrets.

Vấn đề: đó là **mật khẩu sống nhiều tháng**. Lộ repo là lộ luôn tài khoản cloud. Mà secret
thì bị copy qua lại, nằm trong log, nằm trong file `.env` của ai đó.

### Cách đang dùng: federated credential

```
GitHub Actions                          Azure
     │                                    │
     │  1. phát OIDC token (sống 1 tiếng) │
     │     "tôi là workflow chạy trên     │
     │      nhánh main của repo X"        │
     ├───────────────────────────────────►│
     │                                    │ 2. đối chiếu federated credential
     │                                    │    đã đăng ký: đúng repo? đúng nhánh?
     │  3. cấp credential ngắn hạn        │
     │◄───────────────────────────────────┤
```

**Không có mật khẩu nào được lưu ở đâu cả.** Ba thứ trong GitHub Secrets
(`AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`) chỉ là **định danh** — biết
chúng cũng không đăng nhập được, y như biết số căn cước của ai đó không có nghĩa là giả mạo
được người ta.

Điều kiện bắt buộc trong workflow:

```yaml
permissions:
  id-token: write    # thiếu dòng này GitHub không phát token
```

### Phạm vi quyền

Vai trò `Contributor` nhưng gán ở mức **resource group**, không phải subscription. Danh tính
deploy toàn quyền trong cái hộp `rg-travel-agent` và không đụng được gì bên ngoài.

Mặt trái đã gặp thật: vì chỉ có quyền ở resource group nên workflow **không tự đăng ký được
resource provider** — việc đó ở cấp subscription. Đó là cái giá của quyền tối thiểu: an toàn
hơn nhưng có lúc phải làm tay một bước.

---

## 6. Azure Container Apps — vì sao không phải AKS

| | Container Apps | AKS (Kubernetes) |
|---|---|---|
| Phải quản node không | Không | Có |
| Scale về 0 | Có | Không |
| Free tier | Có | Không |
| Hợp với | dịch vụ nhỏ, ít lưu lượng | hệ thống lớn, nhiều dịch vụ |

Một agent hai tool **không cần Kubernetes**. Chọn AKS cho project này là dùng dao mổ trâu
giết gà — và tốn tiền thật.

### `min-replicas = 0`: mấu chốt của $0/tháng

Không ai gọi thì **không có replica nào chạy** → không tính tiền. Có request thì Azure bật
container lên.

**Đánh đổi:** request đầu tiên sau khi ngủ mất ~15-20 giây (cold start). Với demo trên CV thì
chấp nhận được. Với sản phẩm thật có người dùng thì không — khi đó đặt `min-replicas 1` và
trả tiền cho một replica luôn chạy.

Nói được đánh đổi này là dấu hiệu hiểu thật, không phải chép lệnh.

---

## 7. Idempotent — chạy lại nhiều lần vẫn đúng

Workflow phải chạy được **nhiều lần** mà không hỏng. Trong `cd.yml`:

```bash
# environment: có rồi thì thôi, chưa có thì tạo
az containerapp env show ... || az containerapp env create ...

# app: lần đầu create, những lần sau chỉ đổi image
if az containerapp show ...; then
  az containerapp update --image "$IMAGE:$TAG"
else
  az containerapp create ...
fi
```

Từ khoá: **idempotent** — chạy một lần hay mười lần đều ra cùng một trạng thái. Đây là nguyên
tắc nền của mọi công cụ hạ tầng (Terraform, Ansible, Kubernetes đều dựa vào nó).

---

## 8. Năm lần đỏ — phần đáng học nhất

Deploy lần đầu gần như không bao giờ xanh ngay. Đây là 5 lần đỏ thật và cách lần ra nguyên nhân.

### Lần 1 — `AADSTS700213: No matching federated identity record`

Form Azure có hai ô tuỳ chọn `Organization ID` và `Repository ID`. Bỏ trống thì portal **giữ
nguyên chữ giữ chỗ** trong chuỗi subject:

```
repo:Hieuxuan1112@{Organization ID}/travel-ai-agent@{Repository ID}:ref:refs/heads/main
                  ^^^^^^^^^^^^^^^^^ chữ giữ chỗ, không phải số thật
```

GitHub gửi lên số thật, Azure lưu chữ giữ chỗ → không khớp. **Cách sửa:** điền hai số lấy
ngay trong chính thông báo lỗi.

> **Bài học:** thông báo lỗi in ra chuỗi mà bên kia **thật sự gửi**. So nó với chuỗi mình
> **đã cấu hình** là ra ngay.

### Lần 2 và 3 — `RequestDisallowedByAzure`, target `workspace-...`

`az containerapp env create` **tự tạo kèm một Log Analytics workspace**. Chính cái workspace
đó bị chặn, ở cả `southeastasia` lẫn `eastus`.

Sai lầm đã mắc: thấy chữ "region" trong thông báo là đi đổi region, **bỏ qua chữ
`Target: workspace-...`**. Mất hai lần chạy (~20 phút) vì không đọc kỹ.

**Cách sửa đúng:** `--logs-destination none` — bỏ hẳn workspace thì không còn gì để chặn.

> **Bài học:** trường `Target:` nói đích danh cái gì bị từ chối. Đọc nó trước khi dựng giả thuyết.

### Lần 4 — `RequestDisallowedByAzure`, target `travel-agent-env`

Giờ mới thật sự là region. Nhưng danh sách region được phép cho subscription sinh viên
**không tra được ở đâu cả**: không phải Azure Policy, không hiện trong portal, dropdown thì
liệt kê đủ mọi region.

Đoán từng region mỗi lần một push = **10 phút một lần đoán**. Thay bằng vòng lặp thử ngay
trong **một** lần chạy:

```bash
for LOC in southeastasia eastus eastus2 westus2 ... ; do
  if az containerapp env create -l "$LOC" ...; then
    echo "LOCATION=$LOC" >> "$GITHUB_ENV"; exit 0
  fi
done
```

Mỗi lần bị từ chối chỉ mất ~8 giây. **Kết quả: 8 region bị từ chối, `japaneast` được chấp nhận.**

> **Bài học:** khi không tra được thì đừng đoán — cho máy thử hộ. So chi phí: 8 giây một lần
> thử, đổi lấy 10 phút một lần đoán.

### Lần 5 — `InternalServerError`

Một lệnh `az containerapp create` ôm cả image, ingress, scaling, resource **và hai secret**
trả về đúng một dòng lỗi không nói gì.

**Cách sửa:** tách thành ba lệnh nhỏ — tạo app, gắn secret, trỏ biến môi trường. Và truyền
secret qua **biến môi trường** thay vì nối thẳng vào dòng lệnh, vì chuỗi Neon có `?`, `&`, `=`
rất dễ vỡ cú pháp shell.

> **Bài học:** lệnh to thì lỗi mờ. Lệnh nhỏ thì lỗi tự khai ra nó ở đâu.

---

## 9. Tự kiểm tra

Trả lời trước rồi mới mở đáp án.

**1.** Vì sao CD móc vào sau CI (`workflow_run`) thay vì chạy song song?

<details><summary>Đáp án</summary>

Chạy song song thì có lúc image được đẩy lên registry trong khi test đang đỏ. Móc nối tiếp
đảm bảo không image nào ra đời từ code chưa qua test.
</details>

**2.** `ignore-unfixed: true` trong Trivy nghĩa là gì, và vì sao lại bật nó?

<details><summary>Đáp án</summary>

Bỏ qua lỗ hổng **chưa có bản vá**. Bật vì nếu chặn cả những thứ không sửa được thì pipeline đỏ
triền miên, người ta quen mắt và bỏ qua — cổng mất tác dụng. Chỉ chặn khi thật sự có việc để
làm thì màu đỏ mới còn nghĩa.
</details>

**3.** Vì sao deploy dùng tag SHA chứ không dùng `latest`?

<details><summary>Đáp án</summary>

`latest` là con trỏ di động, hôm nay trỏ image này mai trỏ image khác. Khi production hỏng mà
hỏi "đang chạy code nào" thì `latest` không trả lời được. Tag SHA truy ngược thẳng về đúng
một commit.
</details>

**4.** Ba secret `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID` có phải bí mật không?

<details><summary>Đáp án</summary>

Không. Chúng là **định danh**, biết chúng cũng không đăng nhập được. Thứ cho phép đăng nhập là
OIDC token do GitHub phát, sống 1 tiếng, và Azure chỉ chấp nhận nếu nó đến từ đúng repo và
đúng nhánh đã đăng ký trong federated credential.
</details>

**5.** `min-replicas = 0` được gì và mất gì?

<details><summary>Đáp án</summary>

Được: không ai dùng thì không tốn tiền ($0/tháng, nằm trong free grant).
Mất: request đầu tiên sau khi ngủ mất ~15-20 giây cold start. Hợp với demo, không hợp với sản
phẩm có người dùng thật.
</details>

**6.** Gặp `RequestDisallowedByAzure`, việc đầu tiên nên làm là gì?

<details><summary>Đáp án</summary>

Đọc trường **`Target:`** để biết đích danh tài nguyên nào bị từ chối. Hai lần đỏ đầu tiên
target là `workspace-...` (Log Analytics) chứ không phải environment — nhưng vì không đọc kỹ
nên đi đổi region, mất hai lần chạy.
</details>

**7.** Vì sao truyền secret qua biến môi trường thay vì nối thẳng vào dòng lệnh `az`?

<details><summary>Đáp án</summary>

Chuỗi kết nối chứa `?`, `&`, `=` và có thể chứa `$`. Nối thẳng vào dòng lệnh thì shell diễn
giải chúng và giá trị bị vỡ. Ngoài ra giá trị nối vào dòng lệnh sẽ hiện trong danh sách tiến
trình của máy.
</details>

---

## 10. Trả lời phỏng vấn

**"Em deploy dự án lên đâu, bằng cách nào?"**

> Azure Container Apps, deploy thẳng từ GitHub Actions. Pipeline chia hai tầng: CI chạy test
> và eval gate, CD móc vào sau khi CI xanh — build image Docker non-root nhiều tầng, quét
> Trivy **trước** khi đẩy, đẩy lên GHCR, rồi deploy lên Azure. Bước cuối tự gọi `/healthz`,
> không trả 200 thì pipeline đỏ.

**"Em lưu credential Azure ở đâu?"**

> Không lưu. Em dùng federated credential — GitHub phát OIDC token sống một tiếng, Azure kiểm
> token có đúng đến từ nhánh main của repo đó không rồi mới đổi lấy credential ngắn hạn. Ba
> giá trị `AZURE_*` trong repo chỉ là định danh, không phải mật khẩu. Quyền thì gán Contributor
> ở mức resource group chứ không phải subscription.

**"Chi phí bao nhiêu?"**

> Không đồng nào. `min-replicas = 0` nên không ai dùng thì không có replica nào chạy, nằm
> trong free grant. Đánh đổi là cold start 15-20 giây cho request đầu tiên — chấp nhận được
> với demo, còn sản phẩm thật thì phải để `min-replicas 1` và trả tiền.

**"Có gặp khó khăn gì không?"** ← câu này hay được hỏi, và là cơ hội

> Đỏ 5 lần mới xanh. Đáng nhớ nhất là hai lần em mất oan: lỗi báo `RequestDisallowedByAzure`
> nên em đi đổi region, nhưng đọc kỹ thì trường `Target` chỉ đích danh Log Analytics workspace
> — thứ mà lệnh `env create` tự tạo kèm chứ em không hề khai. Bỏ nó đi bằng
> `--logs-destination none` là qua. Sau đó mới thật sự vướng region, mà danh sách region được
> phép thì Azure không công bố ở đâu, nên em cho workflow thử lần lượt 12 region trong cùng
> một lần chạy thay vì đoán mỗi lần một push — mỗi lần bị từ chối chỉ mất 8 giây thay vì 10 phút.

Câu cuối là câu **đáng giá nhất**: nó cho thấy đọc lỗi có phương pháp và biết cân nhắc chi phí
thời gian, chứ không phải may mắn.

---

## 11. Liên quan

- Hạ tầng sản phẩm: [`../DEPLOY.md`](../DEPLOY.md) — mục 9 (CD) và mục 10 (Azure)
- Đóng gói image: [`HOC_DOCKER.md`](HOC_DOCKER.md)
- Đo lường sau khi deploy: [`HOC_PROMETHEUS.md`](HOC_PROMETHEUS.md)
