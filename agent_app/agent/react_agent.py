from langchain.agents import create_agent

from agent_app.agent.tools.agent_tools import rag_summarize, get_weather, get_user_location, get_user_id, \
    get_current_month, fetch_external_data, fill_context_for_report
from agent_app.agent.tools.middleware import monitor_tool, log_before_model, report_prompt_switch
from agent_app.model.factory import chat_model
from agent_app.utils.prompt_loader import load_system_prompt


class ReactAgent:
    def __init__(self):
        self.agent = create_agent(
            model=chat_model,
            system_prompt=load_system_prompt(),
            tools=[rag_summarize, get_weather, get_user_location, get_user_id, get_current_month, fetch_external_data,
                   fill_context_for_report],
            middleware=[monitor_tool, log_before_model, report_prompt_switch],
        )

    def execute_stream(self, query: str):
        input_dict = {
            "messages": [
                {"role": "user", "content": query}
            ]
        }
        for chunk in self.agent.stream(input_dict, stream_mode="values", context={"report": False}):
            last_message = chunk["messages"][-1]
            if last_message.content:
                prefix = f"[{type(last_message).__name__}] "
                yield prefix + last_message.content.strip() + "\n"


if __name__ == "__main__":
    agent = ReactAgent()
    for chunk in agent.execute_stream("扫地机器人在我所在的地区的气温下如何保养?"):
        print(chunk, end="", flush=True)
