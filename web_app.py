from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from orchestrator import app as graph, TeamState
import uvicorn

api = FastAPI()

@api.get("/", response_class=HTMLResponse)
async def form():
    return """
    <html>
    <body>
    <h2>AI Team Оркестратор</h2>
    <form method="post">
        <textarea name="task" rows="6" cols="80" placeholder="Опишите задачу..."></textarea><br>
        <input type="checkbox" name="step_mode" value="yes"> Пошаговый режим<br>
        <select name="lang">
            <option value="python">Python</option>
            <option value="cpp">C++</option>
            <option value="javascript">JavaScript</option>
        </select><br>
        <button type="submit">Запустить</button>
    </form>
    </body>
    </html>
    """

@api.post("/", response_class=HTMLResponse)
async def run(request: Request, task: str = Form(...), step_mode: str = Form(None), lang: str = Form("python")):
    step = (step_mode == "yes")
    state = TeamState(task=task, context={}, next_agent="", step_by_step=step, programming_language=lang)
    final = graph.invoke(state)
    code = final['context'].get('code', '')
    article = final['context'].get('article', '')
    return f"<pre>КОД ({lang}):\n{code}\n\nСТАТЬЯ:\n{article}</pre>"

if __name__ == "__main__":
    uvicorn.run(api, host="127.0.0.1", port=8000)