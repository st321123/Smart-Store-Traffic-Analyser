import httpx
import os
from dotenv import load_dotenv
from typing import Any

load_dotenv()

CUBEJS_API_URL = os.getenv("CUBEJS_API_URL", "http://localhost:4000/cubejs-api/v1")
CUBEJS_API_SECRET = os.getenv("CUBEJS_API_SECRET")
# 3 Functions ----------->>
#  query_cubejs --- connects with semantic layer
#  get_cube_meta --- gets meta data from semantic layer to give context fo llm
#  format_cubejs_response --- it extracts only the required data from the cube.js response




# Function 1: query_cubejs
# WHAT: Sends a JSON query to the Cube.js /Load endpoint.
# WhY:  This is the main function every agent call to fetch data. The agents builds a JSON query 
#       (measures, dimensions, filters) and this function sends it to Cube.js.
#        Cube.js thatn generates SQL, runs it on PostgresSQL, and returns the result.
# WHEN: Called everytime a user asks a question.
# FLOW: Agent-> query_cubejs() -> cube.js -> PostgresSQL ->data back


async def query_cubejs(query:dict) -> dict[str,Any]:
    """
    Send a JSON query to CUBE.js and return the results.
    Example query:
    {
        "measures": ["SalesDaily.total_sales],
        "dimensions": ["SalesDaily.location_id"],
        "timeDimensions":[{}]
    }
    """



    headers = {
        "Content-Type": "application/json",
        "Authorization": CUBEJS_API_SECRET,
    }

    async with httpx.AsyncClient(timeout = 30.0) as client:
        response = await client.post(
            f"{CUBEJS_API_URL}/load",
            json = {"query":query},
            headers = headers,
        )
        response.raise_for_status()
        return response.json()
    

async def get_cube_meta() -> dict[str,Any]:
    """
    Fetch metadata about all available cubes - their dimensions, measures, and joins. 
    The LLM uses this to know what it can query.
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": CUBEJS_API_SECRET,
    }
    async with httpx.AsyncClient(timeout = 30.0) as client:
        response = await client.get(
            f"{CUBEJS_API_URL}/meta",
            headers = headers,
        )
        response.raise_for_status()
        return response.json()
    


def format_cubejs_response(response:dict) -> list[dict]:
    """
    Extract the data array from a Cube.js response.
    Cube.js return : {"data": [...],"annotation": {...}}
    We just need the data.
    """
    return response.get("data",[])