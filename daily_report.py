import re
from datetime import datetime
from collections import Counter

LOG_FILE = "logs/ai_team.log"
TODAY = datetime.now().strftime("%Y-%m-%d")

def parse_log():
    with open(LOG_FILE, "r", encoding="utf-8", errors='ignore') as f:
        lines = f.readlines()
    today_lines = [l for l in lines if TODAY in l]
    agent_actions = Counter()
    for line in today_lines:
        match = re.search(r'Агент (\S+)', line)
        if match:
            agent_actions[match.group(1)] += 1
    return agent_actions, len(today_lines)

def main():
    actions, total = parse_log()
    print(f"\n📅 Ежедневный отчёт за {TODAY}")
    print(f"Всего событий в логе: {total}")
    print("Активность агентов:")
    for agent, count in actions.items():
        print(f"  {agent}: {count} вызовов")
    print("\nПодробности смотрите в файле logs/ai_team.log")

if __name__ == "__main__":
    main()