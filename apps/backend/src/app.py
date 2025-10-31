import os
import json
import boto3
import logging
import time
import uuid
import re
from typing import Dict, Iterator

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Try to import New Relic agent for custom instrumentation
# This is optional - the function will still work without it
try:
    import newrelic.agent
    HAS_NEWRELIC = True
    logger.info("New Relic agent imported successfully for custom instrumentation")
except ImportError:
    HAS_NEWRELIC = False
    logger.info("New Relic agent not available for custom instrumentation, continuing without it")

# Initialize Bedrock client
bedrock = boto3.client('bedrock-runtime')

def estimate_tokens(text: str) -> int:
    """
    Estimate the number of tokens in a text string.
    This is an approximation based on GPT tokenization rules.
    """
    # Simple approximation: 4 chars ≈ 1 token for English text
    # This is a rough estimate - actual tokenization depends on the model
    if not text:
        return 0
        
    # Count words (roughly correlates with tokens for English text)
    words = len(re.findall(r'\b\w+\b', text))
    
    # For languages with spaces, tokens are often slightly fewer than words
    estimated_tokens = max(1, int(words * 1.3))
    
    # For JSON or code, add a complexity factor
    if '{' in text and '}' in text:
        estimated_tokens = int(estimated_tokens * 1.2)
    
    logger.info(f"Estimated token count for text: {estimated_tokens}")
    return estimated_tokens

def format_to_html(text: str) -> str:
    """Convert plain text to formatted HTML with nice styling"""
    # Replace newlines with HTML line breaks
    text = text.replace('\n', '<br>')
    
    # Basic styling for the content
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Generated Content</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f9f9f9;
            }}
            h1 {{
                color: #2c3e50;
                border-bottom: 2px solid #3498db;
                padding-bottom: 10px;
            }}
            .content {{
                background-color: white;
                padding: 20px;
                border-radius: 5px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }}
            .footer {{
                margin-top: 20px;
                font-size: 0.8em;
                color: #7f8c8d;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <h1>AI Generated Response</h1>
        <div class="content">
            {text}
        </div>
        <div class="footer">
            Generated with AWS Bedrock. Powered by New Relic and Pulumi
        </div>
    </body>
    </html>
    """
    return html

def stream_response(result: Dict) -> Iterator[Dict]:
    """Stream the response back to the client"""
    # Start with the HTML header
    html_start = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Generated Content</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f9f9f9;
            }
            h1 {
                color: #2c3e50;
                border-bottom: 2px solid #3498db;
                padding-bottom: 10px;
            }
            .content {
                background-color: white;
                padding: 20px;
                border-radius: 5px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            .footer {
                margin-top: 20px;
                font-size: 0.8em;
                color: #7f8c8d;
                text-align: center;
            }
        </style>
    </head>
    <body>
        <h1>AI Generated Response</h1>
        <div class="content">
    """
    
    yield {
        "statusCode": 200,
        "headers": {"Content-Type": "text/html"},
        "body": html_start,
        "isBase64Encoded": False
    }
    
    # Extract the text from the result based on common Bedrock model output formats
    if "outputText" in result:
        content = result["outputText"]
    elif "results" in result and isinstance(result["results"], list) and len(result["results"]) > 0:
        content = result["results"][0].get("outputText", "No content generated")
    elif "generation" in result:
        content = result["generation"]
    elif "completion" in result:
        content = result["completion"]
    else:
        content = json.dumps(result)
    
    # Stream the content in chunks to simulate streaming
    words = content.split()
    chunk_size = 5  # Number of words per chunk
    
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i+chunk_size])
        yield {
            "statusCode": 200,
            "headers": {"Content-Type": "text/html"},
            "body": chunk + " ",
            "isBase64Encoded": False
        }
        time.sleep(0.1)  # Simulate delay between chunks
    
    # End the HTML
    html_end = """
        </div>
        <div class="footer">
            Powered by AWS Bedrock • New Relic and Pulumi
        </div>
    </body>
    </html>
    """
    
    yield {
        "statusCode": 200,
        "headers": {"Content-Type": "text/html"},
        "body": html_end,
        "isBase64Encoded": False
    }

# Define a simple tracing helper for Bedrock calls
def trace_bedrock_call(task_type, model_id, prompt, has_newrelic=False):
    """A helper function to trace Bedrock API calls with or without New Relic"""
    start_time = time.time()
    
    # Estimate input tokens
    input_tokens = estimate_tokens(prompt)
    
    try:
        # Initialize response variable
        response = None
        
        # Make the API call
        if task_type == 'text':
            if model_id == 'amazon.titan-text-lite-v1':
                response = bedrock.invoke_model(
                    modelId=model_id,
                    body=json.dumps(
                        {
                            "inputText": prompt, 
                            "textGenerationConfig": {
                                "maxTokenCount": 512,
                                "temperature": 0.5,
                            }
                        }
                    )
                )
            elif model_id == 'us.amazon.nova-lite-v1:0':
                system_list = [
                            {
                                "text": "Act as a subject matter expert. When the user provides you with a topic, explain about that topic."
                            }
                ]
                message_list = [{"role": "user", "content": [{"text": prompt}]}]
                inf_params = {"maxTokens": 500, "topP": 0.9, "topK": 20, "temperature": 0.7}
                response = bedrock.invoke_model(
                    modelId=model_id,
                    body=json.dumps(
                        {
                            "schemaVersion": "messages-v1",
                            "messages": message_list,
                            "system": system_list,
                            "inferenceConfig": inf_params,
                        }
                    )
                )
            elif model_id == 'mistral.mistral-7b-instruct-v0:2':
                formatted_prompt = f"""
                <s>[INST]
                {prompt}
                [/INST]
                """
                response = bedrock.invoke_model(
                    modelId=model_id,
                    body=json.dumps({
                        "prompt":  formatted_prompt,
                        "max_tokens": 400,
                        "temperature": 0.7,
                        "top_p": 0.7,
                        "top_k": 50
                    })
                )
            elif model_id == 'meta.llama3-8b-instruct-v1:0':
                formatted_prompt = f"""
                <|begin_of_text|><|start_header_id|>user<|end_header_id|>
                {prompt}
                <|eot_id|>
                <|start_header_id|>assistant<|end_header_id|>
                """
                response = bedrock.invoke_model(
                    modelId=model_id,
                    body=json.dumps({
                        "prompt": formatted_prompt,
                        "max_gen_len": 512,
                        "temperature": 0.5,
                    })
                )
            elif model_id == 'us.anthropic.claude-haiku-4-5-20251001-v1:0':
                formatted_prompt = f"""
                \n\nHuman:
                {prompt}
                \n\nAssistant:
                """
                response = bedrock.invoke_model(
                    modelId=model_id,
                    body=json.dumps({
                        "prompt": formatted_prompt,
                        "max_tokens_to_sample": 300,
                        "temperature": 0.1,
                        "top_p": 0.9,
                    })
                )
            else:
                # If model_id doesn't match any known model, raise an error
                raise ValueError(f"Unsupported text model: {model_id}")

        else:  # image
            response = bedrock.invoke_model(
                modelId=model_id,
                contentType='application/json',
                accept='application/json',
                body=json.dumps({"prompt": prompt, "max_tokens": "image"})
            )
        
        # Check if response was set
        if response is None:
            raise ValueError(f"No response generated for model: {model_id}")
        
        # Parse the response
        result = json.loads(response['body'].read())
        
        # Calculate duration and log
        duration = time.time() - start_time
        logger.info(f"Bedrock {task_type} generation completed in {duration:.2f}s")
        
        # Estimate output tokens for text generation
        output_tokens = 0
        if task_type == 'text':
            output_text = ""
            if "outputText" in result:
                output_text = result["outputText"]
            elif "results" in result and isinstance(result["results"], list) and len(result["results"]) > 0:
                output_text = result["results"][0].get("outputText", "")
            elif "generation" in result:
                output_text = result["generation"]
            elif "completion" in result:
                output_text = result["completion"]
                
            output_tokens = estimate_tokens(output_text)
            logger.info(f"Text generation - Input tokens: {input_tokens}, Output tokens: {output_tokens}")
        
        # Record custom metrics in New Relic if available
        if has_newrelic:
            # Record duration
            newrelic.agent.record_custom_metric(
                f'Custom/Bedrock/{task_type}_generation_time', 
                duration
            )
            
            # Record token usage
            current_transaction = newrelic.agent.current_transaction()
            if current_transaction:
                current_transaction.add_custom_attribute('input_tokens', input_tokens)
                if task_type == 'text':
                    current_transaction.add_custom_attribute('output_tokens', output_tokens)
                    current_transaction.add_custom_attribute('total_tokens', input_tokens + output_tokens)
                    
                    # Record token metrics for aggregation
                    newrelic.agent.record_custom_metric(
                        f'Custom/Bedrock/input_tokens', 
                        input_tokens
                    )
                    newrelic.agent.record_custom_metric(
                        f'Custom/Bedrock/output_tokens', 
                        output_tokens
                    )
                    newrelic.agent.record_custom_metric(
                        f'Custom/Bedrock/total_tokens', 
                        input_tokens + output_tokens
                    )
                    
                    # Record tokens per model
                    model_short_name = model_id.split('.')[-1] if '.' in model_id else model_id
                    newrelic.agent.record_custom_metric(
                        f'Custom/Bedrock/Models/{model_short_name}/tokens', 
                        input_tokens + output_tokens
                    )
        
        return result
    except Exception as e:
        # Log error
        logger.error(f"Error calling Bedrock for {task_type}: {str(e)}")
        # Record error in New Relic if available
        if has_newrelic:
            current_transaction = newrelic.agent.current_transaction()
            if current_transaction:
                current_transaction.notice_error()
        raise  # Re-raise the exception

def handler(event, context):
    # Generate a unique request ID for tracking in New Relic
    request_id = str(uuid.uuid4())
    
    # Start recording metrics for this transaction
    if HAS_NEWRELIC:
        # Add custom attributes for New Relic
        current_transaction = newrelic.agent.current_transaction()
        print(current_transaction)
        if current_transaction:
            current_transaction.add_custom_attribute('request_id', request_id)
            current_transaction.add_custom_attribute('service_name', 'bedrock-ai-service')
    
    try:
        # Log the incoming event
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        model_id = body.get('model_id', 'amazon.titan-text-express-v1')
        prompt = body.get('prompt', 'Generate a text about New Relic, Pulumi and Confluent and how AI is bringing it together')
        task = body.get('task', 'text')  # 'text' or 'image'
        stream_mode = body.get('stream', False)  # Whether to stream the response
        
        # Record AI operation metadata for observability
        if HAS_NEWRELIC:
            if current_transaction:
                current_transaction.add_custom_attribute('ai_model', model_id)
                current_transaction.add_custom_attribute('ai_task', task)
                current_transaction.add_custom_attribute('streaming_enabled', stream_mode)
                current_transaction.add_custom_attribute('prompt_length', len(prompt))
                
                # Add the model for cost analysis
                # Extract model family for cost tracking
                if 'claude' in model_id.lower():
                    model_family = 'claude'
                elif 'titan' in model_id.lower():
                    model_family = 'titan'
                elif 'llama' in model_id.lower():
                    model_family = 'llama'
                else:
                    model_family = 'other'
                
                current_transaction.add_custom_attribute('model_family', model_family)
        
        # Call Bedrock API using our helper function
        if task == 'text':
            result = trace_bedrock_call('text', model_id, prompt, HAS_NEWRELIC)
            logger.info(f"Text generation completed: {result}")
            # If streaming is requested, use the streaming response format
            if stream_mode:
                return stream_response(result)
            else:
                # Return formatted HTML for non-streaming response
                # if model_id == "amazon.titan-text-express-v1":
                #     responseGenerated = result.get("results", [{}])[0].get("outputText", "No content generated")
                # elif model_id == "us.amazon.nova-lite-v1:0":
                #     responseGenerated = result.get("outputs", [{}])[0].get("text", "No content generated")
                # elif model_id == "mistral.mistral-7b-instruct-v0:2":
                #     responseGenerated = result.get("results", [{}])[0].get("outputText", "No content generated")
                html_content = format_to_html(
                    json.dumps(result)
                )
                return {
                    "statusCode": 200,
                    "body": html_content,
                    "headers": {"Content-Type": "text/html"},
                    "isBase64Encoded": False
                }
        elif task == 'image':
            # Call Bedrock API for image generation
            result = trace_bedrock_call('image', model_id, prompt, HAS_NEWRELIC)
            
            # For images, we'll create an HTML page with the embedded image
            if "images" in result and result["images"]:
                image_base64 = result["images"][0]  # Get the first image
                html_content = f"""
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>AI Generated Image</title>
                    <style>
                        body {{
                            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                            line-height: 1.6;
                            color: #333;
                            max-width: 800px;
                            margin: 0 auto;
                            padding: 20px;
                            background-color: #f9f9f9;
                            text-align: center;
                        }}
                        h1 {{
                            color: #2c3e50;
                            border-bottom: 2px solid #3498db;
                            padding-bottom: 10px;
                        }}
                        .image-container {{
                            background-color: white;
                            padding: 20px;
                            border-radius: 5px;
                            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                            margin-top: 20px;
                        }}
                        img {{
                            max-width: 100%;
                            border-radius: 5px;
                        }}
                        .prompt {{
                            font-style: italic;
                            color: #7f8c8d;
                            margin: 20px 0;
                        }}
                        .footer {{
                            margin-top: 20px;
                            font-size: 0.8em;
                            color: #7f8c8d;
                            text-align: center;
                        }}
                    </style>
                </head>
                <body>
                    <h1>AI Generated Image</h1>
                    <div class="prompt">Prompt: "{prompt}"</div>
                    <div class="image-container">
                        <img src="data:image/png;base64,{image_base64}" alt="AI Generated Image">
                    </div>
                    <div class="footer">
                        Generated with AWS Bedrock • Powered by New Relic and Pulumi
                    </div>
                </body>
                </html>
                """
                return {
                    "statusCode": 200,
                    "body": html_content,
                    "headers": {"Content-Type": "text/html"},
                    "isBase64Encoded": False
                }
            else:
                return {
                    "statusCode": 500,
                    "body": "<html><body><h1>Error</h1><p>Failed to generate image</p></body></html>",
                    "headers": {"Content-Type": "text/html"},
                    "isBase64Encoded": False
                }
        else:
            # Return an HTML error page
            error_html = """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Error</title>
                <style>
                    body {
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 800px;
                        margin: 0 auto;
                        padding: 20px;
                        background-color: #f9f9f9;
                        text-align: center;
                    }
                    h1 {
                        color: #e74c3c;
                        border-bottom: 2px solid #e74c3c;
                        padding-bottom: 10px;
                    }
                    .error-container {
                        background-color: white;
                        padding: 20px;
                        border-radius: 5px;
                        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                        margin-top: 20px;
                    }
                    .footer {
                        margin-top: 20px;
                        font-size: 0.8em;
                        color: #7f8c8d;
                        text-align: center;
                    }
                </style>
            </head>
            <body>
                <h1>Error</h1>
                <div class="error-container">
                    <p>Invalid task type. Supported types are 'text' and 'image'.</p>
                </div>
                <div class="footer">
                    Powered by New Relic and Pulumi
                </div>
            </body>
            </html>
            """
            return {
                "statusCode": 400,
                "body": error_html,
                "headers": {"Content-Type": "text/html"},
                "isBase64Encoded": False
            }
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        
        # Record error details in New Relic
        if HAS_NEWRELIC:
            if 'current_transaction' in locals() and current_transaction:
                current_transaction.notice_error(error=e, attributes={
                    'error_source': 'handler',
                    'request_id': request_id
                })
        
        # Return an HTML error page
        error_html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Error</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f9f9f9;
                    text-align: center;
                }}
                h1 {{
                    color: #e74c3c;
                    border-bottom: 2px solid #e74c3c;
                    padding-bottom: 10px;
                }}
                .error-container {{
                    background-color: white;
                    padding: 20px;
                    border-radius: 5px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                    margin-top: 20px;
                    text-align: left;
                }}
                .error-message {{
                    background-color: #f8d7da;
                    color: #721c24;
                    padding: 10px;
                    border-radius: 5px;
                    margin-top: 10px;
                    font-family: monospace;
                }}
                .footer {{
                    margin-top: 20px;
                    font-size: 0.8em;
                    color: #7f8c8d;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <h1>Error</h1>
            <div class="error-container">
                <p>An error occurred while processing your request:</p>
                <div class="error-message">{str(e)}</div>
                <p><small>Request ID: {request_id}</small></p>
            </div>
            <div class="footer">
                Powered by New Relic and Pulumi
            </div>
        </body>
        </html>
        """
        return {
            "statusCode": 500,
            "body": error_html,
            "headers": {"Content-Type": "text/html"},
            "isBase64Encoded": False
        }