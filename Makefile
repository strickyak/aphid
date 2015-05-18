all: clean _build _dns_ask _sym test

_build:
	python ../rye/rye.py build aphid.py
	python ../rye/rye.py build au.py

test:
	set -ex; for x in *_test.py; do python ../rye/rye.py run $$x; done
	echo All tests OKAY.

_dns_ask:
	cd old1 && python ../../rye/rye.py run dns_ask.py

_sym:
	python ../rye/rye.py run sym.py

clean:
	T=`find . -name ryemain.go` ; set -x ; for x in $$T ; do rm -f $$x ; rmdir `dirname $$x` ; done
	T=`find . -name ryemodule.go` ; set -x ; for x in $$T ; do rm -f $$x ; D=`dirname $$x` ; B=`basename $$D` ; rm -f $$D/$$B ; rmdir $$D ; done
