"""Load test THAT vao /chat - MOI request goi Gemini that, TON TIEN THAT.

CHI chay voi so luong nho, thoi gian ngan. Vi du duoc kiem chung
(xem loadtest/results.md): -u 3 -r 1 --run-time 20s ~ 10-15 request, du de
co p95 dang tin ma khong dot ngan sach. KHONG chay voi -u lon - moi request
that su goi API tra tien.

RATE_LIMIT_PER_HOUR mac dinh cua docker-compose la 30/gio/IP - Locust chay tu
mot may nen tinh chung la mot client, dung vuot qua nguong nay trong 1 gio
(bao gom ca cac lan hoi thu cong khac cung IP).

Chay (can co api dang chay, vd `docker compose up api` -> localhost:8000):

    venv\\Scripts\\locust.exe -f loadtest/locustfile_chat.py --host http://localhost:8000 \\
        --headless -u 3 -r 1 --run-time 20s --csv loadtest/results_chat
"""

import random

from locust import HttpUser, between, task

QUESTIONS = [
    "What is the weather in St Ives right now?",
    "Tell me about surfing in Cornwall",
    "What can I do in Newquay?",
    "What is the weather in Falmouth, Cornwall right now?",
]


class ChatUser(HttpUser):
    wait_time = between(1, 2)

    @task
    def chat(self):
        question = random.choice(QUESTIONS)
        self.client.post("/chat", json={"question": question}, name="/chat")
