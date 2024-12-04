'use client'

import Link from 'next/link'

interface GridControlsProps {
  rows: number
  cols: number
  onGridChange: (rows: number, cols: number) => void
}

export function GridControls({ rows, cols, onGridChange }: GridControlsProps) {
  return (
    <div className="d-flex align-items-center gap-3">
      <div className="d-flex align-items-center gap-2">
        <label htmlFor="grid_rows" className="form-label mb-0">
          Rows:
        </label>
        <select
          id="grid_rows"
          className="form-select form-select-sm"
          style={{ width: '70px' }}
          value={rows}
          onChange={(e) => onGridChange(Number(e.target.value), cols)}
        >
          {[2, 3, 4, 5].map((n) => (
            <option key={n} value={n}>
              {n}
            </option>
          ))}
        </select>

        <label htmlFor="grid_cols" className="form-label mb-0">
          Columns:
        </label>
        <select
          id="grid_cols"
          className="form-select form-select-sm"
          style={{ width: '70px' }}
          value={cols}
          onChange={(e) => onGridChange(rows, Number(e.target.value))}
        >
          {[2, 3, 4, 5].map((n) => (
            <option key={n} value={n}>
              {n}
            </option>
          ))}
        </select>
      </div>

      <div className="btn-group">
        <Link href="/" className="btn btn-outline-primary">
          <i className="bi bi-table me-1"></i>Table
        </Link>
        <Link href="/grid" className="btn btn-primary">
          <i className="bi bi-grid-3x3-gap me-1"></i>Grid
        </Link>
      </div>
      <Link href="/new" className="btn btn-success">
        New Card
      </Link>
    </div>
  )
}
