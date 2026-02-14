# Nu Home Janitorial Payroll + Contract Costing (MVP)

Django 5 app to enter monthly payroll summary lines and export:
1. Payroll Register
2. Contract Labour Allocation
3. Contract Profitability

## Stack
- Python 3.11+ (code compatible; this environment may use 3.10 for scaffolding)
- Django 5.x
- SQLite (MVP)
- openpyxl for exports

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Auto-seeded data
Migration `payroll.0001_initial` auto-creates:
- Internal contract/cost center: `Projects/Overhead`
- Starter statutory setting + one NIS bracket

## Core workflow
- Manage contracts/employees from app screens or Django admin
- Create a pay period (contribution weeks auto-count Mondays for month)
- Open pay period detail to:
  - Generate base salary lines
  - Enter payroll lines, billings, overheads
  - Lock period (read-only thereafter)
- Run reports and export XLSX files.

## Exports
- `Payroll_Register_<Period>.xlsx`
- `Contract_Labour_<Period>.xlsx`
- `Contract_Profitability_<Period>.xlsx`

## Tests
```bash
python manage.py test
# or
pytest
```
