# So sanh model

Cung mot bo eval 8 cau, cung tool, cung prompt - chi doi model.
Sinh boi `evals/compare_models.py`.

| Model | Gia in/out ($/1M) | Tool-selection | Chat luong | p-trung binh | $/1000 cau |
| --- | --- | :-: | :-: | :-: | --: |
| `gemini-2.5-flash-lite` | 0.10 / 0.40 | 100% | 3.5/5 | 7.8s | $0.21 |
| `gemini-3.1-flash-lite` | 0.25 / 1.50 | 100% | 4.5/5 | 10.2s | $1.19 |
| `gemini-3.5-flash-lite` | 0.30 / 2.50 | 100% | 4.5/5 | 11.5s | $1.55 |
| `gemini-2.5-flash` | 0.30 / 2.50 | 100% | 5.0/5 | 11.4s | $1.87 |
| `gemini-3.7-flash` | 0.75 / 3.75 | 100% | 4.6/5 | 11.3s | $4.49 |
| `gemini-3.6-flash` | 0.75 / 3.75 | 100% | 5.0/5 | 19.5s | $6.09 |
| `gemini-3.5-flash` | 1.50 / 9.00 | 100% | 4.8/5 | 16.7s | $14.69 |

## Doc bang the nao

- `gemini-3.1-flash-lite` dat gap **5.6 lan** `gemini-2.5-flash-lite` nhung chat luong chi lech **+1.0 diem** -> dang can nhac.
- `gemini-3.5-flash-lite` dat gap **7.2 lan** `gemini-2.5-flash-lite` nhung chat luong chi lech **+1.0 diem** -> dang can nhac.
- `gemini-2.5-flash` dat gap **8.7 lan** `gemini-2.5-flash-lite` nhung chat luong chi lech **+1.5 diem** -> dang can nhac.
- `gemini-3.7-flash` dat gap **20.9 lan** `gemini-2.5-flash-lite` nhung chat luong chi lech **+1.1 diem** -> dang can nhac.
- `gemini-3.6-flash` dat gap **28.4 lan** `gemini-2.5-flash-lite` nhung chat luong chi lech **+1.5 diem** -> dang can nhac.
- `gemini-3.5-flash` dat gap **68.6 lan** `gemini-2.5-flash-lite` nhung chat luong chi lech **+1.2 diem** -> dang can nhac.
