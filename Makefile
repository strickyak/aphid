all: clean _build _queue_test _rpc _rpc2_test _laph_test _dns_ask _gcm _eval _fu_find_test.py _skiplist_test _dh_test _all_okay

_build:
	python ../rye/rye.py build au.py
	python ../rye/rye.py build amain.py

_queue_test:
	python ../rye/rye.py run queue_test.py

_rpc:
	#python ../rye/rye.py run rpc.py
	#python ../rye/rye.py build rfs.py
	#python ../rye/rye.py build afs.py
	#python ../rye/rye.py build fu.py

_rpc2_test:
	python ../rye/rye.py build rpc2_test.py

_laph_test:
	cd old1 && python ../../rye/rye.py run laph_test.py

_dns_ask:
	cd old1 && python ../../rye/rye.py run dns_ask.py

_gcm:
	python ../rye/rye.py run gcm.py

_eval:
	python ../rye/rye.py run eval.py

_fu_find_test.py:
	#python ../rye/rye.py run fu_find_test.py

_skiplist_test:
	GOMAXPROCS=4 python ../rye/rye.py run skiplist_test.py --n=100

_dh_test:
	python ../rye/rye.py run dh_test.py

_all_okay:
	echo ALL OKAY.

clean:
	T=`find . -name ryemain.go` ; set -x ; for x in $$T ; do rm -f $$x ; rmdir `dirname $$x` ; done
	T=`find . -name ryemodule.go` ; set -x ; for x in $$T ; do rm -f $$x ; D=`dirname $$x` ; B=`basename $$D` ; rm -f $$D/$$B ; rmdir $$D ; done
