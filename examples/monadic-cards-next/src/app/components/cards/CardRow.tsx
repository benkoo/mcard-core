'use client'

import { Card } from '@/lib/mcard.service'
import { CardActions } from './CardActions'
import { CardPreview } from './CardPreview'

interface CardRowProps {
  card: Card
}

export function CardRow({ card }: CardRowProps) {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <tr>
      <td className="preview-cell">
        <CardPreview card={card} />
      </td>
      <td className="content-type">{card.content_type}</td>
      <td className="hash-cell">
        <code>{card.hash}</code>
      </td>
      <td>{formatDate(card.created_at)}</td>
      <td>
        <CardActions card={card} />
      </td>
    </tr>
  )
}
