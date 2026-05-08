from datetime import datetime
import time


def main() -> None:
    print(f"[{datetime.utcnow().isoformat()}] Society worker started")
    while True:
        time.sleep(60)


if __name__ == "__main__":
    main()
