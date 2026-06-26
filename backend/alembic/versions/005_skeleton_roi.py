"""add show_skeleton and detection_roi_json to sources

Revision ID: 005
Revises: 004
Create Date: 2026-06-26
"""
from alembic import op
import sqlalchemy as sa

revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('sources', sa.Column('show_skeleton', sa.Boolean(), nullable=False, server_default='0'))
    op.add_column('sources', sa.Column('detection_roi_json', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('sources', 'detection_roi_json')
    op.drop_column('sources', 'show_skeleton')
