import os
import openai
from dotenv import load_dotenv

def check_openai_key(api_key=None):
    """
    Check if the provided OpenAI API key is valid.
    If no key is provided, tries to load from .env file.
    
    Returns:
        tuple: (is_valid, message)
    """
    try:
        # If no key provided, try to load from .env
        if api_key is None:
            load_dotenv()
            api_key = os.getenv('OPENAI_API_KEY')
            
            if not api_key:
                return False, "No API key found in .env file"
        
        # Set the API key
        openai.api_key = api_key
        
        # Make a simple API call to validate the key
        openai.models.list()
        
        return True, "✅ API key is valid!"
        
    except openai.AuthenticationError:
        return False, "❌ Invalid API key. Please check your API key and try again."
    except Exception as e:
        return False, f"❌ An error occurred: {str(e)}"

if __name__ == "__main__":
    # Check if the API key is valid
    is_valid, message = check_openai_key()
    print(message)
    
    # If you want to test a specific key directly:
    # is_valid, message = check_openai_key("your-api-key-here")
    # print(message)