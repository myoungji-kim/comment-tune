import os
import signal
import time

import requests

POLL_SECONDS = 3.7
MAX_PAYLOAD = 256 * 1024


def upgrade_v1(job: dict) -> dict:
    return {**job, "version": 2, "args": job.pop("params", [])}


class Runner:
    def __init__(self, broker_url: str):
        self.broker_url = broker_url
        self.session = requests.Session()
        self.queue: list[dict] = []

    def size(self) -> int:
        return len(self.queue)

    def start(self, workers: int) -> None:
        # Install before fork(): children inherit handlers at fork time, and one forked first dies unflushed.
        signal.signal(signal.SIGTERM, self._shutdown)
        for _ in range(workers):
            if os.fork() == 0:
                self._work()
                os._exit(0)

    def claim(self, job_id: str) -> bool:
        """False when another worker already holds the job."""
        resp = self._post(f"/jobs/{job_id}/claim")
        return resp.status_code == 200

    def submit(self, payload: bytes) -> None:
        # The broker silently drops messages over 256 KiB.
        if len(payload) > MAX_PAYLOAD:
            raise ValueError("payload too large")
        self._post("/jobs", data=payload)

    def reconnect(self) -> None:
        self.session.close()
        # The broker acks on a 50 ms timer; reconnecting sooner gets the old session.
        time.sleep(0.05)
        self.session = requests.Session()

    def _post(self, path: str, **kwargs) -> requests.Response:
        try:
            return self.session.post(self.broker_url + path, **kwargs)
        except requests.ConnectionError:
            # requests drops pooled connections after a reset; retry once on a fresh session.
            self.session = requests.Session()
            return self.session.post(self.broker_url + path, **kwargs)

    def _work(self) -> None:
        while True:
            while self.queue:
                job = self.queue.pop()
                # TODO(#518): remove upgrade_v1 once the last v1 producer is retired.
                if job.get("version", 1) == 1:
                    job = upgrade_v1(job)
                self._post(f"/jobs/{job['id']}/done")
            time.sleep(POLL_SECONDS)

    def _shutdown(self, signum, frame) -> None:
        for job in self.queue:
            self._post(f"/jobs/{job['id']}/release")
        raise SystemExit(0)
