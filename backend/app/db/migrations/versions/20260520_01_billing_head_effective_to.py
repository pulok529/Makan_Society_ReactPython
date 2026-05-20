"""add billing head effective to date

Revision ID: 20260520_01
Revises: 20260517_01
Create Date: 2026-05-20
"""

from alembic import op
import sqlalchemy as sa


revision = "20260520_01"
down_revision = "20260517_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    billing_head_columns = {column["name"] for column in inspector.get_columns("billing_heads", schema="billing")}
    if "EffectiveToDate" not in billing_head_columns:
        op.add_column("billing_heads", sa.Column("EffectiveToDate", sa.Date(), nullable=True), schema="billing")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    billing_head_columns = {column["name"] for column in inspector.get_columns("billing_heads", schema="billing")}
    if "EffectiveToDate" in billing_head_columns:
        op.drop_column("billing_heads", "EffectiveToDate", schema="billing")
