import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url=os.getenv("OPENROUTER_BASE_URL"),
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

def engineer_agent(task: str) -> str:
    print(f"\n🚀 Инженер приступил к задаче:\n{task}\n")
    response = client.chat.completions.create(
        model="deepseek/deepseek-chat",
        messages=[
            {"role": "system", "content": "Ты — инженер-программист. Пиши чистый код на Python с комментариями."},
            {"role": "user", "content": task}
        ],
        temperature=0.2,
    )
    result = response.choices[0].message.content
    print("✅ Инженер завершил работу.\n")
    return result

if __name__ == "__main__":
    task_text = "Напиши функцию на Python, которая вычисляет среднеквадратичную ошибку (RMSE) между двумя наборами 3D-точек (списки кортежей (x,y,z))."
    code = engineer_agent(task_text)
    print(code)