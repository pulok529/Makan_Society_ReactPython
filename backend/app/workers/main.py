from datetime import datetime
import time

from app.workers.jobs import process_next_pending_job


def main() -> None:
    print(f"[{datetime.utcnow().isoformat()}] Society worker started")
    while True:
        processed = process_next_pending_job()
        time.sleep(2 if processed else 10)


if __name__ == "__main__":
    main()
