# Run from the repository root, e.g. `make test SKILL=election-voter-guide`; the root Makefile calls this one.
SKILL_DIR := ../../skills/$(notdir $(CURDIR))

.PHONY: test sample check

test:
	python3 -m unittest discover -s tests -v

# Rebuild the example page from the fictional sample data.
sample:
	python3 $(SKILL_DIR)/scripts/build_guide.py --sample examples/sample-guide.html

# CI entry point: tests + a sample build to a throwaway path.
check: test
	python3 $(SKILL_DIR)/scripts/build_guide.py --sample $${TMPDIR:-/tmp}/election-voter-guide-sample.html
