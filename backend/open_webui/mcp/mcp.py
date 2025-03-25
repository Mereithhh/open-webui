from contextlib import AsyncExitStack
import os
import shutil
from fastapi import FastAPI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client
import asyncio
from typing import Any
import logging


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

class Server:
    """Manages MCP server connections and tool execution."""

    def __init__(self, name: str, config: dict[str, Any]) -> None:
        self.name: str = name
        self.config: dict[str, Any] = config
        self.stdio_context: Any | None = None
        self.session: ClientSession | None = None
        self._cleanup_lock: asyncio.Lock = asyncio.Lock()
        self.exit_stack: AsyncExitStack = AsyncExitStack()

    async def initialize(self) -> None:
        """Initialize the server connection."""
        try:
            # 判断是使用 SSE 还是 STDIO 协议
            if self.config.url:
                # 使用 SSE 协议
                log.info(f"Initializing SSE server {self.name} with URL: {self.config.url}")
                streams = await self.exit_stack.enter_async_context(
                    sse_client(self.config.url)
                )
                read, write = streams
                session = await self.exit_stack.enter_async_context(
                    ClientSession(read, write)
                )
            else:
                # 使用 STDIO 协议
                log.info(f"Initializing STDIO server {self.name}")
                command = (
                    shutil.which("npx")
                    if self.config.command == "npx"
                    else self.config.command
                )
                if command is None:
                    raise ValueError("The command must be a valid string and cannot be None.")

                server_params = StdioServerParameters(
                    command=command,
                    args=self.config.args,
                    env={**os.environ, **self.config.env}
                    if self.config.env
                    else None,
                )
                stdio_transport = await self.exit_stack.enter_async_context(
                    stdio_client(server_params)
                )
                read, write = stdio_transport
                session = await self.exit_stack.enter_async_context(
                    ClientSession(read, write)
                )
            
            # 初始化会话
            await session.initialize()
            self.session = session
            log.info(f"[MCP] Server {self.name} initialized successfully")
        except Exception as e:
            log.error(f"[MCP] Error initializing server {self.name}: {e}")
            await self.cleanup()
            raise

    async def list_tools(self) -> list[Any]:
        """List available tools from the server.

        Returns:
            A list of available tools.

        Raises:
            RuntimeError: If the server is not initialized.
        """
        if not self.session:
            raise RuntimeError(f"[MCP] Server {self.name} not initialized")

        tools_response = await self.session.list_tools()
        tools = []

        for item in tools_response:
            if isinstance(item, tuple) and item[0] == "tools":
                for tool in item[1]:
                    tools.append(Tool(tool.name, tool.description, tool.inputSchema))

        return tools

    async def execute_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        retries: int = 2,
        delay: float = 1.0,
    ) -> Any:
        """Execute a tool with retry mechanism.

        Args:
            tool_name: Name of the tool to execute.
            arguments: Tool arguments.
            retries: Number of retry attempts.
            delay: Delay between retries in seconds.

        Returns:
            Tool execution result.

        Raises:
            RuntimeError: If server is not initialized.
            Exception: If tool execution fails after all retries.
        """
        if not self.session:
            raise RuntimeError(f"[MCP] Server {self.name} not initialized")

        attempt = 0
        while attempt < retries:
            try:
                log.info(f"[MCP] Executing {tool_name}...")
                result = await self.session.call_tool(tool_name, arguments)

                return result

            except Exception as e:
                attempt += 1
                log.warning(
                    f"[MCP] Error executing tool: {e}. Attempt {attempt} of {retries}."
                )
                if attempt < retries:
                    log.info(f"[MCP] Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    log.error("[MCP] Max retries reached. Failing.")
                    raise

    async def cleanup(self) -> None:
        """Clean up server resources."""
        async with self._cleanup_lock:
            try:
                await self.exit_stack.aclose()
                self.session = None
                self.stdio_context = None
            except Exception as e:
                log.error(f"[MCP] Error during cleanup of server {self.name}: {e}")


class Tool:
    """Represents a tool with its properties and formatting."""

    def __init__(
        self, name: str, description: str, input_schema: dict[str, Any]
    ) -> None:
        self.name: str = name
        self.description: str = description
        self.input_schema: dict[str, Any] = input_schema

    def format_for_llm(self) -> str:
        """Format tool information for LLM.

        Returns:
            A formatted string describing the tool.
        """
        args_desc = []
        if "properties" in self.input_schema:
            for param_name, param_info in self.input_schema["properties"].items():
                arg_desc = (
                    f"- {param_name}: {param_info.get('description', 'No description')}"
                )
                if param_name in self.input_schema.get("required", []):
                    arg_desc += " (required)"
                args_desc.append(arg_desc)

        return f"""
Tool: {self.name}
Description: {self.description}
Arguments:
{chr(10).join(args_desc)}
"""

async def initialize_mcp_servers(app: FastAPI):
    """Initialize all MCP servers."""
    i = 0
    for server_config in app.state.MCP_CONFIG.mcpServers.values():
        if not server_config.enabled:
            continue
        server = Server(server_config.id, server_config)
        await server.initialize()
        app.state.MCP_SERVERS[server_config.id] = server
        log.info(f"[MCP] Initialized server {server_config.id}")
        i += 1
    log.info(f"[MCP] Initialized {i} servers 😊")
