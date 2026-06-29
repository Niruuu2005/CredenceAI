"""add agent budget table

Revision ID: 4a01_add_agent_budget_table
Revises: 3e01201308cd
Create Date: 2026-06-17

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4a01_add_agent_budget_table'
down_revision = '3e01201308cd'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'agent_budget_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.String(), nullable=False),
        sa.Column('agent_name', sa.String(), nullable=False),
        sa.Column('tokens_used', sa.Integer(), default=0),
        sa.Column('api_calls_made', sa.Integer(), default=0),
        sa.Column('tokens_limit', sa.Integer(), default=10000),
        sa.Column('api_calls_limit', sa.Integer(), default=20),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_agent_budget_records_id', 'agent_budget_records', ['id'])
    op.create_index('ix_agent_budget_records_job_id', 'agent_budget_records', ['job_id'])
    op.create_index('ix_agent_budget_records_agent_name', 'agent_budget_records', ['agent_name'])


def downgrade():
    op.drop_index('ix_agent_budget_records_agent_name', table_name='agent_budget_records')
    op.drop_index('ix_agent_budget_records_job_id', table_name='agent_budget_records')
    op.drop_index('ix_agent_budget_records_id', table_name='agent_budget_records')
    op.drop_table('agent_budget_records')
