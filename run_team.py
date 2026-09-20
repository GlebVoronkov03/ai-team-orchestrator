import sys
import json
from orchestrator import app, TeamState

def save_result(content: str, filename: str):
    import os
    os.makedirs("results", exist_ok=True)
    with open(f"results/{filename}", "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[Сохранено] results/{filename}")

def main():
    print("\n🤖 Команда AI-агентов Глеба Воронкова")
    print("1. Выполнить стандартный сценарий (ручной ввод задачи)")
    print("2. Загрузить задачу из файла task.json")
    choice = input("Выберите режим [1-2]: ")

    if choice == "1":
        task_text = input("Введите описание задачи: ")
        step_mode = input("Включить пошаговое одобрение? (y/n): ").lower() == 'y'
        lang = input("Язык программирования (python/cpp/javascript): ").lower()
        if lang not in ["python", "cpp", "javascript"]:
            lang = "python"
    elif choice == "2":
        with open("task.json", "r", encoding="utf-8") as f:
            task_data = json.load(f)
        task_text = task_data["task"]
        step_mode = task_data.get("step_by_step", False)
        lang = task_data.get("language", "python")
        print(f"Задача загружена: {task_text}")
    else:
        return

    state = TeamState(
        task=task_text,
        context={},
        next_agent="",
        step_by_step=step_mode,
        programming_language=lang
    )
    print("\n🚀 Запуск оркестрации...\n")
    final = app.invoke(state)
    print("\n" + "="*60)
    print("ИТОГОВЫЙ ОТЧЁТ")
    print("="*60)
    if "hypotheses" in final["context"]:
        print("\nГИПОТЕЗЫ:\n", final["context"]["hypotheses"])
    if "verification" in final["context"]:
        print("\nПРОВЕРКА:\n", final["context"]["verification"])
    if "code" in final["context"]:
        print("\nКОД:\n", final["context"]["code"])
        ext = "py" if lang == "python" else ("cpp" if lang == "cpp" else "js")
        save_result(final["context"]["code"], f"generated_code.{ext}")
    if "article" in final["context"]:
        print("\nСТАТЬЯ (Методология):\n", final["context"]["article"])
        save_result(final["context"]["article"], "methodology.txt")

if __name__ == "__main__":
    main()