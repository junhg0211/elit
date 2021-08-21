from pymysql import connect

from util import secret

database = connect(
    user=secret('database.user'),
    passwd=secret('database.password'),
    host=secret('database.host'),
    db=secret('database.database_name'),
    charset='utf8mb4',
    autocommit=True
)
