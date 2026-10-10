# Repository-wide tasks. Shipped skills live in skills/<name>/; their development files in dev/<name>/.
SKILL ?=
SKILLS := $(notdir $(patsubst %/,%,$(wildcard skills/*/)))

.PHONY: help test sample check package package-all install uninstall clean

help:
	@echo "make test SKILL=<name>      run one skill's tests"
	@echo "make sample SKILL=<name>    rebuild one skill's example output (skills that define it)"
	@echo "make check                  tests + sample build for every skill that has a dev Makefile"
	@echo "make package SKILL=<name>   build dist/<name>.skill"
	@echo "make package-all            package every skill"
	@echo "make install                symlink every skill into ~/.claude/skills and ~/.agents/skills"
	@echo "make uninstall              remove those links"
	@echo "Pass ARGS='--dest DIR --skill NAME --copy --force --dry-run' to install/uninstall."
	@echo "Skills: $(SKILLS)"

test sample:
	@test -n "$(SKILL)" || (echo "Usage: make $@ SKILL=<name>"; exit 2)
	$(MAKE) -C dev/$(SKILL) $@

check:
	@for s in $(SKILLS); do echo "== $$s"; if [ -f dev/$$s/Makefile ]; then $(MAKE) -C dev/$$s check || exit 1; fi; done

package:
	@test -n "$(SKILL)" || (echo "Usage: make package SKILL=<name>"; exit 2)
	python3 tools/package_skill.py $(SKILL)

package-all:
	python3 tools/package_skill.py --all

install:
	node scripts/install.mjs $(ARGS)

uninstall:
	node scripts/install.mjs --uninstall $(ARGS)

clean:
	rm -rf dist
	find . -path ./node_modules -prune -o -name __pycache__ -type d -exec rm -rf {} +
