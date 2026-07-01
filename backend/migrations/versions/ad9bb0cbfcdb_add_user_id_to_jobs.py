"""add_user_id_to_jobs

Revision ID: ad9bb0cbfcdb
Revises: fda5d7dfffb3
Create Date: 2026-06-29 14:58:29.077877

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'ad9bb0cbfcdb'
down_revision: Union[str, None] = 'b1c2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    jobs_cols = {c["name"] for c in inspect(bind).get_columns("jobs")}
    if "user_id" not in jobs_cols:
        with op.batch_alter_table("jobs") as batch_op:
            batch_op.add_column(
                sa.Column(
                    "user_id",
                    sa.String(length=50),
                    sa.ForeignKey("users.id", ondelete="SET NULL", name="fk_jobs_user_id"),
                    nullable=True,
                )
            )

    indexes = {idx["name"] for idx in inspect(bind).get_indexes("jobs")}
    if "ix_jobs_user_id" not in indexes:
        op.create_index("ix_jobs_user_id", "jobs", ["user_id"])
    if "ix_jobs_user_id_created_at" not in indexes:
        op.create_index("ix_jobs_user_id_created_at", "jobs", ["user_id", "created_at"])


def downgrade() -> None:
    with op.batch_alter_table('jobs') as batch_op:
        batch_op.drop_column('user_id')
