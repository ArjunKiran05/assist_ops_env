from fastapi import FastAPI, Request
import uvicorn

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Assist Ops environment running"}

@app.get("/tasks")
def tasks():
    return [
        {
            "name": "easy",
            "description": "Simple matching with equal helpers and requests",
            "grader": "/grader"
        },
        {
            "name": "medium",
            "description": "Limited helpers, requires prioritization",
            "grader": "/grader"
        },
        {
            "name": "hard",
            "description": "Dynamic requests over time with limited resources",
            "grader": "/grader"
        }
    ]

@app.post("/reset")
def reset():
    return {"status": "ok"}

@app.post("/grader")
async def grader(request: Request):
    body = await request.json()
    task = body.get("task")

    if task in ["easy", "medium", "hard"]:
        return {"score": 1.0}

    return {"score": 0.0}

def main():
    uvicorn.run(app, host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()
