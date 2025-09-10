from fastapi import FastAPI
from slack.endpoints import router as slack_router
from dotenv import load_dotenv
load_dotenv()

# Create FastAPI instance
app = FastAPI(
    title="Slack Message Retrieval API",
    description="API for retrieving Slack messages with context and replies",
    version="1.0.0"
)

# Include Slack router
app.include_router(slack_router)

# Hello endpoint with a path parameter
@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
