"""
Test script to send a test message to Claude Opus 4.5 and display the response.
"""
import os
import sys
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_claude_opus(test_message: str = None):
    """
    Send a test message to Claude Opus 4.5 and return the response.
    
    Args:
        test_message: Optional test message. If None, uses default.
    
    Returns:
        str: The response from Claude, or error message
    """
    # Check API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return "ERROR: ANTHROPIC_API_KEY not found. Please create a .env file with your API key."
    
    # Initialize client
    try:
        client = Anthropic(api_key=api_key)
    except Exception as e:
        return f"ERROR: Failed to initialize Anthropic client: {str(e)}"
    
    # Default test message
    if not test_message:
        test_message = "Hello! Write a simple Python function that calculates the factorial of a number."
    
    # Try different Opus model identifiers
    model_options = [
        "claude-opus-4-5-20251101",
        "claude-opus-4-20250514",
        "claude-3-opus-20240229"
    ]
    
    last_error = None
    for model_name in model_options:
        try:
            print(f"Attempting to use model: {model_name}...", file=sys.stderr)
            
            message_obj = client.messages.create(
                model=model_name,
                max_tokens=4096,
                messages=[
                    {"role": "user", "content": test_message}
                ]
            )
            
            response_text = message_obj.content[0].text
            print(f"Successfully connected to: {model_name}\n", file=sys.stderr)
            return response_text
            
        except Exception as e:
            last_error = str(e)
            # Continue to next model
            continue
    
    return f"ERROR: Failed to connect to any Opus model. Last error: {last_error}"

if __name__ == "__main__":
    # Get test message from command line or use default
    test_msg = None
    if len(sys.argv) > 1:
        test_msg = " ".join(sys.argv[1:])
    
    print("="*60, file=sys.stderr)
    print("Claude Opus 4.5 Test", file=sys.stderr)
    print("="*60, file=sys.stderr)
    print(f"\nTest Message: {test_msg or 'Hello! Write a simple Python function that calculates the factorial of a number.'}", file=sys.stderr)
    print("\nSending request...\n", file=sys.stderr)
    
    response = test_claude_opus(test_msg)
    
    # Print response to stdout (so it can be captured)
    print(response)

