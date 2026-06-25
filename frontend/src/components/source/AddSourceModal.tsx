import { InboxOutlined } from '@ant-design/icons'
import { Form, Input, InputNumber, Modal, Radio, Upload, message } from 'antd'
import { useState } from 'react'
import { createSource, uploadVideo } from '../../api/sources'
import { useSourceStore } from '../../store/sourceStore'

interface Props {
  onClose: () => void
}

export default function AddSourceModal({ onClose }: Props) {
  const [form] = Form.useForm()
  const [sourceType, setSourceType] = useState<'file' | 'ip_camera'>('ip_camera')
  const [uploading, setUploading] = useState(false)
  const { setSources, sources } = useSourceStore()

  const handleFinish = async (values: object) => {
    try {
      const { data: source } = await createSource(values)
      setSources([...sources, source])
      message.success('视频源已创建')
      onClose()
    } catch {
      message.error('创建失败')
    }
  }

  const handleUpload = async (file: File) => {
    setUploading(true)
    try {
      const res = await uploadVideo(file)
      form.setFieldValue('file_path', res.data.file_path)
      message.success('文件已上传')
    } catch {
      message.error('上传失败')
    } finally {
      setUploading(false)
    }
    return false
  }

  return (
    <Modal title="添加视频源" open onCancel={onClose} onOk={() => form.submit()} okText="创建">
      <Form
        form={form}
        layout="vertical"
        onFinish={handleFinish}
        initialValues={{ source_type: 'ip_camera', port: 554, transport: 'tcp' }}
      >
        <Form.Item name="name" label="名称" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item name="source_type" label="类型">
          <Radio.Group onChange={(e) => { setSourceType(e.target.value); form.setFieldValue('source_type', e.target.value) }}>
            <Radio value="ip_camera">IP摄像头</Radio>
            <Radio value="file">视频文件</Radio>
          </Radio.Group>
        </Form.Item>

        {sourceType === 'ip_camera' ? (
          <>
            <Form.Item name="ip" label="IP地址" rules={[{ required: true }]}>
              <Input placeholder="192.168.1.100" />
            </Form.Item>
            <Form.Item name="port" label="端口">
              <InputNumber min={1} max={65535} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="cam_username" label="用户名">
              <Input />
            </Form.Item>
            <Form.Item name="cam_password" label="密码">
              <Input.Password />
            </Form.Item>
            <Form.Item name="transport" label="传输协议">
              <Radio.Group>
                <Radio value="tcp">TCP</Radio>
                <Radio value="udp">UDP</Radio>
              </Radio.Group>
            </Form.Item>
          </>
        ) : (
          <>
            <Form.Item name="file_path" label="视频文件路径" rules={[{ required: true }]}>
              <Input placeholder="上传后自动填入" readOnly />
            </Form.Item>
            <Upload.Dragger
              beforeUpload={handleUpload}
              showUploadList={false}
              accept="video/*"
              disabled={uploading}
            >
              <p className="ant-upload-drag-icon"><InboxOutlined /></p>
              <p>点击或拖拽上传视频文件</p>
            </Upload.Dragger>
          </>
        )}
      </Form>
    </Modal>
  )
}
