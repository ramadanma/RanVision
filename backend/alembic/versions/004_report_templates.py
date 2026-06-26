"""add subject_template and body_template to report_configs

Revision ID: 004
Revises: 003
Create Date: 2026-06-26
"""
from alembic import op
import sqlalchemy as sa

revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('report_configs', sa.Column('subject_template', sa.Text(), nullable=True))
    op.add_column('report_configs', sa.Column('body_template', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('report_configs', 'body_template')
    op.drop_column('report_configs', 'subject_template')
