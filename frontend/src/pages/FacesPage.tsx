import { DeleteOutlined, InboxOutlined, ReloadOutlined } from '@ant-design/icons'
import {
  Button, Col, Form, Input, Modal, Popconfirm, Row, Table, Tag, Tooltip, Typography, Upload, message
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useEffect, useRef, useState } from 'react'
import client from '../api/client'
import { deleteFace, listFaces, reextractFace, uploadFace } from '../api/faces'
import type { Face } from '../api/types'

function FacePhoto({ faceId }: { faceId: number }) {
  const [url, setUrl] = useState<string | null>(null)
  const blobRef = useRef<string | null>(null)
  useEffect(() => {
    client.get(`/faces/${faceId}/photo`, { responseType: 'blob' })
      .then((r) => {
        const u = URL.createObjectURL(r.data)
        blobRef.current = u
        setUrl(u)
      })
      .catch(() => {})
    return () => { if (blobRef.current) URL.revokeObjectURL(blobRef.current) }
  }, [faceId])
  return url
    ? <img src={url} alt="" style={{ width: 48, height: 48, objectFit: 'cover', borderRadius: 4 }} />
    : <span style={{ color: '#999' }}>—</span>
}

const { Title } = Typography

export default function FacesPage() {
  const [faces, setFaces] = useState<Face[]>([])
  const [loading, setLoading] = useState(true)
  const [showUpload, setShowUpload] = useState(false)
  const [form] = Form.useForm()
  const [uploading, setUploading] = useState(false)
  const [pendingFile, setPendingFile] = useState<File | null>(null)
  const [reextracting, setReextracting] = useState<number | null>(null)

  useEffect(() => {
    listFaces()
      .then((r) => setFaces(r.data))
      .finally(() => setLoading(false))
  }, [])

  const handleDelete = async (id: number) => {
    await deleteFace(id)
    setFaces((prev) => prev.filter((f) => f.id !== id))
  }

  const handleReextract = async (id: number) => {
    setReextracting(id)
    try {
      const res = await reextractFace(id)
      setFaces((prev) => prev.map((f) => (f.id === id ? res.data : f)))
      message.success('人脸特征提取成功')
    } catch {
      message.error('未检测到人脸，请换一张清晰的正脸照片')
    } finally {
      setReextracting(null)
    }
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
    {
      title: '照片',
      dataIndex: 'id',
      width: 72,
      render: (id: number) => <FacePhoto faceId={id} />,
    },
    { title: '人员姓名', dataIndex: 'person_name' },
    {
      title: '特征状态',
      dataIndex: 'embedding_path',
      width: 120,
      render: (v: string | null) =>
        v ? (
          <Tag color="green">已提取</Tag>
        ) : (
          <Tooltip title="人脸特征未提取，识别将不生效。请点击重新提取，或换一张清晰正脸照重新上传。">
            <Tag color="red" style={{ cursor: 'help' }}>未提取</Tag>
          </Tooltip>
        ),
    },
    {
      title: '上传时间',
      dataIndex: 'created_at',
      render: (v: string) => new Date(v).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      width: 120,
      render: (_, record) => (
        <div style={{ display: 'flex', gap: 8 }}>
          {!record.embedding_path && (
            <Tooltip title="重新提取人脸特征">
              <Button
                size="small"
                icon={<ReloadOutlined />}
                loading={reextracting === record.id}
                onClick={() => handleReextract(record.id)}
              />
            </Tooltip>
          )}
          <Popconfirm title="确认删除该人脸？" onConfirm={() => handleDelete(record.id)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </div>
      ),
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
