'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

export function NavBar() {
  const pathname = usePathname()

  const isActive = (path: string) => {
    if (path === '/' && pathname === '/') return true
    if (path !== '/' && pathname.startsWith(path)) return true
    return false
  }

  return (
    <nav className="navbar navbar-expand-lg navbar-light bg-light fixed-top">
      <div className="container">
        <Link href="/" className="navbar-brand">
          MCard CRUD App
        </Link>
        <button
          className="navbar-toggler"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#navbarNav"
          aria-controls="navbarNav"
          aria-expanded="false"
          aria-label="Toggle navigation"
        >
          <span className="navbar-toggler-icon"></span>
        </button>
        <div className="collapse navbar-collapse" id="navbarNav">
          <ul className="navbar-nav me-auto">
            <li className="nav-item">
              <Link
                href="/"
                className={`nav-link ${isActive('/') ? 'active' : ''}`}
              >
                <i className="bi bi-table me-1"></i>
                Table View
              </Link>
            </li>
            <li className="nav-item">
              <Link
                href="/grid"
                className={`nav-link ${isActive('/grid') ? 'active' : ''}`}
              >
                <i className="bi bi-grid-3x3-gap me-1"></i>
                Grid View
              </Link>
            </li>
            <li className="nav-item">
              <Link
                href="/new"
                className={`nav-link ${isActive('/new') ? 'active' : ''}`}
              >
                <i className="bi bi-plus-circle me-1"></i>
                New Card
              </Link>
            </li>
          </ul>
          <ul className="navbar-nav">
            <li className="nav-item">
              <a
                href="https://github.com/codeium/mcard"
                className="nav-link"
                target="_blank"
                rel="noopener noreferrer"
              >
                <i className="bi bi-github me-1"></i>
                GitHub
              </a>
            </li>
          </ul>
        </div>
      </div>
    </nav>
  )
}
