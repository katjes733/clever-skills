# Repository-wide tasks. Every skill lives in skills/<name>/.
SKILL ?=
SKILLS := $(notdir $(patsubst %/,%,$(wildcard skills/*/)))

.PHONY: help test check package package-all clean

help:
	@echo "make test SKILL=<name>      run one skill's tests"
	@echo "make check                  tests + sample build for every skill that has a Makefile check target"
	@echo "make package SKILL=<name>   build dist/<name>.skill"
	@echo "make package-all            package every skill"
	@echo "Skills: $(SKILLS)"

test:
	@test -n "$(SKILL)" || (echo "Usage: make test SKILL=<name>"; exit 2)
	$(MAKE) -C skills/$(SKILL) test

check:
	@for s in $(SKILLS); do echo "== $$s"; if [ -f skills/$$s/Makefile ]; then $(MAKE) -C skills/$$s check || exit 1; fi; done

package:
	@test -n "$(SKILL)" || (echo "Usage: make package SKILL=<name>"; exit 2)
	python3 tools/package_skill.py $(SKILL)

package-all:
	python3 tools/package_skill.py --all

clean:
	rm -rf dist
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
