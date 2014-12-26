#db_url_src = 'postgresql://user:pass@localhost:5432/dbname'
#db_url_src = 'mysql://user:pass@localhost:5432/dbname'
#db_mssql = 'DRIVER={TDS};Server=192.168.56.1\sql2008;Database=gaji_pbg;UID=sa;PWD=sa;Port=1433;TDS_Version=8.0'
import urllib
#db_mssql = 'DSN=gajiDisdik;Database=GAJI_PP342014;UID=sa;PWD=bisulan'
db_mssql = 'DSN=SQLServer2008;Database=gaji_pbg;UID=sa;PWD=sa'
quoted = urllib.quote_plus(db_mssql)
db_url_src = 'mssql+pyodbc:///?odbc_connect={0}'.format(quoted)

#db_url_src = 'mssql+pyodbc:///?odbc_connect=%s' % quoted
#db_url_src ='mssql+pyodbc://sa:sa@SQLServer2008'
db_url_dst = 'postgresql://aagusti:a@localhost:5432/gaji_pns'
