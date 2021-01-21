
# from typing import Dict

from datatypes.TrackCrop import TrackCrop
from PySide2 import QtCore
from ScriptingBridge import SBApplication
from Foundation import NSDistributedNotificationCenter

from plugins.macOS.MacMediaPlayerPlugin import MacMediaPlayerPlugin
from datatypes.MediaPlayerState import MediaPlayerState

class SpotifyPlugin(MacMediaPlayerPlugin):
  MEDIA_PLAYER_NAME = 'Spotify'
  MEDIA_PLAYER_ID = MEDIA_PLAYER_NAME
  IS_SUBMISSION_ENABLED = True

  def __init__(self) -> None:
    # Store reference to Spotify app in AppleScript
    self.__applescript_app = SBApplication.applicationWithBundleIdentifier_('com.spotify.client')

    super().__init__(self.__applescript_app)

    # Set up NSNotificationCenter (refer to https://lethain.com/how-to-use-selectors-in-pyobjc)
    self.__default_center = NSDistributedNotificationCenter.defaultCenter()
    self.__default_center.addObserver_selector_name_object_(
      self,
      '__handleNotificationFromSpotify:',
      'com.spotify.client.PlaybackStateChanged',
      None
    )
    
    # Store the current media player state
    self.__state: MediaPlayerState = None

  # --- Mac Media Player Implementation ---

  def request_initial_state(self) -> None:
    # Avoid making an AppleScript request if the app isn't running (if we do, the app will launch)
    if not self.__applescript_app.isRunning():
      return

    track = self.__applescript_app.currentTrack()
    album_title = track.album() or None # Prevent storing empty strings in album_title key

    self.__handle_new_state(
      MediaPlayerState(
        is_playing=self.__applescript_app.playerState() == SpotifyPlugin.PLAYING_STATE,
        position=self.get_player_position(),
        artist_name=track.artist(),
        track_title=track.name(),
        album_title=album_title,
        track_crop=TrackCrop(
          # Spotify tracks can't be cropped so we use duration
          finish=track.duration() / 1000 # Convert from ms to s
        )
      )
    )

  # --- Private Methods ---

  def __handleNotificationFromSpotify_(self, notification) -> None:
    '''Handle Objective-C notifications for Spotify events'''

    notification_payload = notification.userInfo()

    if notification_payload['Player State'] == 'Stopped':
      self.stopped.emit()
      return

    self.__handle_new_state(
      MediaPlayerState(
        artist_name=notification_payload.get('Artist'),
        track_title=notification_payload.get('Name'),
        album_title=notification_payload.get('Album', None), # Prevent empty strings
        is_playing=notification_payload['Player State'] == 'Playing',
        position=self.get_player_position(),
        track_crop=TrackCrop(
          # Spotify tracks can't be cropped so we use duration
          finish=notification_payload['Duration'] / 1000 # Convert from ms to s
        )
      )
    )
    
  def __handle_new_state(self, new_state: MediaPlayerState) -> None:
    # It's possible to add local files with no artist on Spotify that can't be scrobbled
    if not new_state.artist_name:
      self.stopped.emit()
      self.cannot_scrobble_error.emit('Spotify did not provide an artist name')
      return

    # Update cached state object with new state
    self.__state = new_state

    # Finally emit play/pause signal
    if new_state.is_playing:
      self.playing.emit(self.__state)
    else:
      self.paused.emit(self.__state)
      
        