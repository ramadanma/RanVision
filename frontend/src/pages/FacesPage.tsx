import { DeleteOutlined, InboxOutlined } from '@ant-design/icons'
import {
  Button, Col, Form, Input, Modal, Popconfirm, Row, Spin, Table, Typography, Upload, message
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useEffect, useState } from 'react'
import { deleteFace, listFaces, uploadFace } from '../api/faces'
import type { Face } from '../api/types'

const { Title } = Typography

export default function FacesPage() {
  const [faces, setFaces] = useState<Face[]>([])
  const [loading, setLoading] = useState(true)
  const [showUpload, setShowUpload] = useState(false)
  const [form] = Form.useForm()
  const [uploading, setUploading] = useState(false)
  const [pendingFile, setPendingFile] = useState<File | null>(null)

  useEffect(() => {
    listFaces()
      .then((r) => setFaces(r.data))
      .finally(() => setLoading(false))
  }, [])

  const handleDelete = async (id: number) => {
    await deleteFace(id)
    setFaces((prev) => prev.filter((f) => f.id !== id))
  }

  const handleUpload = async (values: { person_name: string }) => {
    if (!pendingFile) { message.warning('请先选择图片'); return }
    setUploading(true)
    try {
      const res = await uploadFace(values.person_name, pendingFile)
      setFaces((prev) => [...prev, res.data])
      setShowUpload(false)
      form.resetFields()
      setPendingFile(null)
      message.success('上传成功')
    } catch {
      message.error('上传失败')
    } finally {
      setUploading(false)
    }
  }

  const columns: ColumnsType<Face> = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    { title: '人员姓名', dataIndex: 'person_name' },
    {
      title: '上传时间',
      dataIndex: 'created_at',
      render: (v: string) => new Date(v).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      render: (_, record) => (
        <Popconfirm title="确认删除该人脸？" onConfirm={() => handleDelete(record.id)}>
          <Button size="small" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
      width: 80,
    },
  ]

  return (
    <div>
      <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
        <Col><Title level={4} style={{ margin: 0 }}>人脸库</Title></Col>
        <Col><Button type="primary" onClick={() => setShowUpload(true)}>上传人脸</Button></Col>
      </Row>

      <Table
        rowKey="id"
        columns={columns}
        dataSource={faces}
        loading={loading}
        pagination={{ pageSize: 20 }}
      />

      <Modal title="上传人脸照片" open={showUpload} onCancel={() => setShowUpload(false)} footer={null}>
        <Form form={form} layout="vertical" onFinish={handleUpload}>
          <Form.Item name="person_name" label="人员姓名" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Upload.Dragger
            beforeUpload={(file) => { setPendingFile(file); return false }}
            showUploadList={pendingFile ? [{ name: pendingFile.name }] as unknown as true : false}
            accept="image/*"
            maxCount={1}
          >
            <p className="ant-upload-drag-icon"><InboxOutlined /></p>
            <p>点击或拖拽上传人脸照片</p>
          </Upload.Dragger>
          <Button type="primary" htmlType="submit" block style={{ marginTop: 12 }} loading={uploading}>
            上传
          </Button>
        </Form>
      </Modal>
    </div>
  )
}
