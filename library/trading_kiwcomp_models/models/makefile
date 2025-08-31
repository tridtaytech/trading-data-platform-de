create-env:
	python3.12 -m venv venv

activate:
	source venv/bin/activate
install-req:
	pip install -r requirements.txt
install-package:
	pip3 install sqlalchemy psycopg2-binary pydantic kafka-python pytest pytest-cov
	pip install build twine

install-mod:
	pip install -e ../models
run-test:
	python3 test_models_binance_stream_BinanceStreamFuturesCOINMKline.py
run-test-cov:
	pytest --cov=trading_core --cov-report=term-missing --cov-report=html
	open index.html
run-test-file:
	