"""add face_check_front to sources

Revision ID: 003
Revises: 002
Create Date: 2026-06-26
"""
from alembic import op
import sqlalchemy as sa

revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'sources',
        sa.Column('face_check_front', sa.Boolean(), nullable=False, server_default='0'),
    )


def downgrade():
    op.drop_column('sources', 'face_check_front')
