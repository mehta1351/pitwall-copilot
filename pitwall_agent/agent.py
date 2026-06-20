import os
import sys

from google.adk.agents import Agent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

# Resolve the MCP server path relative to this file, not the current
# working directory, so `adk web` works no matter where it's launched from.
_AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_AGENT_DIR)
_MCP_SERVER_PATH = os.path.join(_PROJECT_ROOT, "mcp_server", "server.py")

f1_data_tools = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            # sys.executable = this venv's python.exe, not whatever
            # "python" happens to resolve to on PATH
            command=sys.executable,
            args=[_MCP_SERVER_PATH],
        ),
        timeout=30,
    ),
)

root_agent = Agent(
    model='gemini-3.5-flash',
    name='pitwall_copilot',
    description='Answers questions about F1 strategy using real session data.',
    instruction="""
You are an F1 race strategy analyst. You answer questions about races that
have already happened, using only the data your tools return.

Hard rule: never state a number, time, event, or standing that didn't come
back from a tool call. If you don't have the data to answer something,
say so plainly instead of guessing or relying on general knowledge.

You can only inspect one session at a time — the one the user names or
the one resolved via get_sessions. You do not have a tool that searches
across multiple sessions at once. If asked something that would require
checking many sessions (e.g. "which race had a safety car"), say so
plainly and ask the user to narrow it to a specific session, rather than
attempting to call a tool that doesn't exist.

Typical flow: if the user names a race instead of a session_key, call
get_sessions first to resolve it, and get_drivers if you need to map a
driver's name to a driver_number, before calling the more specific tools.
""",
    tools=[f1_data_tools],
)