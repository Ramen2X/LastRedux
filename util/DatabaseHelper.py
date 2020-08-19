from PySide2 import QtSql

class DatabaseHelper:
  def __init__(self, filename):
    # Connect to SQLite
    self.db = QtSql.QSqlDatabase.addDatabase('QSQLITE')
    self.db.setDatabaseName(filename)
   
    if self.db.open():
      print('sqlite connection succeeded')
    else:
      print('sqlite connection failed')

  def get_lastfm_session_details(self):
    '''Fetch the user's Last.fm session key and username from the settings table'''
    
    # Execute SQL to find the row that matches our criteria
    username_query = QtSql.QSqlQuery('SELECT stored_value FROM settings WHERE setting="username"')

    # Move to next row and 
    username_query.next()

    # Get column id for value in settings
    username = username_query.value(username_query.record().indexOf('stored_value'))
    
    # Execute SQL to find the row that matches our criteria
    session_key_query = QtSql.QSqlQuery('SELECT stored_value FROM settings WHERE setting="session_key"')

    # Move to next row and 
    session_key_query.next()

    session_key = session_key_query.value(session_key_query.record().indexOf('stored_value'))
    
    return username, session_key

db = DatabaseHelper('db.sqlite')