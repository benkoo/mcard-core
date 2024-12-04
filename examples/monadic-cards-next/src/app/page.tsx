import Image from "next/image";
import { CardTable } from './components/cards/CardTable'

export default function Home() {
  return (
    <div className="content-container">
      <div className="row">
        <div className="col">
          <h1 className="mb-4">MCard CRUD App</h1>
          <p className="lead">
            Welcome to the MCard CRUD App. This application allows you to manage your monadic cards.
          </p>
          <div className="btn-toolbar">
            <a href="/new" className="btn btn-primary me-2">
              <i className="fas fa-plus"></i> New Card
            </a>
          </div>
          <CardTable />
        </div>
      </div>
    </div>
  )
}
