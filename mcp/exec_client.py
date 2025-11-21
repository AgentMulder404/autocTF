from e2b import AsyncSandbox
import asyncio
import os

async def exec_command(command: str, timeout=120):
    sandbox = await AsyncSandbox.create()
    print(f"[Exec MCP] Running: {command}")
    result = await sandbox.commands.run(command, timeout=timeout)
    output = result.stdout + "\n" + result.stderr
    await sandbox.close()
    return output