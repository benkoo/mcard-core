import { NewCardForm } from '../components/cards/NewCardForm'

export default function NewCard() {
  return (
    <div className="content-container">
      <div className="row">
        <div className="col">
          <h1 className="mb-4">New Card</h1>
          <p className="lead">Create a new monadic card.</p>
          <div className="btn-toolbar">
            <a href="/" className="btn btn-secondary me-2">
              <i className="fas fa-arrow-left"></i> Back to List
            </a>
          </div>
          <NewCardForm />
        </div>
      </div>
    </div>
  )
}