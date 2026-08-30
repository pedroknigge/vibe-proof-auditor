# Contributing to vibe-proof-auditor

First off, thank you for considering contributing to `vibe-proof-auditor`.

## Development Setup

We use standard Python tools for development.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/pedroknigge/vibe-proof-auditor.git
   cd vibe-proof-auditor
   ```

2. **Create a virtual environment (optional but recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install development dependencies:**
   ```bash
   pip install pytest pytest-cov ruff mypy
   ```

## Running Tests Locally

We use `unittest` for the main test suite, but you can also use `pytest` for coverage.

To run the standard tests:
```bash
python3 -m unittest discover -s tests -v
```

To run with coverage:
```bash
PYTHONPATH=. pytest --cov=vibe_proof_auditor tests/ -v
```

## Linting and Formatting

We use `ruff` and `mypy` to maintain code quality.

Run the linter:
```bash
ruff check vibe_proof_auditor tests
```

Format the code:
```bash
ruff format vibe_proof_auditor tests
```

Run type checking:
```bash
mypy vibe_proof_auditor tests
```

Please make sure all tests, linting, and type checking pass before submitting a pull request.
