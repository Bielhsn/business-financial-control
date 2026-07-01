from fastapi import FastAPI

app = FastAPI(
    title="Business Financial Control API",
    version="0.1.0",
)


@app.get("/")
async def root() -> dict[str, str]:
    return {"name": "business-financial-control-api", "status": "ok"}
