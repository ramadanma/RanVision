export interface User {
  id: number
  username: string
  email: string
  is_active: boolean
}

export interface Source {
  id: number
  name: string
  source_type: 'file' | 'ip_camera'
  file_path: string | null
  ip: string | null
  port: number | null
  cam_username: string | null
  transport: string | null
  rtsp_url: string | null
  is_active: boolean
  show_overlay: boolean
  face_recognition_enabled: boolean
  face_check_front: boolean
  created_at: string
  updated_at: string
}

export interface Zone {
  id: number
  source_id: number
  name: string
  polygon_json: string
  npy_path: string | null
  created_at: string
  updated_at: string
}

export interface Rule {
  id: number
  zone_id: number
  name: string
  rule_type: 'dwell_time' | 'limb_angle'
  is_enabled: boolean
  keypoint_indices_json: string | null
  dwell_seconds: number | null
  dwell_op: 'gt' | 'lt' | null
  arm_side: 'left' | 'right' | 'both' | null
  angle_degrees: number | null
  angle_op: 'gt' | 'lt' | null
  created_at: string
  updated_at: string
}

export interface Face {
  id: number
  user_id: number
  person_name: string
  photo_path: string
  embedding_path: string | null
  created_at: string
}

export interface ReportConfig {
  id: number
  source_id: number
  name: string
  delivery_method: 'email' | 'webhook'
  destination: string
  photo_count: number
  include_person_name: boolean
  save_records: boolean
  is_enabled: boolean
  subject_template: string | null
  body_template: string | null
  trigger_rule_ids: number[]
  created_at: string
  updated_at: string
}

export interface TriggerRecord {
  id: number
  source_id: number
  rule_id: number | null
  zone_id: number | null
  person_name: string | null
  triggered_at: string
  rule_snapshot_json: string | null
  photos_sent: number
  alert_delivered: boolean
  delivery_error: string | null
}

export interface PaginatedRecords {
  total: number
  page: number
  size: number
  items: TriggerRecord[]
}
