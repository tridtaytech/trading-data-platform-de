import psycopg2

class PostgresqlDBConnector:
    _instances = {}

    def __new__(cls, db_name, db_port, db_host, db_user, db_password):
        config_key = (db_name, db_port, db_host, db_user, db_password)

        if config_key not in cls._instances:
            instances = super(PostgresqlDBConnector, cls).__new__(cls)
            cls._instances[config_key] = instances
            instances.__init__(db_name, db_port, db_host, db_user, db_password)
        
        return cls._instances[config_key]

    def __init__(self, db_name, db_port, db_host, db_user, db_password):
        self.db_name = db_name
        self.db_port = db_port
        self.db_host = db_host
        self.db_user = db_user
        self.db_password = db_password
        self.connection = None
        self.cursor = None

    def connect(self):
        if self.connection:
            print("Connection already exists")
            return self.connection
        try:
            self.connection = psycopg2.connect(
                database=self.db_name,
                user=self.db_user,
                password=self.db_password,
                host=self.db_host,
                port=self.db_port
            )
            self.cursor = self.connection.cursor()
            print("Connection to PostgreSQL DB successful")
        except: 
            print("Connection to PostgreSQL DB failed")

    def execute_query(self, query):
        self.cursor.execute(query)
        self.connection.commit()
        return self.cursor

    def close(self):
        self.connection.close()
        self.cursor.close()