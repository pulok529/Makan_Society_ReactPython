"""initial normalized structure

Revision ID: 20260428_01
Revises:
Create Date: 2026-04-28 23:10:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260428_01"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for schema_name in ["auth", "society", "billing", "accounting", "messaging", "files", "reporting"]:
        op.execute(sa.text(f"IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = '{schema_name}') EXEC('CREATE SCHEMA {schema_name}')"))

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("login_name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("username", name=op.f("uq_users_username")),
        sa.UniqueConstraint("login_name", name=op.f("uq_users_login_name")),
        schema="auth",
    )
    op.create_index(op.f("ix_auth_users_login_name"), "users", ["login_name"], unique=False, schema="auth")
    op.create_index(op.f("ix_auth_users_username"), "users", ["username"], unique=False, schema="auth")

    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_roles")),
        sa.UniqueConstraint("name", name=op.f("uq_roles_name")),
        schema="auth",
    )

    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("resource", sa.String(length=100), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_permissions")),
        sa.UniqueConstraint("resource", "action", name="uq_permissions_resource_action"),
        schema="auth",
    )

    op.create_table(
        "member_categories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_member_categories")),
        sa.UniqueConstraint("name", name=op.f("uq_member_categories_name")),
        schema="society",
    )

    op.create_table(
        "packages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("package_type", sa.String(length=100), nullable=True),
        sa.Column("default_price", sa.Numeric(18, 2), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["society.member_categories.id"], name=op.f("fk_packages_category_id_member_categories")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_packages")),
        schema="society",
    )

    op.create_table(
        "members",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("member_code", sa.String(length=50), nullable=False),
        sa.Column("member_id_text", sa.String(length=100), nullable=True),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("father_name", sa.String(length=200), nullable=True),
        sa.Column("mother_name", sa.String(length=200), nullable=True),
        sa.Column("present_address", sa.String(length=500), nullable=True),
        sa.Column("permanent_address", sa.String(length=500), nullable=True),
        sa.Column("cell_no", sa.String(length=30), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("reference", sa.String(length=255), nullable=True),
        sa.Column("national_id", sa.String(length=100), nullable=True),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("member_class", sa.String(length=100), nullable=True),
        sa.Column("joined_on", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["society.member_categories.id"], name=op.f("fk_members_category_id_member_categories")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_members")),
        sa.UniqueConstraint("member_code", name=op.f("uq_members_member_code")),
        schema="society",
    )
    op.create_index(op.f("ix_society_members_cell_no"), "members", ["cell_no"], unique=False, schema="society")
    op.create_index(op.f("ix_society_members_full_name"), "members", ["full_name"], unique=False, schema="society")
    op.create_index(op.f("ix_society_members_member_code"), "members", ["member_code"], unique=False, schema="society")

    op.create_table(
        "member_nominees",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("member_id", sa.Integer(), nullable=False),
        sa.Column("nominee_name", sa.String(length=200), nullable=True),
        sa.Column("nominee_cell", sa.String(length=30), nullable=True),
        sa.ForeignKeyConstraint(["member_id"], ["society.members.id"], name=op.f("fk_member_nominees_member_id_members"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_member_nominees")),
        schema="society",
    )

    op.create_table(
        "member_status_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("member_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("changed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["member_id"], ["society.members.id"], name=op.f("fk_member_status_history_member_id_members"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_member_status_history")),
        schema="society",
    )

    op.create_table(
        "member_packages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("member_id", sa.Integer(), nullable=False),
        sa.Column("package_id", sa.Integer(), nullable=False),
        sa.Column("assigned_on", sa.Date(), nullable=False),
        sa.Column("ended_on", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(["member_id"], ["society.members.id"], name=op.f("fk_member_packages_member_id_members"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["package_id"], ["society.packages.id"], name=op.f("fk_member_packages_package_id_packages")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_member_packages")),
        schema="society",
    )

    op.create_table(
        "package_price_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("package_id", sa.Integer(), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("price", sa.Numeric(18, 2), nullable=False),
        sa.ForeignKeyConstraint(["package_id"], ["society.packages.id"], name=op.f("fk_package_price_history_package_id_packages"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_package_price_history")),
        schema="society",
    )

    op.create_table(
        "billing_periods",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("period_name", sa.String(length=30), nullable=False),
        sa.Column("starts_on", sa.Date(), nullable=False),
        sa.Column("ends_on", sa.Date(), nullable=False),
        sa.Column("is_closed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_billing_periods")),
        sa.UniqueConstraint("year", "month", name="uq_billing_periods_year_month"),
        schema="billing",
    )

    op.create_table(
        "charges",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("member_id", sa.Integer(), nullable=False),
        sa.Column("billing_period_id", sa.Integer(), nullable=True),
        sa.Column("charge_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("total_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("discount_amount", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("net_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("due_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["billing_period_id"], ["billing.billing_periods.id"], name=op.f("fk_charges_billing_period_id_billing_periods")),
        sa.ForeignKeyConstraint(["member_id"], ["society.members.id"], name=op.f("fk_charges_member_id_members")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_charges")),
        schema="billing",
    )

    op.create_table(
        "charge_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("charge_id", sa.Integer(), nullable=False),
        sa.Column("package_id", sa.Integer(), nullable=True),
        sa.Column("item_type", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("unit_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("line_amount", sa.Numeric(18, 2), nullable=False),
        sa.ForeignKeyConstraint(["charge_id"], ["billing.charges.id"], name=op.f("fk_charge_items_charge_id_charges"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["package_id"], ["society.packages.id"], name=op.f("fk_charge_items_package_id_packages")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_charge_items")),
        schema="billing",
    )

    op.create_table(
        "receipts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("receipt_no", sa.String(length=50), nullable=False),
        sa.Column("member_id", sa.Integer(), nullable=True),
        sa.Column("collected_by_user_id", sa.Integer(), nullable=True),
        sa.Column("receipt_type", sa.String(length=50), nullable=False),
        sa.Column("payment_date", sa.Date(), nullable=False),
        sa.Column("subtotal_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("discount_amount", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("total_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("notes", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["collected_by_user_id"], ["auth.users.id"], name=op.f("fk_receipts_collected_by_user_id_users")),
        sa.ForeignKeyConstraint(["member_id"], ["society.members.id"], name=op.f("fk_receipts_member_id_members")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_receipts")),
        sa.UniqueConstraint("receipt_no", name=op.f("uq_receipts_receipt_no")),
        schema="billing",
    )
    op.create_index(op.f("ix_billing_receipts_receipt_no"), "receipts", ["receipt_no"], unique=False, schema="billing")

    op.create_table(
        "receipt_lines",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("receipt_id", sa.Integer(), nullable=False),
        sa.Column("charge_id", sa.Integer(), nullable=True),
        sa.Column("charge_item_id", sa.Integer(), nullable=True),
        sa.Column("line_type", sa.String(length=50), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.ForeignKeyConstraint(["charge_id"], ["billing.charges.id"], name=op.f("fk_receipt_lines_charge_id_charges")),
        sa.ForeignKeyConstraint(["charge_item_id"], ["billing.charge_items.id"], name=op.f("fk_receipt_lines_charge_item_id_charge_items")),
        sa.ForeignKeyConstraint(["receipt_id"], ["billing.receipts.id"], name=op.f("fk_receipt_lines_receipt_id_receipts"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_receipt_lines")),
        schema="billing",
    )

    op.create_table(
        "accounts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("account_type", sa.String(length=50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_accounts")),
        sa.UniqueConstraint("code", name=op.f("uq_accounts_code")),
        schema="accounting",
    )

    op.create_table(
        "income_expense_entries",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=True),
        sa.Column("entry_type", sa.String(length=30), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("remarks", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounting.accounts.id"], name=op.f("fk_income_expense_entries_account_id_accounts")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_income_expense_entries")),
        schema="accounting",
    )

    op.create_table(
        "sms_templates",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("template_type", sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sms_templates")),
        sa.UniqueConstraint("name", name=op.f("uq_sms_templates_name")),
        schema="messaging",
    )

    op.create_table(
        "file_objects",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("storage_key", sa.String(length=255), nullable=False),
        sa.Column("original_name", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_file_objects")),
        sa.UniqueConstraint("storage_key", name=op.f("uq_file_objects_storage_key")),
        schema="files",
    )

    op.create_table(
        "sms_messages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("member_id", sa.Integer(), nullable=True),
        sa.Column("template_id", sa.Integer(), nullable=True),
        sa.Column("recipient", sa.String(length=30), nullable=False),
        sa.Column("message_body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="queued"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["member_id"], ["society.members.id"], name=op.f("fk_sms_messages_member_id_members")),
        sa.ForeignKeyConstraint(["template_id"], ["messaging.sms_templates.id"], name=op.f("fk_sms_messages_template_id_sms_templates")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sms_messages")),
        schema="messaging",
    )

    op.create_table(
        "sms_delivery_attempts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("sms_message_id", sa.Integer(), nullable=False),
        sa.Column("provider_name", sa.String(length=100), nullable=True),
        sa.Column("provider_message_id", sa.String(length=255), nullable=True),
        sa.Column("provider_status", sa.String(length=100), nullable=True),
        sa.Column("error_detail", sa.Text(), nullable=True),
        sa.Column("attempted_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["sms_message_id"], ["messaging.sms_messages.id"], name=op.f("fk_sms_delivery_attempts_sms_message_id_sms_messages"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sms_delivery_attempts")),
        schema="messaging",
    )

    op.create_table(
        "file_links",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("file_object_id", sa.Integer(), nullable=False),
        sa.Column("linked_entity", sa.String(length=100), nullable=False),
        sa.Column("linked_entity_id", sa.Integer(), nullable=False),
        sa.Column("purpose", sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(["file_object_id"], ["files.file_objects.id"], name=op.f("fk_file_links_file_object_id_file_objects"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_file_links")),
        schema="files",
    )

    op.create_table(
        "report_profiles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("header_text", sa.String(length=255), nullable=True),
        sa.Column("address_text", sa.String(length=255), nullable=True),
        sa.Column("phone_text", sa.String(length=100), nullable=True),
        sa.Column("email_text", sa.String(length=255), nullable=True),
        sa.Column("logo_file_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["logo_file_id"], ["files.file_objects.id"], name=op.f("fk_report_profiles_logo_file_id_file_objects")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_report_profiles")),
        sa.UniqueConstraint("name", name=op.f("uq_report_profiles_name")),
        schema="reporting",
    )

    op.create_table(
        "generated_reports",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("report_type", sa.String(length=100), nullable=False),
        sa.Column("requested_by_user_id", sa.Integer(), nullable=True),
        sa.Column("file_object_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["file_object_id"], ["files.file_objects.id"], name=op.f("fk_generated_reports_file_object_id_file_objects")),
        sa.ForeignKeyConstraint(["requested_by_user_id"], ["auth.users.id"], name=op.f("fk_generated_reports_requested_by_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_generated_reports")),
        schema="reporting",
    )

    op.create_table(
        "user_roles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["auth.roles.id"], name=op.f("fk_user_roles_role_id_roles"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["auth.users.id"], name=op.f("fk_user_roles_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_roles")),
        sa.UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_id_role_id"),
        schema="auth",
    )

    op.create_table(
        "role_permissions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("permission_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["permission_id"], ["auth.permissions.id"], name=op.f("fk_role_permissions_permission_id_permissions"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["auth.roles.id"], name=op.f("fk_role_permissions_role_id_roles"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_role_permissions")),
        sa.UniqueConstraint("role_id", "permission_id", name="uq_role_permissions_role_id_permission_id"),
        schema="auth",
    )

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["auth.users.id"], name=op.f("fk_refresh_tokens_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_refresh_tokens")),
        sa.UniqueConstraint("token_hash", name=op.f("uq_refresh_tokens_token_hash")),
        schema="auth",
    )


def downgrade() -> None:
    for table_name, schema_name in [
        ("refresh_tokens", "auth"),
        ("role_permissions", "auth"),
        ("user_roles", "auth"),
        ("generated_reports", "reporting"),
        ("report_profiles", "reporting"),
        ("file_links", "files"),
        ("sms_delivery_attempts", "messaging"),
        ("sms_messages", "messaging"),
        ("file_objects", "files"),
        ("sms_templates", "messaging"),
        ("income_expense_entries", "accounting"),
        ("accounts", "accounting"),
        ("receipt_lines", "billing"),
        ("receipts", "billing"),
        ("charge_items", "billing"),
        ("charges", "billing"),
        ("billing_periods", "billing"),
        ("package_price_history", "society"),
        ("member_packages", "society"),
        ("member_status_history", "society"),
        ("member_nominees", "society"),
        ("members", "society"),
        ("packages", "society"),
        ("member_categories", "society"),
        ("permissions", "auth"),
        ("roles", "auth"),
        ("users", "auth"),
    ]:
        op.drop_table(table_name, schema=schema_name)
