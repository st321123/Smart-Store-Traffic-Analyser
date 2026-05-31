"""
FastAPI server - the entry point for the chatbot API.

Endpoints:
    POST /chat -> Send a user query, get the agent response.
    GET /health -> Health check
"""

import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents.graph import app_graph
from tools.cubejs_client import get_cube_meta


cube_metadata_cache: str = ""

@asynccontextmanager
async def lifespan(app: FastAPI):
    global cube_metadata_cache
    try:
        meta = await get_cube_meta()
        cubes = meta.get("cubes",[])
        summary_lines = []
        for cube in cubes:
            name = cube.get("name","")
            measures = [m["name"] for m in cube.get("measures",[])]
            dimensions = [d["name"] for d in cube.get("dimensions",[])]
            summary_lines.append(
                f"Cube: {name}\n Measures: {measures}\n Dimensions: {dimensions}"

            )
        cube_metadata_cache = "\n".join(summary_lines)
        print(f"Loaded metadata for {len(cubes)} cubes")

    except Exception as e:
        cube_metadata_cache = "Cube metadata unavailable - Cube.js server may not be running."
        print(f"Could not load cube metadata: {e}")
    yield

app = FastAPI(title = "Store Traffic RCA Chatbot", version= "1.0.0", lifespan = lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"]
)

# Request / Response schemas

class ChatRequest(BaseModel):
    query:str
class ChatResponse(BaseModel):
    response: str
    intent: str
    entities:dict
    root_causes: list | None = None


# POST/chat - Main endpoint
# Takes user query  -> runs LangGraph pipeline -> returns response


@app.post("/chat", response_model = ChatResponse)
async def chat(request: ChatRequest):
    initial_state = {
        "user_query": request.query,
        "intent":"",
        "entities":{},
        "cube_metadata": cube_metadata_cache,
        "findings":[],
        "root_causes":[],
        "response":"",
    }
    final_state = await app_graph.ainvoke(initial_state)
    return ChatResponse(
        response = final_state.get("response", "Sorry, I couldn't generate a response."),
        intent = final_state.get("intent","unknown"),
        entities = final_state.get("entities",{}), 
        root_causes = (
    final_state.get("root_causes") if final_state.get("intent") == "rca" else None)
        )

# GET /health - Simple health check 



@app.get("/health")
async def health():
    return {
        "status":"healthy",
        "cube_metadata_loaded": bool(cube_metadata_cache and "unavailable" not in cube_metadata_cache),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host = "0.0.0.0", port = 8000, reload = True)
