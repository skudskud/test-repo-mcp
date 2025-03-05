#!/usr/bin/env python3
import asyncio
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP, Context
from browser import run_browser_agent
import logging
import os
import sys
import json
from pathlib import Path

# Configure ALL logging before any imports
logging.basicConfig(
    level=logging.DEBUG,
    filename='mcp_debug.log',  # Send debug logs to file
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Disable all existing loggers from writing to stdout/stderr
logging.getLogger().handlers = []

# Create JSON formatter for stdout
class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "type": "log",
            "level": record.levelname,
            "message": record.getMessage()
        })

# Setup stdout handler with JSON formatting
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setFormatter(JsonFormatter())

# Configure specific loggers
for logger_name in ['browser_use', 'root', 'mcp', 'server_module']:
    logger = logging.getLogger(logger_name)
    logger.propagate = False
    logger.addHandler(stdout_handler)

# Now safe to import and initialize other components
logger = logging.getLogger('server_module')
logger.debug({"message": "MCP Server Starting", "transport": os.getenv('MCP_TRANSPORT')})

# Load environment variables from .env file
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("uber_eats")

# In-memory storage for search results
search_results = {}

# Add these lines at the start of your main function or entry point
logger.debug("Server starting up")
logger.debug("Current working directory: %s", os.getcwd())
logger.debug("Environment variables: %s", os.environ)

# Add at start of main or server initialization
logger.debug("MCP Server Initialization")
logger.debug(f"Transport: {os.getenv('MCP_TRANSPORT')}")
logger.debug(f"Working Directory: {os.getcwd()}")
logger.debug(f"Python Path: {sys.executable}")

# Add startup marker
logger.debug("=" * 50)
logger.debug("MCP Server Starting")
logger.debug(f"Log file location: {logging.getLogger().handlers[0].baseFilename}")
logger.debug(f"Current directory: {os.getcwd()}")
logger.debug(f"Transport type: {os.getenv('MCP_TRANSPORT')}")
logger.debug(f"Python executable: {sys.executable}")

# Define the log_dict function before using it
def log_dict(message, data):
    try:
        logger.debug(json.dumps({"message": message, "data": data}))
    except Exception as e:
        logger.error(f"Logging error: {e}")

@mcp.tool()
async def find_menu_options(search_term: str, context: Context) -> str:
    """Search Uber Eats for restaurants or food items.
    
    Args:
        search_term: Food or restaurant to search for
    """
    
    # Create the search task
    task = f"""
0. Start by going to: https://www.ubereats.com/se-en/
1. Type "{search_term}" in the global search bar and press enter
2. Go to the first search result (this is the most popular restaurant).
3. When you can see the menu options for the resturant, we need to use the specific search input for the resturant located under the banned (identify it by the placeholder "Search in [restaurant name]"
4. Click the input field and type "{search_term}", then press enter
5. Check for menu options related to "{search_term}"
6. Get the name, url and price of the top 3 items related to "{search_term}". URL is very important
"""
    
    search_results[context.request_id] = f"Search for '{search_term}' in progress. Check back in 30 seconds"

    asyncio.create_task(
        perform_search(context.request_id, search_term, task, context)
    )    
    
    return f"Search for '{search_term}' started. Please wait for 2 minutes, then you can retrieve results using the resource URI: resource://search_results/{context.request_id}. Use a terminal sleep statement to wait for 2 minutes."

async def perform_search(request_id: str, search_term: str, task: str, context: Context):
    """Perform the actual search in the background."""
    try:
        step_count = 0
        
        async def step_handler(*args, **kwargs):
            nonlocal step_count
            step_count += 1
            await context.info(f"Step {step_count} completed")
            await context.report_progress(step_count)
        
        result = await run_browser_agent(task=task, on_step=step_handler)
        
        search_results[request_id] = result
    
    except Exception as e:
        # Store the error with the request ID
        search_results[request_id] = f"Error: {str(e)}"
        await context.error(f"Error searching for '{search_term}': {str(e)}")

@mcp.resource(uri="resource://search_results/{request_id}")
async def get_search_results(request_id: str) -> str:
    """Get the search results for a given request ID.
    
    Args:
        request_id: The ID of the request to get the search results for
    """
    # Check if the results exist
    if request_id not in search_results:
        return f"No search results found for request ID: {request_id}"
    
    # Return the successful search results
    return search_results[request_id]

@mcp.tool()
async def order_food(item_url: str, item_name: str, context: Context) -> str:
    """Order food from a restaurant.
    
    Args:
        restaurant_url: URL of the restaurant
        item_name: Name of the item to order
    """
    
    task = f"""
1. Go to {item_url}
2. Click "Add to order"
3. Wait 3 seconds
4. Click "Go to checkout"
5. If there are upsell modals, click "Skip"
6. Click "Place order"
"""
    
    # Start the background task for ordering
    asyncio.create_task(
        perform_order(item_url, item_name, task, context)
    )
    
    # Return a message immediately
    return f"Order for '{item_name}' started. Your order is being processed."

async def perform_order(restaurant_url: str, item_name: str, task: str, context: Context):
    """Perform the actual food ordering in the background."""
    try:
        step_count = 0
        
        async def step_handler(*args, **kwargs):
            nonlocal step_count
            step_count += 1
            await context.info(f"Order step {step_count} completed")
            await context.report_progress(step_count)
        
        result = await run_browser_agent(task=task, on_step=step_handler)
        
        # Report completion
        await context.info(f"Order for '{item_name}' has been placed successfully!")
        return result
    
    except Exception as e:
        error_msg = f"Error ordering '{item_name}': {str(e)}"
        await context.error(error_msg)
        return error_msg

if __name__ == "__main__":
    mcp.run(transport='stdio') 
