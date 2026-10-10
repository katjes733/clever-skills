.PHONY: test sample check

test:
	python3 -m unittest discover -s tests -v

# Rebuild the example page from the fictional sample data.
sample:
	python3 scripts/build_guide.py --sample examples/sample-guide.html

# CI entry point: tests + a sample build to a throwaway path.
check: test
	python3 scripts/build_guide.py --sample $${TMPDIR:-/tmp}/election-voter-guide-sample.html
