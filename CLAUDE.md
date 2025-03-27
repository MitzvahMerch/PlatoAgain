# Plato Project Documentation

## Overview
Plato is a custom t-shirt ordering system with AI assistance. It helps users select products, place designs, and complete orders through a conversational interface using Claude AI.

## Environment Setup
- Activate virtual environment: `cd backend && source venv/bin/activate`
- Install dependencies: `pip install -r backend/requirements.txt`

## Run Commands
- Start backend server: `cd backend && python app.py`
- Run frontend: Open `frontend/index.html` in browser
- Check server health: `curl http://localhost:5001/api/health`

## Project Architecture

### Backend Components
- **app.py**: Flask application initialization, CORS setup, PlatoBot instantiation
- **routes.py**: HTTP endpoint definitions for chat, product images, health checks
- **claude_client.py**: Claude API wrapper for AI conversation
- **plato_bot.py**: Central controller for processing messages and handling order stages
- **product_decision_tree.py**: Product selection system using Claude to match preferences
- **goal_identifier.py**: Determines user's conversational intent
- **conversation_manager.py**: Manages user conversations and state
- **order_state.py**: Tracks complete order lifecycle
- **firebase_service.py**: Handles data persistence and design uploads
- **paypal_service.py**: Handles PayPal invoice generation
- **utils.py**: General utility functions for parsing and formatting
- **size_utils.py**: Size extraction from customer messages
- **prompts.py**: Claude prompt templates for different conversation stages

### Frontend Components
- **script.js**: Core chat interface and backend communication
- **firebase-config.js**: Firebase initialization and file upload
- **designPlacer.js**: React component for design placement
- **placementModal.js**: Modal dialog for design placement

### Data Flow
1. User sends message through chat interface
2. Backend identifies conversation goal (product selection, design placement, etc.)
3. Specialized handler processes message based on goal
4. Claude AI generates appropriate response
5. Order state is updated and persisted
6. Response is sent back to user
7. For design uploads, Firebase Storage manages file persistence

## Code Style Guidelines

### Python Style
- Follow PEP 8 style guide
- Group imports: standard library, external packages, local modules
- Line length under 100 characters
- Use type hints for function parameters and returns
- Add docstrings for all functions and classes
- Log at appropriate levels (info, warning, error, exception)
- Use f-strings for string formatting

### JavaScript Style
- Use camelCase for variables and functions
- 2-space indentation
- Modern async/await syntax for asynchronous operations
- Proper event handling with removeEventListener when appropriate
- Descriptive variable and function names

### Error Handling
- Use try-except blocks around operations that might fail
- Catch specific exceptions where possible
- Log detailed error information with context
- Transform technical errors into user-friendly messages
- Handle API failures gracefully

### Logging Best Practices
- Initialize module-level loggers with `logger = logging.getLogger(__name__)`
- Include contextual information in log messages (user_id, action name)
- Log both entries and exits from key functions
- Use appropriate log levels based on severity
- Log detailed error information for debugging

## Order Processing Workflow
1. **Product Selection**: User describes needs, AI matches to product catalog
2. **Design Upload**: User uploads custom design through UI
3. **Design Placement**: User positions design on product using placement tool
4. **Quantity Collection**: User specifies sizes and quantities
5. **Customer Information**: User provides shipping details
6. **Order Completion**: PayPal invoice is generated, order is stored in Firebase

## Testing
To implement tests:
- Add unit tests for core business logic (particularly product_decision_tree.py)
- Create API tests for routes.py endpoints
- Mock external services (Claude, PayPal, Firebase)
- Test error handling paths

## External Services
- **Claude AI**: Handles conversational intelligence
- **Firebase**: Stores customer data and design files
- **PayPal**: Processes payments through invoices


Working!
new push
a