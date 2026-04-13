from langchain.tools import tool
from langchain.agents import create_agent
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

load_dotenv()

@tool
def get_weather(location: str) -> str:
    """Get the weather at a location."""
    return f"It's sunny in {location}."

model = init_chat_model(
    model = "deepseek-chat"
)

model_with_tools = model.bind_tools([get_weather])

response = model_with_tools.invoke("What's the weather like in Boston?")
for tool_call in response.tool_calls:
    # View tool calls made by the model
    print(f"Tool: {tool_call['name']}")
    print(f"Args: {tool_call['args']}")

model.profile