PYTHON ?= python3

.PHONY: install
install:
	$(PYTHON) -m pip install -U pip
	pip install -e .

.PHONY: run
run:
	streamlit run streamlit_app/Home.py

.PHONY: test
test:
	$(PYTHON) -m pytest -q


