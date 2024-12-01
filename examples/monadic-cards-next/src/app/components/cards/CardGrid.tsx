'use client'

import { Card } from '@/lib/mcard.service'
import Image from 'next/image'
import Link from 'next/link'

interface CardGridProps {
  cards: Card[]
  cols: number
}

export function CardGrid({ cards, cols }: CardGridProps) {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const isImage = (contentType: string) => contentType.startsWith('image/')
  const isBinary = (contentType: string) =>
    !contentType.startsWith('text/') && !isImage(contentType)

  return (
    <div className="row g-4">
      {cards.map((card) => (
        <div key={card.hash} className={`col-${12 / cols}`}>
          <div className="card h-100">
            <div className="card-header d-flex align-items-center gap-2">
              {isImage(card.content_type) ? (
                <i className="bi bi-image" title="Image"></i>
              ) : isBinary(card.content_type) ? (
                <i className="bi bi-file-binary" title="Binary"></i>
              ) : (
                <i className="bi bi-file-text" title="Text"></i>
              )}
              <small className="text-muted">
                {formatDate(card.created_at)}
              </small>
            </div>
            <div className="card-body">
              {isImage(card.content_type) ? (
                <div className="text-center mb-2">
                  <Image
                    src={`/api/cards/${card.hash}/content`}
                    alt="Card preview"
                    width={150}
                    height={150}
                    style={{
                      maxHeight: '150px',
                      width: 'auto',
                      objectFit: 'contain',
                    }}
                  />
                </div>
              ) : isBinary(card.content_type) ? (
                <div className="text-center text-muted">
                  Binary content
                  <br />({card.content.length} bytes)
                </div>
              ) : (
                <div
                  className="text-preview"
                  style={{
                    height: '150px',
                    overflowY: 'auto',
                    fontSize: '0.9em',
                  }}
                >
                  {card.content.length > 300
                    ? `${card.content.substring(0, 300)}...`
                    : card.content}
                </div>
              )}
            </div>
            <div className="card-footer bg-transparent">
              <div className="btn-group w-100">
                <Link
                  href={`/cards/${card.hash}`}
                  className="btn btn-sm btn-outline-primary"
                >
                  View
                </Link>
                <Link
                  href={`/api/cards/${card.hash}/download`}
                  className="btn btn-sm btn-outline-secondary"
                >
                  Download
                </Link>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
