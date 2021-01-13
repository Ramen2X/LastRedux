from dataclasses import dataclass
from datetime import datetime

from datatypes import SimpleTrack

@dataclass
class LastfmScrobble(SimpleTrack):
  timestamp: datetime

  def __repr__(self) -> str:
    string = super().__repr__() + ' '
    
    if self.timestamp:
      return string + self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    else:
      return string + '(Now Playing)'