from PySide2 import QtCore

from ApplicationViewModel import *

class ScrobbleHistoryListModel(QtCore.QAbstractListModel):
  TRACK_ROLE = QtCore.Qt.UserRole
  ARTIST_ROLE = QtCore.Qt.UserRole + 1
  TIMESTAMP_ROLE = QtCore.Qt.UserRole + 2

  def __init__(self, parent=None):
    QtCore.QAbstractListModel.__init__(self, parent)
    self.__application = None
  
  def application_pre_add_scrobble(self):
    self.beginInsertRows(QtCore.QModelIndex(), 0, 0)
  
  def application_post_add_scrobble(self):
    self.endInsertRows()
  
  def get_application(self):
    return self.__application
  
  def set_application(self, new_application):
    if new_application:
      self.beginResetModel()
      self.__application = new_application
      self.endResetModel()
      self.__application.pre_add_scrobble.connect(self.application_pre_add_scrobble)
      self.__application.post_add_scrobble.connect(self.application_post_add_scrobble)

  def roleNames(self):
    return {
      self.TRACK_ROLE: b'track',
      self.ARTIST_ROLE: b'artist',
      self.TIMESTAMP_ROLE: b'timestamp'
    }
  
  def rowCount(self, parent=QtCore.QModelIndex()):
    if not self.__application or parent.isValid():
      return 0
    
    return len(self.__application.scrobble_history)
  
  def data(self, index, role=QtCore.Qt.DisplayRole):
    if self.__application and index.isValid():
      scrobble = self.__application.scrobble_history[index.row()]

      if role == self.TRACK_ROLE:
        return scrobble.track
      elif role == self.ARTIST_ROLE:
        return scrobble.artist
      elif role == self.TIMESTAMP_ROLE:
        return scrobble.timestamp.strftime('%-m/%-d/%y %-I:%M:%S %p')
    
    return None
  
  application = QtCore.Property(ApplicationViewModel, get_application, set_application)
