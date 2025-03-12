#!/usr/bin/env python3
"""
OpenAI File Search and Web Search Tool

A terminal-based tool for searching through files in an OpenAI vector store
and performing web searches using OpenAI's APIs.
"""

import os
import sys
import json
import argparse
from typing import Dict, List, Optional, Union, Any
import openai
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt, Confirm
from rich.progress import Progress
from rich.table import Table
from rich.text import Text
from rich.style import Style
from rich.box import ROUNDED
from rich.syntax import Syntax
from dotenv import load_dotenv
import re

# Load environment variables from .env file
load_dotenv()

# Initialize Rich console
console = Console()

# Vector store ID
VECTOR_STORE_ID = "vs_67d0cc79ab4c8191a92661559e49dbd2"

# Initialize OpenAI client


def get_openai_client():
    """Initialize and return the OpenAI client."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        console.print(
            "[bold red]Error:[/bold red] OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
        sys.exit(1)
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
        raise Exception(f"File search failed: {str(e)}")


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
        raise Exception(f"Web search failed: {str(e)}")


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
        raise Exception(f"Combined search failed: {str(e)}")


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
        console.print(
            f"[bold red]Error extracting output text:[/bold red] {str(e)}")
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
        console.print(
            f"[bold red]Error extracting citations:[/bold red] {str(e)}")
        return citations


def display_search_results(response: Any, search_type: str) -> None:
    """
    Display search results in a formatted way.

    Args:
        response: The response from the OpenAI API
        search_type: The type of search performed ('file', 'web', or 'combined')
    """
    try:
        # Extract output text
        output_text = get_output_text(response)

        if not output_text:
            console.print(
                "[bold red]Error:[/bold red] No output text found in the response.")
            return

        # Extract citations
        citations = get_citations(response)

        # Display the search results
        console.print(Panel(
            Markdown(output_text),
            title=f"[bold blue]{search_type.capitalize()} Search Results[/bold blue]",
            border_style="blue",
            expand=False,
            padding=(1, 2)
        ))

        # Display citations if any
        if citations:
            table = Table(title="Citations", box=ROUNDED,
                          show_header=True, header_style="bold magenta")

            # Add appropriate columns based on citation types
            has_web_citations = any(
                c.get("type") == "url_citation" for c in citations)
            has_file_citations = any(
                c.get("type") == "file_citation" for c in citations)

            table.add_column("#", style="dim", width=3)
            table.add_column("Type", style="cyan")
            table.add_column("Title", style="green")

            if has_web_citations:
                table.add_column("URL", style="blue")

            if has_file_citations:
                table.add_column("File ID", style="yellow")
                table.add_column("Quote", style="italic")

            for citation in citations:
                row = [
                    str(citation["number"]),
                    citation["type"].replace("_citation", "").capitalize(),
                    citation["title"]
                ]

                if has_web_citations:
                    row.append(citation.get("url", "N/A")
                               if citation["type"] == "url_citation" else "N/A")

                if has_file_citations:
                    row.append(citation.get("file_id", "N/A")
                               if citation["type"] == "file_citation" else "N/A")
                    row.append(citation.get("quote", "N/A")
                               if citation["type"] == "file_citation" else "N/A")

                table.add_row(*row)

            console.print(table)

    except Exception as e:
        console.print(
            f"[bold red]Error processing results:[/bold red] {str(e)}")


def interactive_mode() -> None:
    """Run the search tool in interactive mode."""
    console.print(Panel(
        "[bold]OpenAI File & Web Search Tool[/bold]\n\n"
        "This tool allows you to search through files in your vector store and the web using OpenAI's APIs.\n"
        "Type [bold cyan]'exit'[/bold cyan] or [bold cyan]'quit'[/bold cyan] to exit, or press [bold cyan]Ctrl+C[/bold cyan] at any time.\n"
        "Type [bold cyan]'settings'[/bold cyan] to configure search options.",
        title="Welcome",
        border_style="green",
        expand=False
    ))

    # Default settings
    search_type = "combined"
    context_size = "medium"
    vector_store_id = VECTOR_STORE_ID
    location = None

    try:
        while True:
            # Display current settings
            settings_table = Table(
                title="Current Settings", box=ROUNDED, show_header=True, header_style="bold cyan")
            settings_table.add_column("Setting", style="dim")
            settings_table.add_column("Value", style="green")

            settings_table.add_row("Search Type", search_type.capitalize())
            settings_table.add_row("Vector Store ID", vector_store_id)
            settings_table.add_row("Context Size", context_size)
            settings_table.add_row("Location", str(
                location) if location else "None")

            console.print(settings_table)

            # Get user query
            query = Prompt.ask(
                "\n[bold blue]Enter your search query[/bold blue] ([bold cyan]exit/quit/settings[/bold cyan])")

            if query.lower() in ['exit', 'quit']:
                console.print("[bold green]Goodbye![/bold green]")
                break

            if query.lower() == 'settings':
                # Allow user to change settings
                console.print("\n[bold]Change Settings[/bold]")

                # Choose search type
                search_type_options = ["file", "web", "combined"]
                search_type_idx = search_type_options.index(search_type)

                search_type = Prompt.ask(
                    "Search type",
                    choices=search_type_options,
                    default=search_type_options[search_type_idx]
                )

                # Set context size for web search
                if search_type in ["web", "combined"]:
                    context_size_options = ["low", "medium", "high"]
                    context_size_idx = context_size_options.index(context_size)

                    context_size = Prompt.ask(
                        "Context size for web search",
                        choices=context_size_options,
                        default=context_size_options[context_size_idx]
                    )

                # Set vector store ID for file search
                if search_type in ["file", "combined"]:
                    vector_store_id = Prompt.ask(
                        "Vector store ID",
                        default=vector_store_id
                    )

                # Set location for web search
                if search_type in ["web", "combined"]:
                    use_location = Confirm.ask(
                        "Specify location?", default=False)

                    if use_location:
                        country = Prompt.ask(
                            "Country code (e.g., US)", default="US")
                        city = Prompt.ask("City", default="")
                        region = Prompt.ask("Region/State", default="")

                        location = {}
                        if country:
                            location["country"] = country
                        if city:
                            location["city"] = city
                        if region:
                            location["region"] = region
                    else:
                        location = None

                continue

            # Perform search based on selected type
            with Progress() as progress:
                task = progress.add_task(
                    f"[cyan]Performing {search_type} search...", total=1)

                try:
                    if search_type == "file":
                        response = perform_file_search(query, vector_store_id)
                    elif search_type == "web":
                        response = perform_web_search(
                            query, location, context_size)
                    else:  # combined
                        response = perform_combined_search(
                            query, vector_store_id, location, context_size)

                    progress.update(task, completed=1)

                    # Display results
                    display_search_results(response, search_type)

                except Exception as e:
                    progress.update(task, completed=1)
                    console.print(f"[bold red]Error:[/bold red] {str(e)}")

    except KeyboardInterrupt:
        console.print(
            "\n[bold green]Search interrupted. Goodbye![/bold green]")
        return


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="OpenAI File & Web Search Tool")

    parser.add_argument("-q", "--query", type=str, help="Search query")
    parser.add_argument("--type", choices=["file", "web", "combined"], default="combined",
                        help="Type of search to perform (default: combined)")
    parser.add_argument("--vector-store-id", type=str, default=VECTOR_STORE_ID,
                        help=f"Vector store ID for file search (default: {VECTOR_STORE_ID})")
    parser.add_argument("--context", choices=["low", "medium", "high"], default="medium",
                        help="Search context size for web search (default: medium)")
    parser.add_argument("--country", type=str,
                        help="Two-letter ISO country code (e.g., US)")
    parser.add_argument("--city", type=str, help="City name")
    parser.add_argument("--region", type=str, help="Region/State name")
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug mode")

    return parser.parse_args()


def main():
    """Main entry point for the script."""
    args = parse_arguments()

    try:
        if args.query:
            # Command-line mode
            location = None
            if args.country or args.city or args.region:
                location = {}
                if args.country:
                    location["country"] = args.country
                if args.city:
                    location["city"] = args.city
                if args.region:
                    location["region"] = args.region

            try:
                with Progress() as progress:
                    task = progress.add_task(
                        f"[cyan]Performing {args.type} search...", total=1)

                    if args.type == "file":
                        response = perform_file_search(
                            args.query, args.vector_store_id)
                    elif args.type == "web":
                        response = perform_web_search(
                            args.query, location, args.context)
                    else:  # combined
                        response = perform_combined_search(
                            args.query, args.vector_store_id, location, args.context)

                    progress.update(task, completed=1)

                # Display debug information if requested
                if args.debug:
                    console.print(Panel(
                        Syntax(json.dumps(response, indent=2), "json",
                               theme="monokai", line_numbers=True),
                        title="[bold red]Debug: Raw API Response[/bold red]",
                        border_style="red",
                        expand=False
                    ))

                # Display results
                display_search_results(response, args.type)

            except Exception as e:
                console.print(f"[bold red]Error:[/bold red] {str(e)}")
        else:
            # Interactive mode
            interactive_mode()
    except KeyboardInterrupt:
        console.print(
            "\n[bold green]Search interrupted. Goodbye![/bold green]")
        return 0


if __name__ == "__main__":
    main()
