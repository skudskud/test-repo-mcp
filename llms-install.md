# AI Agents -- Read this!

This guide provides instructions for AI agents to set up the Uber Eats MCP server on behalf of the user.

## Prerequisites

- Python 3.12 or higher
- Anthropic API key or other supported LLM provider

## Setup

1. Create and activate a virtual environment:

   ```
   uv venv
   source .venv/bin/activate  # On Unix/Mac
   ```

2. Install required packages:
   ```
   uv pip install -r requirements.txt
   playwright install
   ```

## MCP Configuration

To use this server with MCP-compatible applications, you need to add it to your MCP settings file:

**Important Notes:**

- Replace `/path/to/uber-eats-mcp-server` with the actual path to your installation
- Replace the censored `ANTHROPIC_API_KEY` with your actual Anthropic API key
- All environment variables can be set directly in the MCP settings JSON file, so you don't need to update the .env file separately
- The command uses `/bin/bash` to activate the virtual environment before running the server
- You may need to restart your application after updating the MCP settings

## Available Tools

This MCP server provides the following tools:

1. `find_menu_options`: Search Uber Eats for restaurants or food items

   - Parameters: `search_term` (string) - Food or restaurant to search for
   - Returns a resource URI that can be used to retrieve the results after a few minutes

2. `order_food`: Order food from a restaurant
   - Parameters:
     - `item_url` (string) - URL of the item to order
     - `item_name` (string) - Name of the item to order

## Example Usage

```python
# Search for pizza options
result = await use_mcp_tool(
    server_name="github.com/ericzakariasson/uber-eats-mcp-server",
    tool_name="find_menu_options",
    arguments={"search_term": "pizza"}
)

# Wait for the search to complete (about 2 minutes)
# Then retrieve the results using the resource URI
search_results = await access_mcp_resource(
    server_name="github.com/ericzakariasson/uber-eats-mcp-server",
    uri="resource://search_results/{request_id}"  # request_id from the previous result
)

# Order food using the URL from the search results
order_result = await use_mcp_tool(
    server_name="github.com/ericzakariasson/uber-eats-mcp-server",
    tool_name="order_food",
    arguments={
        "item_url": "https://www.ubereats.com/...",  # URL from search results
        "item_name": "Pepperoni Pizza"
    }
)
```

## Troubleshooting

If you encounter connection issues:

1. Make sure the virtual environment is activated in the MCP settings file command
2. Check that the paths in your MCP settings file are correct
3. Verify that your Anthropic API key is valid
4. Try adjusting the log levels in the env section of your MCP settings
5. Restart your application after making changes to the MCP settings