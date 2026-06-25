"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-06-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("username", sa.String(64), unique=True, index=True, nullable=False),
        sa.Column("email", sa.String(128), unique=True, nullable=False),
        sa.Column("hashed_password", sa.String(128), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "sources",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("source_type", sa.String(16), nullable=False),
        sa.Column("file_path", sa.String(512)),
        sa.Column("ip", sa.String(64)),
        sa.Column("port", sa.Integer()),
        sa.Column("cam_username", sa.String(64)),
        sa.Column("cam_password_enc", sa.String(512)),
        sa.Column("transport", sa.String(8)),
        sa.Column("rtsp_url", sa.String(512)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("show_overlay", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("face_recognition_enabled", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("hls_output_dir", sa.String(512)),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "zones",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("polygon_json", sa.Text(), nullable=False),
        sa.Column("npy_path", sa.String(512)),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "rules",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("zone_id", sa.Integer(), sa.ForeignKey("zones.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("rule_type", sa.String(16), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("keypoint_indices_json", sa.Text()),
        sa.Column("dwell_seconds", sa.Float()),
        sa.Column("dwell_op", sa.String(4)),
        sa.Column("arm_side", sa.String(8)),
        sa.Column("angle_degrees", sa.Float()),
        sa.Column("angle_op", sa.String(4)),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "faces",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("person_name", sa.String(128), nullable=False),
        sa.Column("photo_path", sa.String(512), nullable=False),
        sa.Column("embedding_path", sa.String(512)),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "report_configs",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("delivery_method", sa.String(16), nullable=False),
        sa.Column("destination", sa.String(256), nullable=False),
        sa.Column("photo_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("include_person_name", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("save_records", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "report_config_rules",
        sa.Column("report_config_id", sa.Integer(), sa.ForeignKey("report_configs.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("rule_id", sa.Integer(), sa.ForeignKey("rules.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "trigger_records",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("rule_id", sa.Integer(), sa.ForeignKey("rules.id", ondelete="SET NULL")),
        sa.Column("zone_id", sa.Integer(), sa.ForeignKey("zones.id", ondelete="SET NULL")),
        sa.Column("person_name", sa.String(128)),
        sa.Column("triggered_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), index=True),
        sa.Column("rule_snapshot_json", sa.Text()),
        sa.Column("photos_sent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("alert_delivered", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("delivery_error", sa.String(512)),
    )


def downgrade() -> None:
    op.drop_table("trigger_records")
    op.drop_table("report_config_rules")
    op.drop_table("report_configs")
    op.drop_table("faces")
    op.drop_table("rules")
    op.drop_table("zones")
    op.drop_table("sources")
    op.drop_table("users")
