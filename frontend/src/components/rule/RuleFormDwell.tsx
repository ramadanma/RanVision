import { Button, Checkbox, Form, Input, InputNumber, Select, message } from 'antd'
import { createRule } from '../../api/rules'
import type { Rule } from '../../api/types'

const KEYPOINTS = [
  { label: '鼻子', value: 0 },
  { label: '左肩', value: 5 },
  { label: '右肩', value: 6 },
  { label: '左肘', value: 7 },
  { label: '右肘', value: 8 },
  { label: '左腕', value: 9 },
  { label: '右腕', value: 10 },
  { label: '左髋', value: 11 },
  { label: '右髋', value: 12 },
  { label: '左膝', value: 13 },
  { label: '右膝', value: 14 },
  { label: '左踝', value: 15 },
  { label: '右踝', value: 16 },
]

interface Props {
  zoneId: number
  onCreated: (rule: Rule) => void
  onClose: () => void
}

export default function RuleFormDwell({ zoneId, onCreated, onClose }: Props) {
  const [form] = Form.useForm()

  const handleFinish = async (values: {
    name: string
    keypoint_indices: number[]
    dwell_op: string
    dwell_seconds: number
  }) => {
    try {
      const res = await createRule({ ...values, zone_id: zoneId, rule_type: 'dwell_time' })
      onCreated(res.data)
      message.success('规则已创建')
      onClose()
    } catch {
      message.error('创建失败')
    }
  }

  return (
    <Form form={form} layout="vertical" onFinish={handleFinish}>
      <Form.Item name="name" label="规则名称" rules={[{ required: true }]}>
        <Input />
      </Form.Item>
      <Form.Item name="keypoint_indices" label="检测关键点（可多选）" rules={[{ required: true }]}>
        <Checkbox.Group options={KEYPOINTS} style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }} />
      </Form.Item>
      <Form.Item label="时间条件" required style={{ marginBottom: 0 }}>
        <Form.Item name="dwell_op" style={{ display: 'inline-block', width: 120 }} initialValue="gt">
          <Select options={[{ label: '超过', value: 'gt' }, { label: '小于', value: 'lt' }]} />
        </Form.Item>
        <Form.Item name="dwell_seconds" style={{ display: 'inline-block', marginLeft: 8, width: 140 }} rules={[{ required: true }]}>
          <InputNumber min={0.1} step={0.1} precision={1} addonAfter="秒" style={{ width: '100%' }} />
        </Form.Item>
      </Form.Item>
      <Button type="primary" htmlType="submit" block style={{ marginTop: 8 }}>创建规则</Button>
    </Form>
  )
}
