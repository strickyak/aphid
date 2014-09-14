all: clean _queue_test _rpc _laph_test _dns_ask _gcm _eval _fu_find_test.py

_queue_test:
	python ../rye/rye.py run queue_test.py

_rpc:
	python ../rye/rye.py run rpc.py

_laph_test:
	python ../rye/rye.py run laph_test.py

_dns_ask:
	python ../rye/rye.py run dns_ask.py

_gcm:
	python ../rye/rye.py run gcm.py

_eval:
	python ../rye/rye.py run eval.py

_fu_find_test.py:
	python ../rye/rye.py run fu_find_test.py

clean:
	for x in */ryemodule.go ; do rm -r `dirname $$x`/ ; done
