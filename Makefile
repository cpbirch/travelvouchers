.PHONY: run dev test lint typecheck install

PYTHONPATH := src/main
MODULE := voucher_merger.main:app

install:
	pip install -e ".[dev]"

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
