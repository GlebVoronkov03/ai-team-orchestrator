import os
import re
import logging
from logging.handlers import TimedRotatingFileHandler
from openai import OpenAI
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from typing import TypedDict, Dict, Any, Literal, Optional

# RAG
import chromadb
from chromadb.utils import embedding_functions

# Локальный fallback (Ollama)
import requests
import json

load_dotenv()

# ---------- API ----------
client = OpenAI(
    base_url=os.getenv("OPENROUTER_BASE_URL"),
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

# ---------- Фильтр ----------
from ip_filter import IPFilter
ip_filter = IPFilter("codename_map.json")

# ---------- Логирование (utf-8) ----------
os.makedirs("logs", exist_ok=True)
logger = logging.getLogger("AITeam")
logger.setLevel(logging.INFO)
handler = TimedRotatingFileHandler("logs/ai_team.log", when="midnight", interval=1, backupCount=30, encoding='utf-8')
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

# ---------- RAG: chromadb ----------
CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "gleb_papers"

embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
try:
    collection = chroma_client.get_collection(name=COLLECTION_NAME, embedding_function=embedding_fn)
except:
    collection = chroma_client.create_collection(name=COLLECTION_NAME, embedding_function=embedding_fn)

def retrieve_context(query: str, n_results: int = 3) -> str:
    if collection.count() == 0:
        return ""
    try:
        results = collection.query(query_texts=[query], n_results=n_results)
        docs = results['documents'][0]
        return "\n\n".join(docs)
    except Exception as e:
        logger.warning(f"RAG query failed: {e}")
        return ""

# ---------- Ollama fallback ----------
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5-coder:3b"

def is_ollama_available() -> bool:
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=2)
        return resp.status_code == 200
    except:
        return False

def call_ollama(prompt: str, temperature: float = 0.2) -> str:
    payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False, "options": {"temperature": temperature}}
    resp = requests.post(OLLAMA_URL, json=payload, timeout=60)
    if resp.status_code == 200:
        return resp.json().get("response", "")
    raise Exception(f"Ollama error: {resp.text}")

def safe_llm_call(messages, temperature=0.2, force_api=False) -> str:
    anonymized = []
    for msg in messages:
        if msg["role"] == "user":
            anonymized.append({"role": "user", "content": ip_filter.anonymize(msg["content"])})
        else:
            anonymized.append(msg)
    try:
        response = client.chat.completions.create(
            model="deepseek/deepseek-chat",
            messages=anonymized,
            temperature=temperature,
            timeout=30
        )
        result = response.choices[0].message.content
        return ip_filter.deanonymize(result)
    except Exception as e:
        logger.warning(f"API call failed: {e}, switching to Ollama")
        if not force_api and is_ollama_available():
            prompt = "\n".join([m["content"] for m in anonymized if m["role"] == "user"])
            result = call_ollama(prompt, temperature)
            return ip_filter.deanonymize(result)
        raise e

# ---------- Вспомогательные ----------
def human_approval(agent_name: str, content: str) -> tuple[bool, str]:
    print(f"\n🔍 Результат {agent_name}:")
    print(content[:800] + ("..." if len(content) > 800 else ""))
    while True:
        ans = input("Одобрить? (y - продолжить, n - остановить, e - редактировать): ").lower()
        if ans == 'y':
            return True, content
        if ans == 'n':
            return False, content
        if ans == 'e':
            edited = input("Введите исправленный текст:\n")
            return True, edited

def check_for_question(text: str) -> Optional[str]:
    match = re.search(r'\[ВОПРОС К ГЛЕБУ\]:\s*(.*?)(?=\n|$)', text, re.IGNORECASE)
    return match.group(1).strip() if match else None

# ---------- Состояние ----------
class TeamState(TypedDict):
    task: str
    context: Dict[str, Any]
    next_agent: str
    step_by_step: bool
    programming_language: str   # "python", "cpp", "javascript"

# ---------- Агенты ----------
def provident(state: TeamState) -> TeamState:
    agent_name = "Провидец"
    logger.info(f"{agent_name} начал: {state['task'][:100]}")
    print("\n🧠 Провидец генерирует гипотезы...")
    rag = retrieve_context(state['task'])
    prompt = f"Задача: {state['task']}.\n"
    if rag:
        prompt += f"Используй знания из моих статей:\n{rag}\n\n"
    prompt += "Сформулируй 2-3 гипотезы решения. Если нужны уточнения, напиши [ВОПРОС К ГЛЕБУ]: ..."
    result = safe_llm_call([{"role": "user", "content": prompt}], temperature=0.7)
    q = check_for_question(result)
    if q:
        print(f"\n❓ {agent_name} спрашивает: {q}")
        ans = input("Ваш ответ: ")
        result = safe_llm_call([
            {"role": "user", "content": f"Вопрос: {q}\nОтвет: {ans}\nПродолжай генерацию гипотез."}
        ], temperature=0.7)
    if state.get("step_by_step", False):
        ok, final = human_approval(agent_name, result)
        if not ok:
            raise Exception("Остановлено пользователем")
        result = final
    state["context"]["hypotheses"] = result
    state["next_agent"] = "logicus"
    logger.info(f"{agent_name} завершил")
    return state

def logicus(state: TeamState) -> TeamState:
    agent_name = "Логикус"
    logger.info(f"{agent_name} начал проверку")
    print("\n📐 Логикус проверяет гипотезы...")
    hypotheses = state["context"].get("hypotheses", "")
    rag = retrieve_context(hypotheses + " " + state['task'])
    prompt = f"Проверь математическую состоятельность идей:\n{hypotheses}\n"
    if rag:
        prompt += f"Опирайся на эти материалы:\n{rag}\n\n"
    prompt += "Укажи слабые места. Если нужно уточнение, напиши [ВОПРОС К ГЛЕБУ]: ..."
    result = safe_llm_call([{"role": "user", "content": prompt}], temperature=0.3)
    q = check_for_question(result)
    if q:
        print(f"\n❓ {agent_name} спрашивает: {q}")
        ans = input("Ваш ответ: ")
        result = safe_llm_call([
            {"role": "user", "content": f"Вопрос: {q}\nОтвет: {ans}\nПродолжи проверку."}
        ], temperature=0.3)
    if state.get("step_by_step", False):
        ok, final = human_approval(agent_name, result)
        if not ok:
            raise Exception("Остановлено пользователем")
        result = final
    state["context"]["verification"] = result
    state["next_agent"] = "engineer"
    logger.info(f"{agent_name} завершил")
    return state

def engineer(state: TeamState) -> TeamState:
    agent_name = "Инженер"
    lang = state.get("programming_language", "python")
    logger.info(f"{agent_name} ({lang}) приступил")
    print(f"\n⚙️ Инженер пишет код на {lang}...")
    rag = retrieve_context(state['task'] + " " + lang)
    prompt = f"""
Задача: {state['task']}
Гипотезы: {state['context'].get('hypotheses', '')}
Проверка: {state['context'].get('verification', '')}
Напиши код на {lang}, реализующий лучшее решение. Включи комментарии и пример использования.
"""
    if rag:
        prompt = f"Примеры из моих проектов:\n{rag}\n\n" + prompt
    prompt += "\nЕсли нужны уточнения, напиши [ВОПРОС К ГЛЕБУ]: ..."
    result = safe_llm_call([{"role": "user", "content": prompt}], temperature=0.2)
    q = check_for_question(result)
    if q:
        print(f"\n❓ {agent_name} спрашивает: {q}")
        ans = input("Ваш ответ: ")
        result = safe_llm_call([
            {"role": "user", "content": f"Вопрос: {q}\nОтвет: {ans}\nПродолжи написание кода."}
        ], temperature=0.2)
    if state.get("step_by_step", False):
        ok, final = human_approval(agent_name, result)
        if not ok:
            raise Exception("Остановлено пользователем")
        result = final
    state["context"]["code"] = result
    state["next_agent"] = "writer"
    logger.info(f"{agent_name} завершил")
    return state

def writer(state: TeamState) -> TeamState:
    agent_name = "Словолит"
    logger.info(f"{agent_name} начал оформление")
    print("\n📝 Словолит оформляет результат...")
    rag = retrieve_context(state['task'] + " методология")
    prompt = f"""
Опиши решение научным языком для раздела 'Методология' статьи. Используй следующий код:
{state['context'].get('code', '')}
Приведи формулы в LaTeX.
"""
    if rag:
        prompt = f"Используй стиль из моих статей:\n{rag}\n\n" + prompt
    prompt += "\nЕсли нужны пояснения, напиши [ВОПРОС К ГЛЕБУ]: ..."
    result = safe_llm_call([{"role": "user", "content": prompt}], temperature=0.4)
    q = check_for_question(result)
    if q:
        print(f"\n❓ {agent_name} спрашивает: {q}")
        ans = input("Ваш ответ: ")
        result = safe_llm_call([
            {"role": "user", "content": f"Вопрос: {q}\nОтвет: {ans}\nПродолжи оформление статьи."}
        ], temperature=0.4)
    if state.get("step_by_step", False):
        ok, final = human_approval(agent_name, result)
        if not ok:
            raise Exception("Остановлено пользователем")
        result = final
    state["context"]["article"] = result
    state["next_agent"] = END
    logger.info(f"{agent_name} завершил")
    return state

# ---------- Маршрутизация (исправлена) ----------
def router(state: TeamState) -> str:
    # возвращаем имя следующего агента или END
    return state.get("next_agent", "provident")

workflow = StateGraph(TeamState)
workflow.add_node("provident", provident)
workflow.add_node("logicus", logicus)
workflow.add_node("engineer", engineer)
workflow.add_node("writer", writer)
workflow.set_entry_point("provident")
workflow.add_edge("provident", "logicus")
workflow.add_edge("logicus", "engineer")
workflow.add_edge("engineer", "writer")
workflow.add_conditional_edges("writer", router)   # router возвращает строку, для END край не нужен
app = workflow.compile()