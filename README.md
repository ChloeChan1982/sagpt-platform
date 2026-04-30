# SAGPT - One-stop Global Expansion Service Platform for Chinese Companies

A lightweight, fast MVP backend system for Chinese companies expanding globally.

## 🎯 Features

### 1. Demand Intake + AI Matching Engine
- Collects user expansion needs
- Uses Volcengine's AI to classify user intent and convert to structured tags
- Matches with service providers database
- Generates AI-powered matching explanations

### 2. AI Compliance Report Generator
- Generates compliance reports in English and Chinese
- Covers legal requirements, licensing, data compliance, tax considerations, and risk warnings
- Supports export as JSON and Markdown formats

### 3. AI Chat Assistant (Specialized)
- Context-aware conversation with memory
- Specialized in cross-border legal issues, overseas expansion, and compliance
- System prompt engineering and safety guardrails

### 4. Service Provider System (MVP)
- Simple database schema for service providers
- Manual provider management (admin)
- Provider matching and retrieval

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ 
- npm or yarn
- Volcengine Coding Plan API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd sagpt-backend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   nano .env
   ```

   Edit the `.env` file and add your Volcengine API key:
   ```
   VOLCENGINE_API_KEY=your_api_key_here
   VOLCENGINE_API_BASE_URL=https://api.volcengine.com/coding-plan
   JWT_SECRET=your_jwt_secret
   PORT=3000
   NODE_ENV=development
   ```

4. **Start the server**
   ```bash
   npm run dev
   ```

### Verify installation

Test the API:
```bash
curl -X GET http://localhost:3000/api/v1/health
```

## 📊 API Documentation

API documentation is available at:
- Swagger UI: `http://localhost:3000/api-docs`
- OpenAPI 3.0 Spec: `http://localhost:3000/api-docs.json`

## 📦 Project Structure

```
sagpt-backend/
├── src/
│   ├── config/                 # Configuration files
│   │   ├── database.js         # Database configuration
│   │   ├── volcengine.js      # Volcengine API configuration
│   │   └── server.js          # Server configuration
│   ├── routes/                 # API routes
│   │   └── v1/                # Version 1 API
│   │       ├── requests.js     # Demand-related routes
│   │       ├── reports.js      # Report-related routes
│   │       ├── chat.js         # Chat assistant routes
│   │       └── providers.js    # Service providers routes
│   ├── controllers/            # Business logic controllers
│   ├── services/               # Core services
│   │   ├── llmService.js       # LLM interface for Volcengine
│   │   ├── matchingService.js  # Provider matching engine
│   │   ├── chatService.js      # Chat management service
│   │   └── reportGenerator.js  # Report generation service
│   ├── models/                 # Data models
│   ├── middlewares/            # Express middlewares
│   ├── utils/                  # Utility functions
│   └── constants/              # Constants
├── data/                       # Data storage (SQLite)
├── docs/                       # API documentation
├── tests/                      # Tests
├── package.json                # Dependencies
├── .env                        # Environment variables
└── README.md                   # This file
```

## 🛠️ Development

### Available commands

```bash
npm run dev          # Development server with hot reload
npm start            # Production server
npm run test         # Run tests
npm run coverage     # Run tests with coverage
npm run docs         # Generate API documentation
npm run lint         # Run linting
```

### Testing

The project uses Jest for testing:

```bash
npm run test
npm run test:watch     # Watch mode
npm run test:coverage  # Coverage report
```

## 🔒 Security

### Authentication
- JWT tokens required for API endpoints
- Token expires in 24 hours

### Rate Limiting
- General endpoints: 15 requests/15 minutes
- AI endpoints: 3 requests/1 minute
- Strict endpoints: 5 requests/1 minute

### Input Validation
- All incoming data validated before processing
- SQL injection prevention via parameterized queries
- XSS protection via helmet and sanitization

## 🌐 Deployment

### Production Deployment

```bash
# Build
npm run build

# Start
npm start
```

### Docker Deployment

```bash
# Build image
docker build -t sagpt-backend .

# Run container
docker run -d -p 3000:3000 --env-file .env sagpt-backend
```

## 📈 Monitoring

### Health Check
```bash
curl -X GET http://localhost:3000/api/v1/health
```

### Log Management
Logs are managed using Winston:
- Console output in development
- File rotation in production

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Create a Pull Request

## 📄 License

MIT License - see [LICENSE](LICENSE) file

## 📞 Support

For support:
1. Check the [API documentation](http://localhost:3000/api-docs)
2. Review the [FAQ](docs/faq.md)
3. File an issue in the repository

## 📚 Resources

- [Volcengine Coding Plan API Documentation](https://www.volcengine.com/docs/6437)
- [Express.js Documentation](https://expressjs.com/)
- [Node.js Documentation](https://nodejs.org/)