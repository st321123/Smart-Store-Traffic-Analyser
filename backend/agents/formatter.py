# """
# Respnose formatter - Agent #10 
# Fromats the final response for both KPI and RCA paths.

# KPI path: Takes the KPI agent's answer and polishes it.
# RCA path: Takes ranked root causes and crates a structured report.

# """
# import json 
# import os 
# from langchain_openai import AzureChatOpenAI
# from agents.state import ChatState

# llm = AzureChatOpenAI(
#     azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
#     azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"),
#     api_key = os.getenv("AZURE_OPENAI_API_KEY"),
#     api_version = os.getenv("AZURE_OPENAI_API_VERSION"),
#     temperature = 0
# )

# RCA_FORMAT_PROMPT = """ You are a retail analytics
# """