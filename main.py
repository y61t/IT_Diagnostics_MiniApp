from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
import uvicorn

app = FastAPI()


@app.get("/")
def index():
    return FileResponse("webapp/index.html")


@app.get("/style.css")
def css():
    return FileResponse("webapp/style.css")


@app.get("/script.js")
def js():
    return FileResponse("webapp/script.js")


# Новый маршрут для получения данных контакта
@app.post("/submit")
async def submit_contact(request: Request):
    data = await request.json()
    print("Новый контакт:", data)
    # Здесь можно интегрировать Bitrix24 или PDF генерацию
    return JSONResponse({"status": "ok"})


@app.get("/download")
def download_pdf():
    return FileResponse("webapp/pdf/checklist.pdf", media_type="application/pdf", filename="checklist.pdf")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
