"""
MCP Client for AI Employee - Silver Tier

Universal MCP client for calling MCP servers via HTTP or stdio.
Used by Agent Skills to interact with external services.

Usage:
    # List tools from HTTP server
    python mcp-client.py list --url http://localhost:8808

    # Call a tool via HTTP
    python mcp-client.py call --url http://localhost:8808 --tool browser_navigate \
        --params '{"url": "https://example.com"}'

    # List tools from stdio server
    python mcp-client.py list --stdio "node mcp-servers/email-mcp/index.js"

    # Call a tool via stdio
    python mcp-client.py call --stdio "node mcp-servers/email-mcp/index.js" \
        --tool send_email --params '{"to": "user@example.com", "subject": "Hi"}'

    # Emit tool schemas as markdown
    python mcp-client.py emit --url http://localhost:8808 > tools.md
"""

import argparse
import json
import subprocess
import sys
import asyncio
from typing import Optional, Dict, Any


class MCPClient:
    """Universal MCP client for HTTP and stdio transports."""

    def __init__(self, url: str = None, stdio_command: str = None):
        self.url = url
        self.stdio_command = stdio_command
        self.process = None

    async def _read_stream(self, stream, timeout: float = 30.0) -> str:
        """Read from stream with timeout."""
        try:
            data = await asyncio.wait_for(stream.read(), timeout=timeout)
            return data.decode('utf-8') if isinstance(data, bytes) else data
        except asyncio.TimeoutError:
            return ""

    async def call_tool_http(self, tool_name: str, params: Dict[str, Any]) -> Dict:
        """Call a tool via HTTP MCP server."""
        import urllib.request
        import urllib.error

        endpoint = f"{self.url}/call"
        payload = json.dumps({
            "tool": tool_name,
            "params": params
        }).encode('utf-8')

        req = urllib.request.Request(
            endpoint,
            data=payload,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result
        except urllib.error.HTTPError as e:
            return {"error": f"HTTP {e.code}: {e.read().decode('utf-8')}"}
        except Exception as e:
            return {"error": str(e)}

    async def list_tools_http(self) -> Dict:
        """List available tools via HTTP."""
        import urllib.request
        import urllib.error

        endpoint = f"{self.url}/list"

        try:
            with urllib.request.urlopen(endpoint, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result
        except Exception as e:
            return {"error": str(e)}

    async def call_tool_stdio(self, tool_name: str, params: Dict[str, Any]) -> Dict:
        """Call a tool via stdio MCP server."""
        try:
            # Start the stdio server process
            self.process = await asyncio.create_subprocess_shell(
                self.stdio_command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Send initialize message (MCP protocol)
            init_msg = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "mcp-client", "version": "1.0.0"}
                }
            }
            self.process.stdin.write((json.dumps(init_msg) + "\n").encode())
            await self.process.stdin.drain()

            # Wait for init response
            await self.process.stdout.readline()

            # Send tool call
            call_msg = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": params
                }
            }
            self.process.stdin.write((json.dumps(call_msg) + "\n").encode())
            await self.process.stdin.drain()

            # Read response
            response_line = await asyncio.wait_for(
                self.process.stdout.readline(),
                timeout=30.0
            )
            response = json.loads(response_line.decode('utf-8'))

            # Close process
            self.process.terminate()
            await self.process.wait()

            return response.get("result", {})

        except asyncio.TimeoutError:
            if self.process:
                self.process.kill()
            return {"error": "Timeout waiting for stdio server"}
        except Exception as e:
            if self.process:
                self.process.kill()
            return {"error": str(e)}

    async def list_tools_stdio(self) -> Dict:
        """List available tools via stdio."""
        try:
            self.process = await asyncio.create_subprocess_shell(
                self.stdio_command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Send initialize
            init_msg = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "mcp-client", "version": "1.0.0"}
                }
            }
            self.process.stdin.write((json.dumps(init_msg) + "\n").encode())
            await self.process.stdin.drain()

            await self.process.stdout.readline()

            # Send tools/list
            list_msg = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list"
            }
            self.process.stdin.write((json.dumps(list_msg) + "\n").encode())
            await self.process.stdin.drain()

            # Read response
            response_line = await asyncio.wait_for(
                self.process.stdout.readline(),
                timeout=10.0
            )
            response = json.loads(response_line.decode('utf-8'))

            self.process.terminate()
            await self.process.wait()

            return response.get("result", {})

        except Exception as e:
            if self.process:
                self.process.kill()
            return {"error": str(e)}

    async def emit_tools(self, output_format: str = "markdown") -> str:
        """Emit tool schemas as documentation."""
        if self.url:
            tools = await self.list_tools_http()
        else:
            tools = await self.list_tools_stdio()

        if "error" in tools:
            return f"Error: {tools['error']}"

        if output_format == "markdown":
            return self._format_tools_markdown(tools)
        return json.dumps(tools, indent=2)

    def _format_tools_markdown(self, tools: Dict) -> str:
        """Format tools as markdown documentation."""
        lines = ["# Available MCP Tools\n"]

        for tool in tools.get("tools", []):
            lines.append(f"## {tool['name']}\n")
            lines.append(f"{tool.get('description', 'No description')}\n")

            if "inputSchema" in tool:
                schema = tool["inputSchema"]
                lines.append("### Parameters\n")

                if "properties" in schema:
                    for name, prop in schema["properties"].items():
                        required = name in schema.get("required", [])
                        req_mark = "**Required**" if required else "Optional"
                        lines.append(f"- **{name}** ({req_mark}): {prop.get('description', '')}")
                        if "type" in prop:
                            lines.append(f"  - Type: {prop['type']}")
                    lines.append("")

        return "\n".join(lines)


async def main():
    parser = argparse.ArgumentParser(description="MCP Client")
    parser.add_argument("command", choices=["list", "call", "emit"], help="Command to run")
    parser.add_argument("--url", "-u", help="HTTP MCP server URL")
    parser.add_argument("--stdio", "-s", help="Stdio command to run MCP server")
    parser.add_argument("--tool", "-t", help="Tool name (for call)")
    parser.add_argument("--params", "-p", help="Tool parameters as JSON string")
    parser.add_argument("--format", "-f", default="markdown", choices=["markdown", "json"],
                       help="Output format (for emit)")

    args = parser.parse_args()

    if not args.url and not args.stdio:
        print("Error: Must specify either --url or --stdio", file=sys.stderr)
        sys.exit(1)

    client = MCPClient(url=args.url, stdio_command=args.stdio)

    if args.command == "list":
        if args.url:
            result = await client.list_tools_http()
        else:
            result = await client.list_tools_stdio()
        print(json.dumps(result, indent=2))

    elif args.command == "call":
        if not args.tool:
            print("Error: --tool required for call", file=sys.stderr)
            sys.exit(1)

        params = json.loads(args.params) if args.params else {}

        if args.url:
            result = await client.call_tool_http(args.tool, params)
        else:
            result = await client.call_tool_stdio(args.tool, params)

        print(json.dumps(result, indent=2))

    elif args.command == "emit":
        result = await client.emit_tools(args.format)
        print(result)


if __name__ == "__main__":
    asyncio.run(main())
