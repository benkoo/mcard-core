'use client'

import { useState, useEffect } from 'react'
import { Card } from '@/lib/mcard.service'
import { CardGrid } from '../components/cards/CardGrid'
import { GridControls } from '../components/cards/GridControls'

export default function GridPage() {
  const [cards, setCards] = useState<Card[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [rows, setRows] = useState(3)
  const [cols, setCols] = useState(3)
  const [page, setPage] = useState(1)
  const [totalItems, setTotalItems] = useState(0)

  useEffect(() => {
    const fetchCards = async () => {
      try {
        setLoading(true)
        setError(null)
        
        const response = await fetch(`/api/cards?page=${page}&rows=${rows}&cols=${cols}`)
        const data = await response.json()
        
        if (!response.ok) {
          throw new Error(data.error || 'Failed to fetch cards')
        }
        
        setCards(data.cards || [])
        setTotalItems(data.total || 0)
      } catch (err) {
        console.error('Error fetching cards:', err)
        setError(err instanceof Error ? err.message : 'An error occurred while fetching cards')
        setCards([])
      } finally {
        setLoading(false)
      }
    }

    fetchCards()
  }, [page, rows, cols])

  const handleGridChange = (newRows: number, newCols: number) => {
    setRows(newRows)
    setCols(newCols)
    setPage(1)
  }

  const handlePageChange = (newPage: number) => {
    setPage(newPage)
  }

  if (loading) {
    return <div className="text-center py-4">Loading cards...</div>
  }

  if (error) {
    return <div className="alert alert-danger">{error}</div>
  }

  return (
    <div className="container mt-4">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h1>Grid View</h1>
        <GridControls
          rows={rows}
          cols={cols}
          onGridChange={handleGridChange}
        />
      </div>

      <CardGrid
        cards={cards}
        cols={cols}
      />

      {Math.ceil(totalItems / (rows * cols)) > 1 && (
        <nav aria-label="Page navigation" className="mt-4">
          <div className="d-flex justify-content-between align-items-center">
            <div className="text-muted">
              Showing {cards.length} of {totalItems} items
            </div>
            <ul className="pagination mb-0">
              <li className={`page-item ${page === 1 ? 'disabled' : ''}`}>
                <button
                  className="page-link"
                  onClick={() => handlePageChange(page - 1)}
                  disabled={page === 1}
                >
                  &laquo;
                </button>
              </li>
              {Array.from(
                { length: Math.ceil(totalItems / (rows * cols)) },
                (_, i) => i + 1
              ).map((p) => (
                <li
                  key={p}
                  className={`page-item ${p === page ? 'active' : ''}`}
                >
                  <button
                    className="page-link"
                    onClick={() => handlePageChange(p)}
                  >
                    {p}
                  </button>
                </li>
              ))}
              <li
                className={`page-item ${
                  page === Math.ceil(totalItems / (rows * cols))
                    ? 'disabled'
                    : ''
                }`}
              >
                <button
                  className="page-link"
                  onClick={() => handlePageChange(page + 1)}
                  disabled={page === Math.ceil(totalItems / (rows * cols))}
                >
                  &raquo;
                </button>
              </li>
            </ul>
          </div>
        </nav>
      )}
    </div>
  )
}
