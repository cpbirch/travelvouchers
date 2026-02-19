.PHONY: run dev test lint typecheck install clean

PYTHONPATH := src/main
MODULE := voucher_merger.main:app

install:
	pip install -e ".[dev]"

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
	rm -rf build/ dist/ src/main/*.egg-info/ 2>/dev/null || true

run:
	PYTHONPATH=$(PYTHONPATH) uvicorn $(MODULE) --host 0.0.0.0 --port 8000

dev:
	PYTHONPATH=$(PYTHONPATH) uvicorn $(MODULE) --host 0.0.0.0 --port 8000 --reload

test:
	PYTHONPATH=$(PYTHONPATH) pytest src/tests/ -v

lint:
	ruff check src/

typecheck:
	mypy src/main/
