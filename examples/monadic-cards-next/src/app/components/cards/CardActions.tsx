'use client'

import { Card } from '@/lib/mcard.service'
import Link from 'next/link'
import { useRouter } from 'next/navigation'

interface CardActionsProps {
  card: Card
}

export function CardActions({ card }: CardActionsProps) {
  const router = useRouter()

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this card? This action cannot be undone.')) {
      return
    }

    try {
      const response = await fetch(`/api/cards/${card.hash}`, {
        method: 'DELETE',
      })

      if (!response.ok) {
        throw new Error('Failed to delete card')
      }

      router.refresh()
    } catch (error) {
      console.error('Error deleting card:', error)
      alert('Failed to delete card. Please try again.')
    }
  }

  return (
    <div className="btn-group" role="group">
      <Link href={`/cards/${card.hash}`} className="btn btn-primary btn-sm">
        View
      </Link>
      <button onClick={handleDelete} className="btn btn-danger btn-sm">
        Delete
      </button>
    </div>
  )
}
