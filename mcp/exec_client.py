from e2b import Session
import asyncio
import os

async def exec_command(command: str, timeout=120):
    session = await Session.create("security")
    print(f"[Exec MCP] Running: {command}")
    proc = await session.process.start(command, timeout=timeout)
    await proc
    output = proc.stdout + "\n" + proc.stderr
    await session.close()
    return output