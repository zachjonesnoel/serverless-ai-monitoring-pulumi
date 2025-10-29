# Streamlit Test Client

A user-friendly web interface for testing your AWS Bedrock serverless AI application.

## Features

- 📝 **Text Generation** - Test various text models with customizable parameters
- 🖼️ **Image Generation** - Generate images with different AI models
- 🎯 **Model Selection** - Easy dropdown selection for all supported models
- ⚙️ **Configurable Parameters** - Adjust max tokens, image dimensions, and streaming options
- 📊 **Response Details** - View detailed metrics about each request
- 💾 **Download Images** - Save generated images directly from the interface

## Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Running the Client

1. Start the Streamlit application:

```bash
streamlit run streamlit_client.py
```

2. Your browser will automatically open to `http://localhost:8501`

3. Enter your Lambda Function URL in the sidebar (get this from `pulumi stack output function_url`)

## Usage

### Text Generation

1. Navigate to the **Text Generation** tab
2. Select a model from the dropdown:
   - Amazon Titan models (Express, Lite, Premier)
   - Anthropic Claude models (3 Sonnet, 3 Haiku, 3.5 Sonnet)
   - Meta Llama models (3.1 8B, 3.1 70B)
   - Mistral models (7B Instruct, Large)
3. Enter your prompt
4. (Optional) Enable streaming for real-time responses
5. Adjust max tokens as needed
6. Click **Generate Text**

### Image Generation

1. Navigate to the **Image Generation** tab
2. Select an image model:
   - Amazon Titan Image Generator
   - Stability AI Stable Diffusion XL
3. Enter your image description
4. Select desired width and height
5. Click **Generate Image**
6. Download the generated image using the download button

## Supported Models

### Text Models
- Amazon Titan Text Express
- Amazon Titan Text Lite
- Amazon Titan Text Premier
- Anthropic Claude 3 Sonnet
- Anthropic Claude 3 Haiku
- Anthropic Claude 3.5 Sonnet
- Meta Llama 3.1 8B Instruct
- Meta Llama 3.1 70B Instruct
- Mistral 7B Instruct
- Mistral Large

### Image Models
- Amazon Titan Image Generator
- Stability AI Stable Diffusion XL

## Tips

- For longer responses, increase the max tokens parameter
- Enable streaming to see text generation in real-time
- Try different models to compare quality and response times
- Use the response details expander to see performance metrics

## Troubleshooting

**Connection Error:**
- Verify your Lambda Function URL is correct
- Ensure the Lambda function is deployed and running
- Check that CORS is properly configured on the Function URL

**Timeout Error:**
- Increase the timeout in the Streamlit client (currently 300 seconds)
- Check your Lambda function timeout settings (should be 300 seconds)

**Model Not Available:**
- Verify you have access to the selected model in AWS Bedrock
- Check your AWS region supports the chosen model
- Ensure your Lambda IAM role has the correct Bedrock permissions

## Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│  Streamlit  │ ──────> │ AWS Lambda   │ ──────> │ AWS Bedrock │
│   Client    │  HTTPS  │  Function    │   API   │   Models    │
└─────────────┘         └──────────────┘         └─────────────┘
                               │
                               ↓
                        ┌──────────────┐
                        │  New Relic   │
                        │ Observability│
                        └──────────────┘
```

## License

MIT License
