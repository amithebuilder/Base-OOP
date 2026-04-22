# Банковская платформа (Python)

Проект в production-like структуре: пакет с бизнес-логикой отдельно, сценарии запуска отдельно.

## Структура

```text
banking/
├── pyproject.toml
├── requirements.txt
├── README.md
├── .gitignore
├── src/banking/          # только бизнес-логика
│   ├── accounts/
│   ├── customers/
│   ├── core/
│   ├── transactions/
│   ├── audit/
│   └── reports/
├── scripts/              # сценарии и утилиты запуска
│   ├── demo.py
│   ├── generate_reports.py
│   └── scenario_data.py
└── tests/
```

## Запуск

```bash
pip install -e .
python scripts/demo.py
python scripts/generate_reports.py
```

Локально без entrypoint-команд:

```bash
python scripts/demo.py
python scripts/generate_reports.py
```

При запуске создаётся `var/` с логами и отчётами (в git не хранится).
