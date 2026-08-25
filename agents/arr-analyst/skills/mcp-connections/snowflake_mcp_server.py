#!/usr/bin/env python3
"""
Custom Snowflake MCP Server — supports externalbrowser (SSO) auth.
Usage: python3 snowflake_mcp_server.py
"""

import os
import json
import asyncio
import snowflake.connector
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

ACCOUNT   = os.environ.get("SNOWFLAKE_ACCOUNT",   "KTAZVPL-EVB32354")
USER      = os.environ.get("SNOWFLAKE_USER",      "KOTESWARARAO.VENKATA@WORKDAY.COM")
AUTH      = os.environ.get("SNOWFLAKE_AUTHENTICATOR", "externalbrowser")
ROLE      = os.environ.get("SNOWFLAKE_ROLE",      "ROLE_ANALYTICS_ENGINEER")
WAREHOUSE = os.environ.get("SNOWFLAKE_WAREHOUSE", "ANALYTICS_ENGINEER_WH")
DATABASE  = os.environ.get("SNOWFLAKE_DATABASE",  "CERTIFIED_DEV")
SCHEMA    = os.environ.get("SNOWFLAKE_SCHEMA",    "FINANCE")

_conn = None

def get_connection():
    global _conn
    if _conn is None:
        _conn = snowflake.connector.connect(
            account=ACCOUNT,
            user=USER,
            authenticator=AUTH,
            role=ROLE,
            warehouse=WAREHOUSE,
            database=DATABASE,
            schema=SCHEMA,
        )
    return _conn

server = Server("snowflake")

@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="snowflake_query",
            description="Execute SQL queries against Snowflake database",
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "The SQL query to execute"
                    }
                },
                "required": ["sql"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name != "snowflake_query":
        raise ValueError(f"Unknown tool: {name}")

    sql = arguments.get("sql", "").strip()
    if not sql:
        return [types.TextContent(type="text", text="Error: No SQL provided.")]

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        cols = [desc[0] for desc in cur.description] if cur.description else []

        if not rows:
            return [types.TextContent(type="text", text="Query returned no rows.")]

        # Format as aligned text table
        col_widths = [len(c) for c in cols]
        for row in rows:
            for i, val in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(val) if val is not None else "NULL"))

        header = " | ".join(c.ljust(col_widths[i]) for i, c in enumerate(cols))
        divider = "-+-".join("-" * w for w in col_widths)
        lines = [header, divider]
        for row in rows:
            lines.append(" | ".join(
                (str(v) if v is not None else "NULL").ljust(col_widths[i])
                for i, v in enumerate(row)
            ))

        result = "\n".join(lines)
        result += f"\n\n({len(rows)} row{'s' if len(rows) != 1 else ''} returned)"
        return [types.TextContent(type="text", text=result)]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
