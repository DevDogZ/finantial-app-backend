from fastapi import FastAPI

app = FastAPI()

@app.get("/")

def home():
    return {"messagem": "Finanças da casa no ar!"}

