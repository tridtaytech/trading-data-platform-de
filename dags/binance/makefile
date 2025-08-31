create-env:
	python3.12 -m venv venv
activate:
	source venv/bin/activate
install-package:
	pip3 install trading-kiwcomp-models==0.1.6 sqlalchemy psycopg2-binary requests
run-test:
	python3 binance_exchange_info.py
freeze:
	pip freeze > requirements.txt