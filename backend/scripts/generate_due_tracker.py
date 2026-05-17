from app.db.session import SessionLocal
from app.modules.billing.service import BillingService


def main() -> None:
    db = SessionLocal()
    try:
        processed = BillingService(db).sync_due_tracker_for_all_members()
        print(f"Due tracker synchronized for {processed} member(s).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
