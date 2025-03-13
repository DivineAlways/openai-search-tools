# OpenAI Search Tools

A collection of tools for searching through files and the web using OpenAI's APIs.

## Features

- **File Search**: Search through files in your OpenAI vector store
- **Web Search**: Search the web for current information
- **Combined Search**: Use both file and web search for comprehensive results
- **Multiple Interfaces**: Choose between terminal-based or web-based UI
- **Enhanced Location Selection**: Specify country, state/region, and city for localized results
- **Citation Tracking**: View and access sources for search results
- **User-Friendly UI**: Modern, responsive interfaces for both terminal and web applications

## Available Tools

### 1. Terminal-Based Search Tool (`search.py`)

A command-line interface for performing web searches using OpenAI's Web Search API.

**Key Features:**

- Simple command-line arguments
- Interactive mode for multiple searches
- Rich text formatting for results
- Citation tracking and display
- Basic location specification

### 2. Terminal-Based File & Web Search Tool (`file_search.py`)

A comprehensive terminal tool that supports file search, web search, and combined search with rich formatting.

**Key Features:**

- Interactive menu-driven interface
- Support for file, web, and combined searches
- Vector store integration
- Enhanced error handling
- Rich text output with citations

### 3. Streamlit Web Search Interface (`streamlit_search.py`)

A web-based interface for OpenAI's Web Search API with a modern UI.

**Key Features:**

- Clean, responsive web interface
- Advanced location selection with country/state/city dropdowns
- Search history tracking
- Clickable citations
- Customizable search options
- Dark theme with modern styling

### 4. Streamlit File & Web Search Interface (`streamlit_file_search.py`)

A full-featured web application that combines file search and web search capabilities with an intuitive interface.

**Key Features:**

- Comprehensive search options (file, web, combined)
- Advanced location selection with country/state/city dropdowns
- Vector store management
- Search history tracking
- Detailed result display with citations
- Modern, responsive design

## Installation

1. Clone this repository:

   ```
   git clone https://github.com/dynamikapps/openai-search-tools.git
   cd openai-search-tools
   ```

2. Install the required dependencies:

   ```
   pip install -r requirements.txt
   ```

3. Set up your OpenAI API key:
   - Create a `.env` file in the project root
   - Add your API key: `OPENAI_API_KEY=your_api_key_here`

### Using Conda Environment (Recommended)

1. Install Miniconda or Anaconda if you haven't already:

   - [Miniconda](https://docs.conda.io/en/latest/miniconda.html)
   - [Anaconda](https://www.anaconda.com/products/distribution)

2. Create a new conda environment:

   ```bash
   conda create -n openai-search python=3.10
   ```

3. Activate the environment:

   ```bash
   conda activate openai-search
   ```

4. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

5. When you're done using the tools, you can deactivate the environment:

   ```bash
   conda deactivate
   ```

## Usage

### Terminal-Based Tools

#### Web Search Tool

```bash
# Basic usage
python search.py "your search query"

# With options
python search.py "your search query" --context medium --force

# Interactive mode
python search.py --interactive
```

#### File & Web Search Tool

```bash
# Interactive mode
python file_search.py

# Command-line mode
python file_search.py -q "your search query" --type combined
python file_search.py -q "your search query" --type file --vector-store-id "your_vector_store_id"
python file_search.py -q "your search query" --type web --country US --city "New York"
```

### Streamlit Web Interfaces

#### Web Search Interface

```bash
streamlit run streamlit_search.py
```

Features:

- Enter your search query in the text input field
- Customize search options in the sidebar:
  - Select context size (low, medium, high)
  - Force web search option
  - Specify location with country/state/city dropdowns
- View search results with clickable citations
- Access search history

#### File & Web Search Interface

```bash
streamlit run streamlit_file_search.py
```

Features:

- Choose between file search, web search, or combined search
- Configure vector store settings for file search
- Specify location with country/state/city dropdowns
- Customize search options
- View and manage search history
- Access detailed citation information

## Location Selection

Both Streamlit applications now feature enhanced location selection:

- **Country Selection**: Choose from 30 common countries
- **State/Region Selection**:
  - For US: All 50 states plus DC available as dropdown options
  - For other countries: Optional region text input
- **City Selection**:
  - For US: Major cities by state available as dropdown options
  - For other countries: Major cities available as dropdown options

This feature helps provide more localized and relevant search results based on geographic context.

## Configuration

### Vector Store ID

The default vector store ID is set to `vs_67d0cc79ab4cfdcwmdT38dfGvwdkp`. You can change this in the settings or via command-line arguments.

### Search Context Size

You can choose between three context sizes for web search:

- **Low**: Minimal context, faster response, lower cost
- **Medium**: Balanced context, speed, and cost (default)
- **High**: Maximum context, slower response, higher cost

### Location Settings

Customize search results by specifying:

- Country (selected from dropdown menu)
- Region/State (selected from dropdown for US, text input for others)
- City (selected from dropdown based on country/state)

## Requirements

- Python 3.10+
- OpenAI API key with access to the Responses API
- Required Python packages:
  - openai>=1.66.0
  - rich>=13.3.0
  - python-dotenv>=1.0.0
  - streamlit>=1.30.0
  - pandas>=2.0.0

## License

MIT License

## Acknowledgements

- This project uses OpenAI's Responses API with web_search_preview and file_search tools
- UI components powered by Rich (terminal) and Streamlit (web)
- Location data includes 30 countries, all US states, and major cities worldwide
