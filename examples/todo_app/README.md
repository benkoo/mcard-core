# MCard Todo App

A demonstration of the [[Cubical Logic Model]] ([[CLM]]) principles applied to a practical todo application. This example showcases how MCard's content-addressable storage can be integrated with modern web technologies while maintaining theoretical soundness and practical utility.

## Abstract Specification (Design Intentions)

### Context
- A web-based todo application that demonstrates MCard's capabilities as a data operating system
- Integrates natural language content (todo descriptions) with computable data (states, timestamps)
- Leverages Flask's application context for thread-safe operations
- Implements clean separation of concerns following CLM principles

### Goals
- Create a responsive, user-friendly todo management interface
- Demonstrate MCard's content-addressable storage capabilities
- Showcase proper integration with web frameworks
- Provide a foundation for more complex workflow applications

### Success Criteria
- Thread-safe database operations
- Proper transaction management
- Comprehensive error handling
- Clean and responsive UI

## Concrete Implementation (Process Models)

### Technology Stack
- **Web Framework**: Flask for HTTP request handling
- **Storage System**: MCard for content-addressable storage
- **Database**: SQLite (via MCard) for persistent storage
- **Frontend**: Tailwind CSS for modern UI components

### Data Structure
Each todo item is stored as an MCard with the following structure:
```json
{
    "title": "Todo title",
    "description": "Optional description",
    "done": false,
   "clm": {
      "abstract_spec": {
         "context": "The spatial-temporal context of the todo.",
         "goals": ["A list of goal statements for the todo."],
         "success_criteria": {
            "verification": "Verification criteria for the todo.",
            "validation": "Validation criteria for the todo.",
            "performance": "Performance metrics for the todo."
            }
      },
      "concrete_impl": {
         "inputs": {},
         "activities": {},
         "outputs": {}
      },
      "realistic_expectations": {
         "practical_boundaries": {},
         "traces": ["A list of execution traces for the todo."],
         "external_feedback": {}
      }
   },
    "created_at": "timestamp",
    "updated_at": "timestamp"
}
```

### System Components
1. **Database Management**
   - Flask application context (`g`) for thread safety
   - Connection lifecycle management
   - Transaction handling with commit/rollback
   - Automatic initialization

2. **API Endpoints**
   - Create new todos
   - Mark todos as complete/incomplete
   - Delete todos
   - View timestamps and status

3. **Frontend Interface**
   - Responsive design
   - Real-time updates
   - Error feedback
   - Status indicators

## Realistic Expectations (Test Cases & Validation)

### Setup & Usage
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the application:
   ```bash
   flask --app app run --port 5002 --debug
   ```
3. Access the interface at `http://localhost:5002`

### Test Scenarios
1. **Basic Operations**
   - Create, read, update, delete todos
   - Mark todos as complete/incomplete
   - View creation/update timestamps

2. **Error Handling**
   - Invalid input validation
   - Database transaction failures
   - Concurrent access handling

3. **Performance Metrics**
   - Response time monitoring
   - Resource utilization
   - Transaction throughput

### Best Practices
- Clean code organization
- Comprehensive error handling
- Proper logging implementation
- Consistent coding style

## Future Extensions

### Enhanced Capabilities
- Natural language processing for todo categorization
- Workflow definitions using Petri Net formalism
- Integration with Content Analyzer
- Advanced task dependencies

### Statistical Analysis
- Task completion patterns
- Time estimation
- Priority optimization
- Resource allocation

### System Integration
- External API connectivity
- Notification systems
- Calendar integration
- Mobile applications

## Development

To run in development mode with debug logging:
```bash
flask --app app run --port 5002 --debug
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
