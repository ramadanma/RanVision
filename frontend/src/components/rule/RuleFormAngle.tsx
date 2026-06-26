import { Button, Form, Input, InputNumber, Radio, Select, message } from 'antd'
import { useTranslation } from 'react-i18next'
import { createRule } from '../../api/rules'
import type { Rule } from '../../api/types'

interface Props {
  zoneId: number
  onCreated: (rule: Rule) => void
  onClose: () => void
}

export default function RuleFormAngle({ zoneId, onCreated, onClose }: Props) {
  const { t } = useTranslation()
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
      <Form.Item name="arm_side" label={t('rules.arm_side')} rules={[{ required: true }]} initialValue="both">
        <Radio.Group
          options={[
            { label: t('rules.left'), value: 'left' },
            { label: t('rules.right'), value: 'right' },
            { label: t('rules.both'), value: 'both' },
          ]}
        />
      </Form.Item>
      <Form.Item label={t('rules.angle_cond')} required style={{ marginBottom: 0 }}>
        <Form.Item name="angle_op" style={{ display: 'inline-block', width: 120 }} initialValue="gt">
          <Select options={[{ label: t('rules.gt'), value: 'gt' }, { label: t('rules.lt'), value: 'lt' }]} />
        </Form.Item>
        <Form.Item name="angle_degrees" style={{ display: 'inline-block', marginLeft: 8, width: 140 }} rules={[{ required: true }]}>
          <InputNumber min={0} max={180} step={1} addonAfter={t('rules.degrees')} style={{ width: '100%' }} />
        </Form.Item>
      </Form.Item>
      <Button type="primary" htmlType="submit" block style={{ marginTop: 8 }}>{t('rules.create')}</Button>
    </Form>
  )
}
