'use client'

import { Card } from '@/lib/mcard.service'
import { useEffect, useState } from 'react'
import { CardRow } from './CardRow'

export function CardTable() {
  const [cards, setCards] = useState<Card[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchCards = async () => {
      try {
        const response = await fetch('/api/cards')
        if (!response.ok) {
          throw new Error('Failed to fetch cards')
        }
        const data = await response.json()
        setCards(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred')
      } finally {
        setLoading(false)
      }
    }

    fetchCards()
  }, [])

  if (loading) {
    return <div className="text-center py-4">Loading cards...</div>
  }

  if (error) {
    return <div className="alert alert-danger">{error}</div>
  }

  return (
    <div className="table-responsive mt-4">
      <table className="table table-hover align-middle">
        <thead>
          <tr>
            <th>Preview</th>
            <th>Type</th>
            <th>Hash</th>
            <th>g_time</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {cards.length > 0 ? (
            cards.map((card) => <CardRow key={card.hash} card={card} />)
          ) : (
            <tr>
              <td colSpan={5} className="text-center">
                No cards found
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}