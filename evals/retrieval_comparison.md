# So sanh cach tim kiem

92 chunk Wikivoyage - 12 cau hoi - nhan yeu (chunk chua tu khoa moc = lien quan).
Sinh boi `evals/eval_retrieval.py`. Khong goi LLM.

| Cach tim | recall@1 | recall@3 | recall@5 |
| --- | :-: | :-: | :-: |
| Vector only (truoc) | 92% | 100% | 100% |
| BM25 only | 67% | 83% | 92% |
| **Hybrid (RRF)** (sau) | 83% | 100% | 100% |

## Tach theo kieu cau hoi (recall@5)

| Cach tim | Cau dien dat vong | Ten rieng / tu khoa |
| --- | :-: | :-: |
| Vector only (truoc) | 100% | 100% |
| BM25 only | 83% | 100% |
| **Hybrid (RRF)** (sau) | 100% | 100% |

## Doc bang the nao

- Vector manh o cau **dien dat vong** (100%) vi no hieu nghia chu khong doi trung chu.
- BM25 manh o **ten rieng** (100%) vi no khop chinh xac chuoi ky tu.

### Ket luan

**Hybrid KHONG cai thien gi tren kho nay.** Vector don thuan da dat recall@1 92% va recall@3 100%; hybrid duoc 83% va 100%.

Ly do: kho chi co 92 chunk va bo cau hoi de - vector da cham tran, khong con cho de cai thien. Tron them BM25 chi lam mot vai ket qua tot bi day xuong. Hybrid chi thang khi kho lon, nhieu tai lieu gan giong nhau, va co ma so / ten rieng hiem ma embedding khong nam duoc.

**Quyet dinh ky thuat:** giu code hybrid nhung de MAC DINH TAT (`RETRIEVAL_MODE=vector`). Them phuc tap ma khong do duoc loi ich la cai gia phai tra vo ich. Kho lon len thi bat lai va do lai.

(Hybrid ngang bang o recall@3, recall@5.)

**Han che cua phep do:** nhan la nhan yeu (chunk chua tu khoa moc), khong phai nguoi danh gia. Con so de so ba cach voi nhau, khong phai diem tuyet doi.
