"""add smtp_configs table

Revision ID: 002
Revises: 001
Create Date: 2026-06-26

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "smtp_configs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("host", sa.String(256), nullable=False, server_default=""),
        sa.Column("port", sa.Integer(), nullable=False, server_default="587"),
        sa.Column("username", sa.String(256), nullable=False, server_default=""),
        sa.Column("password", sa.String(256), nullable=False, server_default=""),
        sa.Column("from_addr", sa.String(256), nullable=False, server_default=""),
        sa.Column("use_tls", sa.Boolean(), nullable=False, server_default="1"),
    )
    op.execute("INSERT INTO smtp_configs (id) VALUES (1)")


def downgrade() -> None:
    op.drop_table("smtp_configs")
