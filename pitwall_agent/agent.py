import os
import sys

from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

_AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_AGENT_DIR)
_MCP_SERVER_PATH = os.path.join(_PROJECT_ROOT, "mcp_server", "server.py")

f1_data_tools = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=sys.executable,
            args=[_MCP_SERVER_PATH],
        ),
        timeout=30,
    ),
)

data_agent = Agent(
    model='gemini-2.5-flash',
    name='data_agent',
    description=(
        "Fetches raw F1 session data — sessions, drivers, results, laps, "
        "pit stops, tire stints, weather, radio activity, race control "
        "events, and championship standings — and reports it as-is."
    ),
    instruction="""
You retrieve F1 data using your tools and report back exactly what they
return — raw facts, not analysis or opinions. Never state a number or
event that didn't come back from a tool call; if a tool returns nothing,
say so plainly instead of guessing. Be complete but not repetitive — keep
your report reasonably concise, since it becomes input for two more
agents downstream.

You can only inspect one session at a time — the one named or resolved
via get_sessions. You do not have a tool that searches across multiple
sessions at once; if asked for something requiring that, say so rather
than inventing a tool that doesn't exist.

Workflow: get_lap_times, get_pit_stops, get_tire_stints, and
get_team_radio all require a driver_number, not a name. If you're given
a driver's name instead of a number, call get_drivers for the session
first to resolve it before calling any of those tools — never guess a
driver_number or skip straight to "no data" without doing that lookup.
""",
    tools=[f1_data_tools],
)

strategy_agent = Agent(
    model='gemini-2.5-flash',
    name='strategy_agent',
    description=(
        "Reasons over F1 race data already gathered to judge whether "
        "strategy calls — pit timing, tire choice, safety car reactions "
        "— were good ones, and why."
    ),
    instruction="""
You analyze F1 strategy using only the data given to you in the request —
you have no tools of your own and cannot fetch anything new. Reason about
pit timing, tire degradation, safety car windows, and championship stakes
using the actual numbers you were handed. Cite specific values (lap
numbers, durations, gaps) to support each judgment. If the data you were
given is insufficient to answer something, say so plainly rather than
filling gaps with assumptions.
""",
    tools=[],
)

commentator_agent = Agent(
    model='gemini-2.5-flash-lite',
    name='commentator_agent',
    description=(
        "Turns a strategy analysis into a short, readable race-engineer-"
        "style briefing for the user."
    ),
    instruction="""
You rewrite strategy analysis you're given into a clear, engaging briefing
a fan or strategist would actually want to read — concise, well-organized,
no invented details beyond what's in the analysis you were handed.
""",
    tools=[],
)

root_agent = Agent(
    model='gemini-2.5-flash',
    name='pitwall_copilot',
    description='Answers questions about F1 strategy using real session data.',
    instruction="""
You are the orchestrator for an F1 strategy analyst system. You don't
fetch or analyze data yourself — you coordinate three specialists and
assemble their work into one answer.

Hard rule: never call strategy_agent before you have already called
data_agent in this same turn and have its actual output in hand to pass
along. strategy_agent has no tools of its own and cannot fetch anything —
if you call it with only the user's raw question, it will have nothing
to work with and fail. Always gather facts first, then reason over them.

If strategy_agent's response indicates it doesn't have enough data to
answer — it asks for more information, or says something is missing or
insufficient — that means data_agent's first pass didn't gather
everything needed. Call data_agent again with a more specific request
based on what strategy_agent said was missing, then retry strategy_agent
with the additional data. Never relay "please provide more data" back to
the user as if it were your final answer — you have data_agent available
specifically to get that; use it instead of asking the user to do your
job.

Typical flow: call data_agent first to gather the relevant facts (it
will resolve a session via get_sessions if the user named a race instead
of a session_key, and resolve a driver's name to a number via
get_drivers if needed). Then call strategy_agent, handing it exactly
what data_agent returned, to get a judgment. For anything that should
read like a briefing rather than a raw analysis, call commentator_agent
last with strategy_agent's output. For simple factual lookups that don't
need real judgment (e.g. "what were the pit stops"), data_agent's answer
alone may be enough — use your judgment about which specialists a
question actually needs, but never skip straight to strategy_agent or
commentator_agent without data_agent running first.

Never state anything as fact that didn't ultimately come from data_agent.
""",
    tools=[
        AgentTool(agent=data_agent),
        AgentTool(agent=strategy_agent),
        AgentTool(agent=commentator_agent),
    ],
)