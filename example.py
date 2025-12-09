"""
Example script to use Claude Opus 4.5 via Anthropic API
"""
import os
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize the Anthropic client
client = Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

def chat_with_opus(message: str, model: str = None):
    """
    Send a message to Claude Opus 4.5 and get a response.
    
    Args:
        message: The message/prompt to send
        model: The model to use. If None, will try Opus 4.5 variants.
    
    Returns:
        tuple: (response_text, error_message). response_text is None if error.
    """
    # Try common Opus 4.5 model identifiers
    model_options = [
        model,
        "claude-opus-4-5-20251101",
        "claude-opus-4-20250514", 
        "claude-3-opus-20240229"  # Fallback to Opus 3 if 4.5 not available
    ]
    
    # Remove None values and duplicates
    model_options = list(dict.fromkeys([m for m in model_options if m]))
    
    for model_name in model_options:
        try:
            message_obj = client.messages.create(
                model=model_name,
                max_tokens=4096,
                messages=[
                    {"role": "user", "content": message}
                ]
            )
            
            response_text = message_obj.content[0].text
            return (response_text, None)
        except Exception as e:
            error_msg = str(e)
            # If it's not a model name error, return immediately
            if "model" not in error_msg.lower() or "not found" not in error_msg.lower():
                return (None, error_msg)
            # Otherwise, try next model
            continue
    
    return (None, "Could not connect with any available Opus model. Please check your API key and model availability.")

if __name__ == "__main__":
    # Example usage
    print("Claude Opus 4.5 Example\n" + "="*50)
    
    # Check API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not found in environment variables.")
        print("Please create a .env file with: ANTHROPIC_API_KEY=your-key-here")
        exit(1)
    
    prompt = input("Enter your prompt (or press Enter for example): ").strip()
    if not prompt:
        prompt = "Hello! Can you explain what you are and what you can do?"
    
    print("\nSending to Claude Opus 4.5...\n")
    response, error = chat_with_opus(prompt)
    
    if error:
        print(f"Error: {error}\n")
    else:
        print(f"Response:\n{response}\n")


