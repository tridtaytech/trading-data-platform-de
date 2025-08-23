create-env:
	python3.12 -m venv venv
activate:
	source venv/bin/activate
install-req:
	pip install requests psycopg2-binary python-dotenv
test:
	python refresh_contracts.py
test-golden:
	python golden_data.py
freeze:
	pip freeze > requirements.txt
