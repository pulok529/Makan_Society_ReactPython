import threading
import sys
import os
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException

# Add app to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import SessionLocal
from app.modules.billing.models import BillingInvoice, BillingDueTracker
from app.modules.billing.service import BillingService
from app.modules.billing.schemas import BillingInvoiceCreate, BillingInvoiceLineCreate
from app.modules.auth.models import User
from app.modules.members.models import Member

def get_test_user_and_member(db: Session):
    user = db.query(User).first()
    member = db.query(Member).first()
    return user, member

def test_normal_invoice_creation():
    db = SessionLocal()
    try:
        user, member = get_test_user_and_member(db)
        head = db.execute(text("SELECT TOP 1 BillingHeadID FROM billing.billing_heads WHERE HeadType = 'OneTime' AND BillingMode = 'Optional'")).scalar()
        if not head:
            head = db.execute(text("SELECT TOP 1 BillingHeadID FROM billing.billing_heads WHERE HeadType = 'OneTime' AND BillingMode = 'Optional'")).scalar()
            
        payload = BillingInvoiceCreate(
            member_id=member.id,
            invoice_date=date.today(),
            discount_amount=0,
            lines=[
                BillingInvoiceLineCreate(
                    billing_head_id=head,
                    period_date=None,
                    fee_amount=100.0,
                    receive_amount=100.0,
                    discount_amount=0
                )
            ]
        )
        service = BillingService(db)
        count_before = db.query(BillingInvoice).count()
        invoice_response = service.create_invoice(payload, user)
        assert invoice_response is not None
        assert invoice_response.invoice_no.startswith("INV-")
        count_after = db.query(BillingInvoice).count()
        assert count_after == count_before + 1
        print("test_normal_invoice_creation passed!")
    finally:
        db.close()

def test_invoice_creation_after_deletion():
    db = SessionLocal()
    try:
        user, member = get_test_user_and_member(db)
        head = db.execute(text("SELECT TOP 1 BillingHeadID FROM billing.billing_heads WHERE HeadType = 'OneTime' AND BillingMode = 'Optional'")).scalar()
        
        payload = BillingInvoiceCreate(
            member_id=member.id,
            invoice_date=date.today(),
            discount_amount=0,
            lines=[
                BillingInvoiceLineCreate(
                    billing_head_id=head,
                    period_date=None,
                    fee_amount=100.0,
                    receive_amount=100.0,
                    discount_amount=0
                )
            ]
        )
        service = BillingService(db)
        inv1 = service.create_invoice(payload, user)
        inv1_no = inv1.invoice_no
        inv1_seq = int(inv1_no.split("-")[-1])
        service.cancel_invoice(inv1.id, type("Payload", (), {"cancel_reason": "test"})(), user)
        inv2 = service.create_invoice(payload, user)
        inv2_no = inv2.invoice_no
        inv2_seq = int(inv2_no.split("-")[-1])
        assert inv2_seq > inv1_seq
        print("test_invoice_creation_after_deletion passed!")
    finally:
        db.close()

def test_concurrent_invoice_generation():
    db_main = SessionLocal()
    user, member = get_test_user_and_member(db_main)
    head = db_main.execute(text("SELECT TOP 1 BillingHeadID FROM billing.billing_heads WHERE HeadType = 'OneTime' AND BillingMode = 'Optional'")).scalar()
    db_main.close()
    
    payload = BillingInvoiceCreate(
        member_id=member.id,
        invoice_date=date.today(),
        discount_amount=0,
        lines=[
            BillingInvoiceLineCreate(
                billing_head_id=head,
                period_date=None,
                fee_amount=10.0,
                receive_amount=10.0,
                discount_amount=0
            )
        ]
    )

    results = []
    def worker():
        db = SessionLocal()
        try:
            service = BillingService(db)
            inv = service.create_invoice(payload, user)
            results.append(inv.invoice_no)
        except Exception as e:
            results.append(e)
        finally:
            db.close()
            
    threads = []
    for _ in range(10):
        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    successes = [r for r in results if isinstance(r, str)]
    assert len(successes) == 10
    assert len(set(successes)) == 10
    print("test_concurrent_invoice_generation passed!")

def test_transaction_rollback():
    db = SessionLocal()
    try:
        user, member = get_test_user_and_member(db)
        payload = BillingInvoiceCreate(
            member_id=member.id,
            invoice_date=date.today(),
            discount_amount=0,
            lines=[
                BillingInvoiceLineCreate(
                    billing_head_id=-999,
                    period_date=None,
                    fee_amount=100.0,
                    receive_amount=100.0,
                    discount_amount=0
                )
            ]
        )
        service = BillingService(db)
        count_before = db.query(BillingInvoice).count()
        try:
            service.create_invoice(payload, user)
            assert False, "Should have failed"
        except HTTPException:
            pass
        count_after = db.query(BillingInvoice).count()
        assert count_after == count_before
        print("test_transaction_rollback passed!")
    finally:
        db.close()

if __name__ == "__main__":
    test_normal_invoice_creation()
    test_invoice_creation_after_deletion()
    test_transaction_rollback()
    test_concurrent_invoice_generation()
    print("All tests passed!")
