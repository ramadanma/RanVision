import { DeleteOutlined, InboxOutlined, ReloadOutlined } from '@ant-design/icons'
import {
  Button, Col, Form, Input, Modal, Popconfirm, Row, Table, Tag, Tooltip, Typography, Upload, message
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
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
  const { t, i18n } = useTranslation()
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
      message.success(t('faces.reextract_ok'))
    } catch {
      message.error(t('faces.reextract_fail'))
    } finally {
      setReextracting(null)
    }
  }

  const handleUpload = async (values: { person_name: string }) => {
    if (!pendingFile) { message.warning(t('faces.select_image')); return }
    setUploading(true)
    try {
      const res = await uploadFace(values.person_name, pendingFile)
      setFaces((prev) => [...prev, res.data])
      setShowUpload(false)
      form.resetFields()
      setPendingFile(null)
      message.success(t('faces.upload_ok'))
    } catch {
      message.error(t('faces.upload_fail'))
    } finally {
      setUploading(false)
    }
  }

  const locale = i18n.language === 'zh' ? 'zh-CN' : 'en-US'

  const columns: ColumnsType<Face> = [
    { title: t('common.id'), dataIndex: 'id', width: 60 },
    {
      title: t('faces.col_photo'),
      dataIndex: 'id',
      width: 72,
      render: (id: number) => <FacePhoto faceId={id} />,
    },
    { title: t('faces.col_name'), dataIndex: 'person_name' },
    {
      title: t('faces.col_status'),
      dataIndex: 'embedding_path',
      width: 120,
      render: (v: string | null) =>
        v ? (
          <Tag color="green">{t('faces.extracted')}</Tag>
        ) : (
          <Tooltip title={t('faces.not_extracted_tip')}>
            <Tag color="red" style={{ cursor: 'help' }}>{t('faces.not_extracted')}</Tag>
          </Tooltip>
        ),
    },
    {
      title: t('faces.col_created'),
      dataIndex: 'created_at',
      render: (v: string) => new Date(v).toLocaleString(locale),
    },
    {
      title: t('faces.col_actions'),
      width: 120,
      render: (_, record) => (
        <div style={{ display: 'flex', gap: 8 }}>
          {!record.embedding_path && (
            <Tooltip title={t('faces.reextract_tip')}>
              <Button
                size="small"
                icon={<ReloadOutlined />}
                loading={reextracting === record.id}
                onClick={() => handleReextract(record.id)}
              />
            </Tooltip>
          )}
          <Popconfirm title={t('faces.confirm_delete')} onConfirm={() => handleDelete(record.id)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </div>
      ),
    },
  ]

  return (
    <div>
      <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
        <Col><Title level={4} style={{ margin: 0 }}>{t('faces.title')}</Title></Col>
        <Col><Button type="primary" onClick={() => setShowUpload(true)}>{t('faces.upload')}</Button></Col>
      </Row>

      <Table
        rowKey="id"
        columns={columns}
        dataSource={faces}
        loading={loading}
        pagination={{ pageSize: 20 }}
      />

      <Modal title={t('faces.modal_title')} open={showUpload} onCancel={() => setShowUpload(false)} footer={null}>
        <Form form={form} layout="vertical" onFinish={handleUpload}>
          <Form.Item name="person_name" label={t('faces.col_name')} rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Upload.Dragger
            beforeUpload={(file) => { setPendingFile(file); return false }}
            showUploadList={pendingFile ? [{ name: pendingFile.name }] as unknown as true : false}
            accept="image/*"
            maxCount={1}
          >
            <p className="ant-upload-drag-icon"><InboxOutlined /></p>
            <p>{t('faces.upload_hint')}</p>
          </Upload.Dragger>
          <Button type="primary" htmlType="submit" block style={{ marginTop: 12 }} loading={uploading}>
            {t('faces.btn_upload')}
          </Button>
        </Form>
      </Modal>
    </div>
  )
}
