#!/usr/bin/env python3
from __future__ import annotations

import os
import signal
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


WORKER_COMMAND = [
    os.getenv("PREFECT_BINARY", "/app/ingest/.venv/bin/prefect"),
    "worker",
    "start",
    "--install-policy",
    "never",
    "--with-healthcheck",
    "-p",
    "parleman-work-pool",
    "-t",
    "cloud-run",
]


def main() -> None:
    port = int(os.getenv("PORT", "8080"))
    health_path = os.getenv("WORKER_HEALTH_PATH", "/health")

    worker_process = subprocess.Popen(WORKER_COMMAND)
    httpd = ThreadingHTTPServer(("0.0.0.0", port), _build_handler(worker_process, health_path))

    def shutdown_worker(*_args: object) -> None:
        if worker_process.poll() is None:
            worker_process.terminate()
            try:
                worker_process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                worker_process.kill()
        httpd.shutdown()

    def monitor_worker() -> None:
        worker_process.wait()
        httpd.shutdown()

    signal.signal(signal.SIGTERM, shutdown_worker)
    signal.signal(signal.SIGINT, shutdown_worker)

    monitor_thread = threading.Thread(target=monitor_worker, daemon=True)
    monitor_thread.start()

    try:
        httpd.serve_forever()
    finally:
        shutdown_worker()
        monitor_thread.join(timeout=5)

    if worker_process.returncode not in (None, 0):
        raise SystemExit(worker_process.returncode)


def _build_handler(worker_process: subprocess.Popen[str], health_path: str) -> type[BaseHTTPRequestHandler]:
    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path != health_path:
                self.send_response(404)
                self.end_headers()
                return

            if worker_process.poll() is None:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"status":"ok"}')
                return

            self.send_response(503)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"worker-stopped"}')

        def log_message(self, format: str, *args: object) -> None:
            return

    return HealthHandler


if __name__ == "__main__":
    main()