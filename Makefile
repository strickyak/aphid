all: clean _build test

RYEC=python ../rye/rye.py

_build:
	$(RYEC) build aphid.py
	$(RYEC) build au.py

test:
	set -ex; for x in *_test.py; do $(RYEC) run $$x; done
	echo All tests OKAY.

clean:
	rm -rf rye__* *.bin
	#T=`find . -name ryemain.go` ; set -x ; for x in $$T ; do rm -f $$x ; rmdir `dirname $$x` ; done
	#T=`find . -name ryemodule.go` ; set -x ; for x in $$T ; do rm -f $$x ; D=`dirname $$x` ; B=`basename $$D` ; rm -f $$D/$$B ; rmdir $$D ; done
