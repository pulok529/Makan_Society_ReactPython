"""add background job scaffold

Revision ID: 20260603_03
Revises: 20260603_02
Create Date: 2026-06-03
"""

from alembic import op
import sqlalchemy as sa


revision = "20260603_03"
down_revision = "20260603_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'system') EXEC('CREATE SCHEMA [system]')")
    op.create_table(
        "background_jobs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("job_type", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("payload_json", sa.Text(), nullable=True),
        sa.Column("result_summary", sa.Text(), nullable=True),
        sa.Column("result_path", sa.String(length=500), nullable=True),
        sa.Column("output_filename", sa.String(length=255), nullable=True),
        sa.Column("output_content_type", sa.String(length=120), nullable=True),
        sa.Column("progress_current", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("progress_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["auth.users.id"]),
        sa.PrimaryKeyConstraint("id"),
        schema="system",
    )
    op.create_index("ix_system_background_jobs_type_created", "background_jobs", ["job_type", "created_at"], schema="system")
    op.create_index("ix_system_background_jobs_status_created", "background_jobs", ["status", "created_at"], schema="system")


def downgrade() -> None:
    op.drop_index("ix_system_background_jobs_status_created", table_name="background_jobs", schema="system")
    op.drop_index("ix_system_background_jobs_type_created", table_name="background_jobs", schema="system")
    op.drop_table("background_jobs", schema="system")
