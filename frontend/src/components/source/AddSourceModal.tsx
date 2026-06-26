import { InboxOutlined } from '@ant-design/icons'
import { Form, Input, InputNumber, Modal, Radio, Upload, message } from 'antd'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { createSource, uploadVideo } from '../../api/sources'
import { useSourceStore } from '../../store/sourceStore'

interface Props {
  onClose: () => void
}

export default function AddSourceModal({ onClose }: Props) {
  const { t } = useTranslation()
  const [form] = Form.useForm()
  const [sourceType, setSourceType] = useState<'file' | 'ip_camera'>('ip_camera')
  const [uploading, setUploading] = useState(false)
  const { setSources, sources } = useSourceStore()

  const handleFinish = async (values: object) => {
    try {
      const { data: source } = await createSource(values)
      setSources([...sources, source])
      message.success(t('add_source.created'))
      onClose()
    } catch {
      message.error(t('add_source.create_failed'))
    }
  }

  const handleUpload = async (file: File) => {
    setUploading(true)
    try {
      const res = await uploadVideo(file)
      form.setFieldValue('file_path', res.data.file_path)
      message.success(t('add_source.file_uploaded'))
    } catch {
      message.error(t('add_source.upload_failed'))
    } finally {
      setUploading(false)
    }
    return false
  }

  return (
    <Modal title={t('add_source.title')} open onCancel={onClose} onOk={() => form.submit()} okText={t('add_source.btn_create')}>
      <Form
        form={form}
        layout="vertical"
        onFinish={handleFinish}
        initialValues={{ source_type: 'ip_camera', port: 554, transport: 'tcp' }}
      >
        <Form.Item name="name" label={t('add_source.name')} rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item name="source_type" label={t('add_source.type')}>
          <Radio.Group onChange={(e) => { setSourceType(e.target.value); form.setFieldValue('source_type', e.target.value) }}>
            <Radio value="ip_camera">{t('source.type_camera')}</Radio>
            <Radio value="file">{t('source.type_file')}</Radio>
          </Radio.Group>
        </Form.Item>

        {sourceType === 'ip_camera' ? (
          <>
            <Form.Item name="ip" label={t('add_source.ip')} rules={[{ required: true }]}>
              <Input placeholder="192.168.1.100" />
            </Form.Item>
            <Form.Item name="port" label={t('add_source.port')}>
              <InputNumber min={1} max={65535} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="cam_username" label={t('add_source.username')}>
              <Input />
            </Form.Item>
            <Form.Item name="cam_password" label={t('add_source.password')}>
              <Input.Password />
            </Form.Item>
            <Form.Item name="transport" label={t('add_source.transport')}>
              <Radio.Group>
                <Radio value="tcp">TCP</Radio>
                <Radio value="udp">UDP</Radio>
              </Radio.Group>
            </Form.Item>
          </>
        ) : (
          <>
            <Form.Item name="file_path" label={t('add_source.file_path')} rules={[{ required: true }]}>
              <Input placeholder={t('add_source.file_path_placeholder')} readOnly />
            </Form.Item>
            <Upload.Dragger
              beforeUpload={handleUpload}
              showUploadList={false}
              accept="video/*"
              disabled={uploading}
            >
              <p className="ant-upload-drag-icon"><InboxOutlined /></p>
              <p>{t('add_source.upload_hint')}</p>
            </Upload.Dragger>
          </>
        )}
      </Form>
    </Modal>
  )
}
