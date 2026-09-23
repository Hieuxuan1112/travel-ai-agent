# Mô phỏng phỏng vấn — người phỏng vấn đào tới đáy

> Mọi tài liệu khác có mục *"trả lời phỏng vấn"* với câu hỏi và câu trả lời. Thực tế **không
> diễn ra như vậy**. Người phỏng vấn giỏi không dừng ở câu trả lời đầu tiên — họ hỏi tiếp,
> hỏi tiếp nữa, cho tới khi chạm đáy hiểu biết của bạn.
>
> Bài này mô phỏng đúng chuyện đó. Đọc **câu hỏi trước, tự trả lời trong đầu, rồi mới xem**.
> Chỗ nào bạn đuối trước khi hết đoạn hội thoại — đó là chỗ cần học lại.
>
> **Ký hiệu:** 🎤 người phỏng vấn · 🙂 câu trả lời tốt · ⚠️ câu trả lời yếu (và vì sao yếu)

**Mục lục**

1. [Cách người phỏng vấn đào sâu](#1-cách-người-phỏng-vấn-đào-sâu)
2. [Buổi 1 — "Kể tôi nghe về dự án của em"](#2-buổi-1--kể-tôi-nghe-về-dự-án-của-em)
3. [Buổi 2 — RAG và truy hồi](#3-buổi-2--rag-và-truy-hồi)
4. [Buổi 3 — Đo lường và chất lượng](#4-buổi-3--đo-lường-và-chất-lượng)
5. [Buổi 4 — Xác thực (SlangWord)](#5-buổi-4--xác-thực-slangword)
6. [Buổi 5 — Hỏng hóc và quy mô](#6-buổi-5--hỏng-hóc-và-quy-mô)
7. [Buổi 6 — Khi bạn KHÔNG biết](#7-buổi-6--khi-bạn-không-biết)
8. [Năm mức câu hỏi để tự luyện](#8-năm-mức-câu-hỏi-để-tự-luyện)

---

## 1. Cách người phỏng vấn đào sâu

Họ gần như luôn đi theo cùng một chuỗi. Biết chuỗi này là biết trước sẽ bị hỏi gì:

```
"Em dùng X"
   → "Vì sao X?"                        (có lý do hay chỉ làm theo tutorial?)
   → "Em có cân nhắc gì khác không?"    (có biết bối cảnh không?)
   → "Vì sao loại chúng?"               (có so sánh thật không?)
   → "Đánh đổi là gì?"                  (có biết cái giá không?)
   → "Làm sao biết nó có tác dụng?"     (có đo không hay chỉ tin?)
   → "Số cụ thể là bao nhiêu?"          (đo thật hay nói cho có?)
   → "Nếu X hỏng thì sao?"              (có nghĩ tới vận hành không?)
   → "Khi nào em sẽ đổi sang cách khác?" (có biết giới hạn không?)
```

**Câu hỏi lọc mạnh nhất là *"làm sao biết nó có tác dụng?"*** — vì nó phân biệt người **đã
đo** với người **đang tin**. Và câu tiếp theo *"số cụ thể là bao nhiêu?"* thì không bịa được.

---

## 2. Buổi 1 — "Kể tôi nghe về dự án của em"

🎤 **Kể tôi nghe về dự án AI của em.**

🙂 Em làm một agent du lịch trả lời câu hỏi về Cornwall. Nó có hai công cụ: tìm kiếm ngữ nghĩa
trên dữ liệu Wikivoyage, và tra thời tiết thật qua Open-Meteo. Điểm chính là **model tự quyết
gọi công cụ nào, theo thứ tự nào** — không có dòng code nào ra lệnh "tìm trước, tra thời tiết
sau".

🎤 **Vì sao phải là agent? Sao không viết luôn hai bước đó cho chắc?**

🙂 Vì **số bước không biết trước lúc viết code**. Hỏi *"gợi ý hai thị trấn biển có thời tiết
đẹp"* thì agent chưa biết phải tra thời tiết của thị trấn nào — nó phải tìm trước, đọc kết
quả, rồi mới biết cần gọi bao nhiêu lần và cho những tên nào. Workflow cứng không làm được.

⚠️ *"Vì agent thông minh hơn ạ"* — không phải lý do kỹ thuật. Người phỏng vấn sẽ hỏi ngay
*"thông minh hơn ở chỗ nào?"* và bạn hết đường.

🎤 **Vậy có bài toán nào em thấy KHÔNG nên dùng agent không?**

🙂 Có, và phần lớn là vậy. Nếu các bước luôn giống nhau — tóm tắt tài liệu, phân loại email —
thì chain là đúng: rẻ hơn, đoán trước được, test như code thường. Em nghĩ nguyên tắc là **chọn
mức tự do thấp nhất mà vẫn giải được bài toán**, vì mỗi bậc tự do là thêm một chỗ cư xử bất ngờ
và thêm tiền mỗi câu hỏi.

🎤 **Model tự quyết thì em kiểm soát nó kiểu gì?**

🙂 Ba thứ. Một là **ngân sách gọi tool**, mặc định 8 — model tự quyết khi nào dừng nên nó có
thể không dừng. Hai là **cắt cửa sổ lịch sử** để chi phí không phình theo hội thoại. Ba là
**đo**: em ghi lại mỗi lần gọi tool và token từng vòng.

🎤 **Chạm trần 8 tool call thì sao? Em ném lỗi à?**

🙂 Không — nó **trả lời bằng những gì đã lấy được**. Lúc đó agent đã có một phần thông tin, nên
câu trả lời chưa đầy đủ vẫn hữu ích hơn màn hình lỗi. Ngân sách để chặn đốt tiền và treo
request, không phải để phạt người dùng.

🎤 **Vì sao là 8 mà không phải 5 hay 20?**

🙂 Thành thật thì con số đó em chọn theo cảm giác: đủ cho câu khó nhất trong bộ eval, vốn gọi 5
tool. **Em chưa đo đường cong đánh đổi.** Cách kiểm là chạy lại eval với `MAX_TOOL_CALLS=4`,
`6`, `8` rồi xem chất lượng và chi phí đổi thế nào — bài đó em có ghi trong tài liệu thí nghiệm
nhưng chưa chạy.

> **Vì sao đoạn này là câu trả lời mạnh, không phải điểm yếu:** thừa nhận đúng chỗ chưa đo,
> nhưng **kèm ngay cách đo**. Người phỏng vấn thấy một người biết ranh giới hiểu biết của mình.
> Bịa ra *"em đã thử nghiệm và 8 là tối ưu"* thì câu hỏi tiếp theo — *"kết quả với 6 là bao
> nhiêu?"* — sẽ lật tẩy.

---

## 3. Buổi 2 — RAG và truy hồi

🎤 **Em làm RAG. Vì sao không fine-tune model cho nó nhớ luôn?**

🙂 Ba lý do. Fine-tune tốn tiền và thời gian, dữ liệu đổi là phải train lại. Quan trọng hơn: nó
**không trích dẫn được nguồn** — em không chỉ ra được câu trả lời dựa trên đoạn nào. Và model
vẫn có thể bịa. RAG thì kiến thức nằm **ngoài** model, trong kho em kiểm soát được.

🎤 **Cửa sổ ngữ cảnh giờ hàng trăm nghìn token. Sao không nhét cả 4 trang vào prompt?**

🙂 Ba lý do. **Tiền** — trả token cho *mỗi* câu hỏi. **"Lost in the middle"** — model chú ý tốt
phần đầu và cuối prompt, phần giữa kém hẳn, nên nhồi nhiều không đồng nghĩa dùng được nhiều.
Và **độ trễ** tăng theo độ dài prompt.

🎤 **Em cắt chunk 1024 ký tự. Vì sao con số đó?**

🙂 Là đánh đổi hai đầu. Cắt quá nhỏ thì mỗi mảnh mất ngữ cảnh, "nó" trỏ vào cái gì không rõ.
Cắt quá to thì một mảnh chứa nhiều chủ đề, vector bị trung bình hoá nên không gần với truy vấn
nào. 1024 ký tự khoảng một đoạn văn dài — đủ trọn một ý mà chưa lẫn sang ý khác.

🎤 **Em có thử 512 hay 2048 để so chưa?**

🙂 **Chưa.** Em có bộ đo recall@k sẵn ở `eval_retrieval.py` nên chạy được ngay — đổi
`chunk_size`, dựng lại kho, chạy lại 12 câu hỏi. Em chọn 1024 theo lý lẽ chứ chưa theo số đo.

🎤 **Rồi. Em có làm hybrid search không?**

🙂 Có làm, đo xong rồi **tắt mặc định**. Giả thuyết ban đầu là vector yếu ở tên riêng nên trộn
BM25 sẽ tốt hơn. Đo ra ngược lại: vector đơn thuần recall@1 **92%**, hybrid chỉ **83%** — hybrid
làm *tệ đi*.

🎤 **Vì sao lại tệ đi?**

🙂 Vì vector **đã chạm trần** trên kho này. Tách theo loại câu hỏi thì vector đạt 100% ở cả câu
diễn đạt vòng lẫn tên riêng. Không còn chỗ để cải thiện, nên trộn thêm BM25 chỉ đẩy vài kết quả
tốt tụt hạng.

🎤 **Sao không xoá code hybrid đi?**

🙂 Hai lý do. Kho lớn lên thì bật lại và đo lại được — hybrid thắng khi có nhiều tài liệu gần
giống nhau và có mã số hiếm mà embedding không nắm được. Và giữ lại thì em nói được *"đã thử và
đã đo"* thay vì *"nghe nói hybrid tốt hơn"*.

🎤 **Bộ đo của em có đáng tin không?**

🙂 Ở mức so sánh thì có, ở mức tuyệt đối thì không. Nhãn là **nhãn yếu** — chunk chứa từ khoá
mốc thì coi là liên quan, không phải người đánh giá. Với 12 câu hỏi thì con số đủ để **so ba
cách với nhau**, không đủ để nói "hệ thống của em đạt 92%".

> **Vì sao câu cuối gây ấn tượng:** tự nêu giới hạn phép đo của mình **trước khi** bị hỏi. Rất
> ít ứng viên fresher làm được, và nó cho thấy bạn hiểu công cụ đo chứ không chỉ đọc kết quả.

---

## 4. Buổi 3 — Đo lường và chất lượng

🎤 **Làm sao em biết agent trả lời tốt?**

🙂 Em có bộ eval 32 câu (ban đầu 8, sau mở rộng cho đa dạng hơn), đo hai chỉ số.
**Tool-selection accuracy** — đọc lịch sử tin nhắn thật xem gọi đúng tool chưa, hoàn toàn
khách quan. Và **answer quality** — một LLM khác chấm 1-5 theo tiêu chí có sẵn. Hiện là 100%
và 4,6/5.

🎤 **Nhờ AI chấm AI thì tin được à?**

🙂 Em nghĩ được, với ba lý do. **Chấm dễ hơn làm** — đọc rồi nói câu trả lời có số liệu cụ thể
hay không dễ hơn tự viết ra nó. **Em không dùng nó để nói "4,6/5 là chất lượng khách quan"**,
em dùng để so bản hôm nay với bản hôm qua — chỉ cần thước không co giãn. Và em **đã đo xem nó
có co giãn không**.

🎤 **Đo bằng cách nào?**

🙂 Đưa judge chấm **cùng một câu trả lời cố định 5 lần**. Bản mỏng ra `2, 2, 2, 2, 2`, bản đầy
đủ ra `5, 5, 5, 5, 5`. Judge **hoàn toàn tất định** — nên khi điểm dao động, em biết nhiễu nằm
ở agent chứ không ở người chấm.

🎤 **Vì sao em nghĩ ra phải làm thí nghiệm đó?**

🙂 Vì hai câu nhiều bước chỉ được 2/5 trong khi câu một bước được 4-5/5, và em cần biết nên đi
sửa chỗ nào. Giả thuyết đầu của em là *"agent không chốt được một thị trấn cụ thể"* — và thí
nghiệm **bác bỏ nó**: bản được 5/5 cũng liệt kê bốn thị trấn, không chốt cái nào.

🎤 **Vậy nguyên nhân thật là gì?**

🙂 Rubric của judge đòi *"real weather numbers"*. Câu một bước chỉ có một kết quả tool nên trích
số vào tự nhiên. Câu nhiều bước gom 3-5 kết quả rồi tóm tắt định tính — **vứt hết số đi** — nên
mất điểm đúng ở tiêu chí đó.

🎤 **Em sửa thế nào?**

🙂 Bốn dòng trong system prompt, yêu cầu trích số thật của từng thị trấn thay vì tóm tắt định
tính. Điểm từ **3,5 lên 4,6**, hai ca 2/5 đều thành 5/5, tool-selection giữ nguyên 100%.

🎤 **Có mất gì không?**

🙂 Có — lúc đó chi phí tăng **11%**, từ $1,25 lên $1,39 cho 1000 câu, vì câu trả lời dài hơn.
Đó là đánh đổi có chủ ý, không phải bữa trưa miễn phí. (Chi phí hiện tại là **$0,94** — giảm
sau đó nhờ sửa một bug hiệu năng thật ở tool xếp hạng thị trấn, không liên quan tới đổi đánh
đổi này.)

🎤 **Sao em không đổi sang kiến trúc plan-and-execute cho câu nhiều bước?**

🙂 Vì em đo trước rồi mới biết vấn đề nằm ở **prompt**, không phải kiến trúc. Đổi kiến trúc tốn
công gấp nhiều lần mà chưa chắc trúng nguyên nhân. Em nghĩ bài học là **đo trước, đổi sau** —
đổi kiến trúc trước khi đo là cách đắt nhất để không sửa được gì.

⚠️ *"Vì plan-and-execute phức tạp quá ạ"* — nghe như né việc. Câu trả lời tốt là **em biết nó
không phải nguyên nhân**, chứ không phải em ngại.

---

## 5. Buổi 4 — Xác thực (SlangWord)

🎤 **Em dùng JWT. Vì sao không dùng session?**

🙂 Vì server không phải lưu gì nên scale ngang dễ — server nào cũng kiểm được chữ ký mà không
cần kho session chung.

🎤 **Cái giá là gì?**

🙂 **Không thu hồi ngay được.** Server không lưu gì nên không biết token nào "đã bị cấm". Đuổi
một người ra thì token của họ vẫn dùng được tới lúc hết hạn.

🎤 **Vậy em xử lý thế nào?**

🙂 Access token sống rất ngắn, ghép với refresh token sống lâu **có thể thu hồi** vì nó nằm
trong database.

🎤 **Refresh token bị đánh cắp thì sao?**

🙂 Có **xoay vòng cộng phát hiện tái sử dụng**. Mỗi refresh token dùng được **đúng một lần** —
dùng xong bị đánh dấu và server phát cái mới. Nếu một token đã dùng lại xuất hiện lần nữa thì
chắc chắn **hai bên đang cầm cùng một token**, một trong hai là kẻ trộm.

🎤 **Em biết bên nào là kẻ trộm không?**

🙂 Không, và đó là lý do em **huỷ cả họ token** — mọi token sinh ra từ cùng lần đăng nhập đó
mang chung `familyId`. Người thật phải đăng nhập lại. Bất tiện nhưng đúng: đã có dấu hiệu token
bị lộ thì kết thúc phiên là phản ứng an toàn.

🎤 **Người dùng mở một trang bắn 5 request cùng lúc thì sao?**

🙂 *(Đây là câu bẫy hay nhất)* — nếu không xử lý thì **cả 5 nhận 401, cả 5 gửi cùng một refresh
token**. Cái đầu thành công và đánh dấu token đã dùng, 4 cái sau bị coi là tái sử dụng → huỷ cả
họ → **người dùng bị đăng xuất chỉ vì mở một trang nặng**.

🎤 **Em chữa thế nào?**

🙂 Frontend chia sẻ **một promise refresh duy nhất**: request đầu tiên tạo ra nó, những cái sau
`await` cùng cái đó thay vì tự gửi refresh riêng. Em nghĩ đây là ví dụ rõ nhất cho việc **một
cơ chế bảo mật ở backend ép ra một yêu cầu thiết kế ở frontend** — không biết server xoay vòng
token thì không nghĩ ra được.

🎤 **Token em để ở localStorage à? Không sợ XSS?**

🙂 Có sợ, và em biết đó là điểm yếu — JS đọc được nên dính XSS là mất token. Em bù bằng nhiều
lớp: **CSP** chặn script lạ nên XSS khó xảy ra, access token ngắn hạn nên lộ cũng nhanh hết
hạn, và refresh token có phát hiện tái sử dụng. Yêu cầu bảo mật cao hơn thì chuyển sang cookie
`httpOnly` kèm chống CSRF.

⚠️ *"localStorage an toàn mà anh"* — sai, và mất điểm ngay. Nêu đúng điểm yếu rồi nói cách bù
thì mạnh hơn nhiều.

🎤 **Database bị lộ thì refresh token có dùng được không?**

🙂 Không. Database chỉ lưu **hash** của token, không lưu token. Kẻ tấn công có bảng hash cũng
không đăng nhập được vì phải đưa ra token gốc.

---

## 6. Buổi 5 — Hỏng hóc và quy mô

🎤 **Gấp 10 lần lưu lượng thì cái gì vỡ trước?**

🙂 **Quota và hoá đơn Gemini**, không phải CPU. Ứng dụng LLM dành phần lớn thời gian **chờ API
bên ngoài** — I/O-bound chứ không CPU-bound. Thêm CPU không giúp gì. Sau đó là bộ đếm rate
limit đếm sai vì nằm trong RAM từng tiến trình, nên 2 replica là giới hạn thật gấp đôi.

🎤 **Em đo được con số nào chứng minh nó I/O-bound chưa?**

🙂 **Chưa.** Đó là suy luận từ kiến trúc, chưa phải kết quả đo. Cách chứng minh: chạy load test
bằng `hey` với mức đồng thời tăng dần, song song mở `docker stats`. **Nếu p95 xấu đi mà CPU vẫn
thấp** thì nút thắt nằm ngoài — đúng luận điểm. Em có ghi thí nghiệm này nhưng chưa chạy.

🎤 **Throughput hiện tại là bao nhiêu?**

🙂 Em chưa đo. p95 thì có — **7,55 giây**, từ Prometheus histogram. Throughput cần load test mà
em chưa chạy lần nào.

> ⚠️ **Cám dỗ lớn nhất ở đây là bịa một con số.** Đừng. Người phỏng vấn hỏi tiếp *"đo bằng công
> cụ gì, ở mức đồng thời nào?"* là lộ ngay. **"Chưa đo, và đây là cách em sẽ đo"** là câu trả
> lời hoàn toàn chấp nhận được với vị trí fresher.

🎤 **Có bộ phận nào hỏng làm sập cả hệ thống không?**

🙂 Có — **Postgres**. Đây là chỗ hở em biết mà chưa vá. `persistence.py` có đường lui về
in-memory khi **thiếu** biến `DATABASE_URL`, nhưng khi có biến mà **kết nối hỏng** thì ném lỗi
lúc khởi động và app không lên được.

🎤 **Sao em không sửa luôn?**

🙂 Vì lui im lặng cũng nguy hiểm: người dùng tưởng hội thoại đang được lưu mà thật ra không.
Em nghĩ phải lui **kèm cảnh báo rõ trên giao diện** thì mới đúng, và đó là thay đổi cần cân
nhắc chứ không phải vá vội.

🎤 **API thời tiết chết thì người dùng thấy gì?**

🙂 Vẫn có câu trả lời, dựa trên thông tin du lịch, và agent nói rõ chưa lấy được thời tiết.
Được vậy vì tool **bắt lỗi và trả kết quả có cấu trúc** thay vì ném exception — agent đọc lỗi
đó như mọi kết quả khác rồi tự quyết. Có test canh.

🎤 **Em có circuit breaker không?**

🙂 **Không.** Hiện chỉ có thử lại kèm chờ tăng dần. Khi dịch vụ ngoài chết hẳn thì mọi request
vẫn cố thử rồi mới chịu thua — tốn thời gian vô ích cho từng người dùng. Circuit breaker sẽ
ngừng thử sau N lỗi liên tiếp. Với quy mô demo thì em thấy chưa cần, có người dùng thật thì cần.

---

## 7. Buổi 6 — Khi bạn KHÔNG biết

Đây là **buổi quan trọng nhất** tài liệu. Bạn sẽ gặp câu không biết — chắc chắn. Cách xử lý
quyết định điểm hơn cả nội dung.

🎤 **Em xử lý race condition khi hai người cùng sửa một từ thế nào?**

⚠️ **Câu trả lời tệ nhất — bịa:** *"Em dùng lock ạ."*
> Câu tiếp theo sẽ là *"lock loại gì, đặt ở đâu, giữ bao lâu?"* và bạn sụp. Một lời bịa bị lật
> tẩy làm hỏng **cả những câu bạn trả lời đúng** — người phỏng vấn bắt đầu nghi ngờ mọi thứ.

⚠️ **Câu trả lời yếu — bỏ cuộc:** *"Dạ em không biết."*
> Trung thực nhưng không cho thấy gì. Bạn để lại một khoảng trống.

🙂 **Câu trả lời tốt — thành thật rồi suy luận tiếp:**
> *"Chỗ này em chưa xử lý, và giờ anh hỏi em mới nhận ra. Hiện hai request cùng sửa một từ thì
> cái sau ghi đè cái trước, không ai biết.*
>
> *Em nghĩ có hai hướng. **Khoá lạc quan**: thêm cột version, khi ghi thì kiểm version có
> khớp không, lệch thì trả `409` để client tải lại. **Khoá bi quan**: `SELECT FOR UPDATE`, khoá
> dòng đó lại. Em nghiêng về hướng đầu vì từ điển này ghi rất hiếm — khoá bi quan sẽ chặn nhau
> vô ích.*
>
> *Cách kiểm là viết một test bắn hai request đồng thời rồi xem kết quả cuối có đúng không."*

Câu đó thừa nhận chưa làm, nhưng cho thấy **bạn suy luận được từ nguyên tắc**, biết tên các
phương án, chọn được một cái **kèm lý do gắn với dự án**, và biết cách kiểm chứng. Với vị trí
fresher, đây gần như là câu trả lời tốt nhất có thể.

### Khuôn ba bước dùng cho mọi câu không biết

| Bước | Nói gì |
|---|---|
| **1. Thành thật, gọn** | *"Chỗ này em chưa làm/chưa đo."* — một câu, không xin lỗi dài dòng |
| **2. Suy luận to ra** | *"Nhưng em nghĩ có hai hướng… em nghiêng về X vì dự án này…"* |
| **3. Nêu cách kiểm chứng** | *"Cách kiểm là…"* |

> **Điều người phỏng vấn thật sự đo:** không phải bạn biết bao nhiêu, mà **bạn xử lý ranh giới
> hiểu biết của mình thế nào**. Người đi làm gặp chuyện chưa biết hằng ngày. Họ tuyển người
> biết nói *"tôi chưa rõ, để tôi kiểm"* — chứ không tuyển người bịa rồi đẩy bug lên production.

---

## 8. Năm mức câu hỏi để tự luyện

Tự trả lời **thành tiếng**, không mở tài liệu. Nói được trôi chảy mới tính là hiểu.

**Mức 1 — Khái niệm nền**
1. RAG là gì, giải quyết vấn đề gì?
2. Embedding là gì, vì sao tìm được theo ý nghĩa?
3. JWT gồm mấy phần, phần nào ai cũng đọc được?
4. `401` khác `403` chỗ nào?
5. Index B-tree hoạt động thế nào?

**Mức 2 — Hiểu dự án**
6. Vẽ kiến trúc travel-ai-agent, giải thích từng lớp.
7. Đi theo một câu hỏi từ lúc gõ tới lúc có câu trả lời.
8. SlangWord có những bảng nào, quan hệ ra sao?
9. Bộ eval đo những gì, kết quả bao nhiêu?

**Mức 3 — Vì sao quyết định thế**
10. Vì sao ReAct chứ không phải chain, router hay multi-agent?
11. Vì sao Chroma chứ không phải FAISS hay Pinecone?
12. Vì sao tắt hybrid search dù đã viết xong code?
13. Vì sao GIN + `pg_trgm` chứ không phải B-tree?
14. Vì sao Trivy chặn `CRITICAL` mà bỏ qua lỗ hổng chưa có bản vá?
15. Vì sao OIDC keyless chứ không phải client secret?

**Mức 4 — Gỡ lỗi và hỏng hóc**
16. API chậm hẳn đi, em tìm ở đâu trước?
17. Người dùng báo bị đăng xuất ngẫu nhiên — chẩn đoán thế nào?
18. Eval tụt từ 4,6 xuống 3,0 sau một PR — làm gì?
19. Hoá đơn Gemini tăng gấp 10 chỉ trong một đêm — làm gì **trong 5 phút tới**?
20. Agent trả lời "không tìm thấy thông tin" cho mọi câu hỏi — nghi gì đầu tiên?

**Mức 5 — Thiết kế và quy mô**
21. Gấp 100 lần lưu lượng thì phải đổi gì?
22. Thêm đăng nhập cho travel-agent thì thiết kế thế nào?
23. Kho kiến thức lên 1 triệu chunk thì đổi gì?
24. Thiết kế cho phép mỗi người dùng tải tài liệu riêng của họ.
25. Làm sao chống một người dùng cố ý làm hệ thống tốn tiền?

> Câu **19** và **25** là loại câu hỏi phỏng vấn hay nhất, vì chúng buộc bạn nói cả về **kỹ
> thuật** lẫn **vận hành**. Với câu 19, câu trả lời tốt bắt đầu bằng
> *"`AI_ENABLED=0` bằng một lệnh `az`, rồi mới đi tìm nguyên nhân"* — **chặn máu trước, khám
> sau**.

---

## 9. Liên quan

- [HOC_VAN_HANH_THAT.md](HOC_VAN_HANH_THAT.md) — đã đo và chưa đo, hỏng hóc, quy mô
- [CHECKLIST_HIEU_SAU.md](CHECKLIST_HIEU_SAU.md) — tự chấm xem đã hiểu tới đâu
- [../MENTOR.md](../MENTOR.md) mục 16 — 23 câu hỏi và đáp án ngắn
- [LO_TRINH_HOC.md](LO_TRINH_HOC.md) — kịch bản nói cho từng dòng CV
