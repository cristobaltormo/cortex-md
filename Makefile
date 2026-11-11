.PHONY: test lint check health

test:
	python3 -m unittest discover -s tests -v

lint:
	shellcheck -x bin/*.sh install.sh
	python3 -m py_compile bin/*.py

health:
	python3 bin/health.py

check: lint test health
