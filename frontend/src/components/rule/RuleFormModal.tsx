import { Modal, Segmented } from 'antd'
import { useState } from 'react'
import type { Rule } from '../../api/types'
import RuleFormDwell from './RuleFormDwell'
import RuleFormAngle from './RuleFormAngle'

interface Props {
  zoneId: number
  onClose: () => void
  onCreated: (rule: Rule) => void
}

export default function RuleFormModal({ zoneId, onClose, onCreated }: Props) {
  const [ruleType, setRuleType] = useState<'dwell_time' | 'limb_angle'>('dwell_time')

  return (
    <Modal title="添加检测规则" open onCancel={onClose} footer={null} width={520}>
      <Segmented
        block
        options={[
          { label: '停留时间', value: 'dwell_time' },
          { label: '肢体角度', value: 'limb_angle' },
        ]}
        value={ruleType}
        onChange={(v) => setRuleType(v as 'dwell_time' | 'limb_angle')}
        style={{ marginBottom: 16 }}
      />
      {ruleType === 'dwell_time' ? (
        <RuleFormDwell zoneId={zoneId} onCreated={onCreated} onClose={onClose} />
      ) : (
        <RuleFormAngle zoneId={zoneId} onCreated={onCreated} onClose={onClose} />
      )}
    </Modal>
  )
}
