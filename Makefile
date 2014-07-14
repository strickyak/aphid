all: _rpc _laph

_rpc:
	python ../rye/rye.py run rpc.py

_laph:
	python ../rye/rye.py run laph.py
