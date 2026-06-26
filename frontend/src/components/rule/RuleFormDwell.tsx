import { Button, Checkbox, Form, Input, InputNumber, Select, message } from 'antd'
import { useTranslation } from 'react-i18next'
import { createRule } from '../../api/rules'
import type { Rule } from '../../api/types'

interface Props {
  zoneId: number
  onCreated: (rule: Rule) => void
  onClose: () => void
}

export default function RuleFormDwell({ zoneId, onCreated, onClose }: Props) {
  const { t } = useTranslation()
  const [form] = Form.useForm()

  const KEYPOINTS = [
    { label: t('rules.kp_nose'), value: 0 },
    { label: t('rules.kp_left_shoulder'), value: 5 },
    { label: t('rules.kp_right_shoulder'), value: 6 },
    { label: t('rules.kp_left_elbow'), value: 7 },
    { label: t('rules.kp_right_elbow'), value: 8 },
    { label: t('rules.kp_left_wrist'), value: 9 },
    { label: t('rules.kp_right_wrist'), value: 10 },
    { label: t('rules.kp_left_hip'), value: 11 },
    { label: t('rules.kp_right_hip'), value: 12 },
    { label: t('rules.kp_left_knee'), value: 13 },
    { label: t('rules.kp_right_knee'), value: 14 },
    { label: t('rules.kp_left_ankle'), value: 15 },
    { label: t('rules.kp_right_ankle'), value: 16 },
  ]

  const handleFinish = async (values: {
    name: string
    keypoint_indices: number[]
    dwell_op: string
    dwell_seconds: number
  }) => {
    try {
      const res = await createRule({ ...values, zone_id: zoneId, rule_type: 'dwell_time' })
      onCreated(res.data)
      message.success(t('rules.created'))
      onClose()
    } catch {
      message.error(t('rules.create_failed'))
    }
  }

  return (
    <Form form={form} layout="vertical" onFinish={handleFinish}>
      <Form.Item name="name" label={t('rules.name')} rules={[{ required: true }]}>
        <Input />
      </Form.Item>
      <Form.Item name="keypoint_indices" label={t('rules.keypoints')} rules={[{ required: true }]}>
        <Checkbox.Group options={KEYPOINTS} style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }} />
      </Form.Item>
      <Form.Item label={t('rules.time_cond')} required style={{ marginBottom: 0 }}>
        <Form.Item name="dwell_op" style={{ display: 'inline-block', width: 120 }} initialValue="gt">
          <Select options={[{ label: t('rules.gt'), value: 'gt' }, { label: t('rules.lt'), value: 'lt' }]} />
        </Form.Item>
        <Form.Item name="dwell_seconds" style={{ display: 'inline-block', marginLeft: 8, width: 140 }} rules={[{ required: true }]}>
          <InputNumber min={0.1} step={0.1} precision={1} addonAfter={t('rules.seconds')} style={{ width: '100%' }} />
        </Form.Item>
      </Form.Item>
      <Button type="primary" htmlType="submit" block style={{ marginTop: 8 }}>{t('rules.create')}</Button>
    </Form>
  )
}
