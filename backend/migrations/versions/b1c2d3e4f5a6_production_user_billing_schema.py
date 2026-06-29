"""Production schema: users, monitors, collections, billing fields, indexes."""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, None] = "ad9bb0cbfcdb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(name: str) -> bool:
    bind = op.get_bind()
    return name in inspect(bind).get_table_names()


def upgrade() -> None:
    if not _table_exists("users"):
        op.create_table(
            "users",
            sa.Column("id", sa.String(50), primary_key=True),
            sa.Column("email", sa.String(100), nullable=False, unique=True),
            sa.Column("name", sa.String(100), nullable=True),
            sa.Column("picture", sa.String(255), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("plan", sa.String(20), server_default="Free"),
            sa.Column("search_quota_limit", sa.Integer(), server_default="50"),
            sa.Column("stripe_customer_id", sa.String(100), nullable=True),
            sa.Column("subscription_id", sa.String(100), nullable=True),
            sa.Column("subscription_status", sa.String(30), nullable=True),
            sa.Column("current_period_end", sa.DateTime(), nullable=True),
            sa.Column("role", sa.String(20), server_default="user"),
            sa.Column("account_status", sa.String(20), server_default="active"),
            sa.Column("usage_period_start", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_users_email", "users", ["email"])
        op.create_index("ix_users_stripe_customer_id", "users", ["stripe_customer_id"])
    else:
        cols = {c["name"] for c in inspect(op.get_bind()).get_columns("users")}
        additions = {
            "plan": sa.Column("plan", sa.String(20), server_default="Free"),
            "search_quota_limit": sa.Column("search_quota_limit", sa.Integer(), server_default="50"),
            "stripe_customer_id": sa.Column("stripe_customer_id", sa.String(100), nullable=True),
            "subscription_id": sa.Column("subscription_id", sa.String(100), nullable=True),
            "subscription_status": sa.Column("subscription_status", sa.String(30), nullable=True),
            "current_period_end": sa.Column("current_period_end", sa.DateTime(), nullable=True),
            "role": sa.Column("role", sa.String(20), server_default="user"),
            "account_status": sa.Column("account_status", sa.String(20), server_default="active"),
            "usage_period_start": sa.Column("usage_period_start", sa.DateTime(), nullable=True),
        }
        for name, col in additions.items():
            if name not in cols:
                op.add_column("users", col)

    if not _table_exists("monitors"):
        op.create_table(
            "monitors",
            sa.Column("id", sa.String(50), primary_key=True),
            sa.Column("user_id", sa.String(50), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("topic", sa.String(255), nullable=False),
            sa.Column("scope", sa.String(255), nullable=True),
            sa.Column("status", sa.String(20), server_default="Active"),
            sa.Column("interval", sa.String(50), server_default="Daily"),
            sa.Column("last_check", sa.String(50), server_default="Just created"),
            sa.Column("health", sa.String(20), server_default="Green"),
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_monitors_user_id", "monitors", ["user_id"])
    elif "user_id" not in {c["name"] for c in inspect(op.get_bind()).get_columns("monitors")}:
        op.add_column("monitors", sa.Column("user_id", sa.String(50), nullable=True))
        op.execute(
            "INSERT INTO users (id, email, name, plan, search_quota_limit, role, account_status) "
            "VALUES ('system', 'system@localhost', 'System', 'Enterprise', 5000, 'admin', 'active') "
            "ON CONFLICT (id) DO NOTHING"
        )
        op.execute("UPDATE monitors SET user_id = 'system' WHERE user_id IS NULL")
        with op.batch_alter_table("monitors") as batch:
            batch.alter_column("user_id", nullable=False)
            batch.create_foreign_key("fk_monitors_user_id", "users", ["user_id"], ["id"], ondelete="CASCADE")
        op.create_index("ix_monitors_user_id", "monitors", ["user_id"])

    if not _table_exists("collections"):
        op.create_table(
            "collections",
            sa.Column("id", sa.String(50), primary_key=True),
            sa.Column("user_id", sa.String(50), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("items_count", sa.Integer(), server_default="0"),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_collections_user_id", "collections", ["user_id"])
    elif "user_id" not in {c["name"] for c in inspect(op.get_bind()).get_columns("collections")}:
        op.add_column("collections", sa.Column("user_id", sa.String(50), nullable=True))
        op.execute(
            "INSERT INTO users (id, email, name, plan, search_quota_limit, role, account_status) "
            "VALUES ('system', 'system@localhost', 'System', 'Enterprise', 5000, 'admin', 'active') "
            "ON CONFLICT (id) DO NOTHING"
        )
        op.execute("UPDATE collections SET user_id = 'system' WHERE user_id IS NULL")
        with op.batch_alter_table("collections") as batch:
            batch.alter_column("user_id", nullable=False)
            batch.create_foreign_key("fk_collections_user_id", "users", ["user_id"], ["id"], ondelete="CASCADE")
        op.create_index("ix_collections_user_id", "collections", ["user_id"])

    if _table_exists("api_keys"):
        api_cols = {c["name"] for c in inspect(op.get_bind()).get_columns("api_keys")}
        if "user_id" not in api_cols:
            op.add_column("api_keys", sa.Column("user_id", sa.String(50), nullable=True))
            op.execute("UPDATE api_keys SET user_id = owner WHERE user_id IS NULL")
            op.create_index("ix_api_keys_user_id", "api_keys", ["user_id"])

    if not _table_exists("stripe_events"):
        op.create_table(
            "stripe_events",
            sa.Column("id", sa.String(100), primary_key=True),
            sa.Column("event_type", sa.String(100), nullable=False),
            sa.Column("processed_at", sa.DateTime(), nullable=True),
        )

    if _table_exists("jobs"):
        bind = op.get_bind()
        indexes = {idx["name"] for idx in inspect(bind).get_indexes("jobs")}
        if "ix_jobs_user_id" not in indexes:
            op.create_index("ix_jobs_user_id", "jobs", ["user_id"])
        if "ix_jobs_user_id_created_at" not in indexes:
            op.create_index("ix_jobs_user_id_created_at", "jobs", ["user_id", "created_at"])


def downgrade() -> None:
    op.drop_table("stripe_events")
    if _table_exists("collections"):
        with op.batch_alter_table("collections") as batch:
            try:
                batch.drop_constraint("fk_collections_user_id", type_="foreignkey")
            except Exception:
                pass
            batch.drop_column("user_id")
    if _table_exists("monitors"):
        with op.batch_alter_table("monitors") as batch:
            try:
                batch.drop_constraint("fk_monitors_user_id", type_="foreignkey")
            except Exception:
                pass
            batch.drop_column("user_id")
