from fastapi import FastAPI

app = FastAPI(title="Brasaland Inventory API")


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "inventory"}
