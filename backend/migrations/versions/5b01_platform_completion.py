"""Add user preferences, collection items, enterprise contacts, monitor jobs, agent memory."""

from alembic import op
import sqlalchemy as sa

revision = "5b01_platform_completion"
down_revision = "ad9bb0cbfcdb"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user_preferences",
        sa.Column("user_id", sa.String(50), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("min_citations", sa.Integer(), server_default="2"),
        sa.Column("scholarly_focus", sa.String(50), server_default="balanced"),
        sa.Column("api_logging_enabled", sa.Boolean(), server_default="1"),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "collection_items",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("collection_id", sa.String(50), sa.ForeignKey("collections.id", ondelete="CASCADE"), nullable=False),
        sa.Column("result_id", sa.String(50), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("snippet", sa.Text(), nullable=True),
        sa.Column("source", sa.String(50), nullable=True),
        sa.Column("job_id", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_collection_items_collection_id", "collection_items", ["collection_id"])
    op.create_table(
        "enterprise_contacts",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), server_default="new"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "monitor_jobs",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("monitor_id", sa.String(50), sa.ForeignKey("monitors.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", sa.String(50), sa.ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_monitor_jobs_monitor_id", "monitor_jobs", ["monitor_id"])
    op.create_table(
        "agent_memory_records",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("job_id", sa.String(50), nullable=False),
        sa.Column("agent_name", sa.String(100), nullable=False),
        sa.Column("step_index", sa.Integer(), server_default="0"),
        sa.Column("decision_json", sa.Text(), nullable=True),
        sa.Column("reasoning", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_agent_memory_records_job_id", "agent_memory_records", ["job_id"])


def downgrade():
    op.drop_index("ix_agent_memory_records_job_id", "agent_memory_records")
    op.drop_table("agent_memory_records")
    op.drop_index("ix_monitor_jobs_monitor_id", "monitor_jobs")
    op.drop_table("monitor_jobs")
    op.drop_table("enterprise_contacts")
    op.drop_index("ix_collection_items_collection_id", "collection_items")
    op.drop_table("collection_items")
    op.drop_table("user_preferences")
