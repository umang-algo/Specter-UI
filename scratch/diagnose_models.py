import os
import anthropic
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

try:
    # Use the legacy models list if available or just try a basic message to see supported models
    # Note: Anthropic doesn't have a public 'list models' endpoint in the standard SDK like OpenAI yet
    # but we can try a known older model or check the error message more deeply.
    
    print("Testing connectivity and identifying available models...")
    # Just try a very basic call with a very generic model name to see what the error reveals
    message = client.messages.create(
        model="claude-instant-1.2",
        max_tokens=10,
        messages=[{"role": "user", "content": "hi"}]
    )
    print(f"Success with claude-instant-1.2")
except Exception as e:
    print(f"Diagnostic result: {e}")
