import os
import streamlit as st
from dotenv import load_dotenv

try:
    import openai
except ModuleNotFoundError:
    st.error("⚠️ The `openai` package is not installed. Please ensure it is installed in your environment using `pip install openai`.")
    st.stop()

# Load environment variables
load_dotenv()

# Load OpenAI API key from Streamlit secrets
API_KEY = st.secrets.get("OPENAI_API_KEY")
if not API_KEY:
    st.error("⚠️ OpenAI API key is missing! Make sure it is set in Streamlit secrets.")
    st.stop()

# Initialize OpenAI client
client = openai.OpenAI(api_key=API_KEY)

# Streamlit page config
st.set_page_config(page_title="OpenAI File & Web Search", page_icon="🔍", layout="wide")

# Sidebar - Search Settings
st.sidebar.header("🔍 Search Settings")
search_type = st.sidebar.radio("Search Type", ["File Search", "Web Search", "Combined"], index=2)

# Optional: Vector Store ID (for File Search)
VECTOR_STORE_ID = st.sidebar.text_input("Vector Store ID", value="vs_67dc7365c2f0819191c1f049dbd761a9")

# Optional: Web Search Context Size (low, medium, high)
context_size = st.sidebar.selectbox("Web Search Context Size", ["low", "medium", "high"], index=1)

# Search Query Input
query = st.text_input("Enter your search query", placeholder="Type something...")
search_button = st.button("🔍 Search")

# Perform File Search
def perform_file_search(query):
    try:
        with st.spinner("Searching files..."):
            file_search_tool = {"type": "file_search", "vector_store_ids": [VECTOR_STORE_ID]}
            response = client.responses.create(
                model="gpt-4-turbo",
                tools=[file_search_tool],
                tool_choice={"type": "file_search"},
                input=query
            )
            return response
    except Exception as e:
        st.error(f"File search failed: {e}")
        return None

# Perform Web Search
def perform_web_search(query):
    try:
        with st.spinner("Searching the web..."):
            web_search_tool = {"type": "web_search_preview", "search_context_size": context_size}
            response = client.responses.create(
                model="gpt-4",  # Use GPT-4 which supports web search
                tools=[web_search_tool],
                tool_choice={"type": "web_search_preview"},
                input=query
            )
            return response
    except Exception as e:
        st.error(f"Web search failed: {e}")
        return None

# Perform Combined Search
def perform_combined_search(query):
    try:
        with st.spinner("Performing combined search..."):
            file_search_tool = {"type": "file_search", "vector_store_ids": [VECTOR_STORE_ID]}
            web_search_tool = {"type": "web_search_preview", "search_context_size": context_size}
            response = client.responses.create(
                model="gpt-4",  # Use GPT-4 since it supports web search
                tools=[file_search_tool, web_search_tool],
                tool_choice="auto",
                input=query
            )
            return response
    except Exception as e:
        st.error(f"Combined search failed: {e}")
        return None

# Process Search Button Click
if search_button and query:
    if search_type == "File Search":
        response = perform_file_search(query)
    elif search_type == "Web Search":
        response = perform_web_search(query)
    else:
        response = perform_combined_search(query)
    
    if response:
        st.subheader("🔎 Search Results:")
        st.write(response)
