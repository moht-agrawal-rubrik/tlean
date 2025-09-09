from fastapi import FastAPI

# Create FastAPI instance
app = FastAPI()

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Hello World"}

# Hello endpoint with a path parameter
@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
