"""Web tools: web_search, fetch_url."""

import httpx
from typing import Any, Dict

from backend.services.chat_service.tools.base import Tool


class WebSearchTool(Tool):
    """Tool for web searching."""
    
    def __init__(self):
        """Initialize web search tool."""
        super().__init__(
            name="web_search",
            description="Search the web for information",
            schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    }
                },
                "required": ["query"]
            },
            required_permissions=["web_search"]
        )
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute web search.
        
        Args:
            args: Tool arguments with 'query' key
            
        Returns:
            Dictionary with search results
        """
        query = args.get("query", "")
        if not query:
            return {"error": "Query is required"}
        
        # For MVP, we'll use DuckDuckGo's instant answer API
        # In production, you might use a proper search API
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Using DuckDuckGo instant answer API
                response = await client.get(
                    "https://api.duckduckgo.com/",
                    params={
                        "q": query,
                        "format": "json",
                        "no_html": "1",
                        "skip_disambig": "1"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    abstract = data.get("AbstractText", "")
                    answer = data.get("Answer", "")
                    
                    if abstract or answer:
                        return {
                            "query": query,
                            "result": abstract or answer,
                            "source": data.get("AbstractURL", "")
                        }
                    else:
                        return {
                            "query": query,
                            "result": f"No instant answer found for: {query}",
                            "note": "Consider using fetch_url to get more detailed information"
                        }
                else:
                    return {
                        "error": f"Search API returned status {response.status_code}",
                        "query": query
                    }
        
        except httpx.TimeoutException:
            return {"error": "Search request timed out", "query": query}
        except Exception as e:
            return {"error": f"Error performing search: {str(e)}", "query": query}


class FetchUrlTool(Tool):
    """Tool for fetching URL content."""
    
    def __init__(self):
        """Initialize fetch URL tool."""
        super().__init__(
            name="fetch_url",
            description="Fetch and extract readable text content from a URL",
            schema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to fetch"
                    }
                },
                "required": ["url"]
            },
            required_permissions=["fetch_url"]
        )
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute URL fetch.
        
        Args:
            args: Tool arguments with 'url' key
            
        Returns:
            Dictionary with URL content
        """
        url = args.get("url", "")
        if not url:
            return {"error": "URL is required"}
        
        # Basic URL validation
        if not url.startswith(("http://", "https://")):
            return {"error": "URL must start with http:// or https://"}
        
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(url, headers={
                    "User-Agent": "LocalAIAssistant/1.0"
                })
                
                if response.status_code == 200:
                    # Try to extract text content
                    content = response.text
                    
                    # Simple text extraction (remove HTML tags crudely)
                    # For production, use a proper HTML parser like BeautifulSoup
                    import re
                    # Remove script and style tags
                    content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
                    content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)
                    # Remove HTML tags
                    content = re.sub(r'<[^>]+>', ' ', content)
                    # Clean up whitespace
                    content = re.sub(r'\s+', ' ', content).strip()
                    
                    # Limit content length
                    max_length = 10000
                    if len(content) > max_length:
                        content = content[:max_length] + "... [truncated]"
                    
                    return {
                        "url": url,
                        "content": content,
                        "length": len(content),
                        "status_code": response.status_code
                    }
                else:
                    return {
                        "error": f"HTTP {response.status_code}",
                        "url": url,
                        "status_code": response.status_code
                    }
        
        except httpx.TimeoutException:
            return {"error": "Request timed out", "url": url}
        except httpx.RequestError as e:
            return {"error": f"Request failed: {str(e)}", "url": url}
        except Exception as e:
            return {"error": f"Error fetching URL: {str(e)}", "url": url}
