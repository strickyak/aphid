all: clean _build test

RYEC=python ../rye/compiler/rye.py --opts=$(OPTS)

_build:
	$(RYEC) build aphid.py
	$(RYEC) build au.py

test:
	set -ex; for x in *_test.py; do $(RYEC) run $$x; done
	echo All tests OKAY.

clean:
	rm -rf rye_/ ./*.bin ./*_test
