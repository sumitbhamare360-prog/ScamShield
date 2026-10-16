from fastapi import FastAPI

app = FastAPI(title="ScamShield API")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
