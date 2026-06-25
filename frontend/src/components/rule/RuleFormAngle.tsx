import { Button, Form, Input, InputNumber, Radio, Select, message } from 'antd'
import { createRule } from '../../api/rules'
import type { Rule } from '../../api/types'

interface Props {
  zoneId: number
  onCreated: (rule: Rule) => void
  onClose: () => void
}

export default function RuleFormAngle({ zoneId, onCreated, onClose }: Props) {
  const [form] = Form.useForm()

  const handleFinish = async (values: {
    name: string
    arm_side: string
    angle_op: string
    angle_degrees: number
  }) => {
    try {
      const res = await createRule({ ...values, zone_id: zoneId, rule_type: 'limb_angle' })
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
      <Form.Item name="arm_side" label="手臂侧别" rules={[{ required: true }]} initialValue="both">
        <Radio.Group
          options={[
            { label: '左臂', value: 'left' },
            { label: '右臂', value: 'right' },
            { label: '双臂', value: 'both' },
          ]}
        />
      </Form.Item>
      <Form.Item label="角度条件" required style={{ marginBottom: 0 }}>
        <Form.Item name="angle_op" style={{ display: 'inline-block', width: 120 }} initialValue="gt">
          <Select options={[{ label: '超过', value: 'gt' }, { label: '小于', value: 'lt' }]} />
        </Form.Item>
        <Form.Item name="angle_degrees" style={{ display: 'inline-block', marginLeft: 8, width: 140 }} rules={[{ required: true }]}>
          <InputNumber min={0} max={180} step={1} addonAfter="度" style={{ width: '100%' }} />
        </Form.Item>
      </Form.Item>
      <Button type="primary" htmlType="submit" block style={{ marginTop: 8 }}>创建规则</Button>
    </Form>
  )
}
