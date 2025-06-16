# app/core/llm_config.py
import streamlit as st
from pandasai.llm import GooglePalm # Assuming Gemini is accessed via GooglePalm or a similar class
import toml

def get_llm():
    """
    Loads the Google AI Studio API key from Streamlit secrets
    and returns an initialized LLM for pandasai.
    """
    try:
        # Attempt to access the nested key directly
        api_key = st.secrets.get("google", {}).get("GOOGLE_API_KEY")
        if not api_key: # Handles case where 'google' exists but 'GOOGLE_API_KEY' does not or is empty
            raise KeyError 
    except KeyError: # Catches if "google" or "GOOGLE_API_KEY" is missing
        st.error("Google API Key not found in .streamlit/secrets.toml under [google] section. Please add it.")
        st.info("Example .streamlit/secrets.toml:\n\n[google]\nGOOGLE_API_KEY = \"YOUR_ACTUAL_KEY_HERE\"")
        return None
    except FileNotFoundError: # This might not be explicitly needed if st.secrets handles it gracefully
        st.error(".streamlit/secrets.toml file not found. Please create it with your Google API Key.")
        st.info("Example .streamlit/secrets.toml:\n\n[google]\nGOOGLE_API_KEY = \"YOUR_ACTUAL_KEY_HERE\"")
        return None


    if api_key == "YOUR_GOOGLE_AI_STUDIO_API_KEY_HERE" or not api_key.strip():
        st.error("Please replace the placeholder API key in .streamlit/secrets.toml with your actual Google AI Studio API Key.")
        st.info("Ensure the key is correctly placed under the [google] section, like:\n\n[google]\nGOOGLE_API_KEY = \"YOUR_ACTUAL_KEY_HERE\"")
        return None

    # Note: As of early 2024, pandasai might use GooglePalm for Gemini models.
    # The exact model name for Gemini Pro 1.5 via google-generativeai SDK is typically "models/gemini-1.5-pro-latest" or "models/gemini-pro"
    # We will need to verify the correct way to specify Gemini 1.5 Pro in pandasai.
    # For now, we use a common Gemini Pro model name.
    # If pandasai has a specific GoogleGenerativeAI connector, that would be preferred.
    # We are using GooglePalm as a placeholder, assuming it's the relevant class.
    # This might need adjustment based on the exact pandasai version and its supported connectors.
    
    # Attempt to use GoogleGenerativeAI first if available in pandasai
    try:
        from pandasai.llm import GoogleGenerativeAI
        # Common model names for Gemini Pro. "gemini-1.5-pro-latest" is more specific for the version.
        llm = GoogleGenerativeAI(api_key=api_key, model_name="models/gemini-1.5-pro-latest")
        # print("Using GoogleGenerativeAI connector.")
    except ImportError:
        # Fallback to GooglePalm if GoogleGenerativeAI is not available
        # print("GoogleGenerativeAI connector not found, falling back to GooglePalm.")
        # For GooglePalm, "gemini-pro" is a common alias that might be supported.
        llm = GooglePalm(api_key=api_key, model_name="models/gemini-pro") 
    
    return llm

if __name__ == "__main__":
    # This part is for testing the function directly.
    # In a Streamlit app, you'd call get_llm() when needed.
    # Note: This test won't work without a running Streamlit app context for st.secrets
    # or if secrets.toml is not set up correctly.
    print("Attempting to configure LLM (direct script run)...")

    # --- Mocking st.secrets for local testing ---
    # This is a simplified mock. In a real test suite, you might use unittest.mock.
    class MockSecrets(dict):
        def __init__(self, *args, **kwargs):
            super(MockSecrets, self).__init__(*args, **kwargs)
            self.__dict__ = self # Allows attribute-style access if your code uses it

        def __getitem__(self, key):
            # Allow dict-style access (e.g. st.secrets["google"])
            return super().__getitem__(key)

        def get(self, key, default=None):
            # Ensure get method behaves as expected for nested access in get_llm
            return super().get(key, default)

    try:
        # import toml # Already imported at the top
        with open(".streamlit/secrets.toml", "r") as f:
            secrets_data = toml.load(f)
        st.secrets = MockSecrets(secrets_data) # Replace st.secrets with our mock
        print("Mocked st.secrets with data from .streamlit/secrets.toml")
    except FileNotFoundError:
        print("Local .streamlit/secrets.toml not found. Mocking with placeholder data for testing structure.")
        # Provide minimal structure for get_llm to run without erroring on st.secrets access
        st.secrets = MockSecrets({
            "google": {
                "GOOGLE_API_KEY": "YOUR_GOOGLE_AI_STUDIO_API_KEY_HERE" # Placeholder
            }
        })
    except Exception as e:
        print(f"Error loading/mocking secrets.toml for local testing: {e}")
        # Provide a basic mock structure even in case of other errors during toml parsing
        st.secrets = MockSecrets({
            "google": {
                "GOOGLE_API_KEY": "YOUR_GOOGLE_AI_STUDIO_API_KEY_HERE_ERROR_CASE"
            }
        })
    # --- End Mocking st.secrets ---

    llm_instance = get_llm()
    if llm_instance:
        print("LLM configured successfully (simulated).")
        print(f"LLM Object: {llm_instance}")
        # PandasAI LLM objects usually have a 'type' or similar attribute.
        # For GooglePalm/GoogleGenerativeAI, it might be 'google-palm' or 'google-generativeai'.
        if hasattr(llm_instance, 'type'):
            print(f"LLM Provider Type: {llm_instance.type}")
        if hasattr(llm_instance, 'model'): # newer pandasai versions
             print(f"LLM Model Name (from .model): {llm_instance.model}")
        elif hasattr(llm_instance, '_model_name'): # older or different attribute
             print(f"LLM Model Name (from ._model_name): {llm_instance._model_name}")
        elif hasattr(llm_instance, 'model_name'): # another common attribute
             print(f"LLM Model Name (from .model_name): {llm_instance.model_name}")
        else:
            print("Model name attribute not found through common names (.model, ._model_name, .model_name).")

    else:
        print("LLM configuration failed. If running directly, ensure .streamlit/secrets.toml is correctly set up and accessible.")
        print("Note: `st.secrets` works best within a running Streamlit application.")
