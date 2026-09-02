.PHONY: compile test examples schemas public-audit links release-gate

compile:
	python -m compileall -q src scripts tests

test:
	python scripts/verify_test_count.py
	python -m unittest discover -s tests -v

examples:
	python scripts/verify_examples.py

schemas:
	python scripts/verify_schemas.py

public-audit:
	python scripts/public_audit.py .

links:
	python scripts/check_markdown_links.py

release-gate: compile schemas test examples public-audit links
