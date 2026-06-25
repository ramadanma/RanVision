from datetime import datetime

from pydantic import BaseModel


class RuleCreate(BaseModel):
    zone_id: int
    name: str
    rule_type: str  # "dwell_time" | "limb_angle"
    # dwell_time fields
    keypoint_indices: list[int] | None = None
    dwell_seconds: float | None = None
    dwell_op: str | None = None  # "gt" | "lt"
    # limb_angle fields
    arm_side: str | None = None  # "left" | "right" | "both"
    angle_degrees: float | None = None
    angle_op: str | None = None  # "gt" | "lt"


class RuleUpdate(BaseModel):
    name: str | None = None
    keypoint_indices: list[int] | None = None
    dwell_seconds: float | None = None
    dwell_op: str | None = None
    arm_side: str | None = None
    angle_degrees: float | None = None
    angle_op: str | None = None


class RuleOut(BaseModel):
    id: int
    zone_id: int
    name: str
    rule_type: str
    is_enabled: bool
    keypoint_indices_json: str | None
    dwell_seconds: float | None
    dwell_op: str | None
    arm_side: str | None
    angle_degrees: float | None
    angle_op: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
