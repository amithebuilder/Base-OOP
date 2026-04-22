# Банковская платформа (Python)

Проект в production-like структуре: пакет с бизнес-логикой отдельно, сценарии запуска отдельно.

## Структура

```text
banking/
├── pyproject.toml
├── requirements.txt
├── README.md
├── .gitignore
├── LICENSE
├── src/banking/          # бизнес-логика
│   ├── accounts/
│   ├── customers/
│   ├── core/
│   ├── transactions/
│   ├── audit/
│   └── reports/
└── scripts/
    ├── demo.py
    ├── generate_reports.py
    └── scenario_data.py
```

## Запуск

```bash
pip install -e .
python scripts/demo.py
python scripts/generate_reports.py
```

При запуске создаётся `var/` с логами и отчётами (в git не хранится).

## Лицензия

См. файл `LICENSE` в репозитории.
