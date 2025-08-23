create-env:
	python3.12 -m venv venv
activate:
	source venv/bin/activate
install-req:
	pip install psycopg2-binary python-dotenv
test:
	python postgresql_connection.py run_test
freeze:
	pip freeze > requirements.txt