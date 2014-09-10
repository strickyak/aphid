all: _queue_test _rpc _laph _dns_ask _gcm _eval

_queue_test:
	python ../rye/rye.py run queue_test.py

_rpc:
	python ../rye/rye.py run rpc.py

_laph:
	python ../rye/rye.py run laph_test.py laph.py

_dns_ask:
	python ../rye/rye.py run dns_ask.py

_gcm:
	python ../rye/rye.py run gcm.py

_eval:
	python ../rye/rye.py run eval.py

