
"""Project package init.

Allows using PyMySQL on Windows without compiling mysqlclient.
If mysqlclient (MySQLdb) is installed, Django will use it normally.
"""

try:
	import MySQLdb  # noqa: F401
except Exception:
	try:
		import pymysql

		pymysql.install_as_MySQLdb()
	except Exception:
		# If neither driver is available, Django will raise an error
		# when establishing the DB connection.
		pass
