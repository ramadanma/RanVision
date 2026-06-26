import { Modal, Segmented } from 'antd'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { Rule } from '../../api/types'
import RuleFormDwell from './RuleFormDwell'
import RuleFormAngle from './RuleFormAngle'

interface Props {
  zoneId: number
  onClose: () => void
  onCreated: (rule: Rule) => void
}

export default function RuleFormModal({ zoneId, onClose, onCreated }: Props) {
  const { t } = useTranslation()
  const [ruleType, setRuleType] = useState<'dwell_time' | 'limb_angle'>('dwell_time')

  return (
    <Modal title={t('rules.modal_title')} open onCancel={onClose} footer={null} width={520}>
      <Segmented
        block
        options={[
          { label: t('rules.type_dwell'), value: 'dwell_time' },
          { label: t('rules.type_limb'), value: 'limb_angle' },
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
