---
trigger: always_on
---

# Pit Wall Co-Pilot — Build Plan

A post-session F1 strategy analyst agent. Feed it any 2026 race that's already happened; ask it natural-language questions about whether pit calls, tire choices, and timing were the right ones, grounded entirely in real session data.

**Track:** Agents for Business
**Data source:** OpenF1 (free, no auth, historical data from 2023 onward)

---

## 1. Tool Specification (MCP server)

All ten tools are thin wrappers around `https://api.openf1.org/v1/`. Each one makes a single GET request and returns the JSON as-is (or lightly filtered) — no transformation logic needed at this layer; reasoning happens in the agent, not the tool.

| # | Tool | Parameters | Wraps | Returns / purpose |
|---|------|-----------|-------|---------------------|
| 1 | `get_sessions` | `year`, `session_name` (optional), `country_name` (optional) | `/sessions` | List of sessions matching filters, including `session_key` — the ID every other tool needs |
| 2 | `get_drivers` | `session_key` | `/drivers` | `driver_number` ↔ `full_name`/`team_name` mapping |
| 3 | `get_race_result` | `session_key` | `/session_result` | Final classification: position, gap to leader, DNF/DSQ |
| 4 | `get_lap_times` | `session_key`, `driver_number` | `/laps` | Lap-by-lap duration and sectors — raw pace data |
| 5 | `get_pit_stops` | `session_key`, `driver_number` (optional) | `/pit` | Lap number and duration of each pit stop |
| 6 | `get_tire_stints` | `session_key`, `driver_number` (optional) | `/stints` | Compound, stint length, tire age per stint |
| 7 | `get_weather` | `session_key` | `/weather` | Track/air temp, rainfall, wind over the session |
| 8 | `get_team_radio` | `session_key`, `driver_number` (optional) | `/team_radio` | Timestamps of radio comms (metadata only — MVP, no transcription) |
| 9 | `get_race_control` | `session_key` | `/race_control` | Flags, safety car, VSC, red flag events — explains "free" pit windows |
| 10 | `get_championship_standings` | `year` | drivers/teams championship (beta) | Points standings — ties strategy calls to title stakes |

**Out of scope for MVP** (deliberately): a predictive ML model (let the LLM reason over real tool output instead), team radio transcription (audio, not text — real upgrade later), gap/interval data for undercut threats (nice-to-have, not core), and anything about team favoritism or driver rivalries (not groundable in data — leave to the LLM's own framing in prose, never asserted as fact).

---

## 2. Project Structure

```
pitwall_copilot/
├── requirements.txt
├── README.md
├── .gitignore
├── mcp_server/
│   ├── openf1.py        # shared HTTP helper (base URL, error handling)
│   └── server.py        # FastMCP server exposing the 10 tools above
└── pitwall_agent/        # ADK agent package — folder name = name shown in `adk web`
    ├── __init__.py       # from . import agent
    ├── agent.py          # root_agent definition, MCPToolset wiring, guardrail instruction
    └── .env              # GOOGLE_API_KEY=...
```

The agent talks to the MCP server as a local subprocess over stdio (`MCPToolset` + `StdioServerParameters`) — no networking, no deployment needed for this layer to work locally.

---

## 3. Build Sequence

**Step 1 — Environment.** Python 3.11+, a venv, `pip install google-adk mcp requests python-dotenv`. Get a free Gemini API key from Google AI Studio (separate from anything Antigravity itself needs).

**Step 2 — Scaffold.** Create the folder structure above. Run `adk create pitwall_agent` to let ADK generate a verified-current `agent.py`/`.env` for whatever ADK version you actually installed, then edit it rather than hand-typing from scratch.

**Step 3 — `openf1.py`.** One function: take an endpoint name and query params, hit the API, return parsed JSON, raise a clear error on failure.

**Step 4 — `server.py`.** Ten small functions, one per tool above, each decorated as an MCP tool and calling the helper. Run it standalone first (`python mcp_server/server.py`) to confirm it starts cleanly before ADK ever touches it.

**Step 5 — `agent.py`.** Single `LlmAgent` (not split yet) with all ten tools attached via `MCPToolset`. System instruction includes the guardrail: *only state numbers and events that came back from a tool call; if you don't have the data, say so instead of guessing.*

**Step 6 — Test.** `adk web` from the project root, pick a 2026 race that's already happened, ask it real questions. This is your MVP — it alone already satisfies Agent (ADK), MCP Server, and Security, three of the six rubric concepts.

**Step 7 — Split (stretch).** Once Step 6 is solid, refactor into the orchestrator + data/strategy/commentator sub-agent pattern using ADK's native multi-agent support — no A2A needed.

**Step 8 — Antigravity.** Open this same folder in Antigravity IDE, use its Agent Manager (Agent-assisted mode) to do at least one real piece of work — e.g. drafting `openf1.py` or debugging an error — and screen-record it. Its built-in MCP store can also connect directly to your `server.py` for a second demo angle.

**Step 9 — Deploy (optional), record, write up.** Cloud Run deploy if time allows; otherwise the GitHub repo with setup instructions satisfies the project-link requirement on its own.