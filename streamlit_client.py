import streamlit as st
import requests
import json
import base64
from io import BytesIO

# Page configuration
st.set_page_config(
    page_title="AI Bedrock Test Client",
    page_icon="🤖",
    layout="wide"
)

# Title and description
st.title("🤖 AWS Bedrock AI Test Client")
st.markdown("Test your serverless AI application with text and image generation")

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    function_url = st.text_input(
        "Lambda Function URL",
        value="https://j2j6el7uv2zuvntuxfaostxoka0sdisq.lambda-url.us-east-1.on.aws/",
        help="Enter your AWS Lambda Function URL from Pulumi output"
    )
    
    st.markdown("---")
    st.markdown("### 📊 Status")
    if function_url:
        st.success("✓ URL configured")
    else:
        st.warning("⚠ URL not set")

# Model options
TEXT_MODELS = {
    "Mistral 7B Instruct": "mistral.mistral-7b-instruct-v0:2",
    "Meta Llama 3 8B Instruct": "meta.llama3-8b-instruct-v1:0",
    "Anthropic Claude Haiku 4.5": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    "Amazon Nova Micro": "amazon.nova-micro-v1:0",
}

IMAGE_MODELS = {
    "Amazon Titan Image Generator": "amazon.titan-image-generator-v1",
    "Stability AI Stable Diffusion XL": "stability.stable-diffusion-xl-v1",
}

# Main content area with tabs
tab1, tab2 = st.tabs(["📝 Text Generation", "🖼️ Image Generation"])

# Text Generation Tab
with tab1:
    st.header("Text Generation")
    
    # Sample prompts
    sample_prompts = [
        "Explain observability for AI and APIs to a 5 year old",
        "Write a haiku about serverless computing",
        "What are the benefits of using AWS Lambda for AI workloads?",
        "Explain how New Relic helps monitor AI applications",
        "What is the difference between monitoring and observability?",
        "How does distributed tracing work in serverless architectures?"
    ]
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Sample prompt selector
        st.markdown("**Sample Prompts:**")
        selected_sample = st.selectbox(
            "Choose a sample prompt or write your own below",
            options=["-- Select a sample prompt --"] + sample_prompts,
            key="sample_prompt_selector",
            label_visibility="collapsed"
        )
        
        # Update session state when a sample is selected
        if selected_sample != "-- Select a sample prompt --":
            st.session_state.text_prompt_input = selected_sample
        
        # Initialize session state if not exists
        if 'text_prompt_input' not in st.session_state:
            st.session_state.text_prompt_input = ""
        
        text_prompt = st.text_area(
            "Enter your prompt",
            value=st.session_state.text_prompt_input,
            placeholder="Generate a text about cloud computing and serverless architecture...",
            height=150,
            key="text_prompt_input",
            on_change=lambda: setattr(st.session_state, 'text_prompt_input', st.session_state.text_prompt_input)
        )
    
    with col2:
        text_model = st.selectbox(
            "Select Model",
            options=list(TEXT_MODELS.keys()),
            key="text_model"
        )
        
        enable_streaming = st.checkbox(
            "Enable Streaming",
            value=False,
            help="Stream the response in real-time"
        )
        
        max_tokens = st.slider(
            "Max Tokens",
            min_value=100,
            max_value=4096,
            value=1024,
            step=100
        )
    
    if st.button("🚀 Generate Text", type="primary", use_container_width=True):
        if not function_url:
            st.error("❌ Please configure the Lambda Function URL in the sidebar")
        elif not text_prompt or text_prompt.strip() == "":
            st.error("❌ Please enter a prompt")
        else:
            with st.spinner("Generating text..."):
                try:
                    payload = {
                        "task": "text",
                        "prompt": text_prompt,
                        "model_id": TEXT_MODELS[text_model],
                        "stream": enable_streaming
                    }
                    
                    response = requests.post(
                        function_url,
                        json=payload,
                        timeout=300
                    )
                    
                    if response.status_code == 200:
                        st.success("✅ Text generated successfully!")
                        
                        # Try to parse JSON response
                        try:
                            result = response.json()
                            
                            # Check if it's a Lambda response with statusCode and body
                            if "statusCode" in result and "body" in result:
                                body = result["body"]
                                
                                # If body is HTML, render it
                                if body.strip().startswith("<!DOCTYPE html>") or body.strip().startswith("<html"):
                                    st.markdown("### Generated Response:")
                                    st.components.v1.html(body, height=600, scrolling=True)
                                else:
                                    # Try to parse body as JSON
                                    try:
                                        body_json = json.loads(body)
                                        st.markdown("### Generated Response:")
                                        st.json(body_json)
                                    except json.JSONDecodeError:
                                        st.markdown("### Generated Text:")
                                        st.text(body)
                            
                            # Standard response with text field
                            elif "text" in result:
                                st.markdown("### Generated Text:")
                                st.markdown(result["text"])
                            
                            # Any other JSON response
                            else:
                                st.markdown("### Response:")
                                st.json(result)
                                
                        except json.JSONDecodeError:
                            # If not JSON, check if it's HTML
                            if response.text.strip().startswith("<!DOCTYPE html>") or response.text.strip().startswith("<html"):
                                st.markdown("### Generated Response:")
                                st.components.v1.html(response.text, height=600, scrolling=True)
                            else:
                                st.markdown("### Response:")
                                st.text(response.text)
                        
                        # Show response details in expander
                        with st.expander("📊 Response Details"):
                            st.write(f"**Status Code:** {response.status_code}")
                            st.write(f"**Model Used:** {TEXT_MODELS[text_model]}")
                            st.write(f"**Response Time:** {response.elapsed.total_seconds():.2f} seconds")
                            st.write(f"**Response Length:** {len(response.text)} characters")
                    else:
                        st.error(f"❌ Error: {response.status_code}")
                        st.text(response.text)
                        
                except requests.exceptions.Timeout:
                    st.error("❌ Request timed out. The model might need more time to generate the response.")
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Request failed: {str(e)}")
                except Exception as e:
                    st.error(f"❌ An error occurred: {str(e)}")

# Image Generation Tab
with tab2:
    st.header("Image Generation")
    
    # Sample image prompts
    sample_image_prompts = [
        "A beautiful landscape with mountains and a lake at sunset",
        "A futuristic data center with glowing servers and holographic displays",
        "An abstract representation of cloud computing with flowing data streams",
        "A serene forest path with sunlight filtering through the trees",
        "A modern office workspace with multiple monitors showing analytics dashboards",
        "A cyberpunk cityscape at night with neon lights"
    ]
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Sample prompt selector
        st.markdown("**Sample Image Prompts:**")
        selected_image_sample = st.selectbox(
            "Choose a sample prompt or write your own below",
            options=["-- Select a sample prompt --"] + sample_image_prompts,
            key="sample_image_prompt_selector",
            label_visibility="collapsed"
        )
        
        # Update session state when a sample is selected
        if selected_image_sample != "-- Select a sample prompt --":
            st.session_state.image_prompt_input = selected_image_sample
        
        # Initialize session state if not exists
        if 'image_prompt_input' not in st.session_state:
            st.session_state.image_prompt_input = ""
        
        image_prompt = st.text_area(
            "Enter your image description",
            value=st.session_state.image_prompt_input,
            placeholder="A beautiful landscape with mountains and a lake at sunset...",
            height=150,
            key="image_prompt_input",
            on_change=lambda: setattr(st.session_state, 'image_prompt_input', st.session_state.image_prompt_input)
        )
    
    with col2:
        image_model = st.selectbox(
            "Select Model",
            options=list(IMAGE_MODELS.keys()),
            key="image_model"
        )
        
        image_width = st.selectbox(
            "Width",
            options=[512, 768, 1024],
            index=1
        )
        
        image_height = st.selectbox(
            "Height",
            options=[512, 768, 1024],
            index=1
        )
    
    if st.button("🎨 Generate Image", type="primary", use_container_width=True):
        if not function_url:
            st.error("❌ Please configure the Lambda Function URL in the sidebar")
        elif not image_prompt:
            st.error("❌ Please enter an image description")
        else:
            with st.spinner("Generating image..."):
                try:
                    payload = {
                        "task": "image",
                        "prompt": image_prompt,
                        "model_id": IMAGE_MODELS[image_model],
                        "width": image_width,
                        "height": image_height
                    }
                    
                    response = requests.post(
                        function_url,
                        json=payload,
                        timeout=300
                    )
                    
                    if response.status_code == 200:
                        st.success("✅ Image generated successfully!")
                        
                        # Try to parse JSON response with base64 image
                        try:
                            result = response.json()
                            if "image" in result:
                                # Decode base64 image
                                image_data = base64.b64decode(result["image"])
                                st.image(image_data, caption="Generated Image", use_container_width=True)
                                
                                # Download button
                                st.download_button(
                                    label="💾 Download Image",
                                    data=image_data,
                                    file_name="generated_image.png",
                                    mime="image/png"
                                )
                            else:
                                st.json(result)
                        except (json.JSONDecodeError, KeyError):
                            # If HTML response with embedded image
                            if "img src=" in response.text:
                                st.markdown("### Generated Image:")
                                st.components.v1.html(response.text, height=800, scrolling=True)
                            else:
                                st.text(response.text)
                        
                        # Show response details in expander
                        with st.expander("📊 Response Details"):
                            st.write(f"**Status Code:** {response.status_code}")
                            st.write(f"**Model Used:** {IMAGE_MODELS[image_model]}")
                            st.write(f"**Response Time:** {response.elapsed.total_seconds():.2f} seconds")
                            st.write(f"**Dimensions:** {image_width}x{image_height}")
                    else:
                        st.error(f"❌ Error: {response.status_code}")
                        st.text(response.text)
                        
                except requests.exceptions.Timeout:
                    st.error("❌ Request timed out. Image generation might need more time.")
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Request failed: {str(e)}")
                except Exception as e:
                    st.error(f"❌ An error occurred: {str(e)}")

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center'>
        <p>Built with Streamlit | AWS Lambda | AWS Bedrock | New Relic</p>
    </div>
""", unsafe_allow_html=True)
