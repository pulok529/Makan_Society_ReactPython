import sys
import os
from sqlalchemy import select, func

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import SessionLocal
from app.modules.billing.models import BillingInvoice, BillingInvoiceDetail
from app.modules.members.models import Member
from app.modules.auth.models import User

def patch_invoices():
    db = SessionLocal()
    try:
        # Get all invoices
        invoices = db.query(BillingInvoice).all()
        
        total_scanned = len(invoices)
        total_corrected = 0
        total_skipped = 0
        
        print("--- Data Patch Report ---")
        print(f"Total Records Scanned: {total_scanned}")
        
        for invoice in invoices:
            # Calculate the sum of fee_amount from details
            sum_fee = db.scalar(
                select(func.coalesce(func.sum(BillingInvoiceDetail.fee_amount), 0))
                .where(BillingInvoiceDetail.invoice_id == invoice.id)
            )
            
            if sum_fee is None:
                sum_fee = 0
                
            sum_fee = float(sum_fee)
            current_subtotal = float(invoice.subtotal_amount)
            
            if abs(current_subtotal - sum_fee) > 0.01:
                old_subtotal = current_subtotal
                old_net = float(invoice.net_amount)
                
                # Correct it
                invoice.subtotal_amount = sum_fee
                invoice.net_amount = sum_fee - float(invoice.discount_amount)
                
                print(f"Corrected Invoice {invoice.invoice_no} (ID: {invoice.id}):")
                print(f"  Subtotal: {old_subtotal} -> {invoice.subtotal_amount}")
                print(f"  Net     : {old_net} -> {invoice.net_amount}")
                total_corrected += 1
            else:
                total_skipped += 1
                
        db.commit()
        print(f"\nTotal Records Corrected: {total_corrected}")
        print(f"Total Records Skipped: {total_skipped}")
        
    except Exception as e:
        db.rollback()
        print(f"Error occurred: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    patch_invoices()
