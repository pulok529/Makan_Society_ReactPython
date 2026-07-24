import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import SessionLocal
from app.modules.billing.service import BillingService
from app.modules.members.models import Member

def find_mismatch():
    db = SessionLocal()
    service = BillingService(db)
    
    members = db.query(Member).all()
    
    mismatches = []
    
    for member in members:
        res = service.billing_invoice_table(
            draw=1, start=0, length=10000, search='', 
            order_key='date', order_dir='desc', 
            member_id=member.id, from_date=None, to_date=None
        )
        
        rows = res['data']
        totals = res['totals']
        
        sum_bill = sum(float(r['subtotal_amount']) for r in rows)
        sum_paid = sum(float(r['total_receive_amount']) for r in rows)
        sum_due = sum(float(r['total_due_amount']) for r in rows)
        
        if (abs(sum_bill - totals['total_bill_amount']) > 0.01 or
            abs(sum_paid - totals['total_paid']) > 0.01 or
            abs(sum_due - totals['total_due']) > 0.01):
            
            mismatches.append({
                'member': member.id,
                'code': member.member_code,
                'name': member.full_name,
                'rows_sum_bill': sum_bill,
                'rows_sum_paid': sum_paid,
                'rows_sum_due': sum_due,
                'totals_bill': totals['total_bill_amount'],
                'totals_paid': totals['total_paid'],
                'totals_due': totals['total_due'],
            })
            
    for m in mismatches:
        print(f"Mismatch for Member {m['code']} ({m['name']}):")
        print(f"  Rows Sum : Bill={m['rows_sum_bill']}, Paid={m['rows_sum_paid']}, Due={m['rows_sum_due']}")
        print(f"  Totals   : Bill={m['totals_bill']}, Paid={m['totals_paid']}, Due={m['totals_due']}")
        print()
        
    print(f"Found {len(mismatches)} mismatches.")

if __name__ == "__main__":
    find_mismatch()
