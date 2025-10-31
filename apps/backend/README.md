# Serverless AI Application with AWS Lambda, Bedrock, and New Relic

This project demonstrates a serverless AI application that uses AWS Lambda, Bedrock SDK, and New Relic for observability. The application provides an API for generating text and images using various AI models available in AWS Bedrock.

## Features

- **AWS Lambda Function** with Function URL for HTTP access
- **Response Streaming** for real-time AI-generated content
- **AWS Bedrock SDK** integration for text and image generation
- **New Relic** observability with Lambda Layers for comprehensive monitoring
- **Infrastructure as Code** using Pulumi
- **HTML Response Formatting** for user-friendly output

## Prerequisites

- [AWS CLI](https://aws.amazon.com/cli/) installed and configured
- [Python 3.9+](https://www.python.org/downloads/)
- [Pulumi CLI](https://www.pulumi.com/docs/get-started/install/)
- [Node.js](https://nodejs.org/) (required by Pulumi)
- Access to AWS Bedrock service
- New Relic account and license key

## Environment Setup

1. Set up the required environment variables:

```bash
# AWS credentials (if not already configured)
export AWS_ACCESS_KEY_ID="your-aws-access-key"
export AWS_SECRET_ACCESS_KEY="your-aws-secret-key"
export AWS_REGION="us-east-1"  # or your preferred region

# New Relic credentials (required)
export NEW_RELIC_LICENSE_KEY="your-new-relic-license-key"
export NEW_RELIC_ACCOUNT_ID="your-new-relic-account-id"
```

2. Install Python dependencies:

```bash
pip install -r requirements.txt
```

## Project Structure

- `__main__.py` - Pulumi infrastructure code
- `src/app.py` - Lambda function code
- `requirements.txt` - Python dependencies

## Deployment

1. Initialize a new Pulumi stack:

```bash
pulumi stack init dev
```

2. Deploy the application:

```bash
pulumi up
```

3. Once deployed, Pulumi will output the Function URL. Save this URL for testing.

```
Outputs:
  function_url: "https://xxxxxxxxxxxx.lambda-url.us-east-1.on.aws/"
```

## Testing the API

### Text Generation

To generate text, send a POST request to the Function URL:

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"task": "text", "prompt": "Generate a text about cloud computing", "model_id": "amazon.titan-text-express-v1", "stream": false}' \
  "YOUR_FUNCTION_URL"
```

Parameters:
- `task`: Set to "text" for text generation
- `prompt`: Your input prompt for the AI model
- `model_id`: (Optional) Specify the Bedrock model ID
- `stream`: (Optional) Set to `true` for streaming response

### Image Generation

To generate an image, send a POST request:

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"task": "image", "prompt": "A beautiful landscape with mountains and a lake"}' \
  "YOUR_FUNCTION_URL"
```

Parameters:
- `task`: Set to "image" for image generation
- `prompt`: Your description of the image to generate

### Using a Web Browser

You can also test the API directly in a web browser:

1. For text generation with streaming:
   - Open the Function URL with a tool like Postman or use JavaScript fetch in a browser console
   - Send a POST request with the JSON body as described above

2. For image generation:
   - The response is an HTML page with the embedded image

## Observability with New Relic

This application is fully instrumented with New Relic:

1. Navigate to your New Relic account
2. Go to the "Lambda" section to see your function metrics
3. View distributed traces, error rates, and response times
4. Set up alerts based on performance thresholds

Key metrics available:
- Invocation count and duration
- Error rates and types
- Cold start frequency
- AI model response times
- Custom attributes for AI operations

## Cleanup

To remove all resources created by this project:

```bash
pulumi destroy
```

## Troubleshooting

- **Lambda Execution Error**: Check CloudWatch Logs for detailed error messages
- **New Relic Not Reporting**: Verify that environment variables are correctly set
- **Bedrock Access Issues**: Ensure your AWS role has proper permissions for Bedrock

## License

This project is licensed under the MIT License - see the LICENSE file for details.
