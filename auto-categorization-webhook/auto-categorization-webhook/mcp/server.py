"""
MCP (Model Context Protocol) Server for Ticket Knowledge Search.
Provides tools for searching historical ticket examples to aid classification.
"""
import json
import sys
import os
import logging
from typing import Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MCP Protocol constants
JSONRPC_VERSION = "2.0"
MCP_VERSION = "2024-11-05"


class MCPServer:
    """
    Simple MCP Server implementing the Model Context Protocol.
    Exposes ticket knowledge search as an MCP tool.
    """

    def __init__(self):
        self.server_info = {
            "name": "ticket-knowledge-mcp",
            "version": "1.0.0"
        }
        self.tools = self._define_tools()
        from mcp.tools import TicketKnowledgeTool
        self.ticket_tool = TicketKnowledgeTool()

    def _define_tools(self) -> list:
        """Define available MCP tools."""
        return [
            {
                "name": "search_ticket_examples",
                "description": "Search historical support ticket examples to find similar cases. Useful for improving ticket classification by finding relevant precedents.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query to find relevant ticket examples (e.g., 'login issue', 'payment failed', 'slow performance')"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default: 5, max: 10)",
                            "default": 5,
                            "minimum": 1,
                            "maximum": 10
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_category_examples",
                "description": "Get all ticket examples for a specific category to understand classification patterns.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "description": "Category name (Authentication, Billing, Technical, Network, Account, General Inquiry)"
                        }
                    },
                    "required": ["category"]
                }
            }
        ]

    def handle_request(self, request: dict) -> dict:
        """Handle incoming MCP JSON-RPC request."""
        method = request.get("method", "")
        req_id = request.get("id")
        params = request.get("params", {})

        logger.info(f"MCP Request: method={method}")

        try:
            if method == "initialize":
                result = self._handle_initialize(params)
            elif method == "tools/list":
                result = self._handle_tools_list()
            elif method == "tools/call":
                result = self._handle_tools_call(params)
            elif method == "notifications/initialized":
                return None  # Notification, no response needed
            else:
                return self._error_response(req_id, -32601, f"Method not found: {method}")

            return {
                "jsonrpc": JSONRPC_VERSION,
                "id": req_id,
                "result": result
            }
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return self._error_response(req_id, -32603, str(e))

    def _handle_initialize(self, params: dict) -> dict:
        """Handle MCP initialize handshake."""
        return {
            "protocolVersion": MCP_VERSION,
            "capabilities": {
                "tools": {}
            },
            "serverInfo": self.server_info
        }

    def _handle_tools_list(self) -> dict:
        """Return list of available tools."""
        return {"tools": self.tools}

    def _handle_tools_call(self, params: dict) -> dict:
        """Execute a tool call."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name == "search_ticket_examples":
            result = self.ticket_tool.search_examples(
                query=arguments.get("query", ""),
                max_results=arguments.get("max_results", 5)
            )
        elif tool_name == "get_category_examples":
            result = self.ticket_tool.get_category_examples(
                category=arguments.get("category", "")
            )
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result, indent=2)
                }
            ]
        }

    def _error_response(self, req_id: Any, code: int, message: str) -> dict:
        """Build JSON-RPC error response."""
        return {
            "jsonrpc": JSONRPC_VERSION,
            "id": req_id,
            "error": {"code": code, "message": message}
        }

    def run_stdio(self):
        """Run MCP server using stdio transport (standard for MCP)."""
        logger.info("MCP Server starting on stdio transport...")
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                request = json.loads(line)
                response = self.handle_request(request)
                if response is not None:
                    print(json.dumps(response), flush=True)
            except json.JSONDecodeError as e:
                error = {
                    "jsonrpc": JSONRPC_VERSION,
                    "id": None,
                    "error": {"code": -32700, "message": f"Parse error: {e}"}
                }
                print(json.dumps(error), flush=True)

    def run_http(self, host: str = "0.0.0.0", port: int = 8001):
        """Run MCP server as HTTP server for easier testing."""
        from http.server import HTTPServer, BaseHTTPRequestHandler
        import json

        server_instance = self

        class MCPHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length)
                try:
                    request = json.loads(body)
                    response = server_instance.handle_request(request)
                    response_bytes = json.dumps(response).encode()
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Content-Length', len(response_bytes))
                    self.end_headers()
                    self.wfile.write(response_bytes)
                except Exception as e:
                    self.send_response(500)
                    self.end_headers()

            def do_GET(self):
                if self.path == "/health":
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "ok", "server": "ticket-knowledge-mcp"}).encode())

            def log_message(self, format, *args):
                logger.info(f"HTTP {format}" % args)

        httpd = HTTPServer((host, port), MCPHandler)
        logger.info(f"MCP HTTP Server running at http://{host}:{port}")
        httpd.serve_forever()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Ticket Knowledge MCP Server")
    parser.add_argument("--transport", choices=["stdio", "http"], default="http")
    parser.add_argument("--port", type=int, default=8001)
    args = parser.parse_args()

    server = MCPServer()
    if args.transport == "stdio":
        server.run_stdio()
    else:
        server.run_http(port=args.port)
