import { useState } from 'react';
import './App.css';

const LLM_MODELS = [
  { value: 'mistral.mistral-7b-instruct-v0:2', label: 'Mistral 7B Instruct' },
  { value: 'meta.llama3-8b-instruct-v1:0', label: 'Llama 3 8B Instruct' },
  { value: 'us.amazon.nova-lite-v1:0', label: 'Amazon Nova Lite' },
  { value: 'amazon.titan-text-lite-v1', label: 'Amazon Titan Text Lite' },
];

function App() {
  const [selectedModel, setSelectedModel] = useState<string>(LLM_MODELS[0].value);
  const [prompt, setPrompt] = useState<string>('');
  const [response, setResponse] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  const handleSubmit = async () => {
    if (!prompt.trim()) {
      setError('Please enter a prompt');
      return;
    }

    setLoading(true);
    setError('');
    setResponse('');

    try {
      const apiEndpoint = process.env.REACT_APP_API_ENDPOINT;
      if (!apiEndpoint) {
        throw new Error('API endpoint not configured');
      }

      const requestBody = {
        task: 'text',
        prompt: prompt.trim(),
        model_id: selectedModel,
        stream: false
      };

      const apiResponse = await fetch(apiEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (!apiResponse.ok) {
        throw new Error(`HTTP error! status: ${apiResponse.status}`);
      }

      const responseText = await apiResponse.text();
      setResponse(responseText);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An unexpected error occurred';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <div className="container">
        <h1>AI Chat Interface</h1>

        <div className="form-section">
          <div className="input-group">
            <label htmlFor="model-select">Select LLM Model:</label>
            <select
              id="model-select"
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="model-select"
            >
              {LLM_MODELS.map((model) => (
                <option key={model.value} value={model.value}>
                  {model.label}
                </option>
              ))}
            </select>
          </div>

          <div className="input-group">
            <label htmlFor="prompt-input">Enter your prompt:</label>
            <textarea
              id="prompt-input"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Type your question or prompt here..."
              className="prompt-input"
              rows={4}
            />
          </div>

          <button
            onClick={handleSubmit}
            disabled={loading || !prompt.trim()}
            className="submit-button"
          >
            {loading ? 'Generating...' : 'Send'}
          </button>
        </div>

        {error && (
          <div className="error-section">
            <h3>Error:</h3>
            <p>{error}</p>
          </div>
        )}

        {response && (
          <div className="response-section">
            <h3>Response:</h3>
            <div
              className="response-content"
              dangerouslySetInnerHTML={{ __html: response }}
            />
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
