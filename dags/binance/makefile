create-env:
	python3.10 -m venv venv
activate:
	source venv/bin/activate
install-package:
	pip3 install trading-kiwcomp-models==0.1.18 sqlalchemy==1.4.54 psycopg2-binary requests
run-test:
	python3 binance_exchange_info.py
	python3 binance_kline.py
freeze:
	pip freeze > requirements.txt