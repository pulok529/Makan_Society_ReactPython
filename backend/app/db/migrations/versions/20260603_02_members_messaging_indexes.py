"""add member and messaging indexes for paged search

Revision ID: 20260603_02
Revises: 20260603_01
Create Date: 2026-06-03
"""

from alembic import op
import sqlalchemy as sa


revision = "20260603_02"
down_revision = "20260603_01"
branch_labels = None
depends_on = None


def _index_names(inspector, table_name: str, schema: str) -> set[str]:
    return {index["name"] for index in inspector.get_indexes(table_name, schema=schema)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    member_indexes = _index_names(inspector, "members", "society")
    if "ix_society_members_is_active" not in member_indexes:
        op.create_index("ix_society_members_is_active", "members", ["is_active"], schema="society")

    sms_message_indexes = _index_names(inspector, "sms_messages", "messaging")
    if "ix_messaging_sms_messages_member_created" not in sms_message_indexes:
        op.create_index("ix_messaging_sms_messages_member_created", "sms_messages", ["member_id", "created_at"], schema="messaging")
    if "ix_messaging_sms_messages_status_created" not in sms_message_indexes:
        op.create_index("ix_messaging_sms_messages_status_created", "sms_messages", ["status", "created_at"], schema="messaging")
    if "ix_messaging_sms_messages_sent_at" not in sms_message_indexes:
        op.create_index("ix_messaging_sms_messages_sent_at", "sms_messages", ["sent_at"], schema="messaging")

    sms_attempt_indexes = _index_names(inspector, "sms_delivery_attempts", "messaging")
    if "ix_messaging_sms_attempts_message_attempted" not in sms_attempt_indexes:
        op.create_index("ix_messaging_sms_attempts_message_attempted", "sms_delivery_attempts", ["sms_message_id", "attempted_at"], schema="messaging")
    if "ix_messaging_sms_attempts_status_attempted" not in sms_attempt_indexes:
        op.create_index("ix_messaging_sms_attempts_status_attempted", "sms_delivery_attempts", ["provider_status", "attempted_at"], schema="messaging")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    member_indexes = _index_names(inspector, "members", "society")
    if "ix_society_members_is_active" in member_indexes:
        op.drop_index("ix_society_members_is_active", table_name="members", schema="society")

    sms_message_indexes = _index_names(inspector, "sms_messages", "messaging")
    if "ix_messaging_sms_messages_member_created" in sms_message_indexes:
        op.drop_index("ix_messaging_sms_messages_member_created", table_name="sms_messages", schema="messaging")
    if "ix_messaging_sms_messages_status_created" in sms_message_indexes:
        op.drop_index("ix_messaging_sms_messages_status_created", table_name="sms_messages", schema="messaging")
    if "ix_messaging_sms_messages_sent_at" in sms_message_indexes:
        op.drop_index("ix_messaging_sms_messages_sent_at", table_name="sms_messages", schema="messaging")

    sms_attempt_indexes = _index_names(inspector, "sms_delivery_attempts", "messaging")
    if "ix_messaging_sms_attempts_message_attempted" in sms_attempt_indexes:
        op.drop_index("ix_messaging_sms_attempts_message_attempted", table_name="sms_delivery_attempts", schema="messaging")
    if "ix_messaging_sms_attempts_status_attempted" in sms_attempt_indexes:
        op.drop_index("ix_messaging_sms_attempts_status_attempted", table_name="sms_delivery_attempts", schema="messaging")
