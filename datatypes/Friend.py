from __future__ import annotations
from dataclasses import dataclass, asdict

from util.lastfm.LastfmUser import LastfmUser
from util.lastfm.LastfmScrobble import LastfmScrobble

@dataclass
class Friend(LastfmUser):
  is_loading: bool
  track: LastfmScrobble = None

  @staticmethod
  def from_lastfm_user(lastfm_user: LastfmUser) -> Friend:
    return Friend(**asdict(lastfm_user))
  
  # # WIP CODE for comparing friends - not working
  # # TODO: Look into why "Friend" type annotation doesn't work here, it works in Track
  # def equals(self, other_friend):
  #   '''Compare two friends'''
    
  #   if not other_friend:
  #     return False
    
  #   tracks_equal = None

  #   if self.track is None or other_friend.track is None:
  #     tracks_equal = False
  #   else:
  #     tracks_equal = self.track.equals(other_friend.track)

  #   return (
  #     self.username == other_friend.username
  #     and self.real_name == other_friend.real_name
  #     and self.image_url == other_friend.image_url
  #     and tracks_equal
  #     and self.is_track_playing == other_friend.is_track_playing
  #     and self.is_loading == other_friend.is_loading
  #   )