"""add agent decisions table

Revision ID: 4a02_add_agent_decisions_table
Revises: 4a01_add_agent_budget_table
Create Date: 2026-06-17

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '4a02_add_agent_decisions_table'
down_revision = '4a01_add_agent_budget_table'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'agent_decisions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.String(), nullable=False),
        sa.Column('agent_name', sa.String(), nullable=False),
        sa.Column('input_data', sa.JSON(), nullable=True),
        sa.Column('output_data', sa.JSON(), nullable=True),
        sa.Column('reasoning', sa.Text(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('success', sa.Boolean(), default=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_agent_decisions_id', 'agent_decisions', ['id'])
    op.create_index('ix_agent_decisions_job_id', 'agent_decisions', ['job_id'])
    op.create_index('ix_agent_decisions_agent_name', 'agent_decisions', ['agent_name'])
    op.create_index('ix_agent_decisions_timestamp', 'agent_decisions', ['timestamp'])


def downgrade():
    op.drop_index('ix_agent_decisions_timestamp', table_name='agent_decisions')
    op.drop_index('ix_agent_decisions_agent_name', table_name='agent_decisions')
    op.drop_index('ix_agent_decisions_job_id', table_name='agent_decisions')
    op.drop_index('ix_agent_decisions_id', table_name='agent_decisions')
    op.drop_table('agent_decisions')
