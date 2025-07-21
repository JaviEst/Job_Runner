
A modern Python project setup using:
- [`tox`](https://tox.readthedocs.io/) – for test, lint, and format automation
- [`uv`](https://github.com/astral-sh/uv) – for fast dependency installation and environment management
- [`ruff`](https://docs.astral.sh/ruff/) – for linting and formatting
---

## 🧪 Run Tasks with Tox
### ✅ Run tests
```bash
uv run tox -e test
```

### 🔍 Run Ruff linter
```bash
uv run tox -e lint
```

### 🎨 Check formatting with Ruff
```bash
uv run tox -e format
```
---

## 💡 Manual Ruff Usage
If you want to run Ruff directly:

### Format the code
```bash
uv run ruff format .
```

### Check for lint issues
```bash
uv run ruff check .
```
---

## 📁 Project Structure
```
agent-0.1/
├── tests/                  # Tests
├── requirements-agent.txt  # Agent dependencies
├── requirements-test.txt   # Test dependencies
├── tox.ini                 # Tox environment definitions
├── pyproject.toml          # Tool configurations (ruff, etc)
└── README.md               # Project documentation
```
---

## ✅ Add More Tox Environments
You can expand the `tox.ini` file to include:
- Integration or end to end test suites
---

## 🧊 Using UV
This project uses [`uv`](https://github.com/astral-sh/uv) for:
- Creating fast virtual environments (`uv venv`)
- Installing packages (`uv pip install`)
- Installing dependencies in Tox (`installer = uv`)
---

## 🔗 Useful Links
- [Tox Documentation](https://tox.readthedocs.io/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [UV Project](https://github.com/astral-sh/uv)
---

Happy hacking 🎉
