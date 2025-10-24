from fastapi import FastAPI
app = FastAPI(title="Aurelia FastAPI Clean")

@app.get("/healthz")
def healthz():
    return {"ok": True}
