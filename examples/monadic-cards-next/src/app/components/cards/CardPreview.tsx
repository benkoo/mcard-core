'use client'

import { Card } from '@/lib/mcard.service'
import Image from 'next/image'

interface CardPreviewProps {
  card: Card
}

export function CardPreview({ card }: CardPreviewProps) {
  const renderPreview = () => {
    const isImage = card.content_type.startsWith('image/')
    const isPDF = card.content_type === 'application/pdf'
    const isText = !isImage && !isPDF

    if (isImage) {
      return (
        <div className="preview-container">
          <Image
            src={`/api/cards/${card.hash}/content`}
            alt="Card preview"
            width={65}
            height={65}
            style={{ objectFit: 'contain' }}
          />
        </div>
      )
    }

    if (isPDF) {
      return (
        <div className="preview-container">
          <i className="fas fa-file-pdf fa-2x text-danger"></i>
        </div>
      )
    }

    if (isText) {
      return (
        <div className="preview-container">
          <div className="text-preview">
            {card.content.length > 100 ? `${card.content.substring(0, 100)}...` : card.content}
          </div>
        </div>
      )
    }

    return (
      <div className="preview-container">
        <i className="fas fa-file fa-2x text-secondary"></i>
      </div>
    )
  }

  return (
    <div className="preview-cell">
      <style jsx>{`
        .preview-cell {
          width: 70px;
          max-width: 100px;
          height: 75px !important;
          vertical-align: middle !important;
        }
        
        .preview-container {
          height: 65px;
          display: flex;
          align-items: center;
          justify-content: center;
          overflow: hidden;
          background-color: #f8f9fa;
          border-radius: 4px;
          margin: 5px;
        }
        
        .preview-container img {
          max-height: 65px;
          max-width: 100%;
          object-fit: contain;
        }
        
        .text-preview {
          padding: 5px;
          width: 100%;
          overflow: hidden;
          max-height: 65px;
          font-size: 0.875rem;
          color: #495057;
        }
      `}</style>
      {renderPreview()}
    </div>
  )
}
