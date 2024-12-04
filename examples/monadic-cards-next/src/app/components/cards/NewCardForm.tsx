'use client'

import { useState, useRef, ChangeEvent } from 'react'
import { useRouter } from 'next/navigation'

export function NewCardForm() {
  const router = useRouter()
  const [activeTab, setActiveTab] = useState<'text' | 'file'>('text')
  const [content, setContent] = useState('')
  const [type, setType] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const contentInputRef = useRef<HTMLTextAreaElement>(null)

  const handleTabChange = (tab: 'text' | 'file') => {
    setActiveTab(tab)
    setError(null)
    if (tab === 'text') {
      setFile(null)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    } else {
      setContent('')
    }
  }

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files
    if (files && files.length > 0) {
      setFile(files[0])
      setContent('')
      if (contentInputRef.current) {
        contentInputRef.current.disabled = true
      }
    }
  }

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    setError(null)
    setIsSubmitting(true)

    try {
      const formData = new FormData()
      
      if (activeTab === 'text') {
        if (!content.trim()) {
          throw new Error('Please enter content')
        }
        formData.append('content', content)
      } else {
        if (!file) {
          throw new Error('Please select a file')
        }
        formData.append('file', file)
      }

      if (type) {
        formData.append('type', type)
      }

      const response = await fetch('/api/cards', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error('Failed to create card')
      }

      router.push('/')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="card">
      <div className="card-header">
        <ul className="nav nav-tabs card-header-tabs" role="tablist">
          <li className="nav-item" role="presentation">
            <button
              className={`nav-link ${activeTab === 'text' ? 'active' : ''}`}
              onClick={() => handleTabChange('text')}
              type="button"
              role="tab"
            >
              Text Input
            </button>
          </li>
          <li className="nav-item" role="presentation">
            <button
              className={`nav-link ${activeTab === 'file' ? 'active' : ''}`}
              onClick={() => handleTabChange('file')}
              type="button"
              role="tab"
            >
              File Upload
            </button>
          </li>
        </ul>
      </div>
      <div className="card-body">
        <form onSubmit={handleSubmit} encType="multipart/form-data">
          <div className="tab-content">
            <div className={`tab-pane fade ${activeTab === 'text' ? 'show active' : ''}`}>
              <div className="mb-3">
                <label htmlFor="content" className="form-label">
                  Content
                </label>
                <textarea
                  ref={contentInputRef}
                  className="form-control"
                  id="content"
                  rows={5}
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  disabled={activeTab === 'file'}
                />
              </div>
            </div>
            <div className={`tab-pane fade ${activeTab === 'file' ? 'show active' : ''}`}>
              <div className="mb-3">
                <label htmlFor="file" className="form-label">
                  File
                </label>
                <input
                  ref={fileInputRef}
                  type="file"
                  className="form-control"
                  id="file"
                  onChange={handleFileChange}
                  disabled={activeTab === 'text'}
                />
              </div>
            </div>
          </div>

          <div className="mb-3">
            <label htmlFor="type" className="form-label">
              Type
            </label>
            <input
              type="text"
              className="form-control"
              id="type"
              value={type}
              onChange={(e) => setType(e.target.value)}
              placeholder="Optional: Specify card type"
            />
          </div>

          {error && <div className="alert alert-danger">{error}</div>}

          <div className="d-flex justify-content-between">
            <button
              type="submit"
              className="btn btn-primary"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Creating...' : 'Create Card'}
            </button>
            <a href="/" className="btn btn-secondary">
              Cancel
            </a>
          </div>
        </form>
      </div>
    </div>
  )
}
