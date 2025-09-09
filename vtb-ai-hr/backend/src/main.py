import asyncio
from fastapi import FastAPI
import uvicorn
from candidate.router import router as candidate_router
from contract.router import router as contract_router

from recruiter.router import router as recruiter_router

app = FastAPI()

app.include_router(candidate_router)
app.include_router(recruiter_router)
app.include_router(contract_router)


async def main():
    config = uvicorn.Config("main:app", port=9200, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


import os

from dotenv import load_dotenv
from populate import populate

if __name__ == "__main__":
    load_dotenv()
    if os.getenv("POPULATE_DATABASE") == "true":
        populate()
    asyncio.run(main())
