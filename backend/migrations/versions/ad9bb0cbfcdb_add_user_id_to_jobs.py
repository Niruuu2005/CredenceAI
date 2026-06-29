"""add_user_id_to_jobs

Revision ID: ad9bb0cbfcdb
Revises: fda5d7dfffb3
Create Date: 2026-06-29 14:58:29.077877

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ad9bb0cbfcdb'
down_revision: Union[str, None] = 'fda5d7dfffb3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('jobs') as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.String(length=50), sa.ForeignKey('users.id', ondelete='SET NULL', name='fk_jobs_user_id'), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('jobs') as batch_op:
        batch_op.drop_column('user_id')
