import { DeleteOutlined, PlusOutlined } from '@ant-design/icons'
import { Button, Collapse, Empty, List, Popconfirm, Space, Tag, Typography, message } from 'antd'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { deleteZone } from '../../api/zones'
import { listRules } from '../../api/rules'
import type { Rule, Zone } from '../../api/types'
import RuleFormModal from '../rule/RuleFormModal'

const { Text } = Typography

interface Props {
  zones: Zone[]
  onZoneDeleted: (id: number) => void
}

export default function ZoneList({ zones, onZoneDeleted }: Props) {
  const { t } = useTranslation()
  const [rulesMap, setRulesMap] = useState<Record<number, Rule[]>>({})
  const [addingRuleZoneId, setAddingRuleZoneId] = useState<number | null>(null)

  const handleOpen = async (zoneId: number) => {
    if (!rulesMap[zoneId]) {
      const res = await listRules(zoneId)
      setRulesMap((prev) => ({ ...prev, [zoneId]: res.data }))
    }
  }

  const handleDeleteZone = async (id: number) => {
    await deleteZone(id)
    onZoneDeleted(id)
    message.success(t('zones.deleted'))
  }

  const handleRuleAdded = (zoneId: number, rule: Rule) => {
    setRulesMap((prev) => ({ ...prev, [zoneId]: [...(prev[zoneId] || []), rule] }))
  }

  if (zones.length === 0) return <Empty description={t('zones.empty')} />

  const items = zones.map((zone) => ({
    key: zone.id,
    label: (
      <Space>
        <Text strong>{zone.name}</Text>
        <Tag>{JSON.parse(zone.polygon_json).length} {t('zones.points')}</Tag>
        <Popconfirm title={t('zones.confirm_delete')} onConfirm={() => handleDeleteZone(zone.id)}>
          <Button size="small" danger icon={<DeleteOutlined />} onClick={(e) => e.stopPropagation()} />
        </Popconfirm>
      </Space>
    ),
    children: (
      <div>
        <List
          size="small"
          dataSource={rulesMap[zone.id] || []}
          renderItem={(rule) => (
            <List.Item>
              <Space>
                <Tag color={rule.is_enabled ? 'green' : 'default'}>{rule.is_enabled ? t('zones.enabled') : t('zones.disabled')}</Tag>
                <Tag color="blue">{rule.rule_type === 'dwell_time' ? t('zones.rule_dwell') : t('zones.rule_limb')}</Tag>
                <Text>{rule.name}</Text>
              </Space>
            </List.Item>
          )}
          locale={{ emptyText: t('zones.no_rules') }}
        />
        <Button
          size="small"
          icon={<PlusOutlined />}
          style={{ marginTop: 8 }}
          onClick={() => setAddingRuleZoneId(zone.id)}
        >
          {t('zones.add_rule')}
        </Button>
      </div>
    ),
  }))

  return (
    <>
      <Collapse items={items} onChange={(keys) => keys.forEach((k) => handleOpen(Number(k)))} />
      {addingRuleZoneId !== null && (
        <RuleFormModal
          zoneId={addingRuleZoneId}
          onClose={() => setAddingRuleZoneId(null)}
          onCreated={(rule) => handleRuleAdded(addingRuleZoneId, rule)}
        />
      )}
    </>
  )
}
