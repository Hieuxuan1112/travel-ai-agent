"""Load test BASELINE - chi cham vao /healthz, khong dung toi Gemini, KHONG TON
TIEN. Do suc chiu tai THUAN HA TANG (Uvicorn + FastAPI + middleware) truoc khi
so sanh voi locustfile_chat.py (co goi AI that).

Muc dich: tra loi cau hoi da neu trong docs/hoc/HOC_VAN_HANH_THAT.md muc 6.1 -
"nut that khi tai cao la CPU/ha tang hay la quota Gemini?" Neu baseline nay
chiu duoc throughput rat cao ma /chat (locustfile_chat.py) lai bi gioi han o
muc thap hon nhieu, do la bang chung nut that nam o Gemini chu khong phai
ha tang.

Chay (can co api dang chay, vd `docker compose up api` -> localhost:8000):

    venv\\Scripts\\locust.exe -f loadtest/locustfile_healthz.py --host http://localhost:8000

Headless, chay 30 giay voi toi da 50 user gia lap, tang dan 10 user/giay, ghi
ket qua ra CSV (loadtest/results_healthz_stats.csv, ...):

    venv\\Scripts\\locust.exe -f loadtest/locustfile_healthz.py \\
        --host http://localhost:8000 --headless \\
        -u 50 -r 10 --run-time 30s --csv loadtest/results_healthz
"""

from locust import HttpUser, between, task


class HealthzUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task
    def healthz(self):
        self.client.get("/healthz")
