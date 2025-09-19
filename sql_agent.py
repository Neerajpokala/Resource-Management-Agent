import os
import pandas as pd
from langchain_experimental.agents.agent_toolkits.pandas.base import create_pandas_dataframe_agent
from langchain.agents import AgentExecutor, AgentType
from langchain_google_genai import ChatGoogleGenerativeAI

def make_pandas_gemini_agent(
    json_path: str,
    gemini_model: str = "gemini-2.5-flash",
    temperature: float = 0.0,
    verbose: bool = True
):
    # 1. Load your JSON data into a DataFrame
    df = pd.read_json(json_path)
    # 2. Setup Gemini LLM
    api_key = os.getenv("GOOGLE_API_KEY", "AIzaSyBEma9ndSH9UI04FK83jfFH-kHmW_N_ge8")
    if not api_key:
        raise ValueError("Please set GOOGLE_API_KEY in your environment.")
    llm = ChatGoogleGenerativeAI(
        model=gemini_model,
        google_api_key=api_key,
        temperature=temperature,
    )
    # 3. Create pandas agent (no extra kwargs here!)
    pandas_agent = create_pandas_dataframe_agent(
        llm=llm,
        df=df,
        agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=verbose,
        include_df_in_prompt=True,
        number_of_head_rows=5,
        allow_dangerous_code=True,  # executes arbitrary code!
    )
    # 4. Wrap in AgentExecutor so we can handle parsing errors
    agent_executor = AgentExecutor.from_agent_and_tools(
        agent=pandas_agent.agent,
        tools=pandas_agent.tools,
        verbose=verbose,
        handle_parsing_errors=True,  #
        max_iterations=10,
        return_intermediate_steps=True,
    )
    return agent_executor
# Example usage:
agent = make_pandas_gemini_agent("project_allocations.json", gemini_model="gemini-2.5-flash", temperature=0.2)
result = agent.invoke({"input": "what is the total allocation for the wellora?"})
print(result.get("output"))