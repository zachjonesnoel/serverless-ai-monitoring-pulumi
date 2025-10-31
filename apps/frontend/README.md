# AI Chat Interface - React Frontend

A React TypeScript application that provides a user-friendly interface for chatting with various Large Language Models (LLMs) through your AWS Lambda backend.

## Features

- **Multiple LLM Models**: Choose from 4 different models:
  - Mistral 7B Instruct (`mistral.mistral-7b-instruct-v0:2`)
  - Llama 3 8B Instruct (`meta.llama3-8b-instruct-v1:0`)
  - Amazon Nova Lite (`us.amazon.nova-lite-v1:0`)
  - Amazon Titan Text Lite (`amazon.titan-text-lite-v1`)

- **Interactive Chat Interface**: Clean, responsive design with real-time feedback
- **Error Handling**: Comprehensive error handling and user feedback
- **HTML Response Rendering**: Supports rich HTML responses from the backend
- **Loading States**: Visual feedback during API calls

## Prerequisites

- Node.js (v14 or higher)
- npm or yarn
- Access to your deployed AWS Lambda backend endpoint

## Setup Instructions

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment Variables

Update the `.env` file in the root directory with your actual Lambda function URL:

```bash
REACT_APP_API_ENDPOINT=https://your-actual-lambda-url.lambda-url.us-east-1.on.aws/
```

**To find your Lambda URL:**
1. Go to AWS Console → Lambda
2. Find your AI chat function
3. Go to Configuration → Function URL
4. Copy the Function URL

### 3. Start the Development Server

```bash
npm start
```

The app will open at [http://localhost:3000](http://localhost:3000)

### 4. Build for Production

```bash
npm run build
```

## API Integration

The frontend sends POST requests to your Lambda backend with the following structure:

```json
{
  "task": "text",
  "prompt": "Your question here",
  "model_id": "selected-model-id",
  "stream": false
}
```

The Lambda function returns HTML-formatted responses that are displayed in the interface.

## Project Structure

```
frontend/
├── public/
├── src/
│   ├── App.tsx          # Main application component
│   ├── App.css          # Styling
│   └── index.tsx        # Entry point
├── .env                 # Environment variables
├── package.json         # Dependencies
└── README.md           # This file
```

## Available Scripts

### `npm start`

Runs the app in the development mode.\
Open [http://localhost:3000](http://localhost:3000) to view it in the browser.

### `npm test`

Launches the test runner in the interactive watch mode.

### `npm run build`

Builds the app for production to the `build` folder.\
The build is minified and optimized for best performance.

### `npm run eject`

**Note: this is a one-way operation. Once you `eject`, you can't go back!**

## Customization

### Adding New Models

To add a new LLM model, update the `LLM_MODELS` array in `src/App.tsx`:

```typescript
const LLM_MODELS = [
  // existing models...
  { value: 'new-model-id', label: 'New Model Display Name' },
];
```

### Styling

The application uses CSS modules. Main styles are in `src/App.css`. The design features:
- Gradient background
- Card-based layout
- Responsive design
- Smooth animations and transitions

## Troubleshooting

### Common Issues

1. **CORS Errors**: Ensure your Lambda function has CORS enabled
2. **API Endpoint Not Found**: Verify the `.env` file has the correct Lambda URL
3. **Build Errors**: Run `npm install` to ensure all dependencies are installed

### Error Messages

- "API endpoint not configured": Check your `.env` file
- "HTTP error! status: XXX": Backend API issues - check Lambda logs
- Network errors: Verify internet connection and Lambda URL accessibility

## Deployment

For production deployment, you can:

1. **Static Hosting**: Deploy the `build/` folder to:
   - AWS S3 + CloudFront
   - Netlify
   - Vercel
   - GitHub Pages

2. **Environment Variables**: Set `REACT_APP_API_ENDPOINT` in your hosting platform's environment variables

## Learn More

- [Create React App documentation](https://facebook.github.io/create-react-app/docs/getting-started)
- [React documentation](https://reactjs.org/)
- [TypeScript documentation](https://www.typescriptlang.org/)
