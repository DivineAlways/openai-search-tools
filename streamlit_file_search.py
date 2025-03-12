import os
import sys
import json
import openai
import streamlit as st
from typing import Dict, List, Optional, Union, Any, Tuple
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime
import re

# Load environment variables from .env file
load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="OpenAI File & Web Search",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://platform.openai.com/docs/guides/tools-file-search',
        'Report a bug': 'https://github.com/yourusername/openai-file-search/issues',
        'About': 'File & Web search tool powered by OpenAI\'s APIs'
    }
)

# Vector store ID
VECTOR_STORE_ID = "vs_67d0cc79ab4c8191a92661559e49dbd2"

# List of common countries with their ISO codes
COUNTRIES = [
    {"name": "United States", "code": "US"},
    {"name": "United Kingdom", "code": "GB"},
    {"name": "Canada", "code": "CA"},
    {"name": "Australia", "code": "AU"},
    {"name": "Germany", "code": "DE"},
    {"name": "France", "code": "FR"},
    {"name": "Japan", "code": "JP"},
    {"name": "India", "code": "IN"},
    {"name": "Brazil", "code": "BR"},
    {"name": "Mexico", "code": "MX"},
    {"name": "Spain", "code": "ES"},
    {"name": "Italy", "code": "IT"},
    {"name": "Netherlands", "code": "NL"},
    {"name": "Sweden", "code": "SE"},
    {"name": "Switzerland", "code": "CH"},
    {"name": "Singapore", "code": "SG"},
    {"name": "South Korea", "code": "KR"},
    {"name": "China", "code": "CN"},
    {"name": "Ireland", "code": "IE"},
    {"name": "New Zealand", "code": "NZ"},
    {"name": "South Africa", "code": "ZA"},
    {"name": "United Arab Emirates", "code": "AE"},
    {"name": "Argentina", "code": "AR"},
    {"name": "Belgium", "code": "BE"},
    {"name": "Denmark", "code": "DK"},
    {"name": "Norway", "code": "NO"},
    {"name": "Poland", "code": "PL"},
    {"name": "Russia", "code": "RU"},
    {"name": "Israel", "code": "IL"},
    {"name": "Turkey", "code": "TR"},
]

# US states with abbreviations
US_STATES = [
    {"name": "Alabama", "code": "AL"},
    {"name": "Alaska", "code": "AK"},
    {"name": "Arizona", "code": "AZ"},
    {"name": "Arkansas", "code": "AR"},
    {"name": "California", "code": "CA"},
    {"name": "Colorado", "code": "CO"},
    {"name": "Connecticut", "code": "CT"},
    {"name": "Delaware", "code": "DE"},
    {"name": "Florida", "code": "FL"},
    {"name": "Georgia", "code": "GA"},
    {"name": "Hawaii", "code": "HI"},
    {"name": "Idaho", "code": "ID"},
    {"name": "Illinois", "code": "IL"},
    {"name": "Indiana", "code": "IN"},
    {"name": "Iowa", "code": "IA"},
    {"name": "Kansas", "code": "KS"},
    {"name": "Kentucky", "code": "KY"},
    {"name": "Louisiana", "code": "LA"},
    {"name": "Maine", "code": "ME"},
    {"name": "Maryland", "code": "MD"},
    {"name": "Massachusetts", "code": "MA"},
    {"name": "Michigan", "code": "MI"},
    {"name": "Minnesota", "code": "MN"},
    {"name": "Mississippi", "code": "MS"},
    {"name": "Missouri", "code": "MO"},
    {"name": "Montana", "code": "MT"},
    {"name": "Nebraska", "code": "NE"},
    {"name": "Nevada", "code": "NV"},
    {"name": "New Hampshire", "code": "NH"},
    {"name": "New Jersey", "code": "NJ"},
    {"name": "New Mexico", "code": "NM"},
    {"name": "New York", "code": "NY"},
    {"name": "North Carolina", "code": "NC"},
    {"name": "North Dakota", "code": "ND"},
    {"name": "Ohio", "code": "OH"},
    {"name": "Oklahoma", "code": "OK"},
    {"name": "Oregon", "code": "OR"},
    {"name": "Pennsylvania", "code": "PA"},
    {"name": "Rhode Island", "code": "RI"},
    {"name": "South Carolina", "code": "SC"},
    {"name": "South Dakota", "code": "SD"},
    {"name": "Tennessee", "code": "TN"},
    {"name": "Texas", "code": "TX"},
    {"name": "Utah", "code": "UT"},
    {"name": "Vermont", "code": "VT"},
    {"name": "Virginia", "code": "VA"},
    {"name": "Washington", "code": "WA"},
    {"name": "West Virginia", "code": "WV"},
    {"name": "Wisconsin", "code": "WI"},
    {"name": "Wyoming", "code": "WY"},
    {"name": "District of Columbia", "code": "DC"}
]

# Major cities by country
MAJOR_CITIES = {
    "US": {},  # Will be populated by state
    "GB": ["London", "Manchester", "Birmingham", "Edinburgh", "Glasgow", "Liverpool", "Bristol"],
    "CA": ["Toronto", "Vancouver", "Montreal", "Calgary", "Ottawa", "Edmonton", "Quebec City"],
    "AU": ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide", "Gold Coast", "Canberra"],
    "DE": ["Berlin", "Munich", "Hamburg", "Frankfurt", "Cologne", "Stuttgart", "Düsseldorf"],
    "FR": ["Paris", "Marseille", "Lyon", "Toulouse", "Nice", "Nantes", "Strasbourg"],
    "JP": ["Tokyo", "Osaka", "Kyoto", "Yokohama", "Nagoya", "Sapporo", "Fukuoka"],
    "IN": ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Kolkata", "Pune"],
    "BR": ["São Paulo", "Rio de Janeiro", "Brasília", "Salvador", "Fortaleza", "Belo Horizonte", "Manaus"],
    "MX": ["Mexico City", "Guadalajara", "Monterrey", "Puebla", "Tijuana", "León", "Juárez"],
    "ES": ["Madrid", "Barcelona", "Valencia", "Seville", "Zaragoza", "Málaga", "Murcia"],
    "IT": ["Rome", "Milan", "Naples", "Turin", "Palermo", "Genoa", "Bologna"],
    "NL": ["Amsterdam", "Rotterdam", "The Hague", "Utrecht", "Eindhoven", "Tilburg", "Groningen"],
    "SE": ["Stockholm", "Gothenburg", "Malmö", "Uppsala", "Västerås", "Örebro", "Linköping"],
    "CH": ["Zurich", "Geneva", "Basel", "Bern", "Lausanne", "Winterthur", "Lucerne"],
    "SG": ["Singapore"],
    "KR": ["Seoul", "Busan", "Incheon", "Daegu", "Daejeon", "Gwangju", "Suwon"],
    "CN": ["Beijing", "Shanghai", "Guangzhou", "Shenzhen", "Chengdu", "Hangzhou", "Wuhan"],
    "IE": ["Dublin", "Cork", "Galway", "Limerick", "Waterford", "Drogheda", "Dundalk"],
    "NZ": ["Auckland", "Wellington", "Christchurch", "Hamilton", "Tauranga", "Napier-Hastings", "Dunedin"],
    "ZA": ["Johannesburg", "Cape Town", "Durban", "Pretoria", "Port Elizabeth", "Bloemfontein", "East London"],
    "AE": ["Dubai", "Abu Dhabi", "Sharjah", "Ajman", "Ras Al Khaimah", "Fujairah", "Umm Al Quwain"],
    "AR": ["Buenos Aires", "Córdoba", "Rosario", "Mendoza", "Tucumán", "La Plata", "Mar del Plata"],
    "BE": ["Brussels", "Antwerp", "Ghent", "Charleroi", "Liège", "Bruges", "Namur"],
    "DK": ["Copenhagen", "Aarhus", "Odense", "Aalborg", "Frederiksberg", "Esbjerg", "Randers"],
    "NO": ["Oslo", "Bergen", "Trondheim", "Stavanger", "Drammen", "Fredrikstad", "Kristiansand"],
    "PL": ["Warsaw", "Kraków", "Łódź", "Wrocław", "Poznań", "Gdańsk", "Szczecin"],
    "RU": ["Moscow", "Saint Petersburg", "Novosibirsk", "Yekaterinburg", "Nizhny Novgorod", "Kazan", "Chelyabinsk"],
    "IL": ["Jerusalem", "Tel Aviv", "Haifa", "Rishon LeZion", "Petah Tikva", "Ashdod", "Netanya"],
    "TR": ["Istanbul", "Ankara", "Izmir", "Bursa", "Adana", "Gaziantep", "Konya"]
}

# Major US cities by state
US_CITIES_BY_STATE = {
    "AL": ["Birmingham", "Montgomery", "Mobile", "Huntsville", "Tuscaloosa"],
    "AK": ["Anchorage", "Fairbanks", "Juneau", "Sitka", "Ketchikan"],
    "AZ": ["Phoenix", "Tucson", "Mesa", "Chandler", "Scottsdale", "Glendale", "Tempe"],
    "AR": ["Little Rock", "Fort Smith", "Fayetteville", "Springdale", "Jonesboro"],
    "CA": ["Los Angeles", "San Francisco", "San Diego", "San Jose", "Sacramento", "Oakland", "Fresno", "Long Beach"],
    "CO": ["Denver", "Colorado Springs", "Aurora", "Fort Collins", "Lakewood", "Boulder"],
    "CT": ["Bridgeport", "New Haven", "Hartford", "Stamford", "Waterbury"],
    "DE": ["Wilmington", "Dover", "Newark", "Middletown", "Smyrna"],
    "FL": ["Miami", "Orlando", "Tampa", "Jacksonville", "St. Petersburg", "Fort Lauderdale", "Tallahassee"],
    "GA": ["Atlanta", "Augusta", "Columbus", "Savannah", "Athens", "Macon"],
    "HI": ["Honolulu", "Hilo", "Kailua", "Kapolei", "Kaneohe"],
    "ID": ["Boise", "Meridian", "Nampa", "Idaho Falls", "Pocatello"],
    "IL": ["Chicago", "Aurora", "Rockford", "Joliet", "Naperville", "Springfield"],
    "IN": ["Indianapolis", "Fort Wayne", "Evansville", "South Bend", "Carmel"],
    "IA": ["Des Moines", "Cedar Rapids", "Davenport", "Sioux City", "Iowa City"],
    "KS": ["Wichita", "Overland Park", "Kansas City", "Topeka", "Olathe"],
    "KY": ["Louisville", "Lexington", "Bowling Green", "Owensboro", "Covington"],
    "LA": ["New Orleans", "Baton Rouge", "Shreveport", "Lafayette", "Lake Charles"],
    "ME": ["Portland", "Lewiston", "Bangor", "South Portland", "Auburn"],
    "MD": ["Baltimore", "Frederick", "Rockville", "Gaithersburg", "Bowie"],
    "MA": ["Boston", "Worcester", "Springfield", "Cambridge", "Lowell", "New Bedford"],
    "MI": ["Detroit", "Grand Rapids", "Warren", "Sterling Heights", "Ann Arbor", "Lansing"],
    "MN": ["Minneapolis", "Saint Paul", "Rochester", "Duluth", "Bloomington"],
    "MS": ["Jackson", "Gulfport", "Southaven", "Hattiesburg", "Biloxi"],
    "MO": ["Kansas City", "St. Louis", "Springfield", "Columbia", "Independence"],
    "MT": ["Billings", "Missoula", "Great Falls", "Bozeman", "Butte"],
    "NE": ["Omaha", "Lincoln", "Bellevue", "Grand Island", "Kearney"],
    "NV": ["Las Vegas", "Henderson", "Reno", "North Las Vegas", "Sparks"],
    "NH": ["Manchester", "Nashua", "Concord", "Derry", "Dover"],
    "NJ": ["Newark", "Jersey City", "Paterson", "Elizabeth", "Trenton", "Camden"],
    "NM": ["Albuquerque", "Las Cruces", "Rio Rancho", "Santa Fe", "Roswell"],
    "NY": ["New York City", "Buffalo", "Rochester", "Yonkers", "Syracuse", "Albany"],
    "NC": ["Charlotte", "Raleigh", "Greensboro", "Durham", "Winston-Salem", "Fayetteville"],
    "ND": ["Fargo", "Bismarck", "Grand Forks", "Minot", "West Fargo"],
    "OH": ["Columbus", "Cleveland", "Cincinnati", "Toledo", "Akron", "Dayton"],
    "OK": ["Oklahoma City", "Tulsa", "Norman", "Broken Arrow", "Edmond"],
    "OR": ["Portland", "Salem", "Eugene", "Gresham", "Hillsboro", "Beaverton"],
    "PA": ["Philadelphia", "Pittsburgh", "Allentown", "Erie", "Reading", "Scranton"],
    "RI": ["Providence", "Warwick", "Cranston", "Pawtucket", "East Providence"],
    "SC": ["Columbia", "Charleston", "North Charleston", "Mount Pleasant", "Rock Hill"],
    "SD": ["Sioux Falls", "Rapid City", "Aberdeen", "Brookings", "Watertown"],
    "TN": ["Nashville", "Memphis", "Knoxville", "Chattanooga", "Clarksville", "Murfreesboro"],
    "TX": ["Houston", "Dallas", "San Antonio", "Austin", "Fort Worth", "El Paso", "Arlington"],
    "UT": ["Salt Lake City", "West Valley City", "Provo", "West Jordan", "Orem"],
    "VT": ["Burlington", "South Burlington", "Rutland", "Essex Junction", "Bennington"],
    "VA": ["Virginia Beach", "Norfolk", "Chesapeake", "Richmond", "Newport News", "Alexandria"],
    "WA": ["Seattle", "Spokane", "Tacoma", "Vancouver", "Bellevue", "Everett"],
    "WV": ["Charleston", "Huntington", "Morgantown", "Parkersburg", "Wheeling"],
    "WI": ["Milwaukee", "Madison", "Green Bay", "Kenosha", "Racine", "Appleton"],
    "WY": ["Cheyenne", "Casper", "Laramie", "Gillette", "Rock Springs"],
    "DC": ["Washington"]
}

# Add US cities to the MAJOR_CITIES dictionary
for state_code, cities in US_CITIES_BY_STATE.items():
    if state_code not in MAJOR_CITIES["US"]:
        MAJOR_CITIES["US"][state_code] = cities

# Custom CSS for dark theme and better styling
st.markdown("""
<style>
    /* Dark theme */
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #262730;
        min-width: 250px;
        max-width: 300px;
        padding: 2rem 1rem;
    }
    
    /* Main content area */
    .main .block-container {
        padding-top: 2rem;
        max-width: 1000px;
        margin: 0 auto;
    }
    
    /* Headers */
    .search-header {
        color: #ffffff;
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .search-subheader {
        color: #9e9e9e;
        font-size: 1rem;
        margin-bottom: 2rem;
    }
    
    .sidebar-header {
        color: #ffffff;
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 1rem;
        border-bottom: 1px solid #3a3a3a;
        padding-bottom: 0.5rem;
    }
    
    /* Search result styling */
    .search-result {
        background-color: #1e1e1e;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1.5rem;
    }
    
    /* Citation styling */
    .citation {
        background-color: #2d2d2d;
        border-left: 3px solid #4299e1;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0.3rem;
    }
    
    .citation-title {
        font-weight: 600;
        color: #4299e1;
    }
    
    .citation-url, .citation-file {
        color: #90cdf4;
        word-break: break-all;
    }
    
    .citation-quote {
        font-style: italic;
        color: #e2e8f0;
        border-left: 2px solid #4299e1;
        padding-left: 1rem;
        margin-top: 0.5rem;
    }
    
    .citation-link {
        color: #90cdf4;
        text-decoration: underline;
    }
    
    /* Button styling */
    .stButton button {
        background-color: #2196f3;
        color: white;
        font-weight: 600;
        border-radius: 0.3rem;
        padding: 0.5rem 1rem;
        width: 100%;
        border: none;
    }
    
    .stButton button:hover {
        background-color: #1976d2;
    }
    
    /* Input fields */
    [data-testid="stTextInput"] input {
        background-color: #3a3a3a;
        color: white;
        border: none;
        border-radius: 0.3rem;
        padding: 0.5rem;
    }
    
    /* Radio buttons */
    .stRadio label {
        color: #e0e0e0;
    }
    
    /* Checkbox */
    .stCheckbox label {
        color: #e0e0e0;
    }
    
    /* Expander */
    .stExpander {
        background-color: #2d2d2d;
        border-radius: 0.3rem;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        margin-top: 3rem;
        color: #9e9e9e;
        font-size: 0.8rem;
    }
    
    /* Help icons */
    [data-testid="stToolbar"] {
        display: none;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-color: #2196f3 !important;
    }
    
    /* Adjust width of text input */
    div[data-testid="stFormSubmitButton"] > button {
        width: 100%;
    }
    
    /* Hide fullscreen button */
    button[title="View fullscreen"] {
        display: none;
    }
    
    /* Hide hamburger menu */
    button[kind="header"] {
        display: none;
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #2d2d2d;
        border-radius: 4px 4px 0 0;
        padding: 10px 16px;
        color: #e0e0e0;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #1976d2 !important;
        color: white !important;
    }
    
    /* History item styling */
    .history-item {
        background-color: #2d2d2d;
        border-radius: 0.3rem;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    .history-query {
        font-weight: 600;
        color: #90cdf4;
    }
    
    .history-time {
        color: #9e9e9e;
        font-size: 0.8rem;
    }
    
    /* Settings panel */
    .settings-panel {
        background-color: #2d2d2d;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize OpenAI client


@st.cache_resource
def get_openai_client():
    """Initialize and return the OpenAI client."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        api_key = st.secrets.get("OPENAI_API_KEY", None)

    if not api_key:
        st.error(
            "OpenAI API key not found. Please set it in your .env file or Streamlit secrets.")
        st.stop()

    return openai.OpenAI(api_key=api_key)


client = get_openai_client()


def perform_file_search(query: str, vector_store_id: str = VECTOR_STORE_ID) -> Any:
    """
    Perform a file search using OpenAI's file search API.

    Args:
        query: The search query
        vector_store_id: The ID of the vector store to search

    Returns:
        The response from the OpenAI API
    """
    try:
        with st.spinner("Searching files..."):
            # Set up file search tool
            file_search_tool = {
                "type": "file_search",
                "vector_store_ids": [vector_store_id]
            }

            # Call OpenAI API with file search tool
            response = client.responses.create(
                model="gpt-4o-mini",
                tools=[file_search_tool],
                tool_choice={"type": "file_search"},
                input=query
            )

            return response
    except Exception as e:
        st.error(f"File search failed: {str(e)}")
        return None


def perform_web_search(query: str, location: Optional[Dict] = None, context_size: str = "medium", force_search: bool = True) -> Any:
    """
    Perform a web search using OpenAI's Web Search API.

    Args:
        query: The search query
        location: User location information (optional)
        context_size: Search context size ('low', 'medium', or 'high')
        force_search: Whether to force using web search

    Returns:
        The response from the OpenAI API
    """
    try:
        with st.spinner("Searching the web..."):
            # Set up web search tool
            web_search_tool = {
                "type": "web_search_preview",
                "search_context_size": context_size
            }

            # Add location data if provided
            if location:
                web_search_tool["user_location"] = {
                    "type": "approximate",
                    **location
                }

            # Set up tool choice if forcing search
            tool_choice = {
                "type": "web_search_preview"} if force_search else "auto"

            # Call OpenAI API with web search tool
            response = client.responses.create(
                model="gpt-4o-mini",
                tools=[web_search_tool],
                tool_choice=tool_choice,
                input=query
            )

            return response
    except Exception as e:
        st.error(f"Web search failed: {str(e)}")
        return None


def perform_combined_search(query: str, vector_store_id: str = VECTOR_STORE_ID,
                            location: Optional[Dict] = None, context_size: str = "medium") -> Any:
    """
    Perform a combined search using both file search and web search.

    Args:
        query: The search query
        vector_store_id: The ID of the vector store to search
        location: User location information (optional)
        context_size: Search context size for web search ('low', 'medium', or 'high')

    Returns:
        The response from the OpenAI API
    """
    try:
        with st.spinner("Performing combined search..."):
            # Set up both tools
            file_search_tool = {
                "type": "file_search",
                "vector_store_ids": [vector_store_id]
            }

            web_search_tool = {
                "type": "web_search_preview",
                "search_context_size": context_size
            }

            # Add location data if provided
            if location:
                web_search_tool["user_location"] = {
                    "type": "approximate",
                    **location
                }

            # Call OpenAI API with both tools
            response = client.responses.create(
                model="gpt-4o-mini",
                tools=[file_search_tool, web_search_tool],
                tool_choice="auto",  # Let the model decide which tool to use
                input=query
            )

            return response
    except Exception as e:
        st.error(f"Combined search failed: {str(e)}")
        return None


def get_output_text(response: Any) -> Optional[str]:
    """
    Extract the output text from a response.

    Args:
        response: The response from the OpenAI API

    Returns:
        The output text, or None if not found
    """
    try:
        # Check if response is a dictionary or JSON string
        if isinstance(response, str):
            try:
                response_data = json.loads(response)
            except json.JSONDecodeError:
                return None
        elif isinstance(response, dict):
            response_data = response
        else:
            # If it's an object with attributes
            response_data = response

        # Handle the structure shown in the example
        if hasattr(response_data, 'output'):
            for item in response_data.output:
                if item.type == "message" and hasattr(item, 'content'):
                    for content_item in item.content:
                        if content_item.type == "output_text":
                            return content_item.text

        # Alternative approach for the example structure
        if isinstance(response_data, list):
            for item in response_data:
                if item.get('type') == 'message' and 'content' in item:
                    for content_item in item['content']:
                        if content_item.get('type') == 'output_text':
                            return content_item.get('text')

        return None
    except Exception as e:
        st.error(f"Error extracting output text: {str(e)}")
        return None


def get_citations(response: Any) -> List[Dict]:
    """
    Extract citations from the response.

    Args:
        response: The response from the OpenAI API

    Returns:
        List of citation dictionaries
    """
    citations = []

    try:
        # Check if response is a dictionary or JSON string
        if isinstance(response, str):
            try:
                response_data = json.loads(response)
            except json.JSONDecodeError:
                return citations
        elif isinstance(response, dict):
            response_data = response
        else:
            # If it's an object with attributes
            response_data = response

        # Handle the structure shown in the example
        if hasattr(response_data, 'output'):
            for item in response_data.output:
                if item.type == "message" and hasattr(item, 'content'):
                    for content_item in item.content:
                        if content_item.type == "output_text" and hasattr(content_item, 'annotations'):
                            for idx, annotation in enumerate(content_item.annotations):
                                if annotation.type == "url_citation" or annotation.type == "file_citation":
                                    citation = {
                                        "number": idx + 1,
                                        "type": annotation.type,
                                        "title": getattr(annotation, 'title', "No title"),
                                        "url": getattr(annotation, 'url', None),
                                        "file_id": getattr(annotation, 'file_id', None),
                                        "quote": getattr(annotation, 'quote', None),
                                        "start_index": getattr(annotation, 'start_index', None),
                                        "end_index": getattr(annotation, 'end_index', None)
                                    }
                                    citations.append(citation)

        # Alternative approach for the example structure
        if isinstance(response_data, list):
            for item in response_data:
                if item.get('type') == 'message' and 'content' in item:
                    for content_item in item['content']:
                        if content_item.get('type') == 'output_text' and 'annotations' in content_item:
                            for idx, annotation in enumerate(content_item['annotations']):
                                if annotation.get('type') in ['url_citation', 'file_citation']:
                                    citation = {
                                        "number": idx + 1,
                                        "type": annotation.get('type'),
                                        "title": annotation.get('title', "No title"),
                                        "url": annotation.get('url', None),
                                        "file_id": annotation.get('file_id', None),
                                        "quote": annotation.get('quote', None),
                                        "start_index": annotation.get('start_index'),
                                        "end_index": annotation.get('end_index')
                                    }
                                    citations.append(citation)

        return citations
    except Exception as e:
        st.error(f"Error extracting citations: {str(e)}")
        return citations


def format_text_with_citations(text: str, citations: List[Dict]) -> str:
    """
    Format text with clickable citation links.

    Args:
        text: The text content
        citations: List of citation dictionaries

    Returns:
        HTML formatted text with citation links
    """
    if not citations:
        return text

    # Sort citations by start_index in reverse order to avoid index shifting
    sorted_citations = sorted(
        [c for c in citations if c["start_index"]
            is not None and c["end_index"] is not None],
        key=lambda x: x["start_index"],
        reverse=True
    )

    # Replace citation text with links
    result = text
    for citation in sorted_citations:
        start = citation["start_index"]
        end = citation["end_index"]
        if start is not None and end is not None and start < len(result) and end <= len(result):
            cited_text = result[start:end]

            if citation["type"] == "url_citation" and citation.get("url"):
                link = f'<a href="{citation["url"]}" target="_blank" class="citation-link">{cited_text}</a>'
            elif citation["type"] == "file_citation" and citation.get("file_id"):
                # For file citations, we can't link directly but we can highlight them
                link = f'<span class="citation-link">{cited_text}</span>'
            else:
                continue

            result = result[:start] + link + result[end:]

    return result


def display_search_results(response: Any, search_type: str) -> None:
    """
    Display search results in a formatted way.

    Args:
        response: The response from the OpenAI API
        search_type: The type of search performed ('file', 'web', or 'combined')
    """
    # Extract output text
    output_text = get_output_text(response)

    if not output_text:
        st.error(
            "No results found or unable to parse the response. Please try a different query.")

        # Debug information in an expander
        with st.expander("Debug Information", expanded=False):
            st.write("Response structure:")
            st.json(response if isinstance(response, dict) else {
                    "info": "Response is not a dictionary"})

        return False

    # Extract citations
    citations = get_citations(response)

    # Display the search results
    st.markdown('<div class="search-result">', unsafe_allow_html=True)

    # Format text with clickable citations
    formatted_text = format_text_with_citations(output_text, citations)
    st.markdown(formatted_text, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Display citations if any
    if citations:
        with st.expander("Sources", expanded=True):
            for citation in citations:
                if citation["type"] == "url_citation":
                    st.markdown(f"""
                    <div class="citation">
                        <div class="citation-title">{citation["title"]}</div>
                        <div class="citation-url"><a href="{citation["url"]}" target="_blank">{citation["url"]}</a></div>
                    </div>
                    """, unsafe_allow_html=True)
                elif citation["type"] == "file_citation":
                    st.markdown(f"""
                    <div class="citation">
                        <div class="citation-title">{citation["title"]}</div>
                        <div class="citation-file">File ID: {citation["file_id"]}</div>
                        {f'<div class="citation-quote">{citation["quote"]}</div>' if citation.get("quote") else ''}
                    </div>
                    """, unsafe_allow_html=True)

    return True


# Initialize session state for storing search history
if 'search_history' not in st.session_state:
    st.session_state.search_history = []

# Main app layout
st.markdown('<h1 class="search-header">OpenAI File & Web Search</h1>',
            unsafe_allow_html=True)
st.markdown('<p class="search-subheader">Search through your files and the web using OpenAI\'s powerful AI</p>', unsafe_allow_html=True)

# Sidebar for search options
st.sidebar.markdown(
    '<div class="sidebar-header">Search Options</div>', unsafe_allow_html=True)

# Search type selection
search_type = st.sidebar.radio(
    "Search Type",
    options=["file", "web", "combined"],
    index=2,  # Default to combined search
    help="Choose where to search for information"
)

# Vector store ID input (for file search)
if search_type in ["file", "combined"]:
    st.sidebar.markdown(
        '<div class="sidebar-header">File Search Settings</div>', unsafe_allow_html=True)
    vector_store_id = st.sidebar.text_input(
        "Vector Store ID",
        value=VECTOR_STORE_ID,
        help="The ID of your OpenAI vector store"
    )

# Web search settings
if search_type in ["web", "combined"]:
    st.sidebar.markdown(
        '<div class="sidebar-header">Web Search Settings</div>', unsafe_allow_html=True)

    # Context size selection
    context_size = st.sidebar.radio(
        "Search Context Size",
        options=["low", "medium", "high"],
        index=1,  # Default to medium
        help="Controls how much context is retrieved from the web"
    )

    # Force search option
    force_search = st.sidebar.checkbox(
        "Force Web Search",
        value=True,
        help="Force the model to use web search for every query"
    )

    # Location settings
    st.sidebar.markdown(
        '<div class="sidebar-header">Location Settings</div>', unsafe_allow_html=True)
    use_location = st.sidebar.checkbox("Specify Location", value=False)

    location = None
    if use_location:
        # Country selection dropdown
        country_options = [country["name"] for country in COUNTRIES]
        country_codes = {country["name"]: country["code"]
                         for country in COUNTRIES}

        selected_country = st.sidebar.selectbox(
            "Country",
            options=country_options,
            # Default to United States
            index=country_options.index("United States"),
            help="Select a country to localize search results"
        )

        selected_country_code = country_codes[selected_country]

        # State/Region selection (for US) or direct city selection (for other countries)
        if selected_country_code == "US":
            state_options = [state["name"] for state in US_STATES]
            state_codes = {state["name"]: state["code"] for state in US_STATES}

            selected_state = st.sidebar.selectbox(
                "State",
                options=state_options,
                help="Select a US state"
            )

            selected_state_code = state_codes[selected_state]

            # City selection based on selected state
            if selected_state_code in US_CITIES_BY_STATE:
                city_options = [""] + US_CITIES_BY_STATE[selected_state_code]
                selected_city = st.sidebar.selectbox(
                    "City",
                    options=city_options,
                    help="Select a city (optional)"
                )
            else:
                selected_city = st.sidebar.text_input(
                    "City", value="", help="Enter a city name (optional)")

            # Build location dictionary
            location = {"country": selected_country_code}
            if selected_state:
                location["region"] = selected_state
            if selected_city:
                location["city"] = selected_city

        else:
            # For non-US countries, show major cities dropdown if available
            if selected_country_code in MAJOR_CITIES:
                if isinstance(MAJOR_CITIES[selected_country_code], dict):
                    # Skip this case as it's only for US
                    selected_city = st.sidebar.text_input(
                        "City", value="", help="Enter a city name (optional)")
                    selected_region = st.sidebar.text_input(
                        "Region", value="", help="Enter a region name (optional)")
                else:
                    city_options = [""] + MAJOR_CITIES[selected_country_code]
                    selected_city = st.sidebar.selectbox(
                        "City",
                        options=city_options,
                        help="Select a city (optional)"
                    )
                    selected_region = st.sidebar.text_input(
                        "Region", value="", help="Enter a region name (optional)")
            else:
                selected_city = st.sidebar.text_input(
                    "City", value="", help="Enter a city name (optional)")
                selected_region = st.sidebar.text_input(
                    "Region", value="", help="Enter a region name (optional)")

            # Build location dictionary
            location = {"country": selected_country_code}
            if selected_region:
                location["region"] = selected_region
            if selected_city:
                location["city"] = selected_city

# About section
with st.sidebar.expander("About"):
    st.markdown("""
    This tool uses OpenAI's APIs to search through:
    
    - **Files** in your vector store
    - **Web** for current information
    - **Both** for comprehensive results
    
    **Features:**
    - File search with vector embeddings
    - Real-time web search
    - Location-based search
    - Citation tracking
    
    **Credits:**
    Powered by OpenAI's Responses API with file_search and web_search_preview tools.
    """)

# Main content area - Search input
query = st.text_input("Enter your search query", key="search_query",
                      help="What would you like to search for?")

# Search button
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    search_pressed = st.button(
        "Search", key="search_button", use_container_width=True)

# Process search when button is pressed
if search_pressed and query:
    # Perform search based on selected type
    if search_type == "file":
        response = perform_file_search(query, vector_store_id)
    elif search_type == "web":
        response = perform_web_search(
            query, location, context_size, force_search)
    else:  # combined
        response = perform_combined_search(
            query, vector_store_id, location, context_size)

    if response:
        # Add to search history
        st.session_state.search_history.append({
            "query": query,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "response": response,
            "search_type": search_type
        })

        # Display results
        display_search_results(response, search_type)

# Tabs for additional features
if st.session_state.search_history:
    st.markdown("<br>", unsafe_allow_html=True)
    tabs = st.tabs(["Search History", "Debug"])

    # Search History Tab
    with tabs[0]:
        st.markdown(
            '<div class="sidebar-header">Previous Searches</div>', unsafe_allow_html=True)

        for i, item in enumerate(reversed(st.session_state.search_history)):
            st.markdown(f"""
            <div class="history-item">
                <div class="history-query">{item['query']}</div>
                <div class="history-time">{item['timestamp']} • {item['search_type'].capitalize()} Search</div>
            </div>
            """, unsafe_allow_html=True)

            if st.button(f"View Results", key=f"history_{i}"):
                # Display results from history
                display_search_results(item['response'], item['search_type'])

            if i < len(st.session_state.search_history) - 1:
                st.markdown("<hr>", unsafe_allow_html=True)

    # Debug Tab
    with tabs[1]:
        st.markdown(
            '<div class="sidebar-header">Debug Information</div>', unsafe_allow_html=True)

        if st.session_state.search_history:
            latest_response = st.session_state.search_history[-1]['response']

            st.json(latest_response if isinstance(latest_response, dict)
                    else {"info": "Response is not a dictionary"})

# Footer
st.markdown("""
<div class="footer">
    <p>OpenAI File & Web Search Tool • Built with Streamlit</p>
</div>
""", unsafe_allow_html=True)
