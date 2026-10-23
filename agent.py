
import json
import os

from dotenv import load_dotenv
from openai import OpenAI
from task_store import create_task, list_tasks, complete_task

load_dotenv()

AI_PROVIDER = os.getenv("AI_PROVIDER", "local").strip().lower()
OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL", "http://localhost:11434/v1"
).rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

CLOUD_API_BASE_URL = os.getenv("CLOUD_API_BASE_URL", "").strip().rstrip("/")
CLOUD_API_KEY = os.getenv("CLOUD_API_KEY", "").strip()
CLOUD_API_MODEL = os.getenv("CLOUD_API_MODEL", "").strip()
CLOUD_API_TIMEOUT = float(os.getenv("CLOUD_API_TIMEOUT", "30"))
MAX_AGENT_STEPS = int(os.getenv("MAX_AGENT_STEPS", "6"))

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_task",
            "description": "Create a task in the user's persistent task list.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Short task title"},
                    "description": {"type": "string"},
                    "due_date": {"type": "string", "description": "Due date, if known"},
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high"]
                    }
                },
                "required": ["title"],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_tasks",
            "description": "List saved tasks. Use open for unfinished tasks, done for completed tasks, or all.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["all", "open", "done"]
                    }
                },
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "complete_task",
            "description": "Mark an existing task as complete using its numeric ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer"}
                },
                "required": ["task_id"],
                "additionalProperties": False
            }
        }
    }
]


def _client(provider):
    if provider == "local":
        return OpenAI(
            base_url=OLLAMA_BASE_URL,
            api_key="ollama",
            timeout=CLOUD_API_TIMEOUT
        ), OLLAMA_MODEL

    if provider == "cloud":
        if not CLOUD_API_BASE_URL or not CLOUD_API_KEY or not CLOUD_API_MODEL:
            raise ValueError(
                "Cloud mode needs CLOUD_API_BASE_URL, CLOUD_API_KEY, "
                "and CLOUD_API_MODEL in your .env file."
            )
        return OpenAI(
            base_url=CLOUD_API_BASE_URL,
            api_key=CLOUD_API_KEY,
            timeout=CLOUD_API_TIMEOUT
        ), CLOUD_API_MODEL

    raise ValueError(f"Unsupported AI provider: {provider}")


def _run_tool(name, arguments):
    if name == "create_task":
        return create_task(
            title=arguments["title"],
            description=arguments.get("description", ""),
            due_date=arguments.get("due_date", ""),
            priority=arguments.get("priority", "medium")
        )

    if name == "list_tasks":
        return list_tasks(arguments.get("status", "all"))

    if name == "complete_task":
        return complete_task(int(arguments["task_id"]))

    return {"ok": False, "error": f"Unknown tool: {name}"}


def _format_tasks(result):
    tasks = result.get("tasks", []) if isinstance(result, dict) else []
    if not tasks:
        return "No tasks found."

    lines = []
    for task in tasks:
        lines.append(
            f"#{task['id']} — {task['title']} "
            f"[{task['status']}; priority: {task['priority']}]"
        )
    return "\n".join(lines)


def _ask_model(provider, message):
    client, model = _client(provider)

    messages = [
        {
            "role": "system",
            "content": (
                "You are TaskPilot, a practical productivity assistant. "
                "Use tools to create, list, and complete tasks; never claim "
                "a task changed unless the tool result confirms success. "
                "Ask for clarification if a task ID is ambiguous. "
                "When asked to make a plan, inspect open tasks and prioritize "
                "high-priority tasks first. Keep responses concise."
            )
        },
        {"role": "user", "content": message}
    ]

    for _ in range(MAX_AGENT_STEPS):
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.2
        )

        assistant_message = response.choices[0].message
        messages.append(assistant_message.model_dump(exclude_none=True))

        if not assistant_message.tool_calls:
            return assistant_message.content or "I couldn't generate a response."

        for tool_call in assistant_message.tool_calls:
            name = tool_call.function.name
            try:
                arguments = json.loads(tool_call.function.arguments or "{}")
                result = _run_tool(name, arguments)
            except Exception as exc:
                result = {"ok": False, "error": str(exc)}

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result, ensure_ascii=False, default=str)
            })

    return "I reached the tool-call limit. Please try a simpler request."



def chat(message: str) -> str:
    provider = os.getenv("AI_PROVIDER", "auto").strip().lower()

    if provider == "local":
        try:
            return _ask_model("local", message)
        except Exception as exc:
            print(f"Ollama failed: {type(exc).__name__}: {exc}")
            return (
                "Ollama is unavailable. Please check that Ollama is running "
                "and your configured model is installed."
            )

    if provider == "cloud":
        try:
            return _ask_model("cloud", message)
        except Exception as exc:
            print(f"Cloud API failed: {type(exc).__name__}: {exc}")
            return (
                "The cloud AI service is unavailable. "
                "Please check your cloud API settings."
            )

    if provider != "auto":
        return "Invalid AI_PROVIDER. Set it to auto, local, or cloud."

    # Try Ollama first.
    try:
        return _ask_model("local", message)
    except Exception as exc:
        print(f"Ollama failed: {type(exc).__name__}: {exc}")

    # Fall back to cloud only if configured and Ollama failed.
    if not (
        CLOUD_API_BASE_URL
        and CLOUD_API_KEY
        and CLOUD_API_MODEL
    ):
        return (
            "Ollama is unavailable, and cloud fallback is not configured. "
            "Start Ollama or add your cloud API settings to .env."
        )

    try:
        return _ask_model("cloud", message)
    except Exception as exc:
        print(f"Cloud fallback failed: {type(exc).__name__}: {exc}")
        return (
            "Both Ollama and the cloud AI service are unavailable. "
            "Please check their configuration and try again."
        )


    raise ValueError(
        "Invalid AI_PROVIDER. Use local, cloud, or auto in your .env file."
    )
