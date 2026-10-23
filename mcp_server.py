
from mcp.server.fastmcp import FastMCP
from task_store import list_tasks

mcp = FastMCP(
    "WorkMate AI",
    host="127.0.0.1",
    port=8001,
)


@mcp.tool()
def get_pending_tasks() -> dict:
    """Get the employee's current tasks that are not completed."""
    result = list_tasks("all")

    if not result.get("ok"):
        return {
            "ok": False,
            "message": "Tasks could not be retrieved."
        }

    pending = [
        task
        for task in result.get("tasks", [])
        if str(task.get("status", "")).lower()
        not in {"completed", "done"}
    ]

    return {
        "ok": True,
        "count": len(pending),
        "tasks": pending,
    }


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
