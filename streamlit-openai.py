import os
import streamlit as st
from dotenv import load_dotenv
import requests

try:
    import openai
except ModuleNotFoundError:
    st.error("⚠️ The `openai` package is not installed. Please ensure it is installed in your environment using `pip install openai`.")
    st.stop()

# Load environment variables
load_dotenv()

# Load OpenAI API key from Streamlit secrets
API_KEY = st.secrets.get("OPENAI_API_KEY")
SERPAPI_KEY = st.secrets.get("SERPAPI_KEY")  # External search API key
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

# Search Query Input
query = st.text_input("Enter your search query", placeholder="Type something...")
search_button = st.button("🔍 Search")

# Perform File Search
def perform_file_search(query):
    try:
        with st.spinner("Searching files..."):
            file_search_tool = {"type": "file_search", "vector_store_ids": [VECTOR_STORE_ID]}
            response = client.responses.create(
                model="gpt-4-turbo",  # Ensure using a working model
                tools=[file_search_tool],
                tool_choice={"type": "file_search"},
                input=query
            )
            return response
    except Exception as e:
        st.error(f"File search failed: {e}")
        return None

# Perform Web Search (Using SerpAPI Instead of OpenAI's Web Search)
def perform_web_search(query):
    if not SERPAPI_KEY:
        st.error("⚠️ SerpAPI key is missing! Please set it in Streamlit secrets.")
        return None
    
    try:
        with st.spinner("Searching the web..."):
            url = f"https://serpapi.com/search.json?q={query}&api_key={SERPAPI_KEY}"
            response = requests.get(url)
            data = response.json()
            
            if "organic_results" in data:
                return data["organic_results"]
            else:
                st.error("No results found.")
                return None
    except Exception as e:
        st.error(f"Web search failed: {e}")
        return None

# Perform Combined Search
def perform_combined_search(query):
    file_results = perform_file_search(query)
    web_results = perform_web_search(query)
    
    if file_results and web_results:
        return {"File Search": file_results, "Web Search": web_results}
    elif file_results:
        return {"File Search": file_results}
    elif web_results:
        return {"Web Search": web_results}
    else:
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
