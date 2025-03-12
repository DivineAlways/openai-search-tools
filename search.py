#!/usr/bin/env python3
import os
import argparse
import json
import openai
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.table import Table
from rich.syntax import Syntax
from rich import box
from rich.text import Text

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client with API key
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize Rich console
console = Console()


def perform_search(query, location=None, context_size="medium", force_search=False):
    """
    Perform a web search using OpenAI's Web Search API via the Responses API

    Args:
        query (str): The search query
        location (dict, optional): User location information
        context_size (str): Search context size ('low', 'medium', or 'high')
        force_search (bool): Whether to force using web search

    Returns:
        dict: The search results
    """
    with Progress() as progress:
        task = progress.add_task("[cyan]Searching the web...", total=1)

        try:
            # Set up web search tool according to official docs
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
                model="gpt-4o",  # Using the standard model as per docs
                tools=[web_search_tool],
                tool_choice=tool_choice,
                input=query
            )

            progress.update(task, advance=1)
            return response

        except Exception as e:
            progress.update(task, advance=1)
            raise Exception(f"Search failed: {str(e)}")


def get_output_text(response):
    """
    Helper function to extract the output text from a response

    Args:
        response: The response from the OpenAI API

    Returns:
        str: The output text, or None if not found
    """
    # Try to get the output_text property directly
    if hasattr(response, 'output_text'):
        return response.output_text

    # If not available, try to extract it from the output items
    if hasattr(response, 'output'):
        for item in response.output:
            if item.type == "message" and hasattr(item, 'content'):
                for content_item in item.content:
                    if content_item.type == "output_text":
                        return content_item.text

    return None


def display_search_results(response, query):
    """
    Display search results in a nicely formatted way

    Args:
        response: The response from the OpenAI API
        query (str): The original search query
    """
    console.print(Panel(f"[bold blue]Search Results for:[/bold blue] [yellow]{query}[/yellow]",
                        border_style="blue", expand=False))

    try:
        # Check if we have a web search call in the response
        web_search_call = None
        message = None

        # The response.output contains the list of outputs
        if hasattr(response, 'output'):
            for item in response.output:
                if item.type == "web_search_call":
                    web_search_call = item
                elif item.type == "message":
                    message = item

        if message and hasattr(message, 'content'):
            # Get the text content
            content_item = next(
                (c for c in message.content if c.type == "output_text"), None)

            if content_item:
                content = content_item.text

                # Check if there are URL citations in the response
                if hasattr(content_item, 'annotations') and content_item.annotations:
                    # Collect citation data
                    citations = []
                    for idx, annotation in enumerate(content_item.annotations):
                        if annotation.type == "url_citation":
                            citations.append({
                                "number": idx + 1,
                                "title": annotation.title if hasattr(annotation, 'title') else "No title",
                                "url": annotation.url
                            })

                    # Display the formatted content
                    console.print(Panel(Markdown(content),
                                        title="[bold]Search Results[/bold]",
                                        border_style="green",
                                        expand=True))

                    # Display citations table if any exist
                    if citations:
                        citation_table = Table(
                            title="Sources", box=box.ROUNDED)
                        citation_table.add_column(
                            "[#]", style="cyan", no_wrap=True)
                        citation_table.add_column("Title", style="magenta")
                        citation_table.add_column("URL", style="blue")

                        for citation in citations:
                            citation_table.add_row(
                                f"[{citation['number']}]",
                                citation['title'],
                                citation['url']
                            )

                        console.print(citation_table)
                else:
                    # No citations, just display the text
                    console.print(Panel(Markdown(content),
                                        title="[bold]AI Assistant Response[/bold]",
                                        border_style="green",
                                        expand=True))
            else:
                console.print(
                    "[bold red]No text content found in the response.[/bold red]")
        else:
            # For convenience, let's also add a shortcut to access the text directly
            output_text = get_output_text(response)
            if output_text:
                console.print(Panel(Markdown(output_text),
                                    title="[bold]AI Assistant Response[/bold]",
                                    border_style="green",
                                    expand=True))
            else:
                console.print(
                    "[bold red]No message content found in the response.[/bold red]")

    except Exception as e:
        console.print(
            f"[bold red]Error processing results: {str(e)}[/bold red]")
        # Print raw response for debugging
        console.print(Panel(str(response), title="[bold red]Raw Response (Debug)[/bold red]",
                            border_style="red", expand=False))


def interactive_search():
    """Run an interactive search session in the terminal"""
    console.print(Panel.fit("[bold cyan]OpenAI Web Search Tool[/bold cyan]",
                            subtitle="[italic]Powered by OpenAI & Rich[/italic]"))

    while True:
        query = Prompt.ask(
            "\n[bold green]Enter your search query[/bold green] (or 'exit' to quit)")

        if query.lower() in ('exit', 'quit', 'q'):
            console.print(
                "[yellow]Thank you for using the OpenAI Web Search Tool. Goodbye![/yellow]")
            break

        try:
            # Get context size preference
            context_choices = {
                "1": "low",
                "2": "medium",
                "3": "high"
            }
            context_choice = Prompt.ask(
                "[bold green]Search context size[/bold green] (1=low, 2=medium, 3=high)",
                default="2",
                choices=["1", "2", "3"]
            )
            context_size = context_choices[context_choice]

            # Ask if user wants to force web search
            force_search = Prompt.ask(
                "[bold green]Force web search?[/bold green]",
                default="n",
                choices=["y", "n"]
            ).lower() == "y"

            # Ask if user wants to specify location
            use_location = Prompt.ask(
                "[bold green]Specify location?[/bold green]",
                default="n",
                choices=["y", "n"]
            )

            location = None
            if use_location.lower() == "y":
                country = Prompt.ask(
                    "[green]Country code[/green] (2-letter ISO code, e.g. US)", default="US")
                city = Prompt.ask("[green]City[/green]", default="")
                region = Prompt.ask("[green]Region/State[/green]", default="")

                location = {}
                if country:
                    location["country"] = country
                if city:
                    location["city"] = city
                if region:
                    location["region"] = region

            with console.status("[bold green]Searching the web...[/bold green]"):
                response = perform_search(
                    query, location=location, context_size=context_size, force_search=force_search)

            display_search_results(response, query)

            # Display attribution
            console.print(
                "\n[dim italic]Results provided by OpenAI Web Search[/dim italic]")
        except Exception as e:
            console.print(f"[bold red]Error: {str(e)}[/bold red]")


def main():
    parser = argparse.ArgumentParser(description="OpenAI Web Search CLI Tool")
    parser.add_argument("-q", "--query", help="Search query")
    parser.add_argument("--context", choices=["low", "medium", "high"], default="medium",
                        help="Search context size (default: medium)")
    parser.add_argument("--force", action="store_true",
                        help="Force using web search")
    parser.add_argument(
        "--country", help="Two-letter ISO country code (e.g., US)")
    parser.add_argument("--city", help="City name")
    parser.add_argument("--region", help="Region/State name")
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug mode (shows raw API responses)")
    args = parser.parse_args()

    if args.query:
        # Single search mode
        try:
            # Set up location if provided
            location = None
            if args.country or args.city or args.region:
                location = {}
                if args.country:
                    location["country"] = args.country
                if args.city:
                    location["city"] = args.city
                if args.region:
                    location["region"] = args.region

            with console.status("[bold green]Searching the web...[/bold green]"):
                response = perform_search(
                    args.query,
                    location=location,
                    context_size=args.context,
                    force_search=args.force
                )

            # If debug mode is enabled, print the raw response
            if args.debug:
                console.print(Panel(str(response), title="[bold cyan]Raw Response[/bold cyan]",
                                    border_style="cyan", expand=False))

            display_search_results(response, query=args.query)
        except Exception as e:
            console.print(f"[bold red]Error: {str(e)}[/bold red]")
            if args.debug:
                import traceback
                console.print(Panel(traceback.format_exc(), title="[bold red]Debug Traceback[/bold red]",
                                    border_style="red", expand=False))
    else:
        # Interactive mode
        interactive_search()


if __name__ == "__main__":
    main()
