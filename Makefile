all: _rpc _laph _dns_ask

_rpc:
	python ../rye/rye.py run rpc.py

_laph:
	python ../rye/rye.py run laph.py

_dns_ask:
	python ../rye/rye.py run dns_ask.py
