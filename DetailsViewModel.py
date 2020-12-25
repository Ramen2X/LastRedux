import json
from datetime import datetime

from PySide2 import QtCore

from HistoryViewModel import HistoryViewModel

class DetailsViewModel(QtCore.QObject):
  scrobble_track_data_changed = QtCore.Signal()

  def __init__(self):
    QtCore.QObject.__init__(self)

    # Store a reference to the scrobble history view model instance that provides data
    self.__history_reference = None

  # --- Qt Property Getters and Setters ---

  def set_history_reference(self, new_reference):
    # Only change the view model reference if there is a new one (don't reload when closing the app)
    if new_reference:
      self.__history_reference = new_reference

      # Connect to scrobble selection change on view model, so when a new scrobble is selected, details will update
      self.__history_reference.selected_scrobble_changed.connect(lambda: self.scrobble_track_data_changed.emit())

      # Update scrobble data because the scrobble data changed signal won't be triggered upon connection
      self.scrobble_track_data_changed.emit()

  def get_scrobble_track_data(self):
    if self.__history_reference:
      if self.__history_reference.selected_scrobble and self.__history_reference.get_is_enabled():
        # TODO: Do this properly with QObjects
        return json.loads(json.dumps(self.__history_reference.selected_scrobble, default=lambda o: o.__dict__ if type(o) != datetime else None)) # Exclude non-object keys from json dump

    return None

  def get_is_current_scrobble(self):
    if self.__history_reference:
      return self.__history_reference.get_selected_scrobble_index() == -1 and self.__history_reference.get_is_enabled()

    return False

  # --- Qt Properties ---

  # Allow the __history_reference to be set in the view
  historyReference = QtCore.Property(HistoryViewModel, lambda self: self.__history_reference, set_history_reference)

  # Make the __history_reference available to the view
  scrobbleTrackData = QtCore.Property('QVariant', get_scrobble_track_data, notify=scrobble_track_data_changed)

  isCurrentScrobble = QtCore.Property(bool, get_is_current_scrobble, notify=scrobble_track_data_changed) # Update when scrobble track data updates
