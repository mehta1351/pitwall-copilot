"""
MCP server exposing OpenF1 data as tools for the Pit Wall Co-Pilot agent.

Run standalone first to sanity-check before wiring into ADK:
    python mcp_server/server.py
"""

from typing import Optional

from mcp.server.fastmcp import FastMCP

from openf1 import fetch, OpenF1Error

mcp = FastMCP("f1-strategy-data")


@mcp.tool()
def get_sessions(
    year: int,
    session_name: Optional[str] = None,
    country_name: Optional[str] = None,
) -> list[dict]:
    """
    Find F1 sessions (race weekends) for a given year, optionally filtered
    by session type (e.g. "Race", "Qualifying") or country. Use this first
    to resolve a session_key, which every other tool needs.
    """
    return fetch(
        "sessions", year=year, session_name=session_name, country_name=country_name
    )


@mcp.tool()
def get_drivers(session_key: int) -> list[dict]:
    """
    Get the list of drivers in a session, mapping driver_number to
    full_name and team_name. Use this to resolve a driver's name into the
    driver_number other tools require.
    """
    return fetch("drivers", session_key=session_key)


@mcp.tool()
def get_race_result(session_key: int) -> list[dict]:
    """
    Get the final classification for a session: finishing position, gap to
    leader, and DNF/DNS/DSQ status for each driver.
    """
    return fetch("session_result", session_key=session_key)


@mcp.tool()
def get_lap_times(session_key: int, driver_number: int) -> list[dict]:
    """
    Get lap-by-lap timing for one driver in a session: lap number, lap
    duration, and sector times. This is the raw pace data strategy
    judgments are built on.
    """
    return fetch("laps", session_key=session_key, driver_number=driver_number)


@mcp.tool()
def get_pit_stops(session_key: int, driver_number: Optional[int] = None) -> list[dict]:
    """
    Get pit stop events for a session: which lap each driver pitted on and
    how long the stop took. Omit driver_number to get every pit stop in
    the session.
    """
    return fetch("pit", session_key=session_key, driver_number=driver_number)


@mcp.tool()
def get_tire_stints(session_key: int, driver_number: Optional[int] = None) -> list[dict]:
    """
    Get tire stint data for a session: compound, stint number, lap range,
    and tire age at the start of each stint. Omit driver_number to get
    every driver's stints.
    """
    return fetch("stints", session_key=session_key, driver_number=driver_number)


@mcp.tool()
def get_weather(session_key: int) -> list[dict]:
    """
    Get weather readings throughout a session: air and track temperature,
    rainfall, humidity, and wind, sampled roughly every minute. Use this
    to explain strategy calls triggered by changing conditions.
    """
    return fetch("weather", session_key=session_key)


@mcp.tool()
def get_team_radio(session_key: int, driver_number: Optional[int] = None) -> list[dict]:
    """
    Get timestamps of team radio communications during a session (metadata
    only — driver number and time, not a transcript of what was said).
    NOTE: F1 only releases a limited selection of radio moments, and
    coverage dropped sharply starting in 2026 — an empty result is normal
    and expected, not an error. Treat it as "no notable radio activity
    recorded," never as a failure.
    """
    return fetch("team_radio", session_key=session_key, driver_number=driver_number)


@mcp.tool()
def get_race_control(session_key: int) -> list[dict]:
    """
    Get race control events for a session: flags, safety car and virtual
    safety car periods, red flags, and incident messages, each with the
    lap or time it happened. Critical for explaining pit stops that only
    make sense relative to a safety car window.
    """
    return fetch("race_control", session_key=session_key)


@mcp.tool()
def get_championship_standings(session_key: int) -> dict:
    """
    Get championship standings as of this session: both driver points
    standings and constructor (team) points standings. Only meaningful for
    race sessions. Use this to frame strategy decisions in terms of what
    was actually at stake in the title fight.
    """
    try:
        drivers = fetch("championship_drivers", session_key=session_key)
    except OpenF1Error:
        drivers = []
    try:
        teams = fetch("championship_teams", session_key=session_key)
    except OpenF1Error:
        teams = []
    return {"drivers": drivers, "teams": teams}


if __name__ == "__main__":
    mcp.run()