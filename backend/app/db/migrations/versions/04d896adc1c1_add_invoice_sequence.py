"""add_invoice_sequence

Revision ID: 04d896adc1c1
Revises: 9959268af13a
Create Date: 2026-07-24 11:54:24.439380
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision: str = '04d896adc1c1'
down_revision: Union[str, Sequence[str], None] = '9959268af13a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SQL Server uses NEXT VALUE FOR sequence_name
    op.execute("CREATE SEQUENCE billing.invoice_sequence START WITH 10000 INCREMENT BY 1")

def downgrade() -> None:
    op.execute("DROP SEQUENCE billing.invoice_sequence")
