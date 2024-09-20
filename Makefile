.PHONY: lint format test clean train eval package

lint:
	find . -name "*.py" | xargs pylint

format:
	black .

test:
	pytest -m unittest discover -s tests

clean:
	rm -rf __pycache__ .pytest_cache .coverage

run:
	uvicorn main:app --reload --port 8000
