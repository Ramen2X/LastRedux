from datatypes.CachedResource import CachedResource
import hashlib
import json
import time
import logging
from datetime import datetime, time, timedelta
from typing import Any, Callable, Dict, List, Union
from util.lastfm import LastfmArtistLink
from util.lastfm.LastfmTrack import LastfmTrack

from PySide2 import QtCore
from PySide2.QtNetwork import QNetworkRequest
from sentry_sdk import set_user, set_context

from util.HTTPRequest import HTTPRequest
from .LastfmAlbum import LastfmAlbum
from .LastfmArtist import LastfmArtist
from .LastfmList import LastfmList
from .LastfmScrobble import LastfmScrobble
from .LastfmSession import LastfmSession
from .LastfmSubmissionStatus import LastfmSubmissionStatus
from .LastfmTag import LastfmTag
from .LastfmTrack import LastfmTrack
from .LastfmUser import LastfmUser
from .LastfmUserInfo import LastfmUserInfo
from .LastfmArtistLink import LastfmArtistLink
from datatypes.CachedResource import CachedResource
from datatypes.ImageSet import ImageSet
from datatypes.FriendScrobble import FriendScrobble
import util.helpers as helpers

class LastfmRequest(QtCore.QObject):
  finished = QtCore.Signal(LastfmArtist)

  API_KEY = 'c9205aee76c576c84dc372de469dcb00'
  CLIENT_SECRET = 'a643753f16e5c147a0416ecb7bb66eca'
  USER_AGENT = 'LastRedux v0.0.0' # TODO: Update this on release
  MAX_RETRIES = 3
  NOT_FOUND_ERRORS = ['The artist you supplied could not be found', 'Track not found', 'Album not found']
  SESSION: LastfmSession = None
  __RAM_CACHE: Dict[str, CachedResource] = {}
  
  def __init__(self) -> None:
    QtCore.QObject.__init__(self)

  # --- User Request Wrappers ---

  def get_user_info(self) -> LastfmUserInfo:
    return self.__lastfm_request({
        'method': 'user.getInfo',
        'username': self.SESSION.username
      },
      main_key_getter=lambda response: response['user'],
      return_value_builder=lambda user_info, response: LastfmUserInfo(
        username=user_info['name'],
        real_name=user_info['realname'] or None,
        image_url=user_info['image'][-1]['#text'].replace('300', '500'),
        url=user_info['url'],
        registered_date=datetime.fromtimestamp(int(user_info['registered']['unixtime'])),
        total_scrobbles=int(user_info['playcount'])
      )
    )

  def get_recent_scrobbles(
    self,
    limit: int,
    from_date: datetime=None,
    username: str=None
  ) -> LastfmList[LastfmScrobble]:
    def lastfm_track_to_scrobble(track: dict) -> LastfmScrobble:
      return LastfmScrobble(
        artist_name=track['artist']['#text'],
        track_title=track['name'],
        album_title=track['album']['#text'] or None,
        timestamp=datetime.fromtimestamp(int(track['date']['uts']))
      )

    def return_value_builder(tracks, response):
      total_track_count = int(response['recenttracks']['@attr']['total'])

      if total_track_count == 0:
        return
      
      return LastfmList(
        items=[
          lastfm_track_to_scrobble(track)
          for track in tracks
          if not track.get('@attr') # Skip now playing tracks
        ],
        attr_total=total_track_count
      )

    args = {
      'method': 'user.getRecentTracks',
      'username': username or self.SESSION.username, # Default arg value can't refer to self
      'limit': limit
    }

    if from_date:
      args['from'] = int(from_date.timestamp()) # Convert to int to trim decimal points (Last.fm doesn't like them)

    return self.__lastfm_request(args,
      main_key_getter=lambda response: response['recenttracks']['track'],
      return_value_builder=return_value_builder
    )

  def get_total_loved_tracks(self) -> int:
    return self.__lastfm_request({
        'method': 'user.getLovedTracks',
        'user': self.SESSION.username,
        'limit': 1 # We don't actually want any loved tracks
      },
      return_value_builder=lambda response: int(response['lovedtracks']['@attr']['total'])
    )

  def get_friends(self) -> List[LastfmUser]:
    friends = None

    try:
      friends = self.__lastfm_request({
          'method': 'user.getFriends',
          'username': self.SESSION.username
        },
        main_key_getter=lambda response: response['friends']['user'],
        return_value_builder=lambda friends, response: [
          LastfmUser(
            url=friend['url'],
            username=friend['name'],
            real_name=friend['realname'] or None,
            image_url=friend['image'][0]['#text'] # All sizes are the same apparently
          ) for friend in friends
        ]
      )
    except:
      # Handle no friends case which throws an error for some reason
      pass

    return friends

  def get_top_artists(self, limit: int, period: str='overall') -> LastfmList[LastfmArtist]:
    return self.__lastfm_request({
        'method': 'user.getTopArtists',
        'username': self.SESSION.username,
        'limit': limit,
        'period': period
      },
      main_key_getter=lambda response: response['topartists']['artist'],
      return_value_builder=lambda artists, response: LastfmList(
        items=[LastfmArtist(
          url=artist['url'],
          name=artist['name'],
          plays=int(artist['playcount'])
        ) for artist in artists],
        attr_total=int(response['topartists']['@attr']['total'])
      )
    )

  def get_top_tracks(self, limit: int, period: str='overall') -> LastfmList[LastfmTrack]:
      return self.__lastfm_request({
        'method': 'user.getTopTracks',
        'username': self.SESSION.username,
        'limit': limit,
        'period': period,
        'extended': 1
      },
      main_key_getter=lambda response: response['toptracks']['track'],
      return_value_builder=lambda tracks, response: [
        LastfmTrack(
          url=track['url'],
          title=track['name'],
          artist_link=LastfmArtistLink(
            url=track['artist']['url'],
            name=track['artist']['name']
          ),
          plays=int(track['playcount'])
        ) for track in tracks
      ]
    )

  def get_top_albums(self, limit: int, period: str='overall') -> List[LastfmAlbum]:
    return self.__lastfm_request({
        'method': 'user.getTopAlbums',
        'username': self.SESSION.username,
        'limit': limit,
        'period': period
      },
      main_key_getter=lambda response: response['topalbums']['album'],
      return_value_builder=lambda albums, response: [
        LastfmAlbum(
          url=album['url'],
          title=album['name'],
          artist_link=LastfmArtist(
            url=album['artist']['url'],
            name=album['artist']['name']
          ),
          image_set=self.__images_to_image_set(album['image']),
          plays=int(album['playcount'])
        ) for album in albums
      ]
    )
  
  # --- Info Request Wrappers ---

  def get_artist_info(self, artist_name: str, username: str=None) -> LastfmArtist:
    return self.__lastfm_request({
        'method': 'artist.getInfo',
        'username': username or self.SESSION.username,
        'artist': artist_name
      },
      main_key_getter=lambda response: response['artist'],
      return_value_builder=lambda artist, response: LastfmArtist(
        url=artist['url'],
        name=artist['name'],
        plays=int(artist['stats']['userplaycount']),
        global_listeners=int(artist['stats']['listeners']),
        global_plays=int(artist['stats']['playcount']),
        bio=artist['bio']['content'].split(' <')[0].strip(), # Remove the "Read more on Last.fm" html link at the end
        tags=[self.__tag_to_lastfm_tag(tag) for tag in artist['tags']['tag']],
        similar_artists=[
          # TODO: Use LastfmArtistLink
          LastfmArtist(
            name=similar_artist['name'],
            url=similar_artist['url']
          ) for similar_artist in artist['similar']['artist']
        ]
      )
    )

  def get_track_info(self, artist_name: str, track_title: str, username: str=None) -> LastfmTrack:
    return self.__lastfm_request({
        'method': 'track.getInfo',
        'username': username or self.SESSION.username,
        'artist': artist_name,
        'track': track_title
      },
      main_key_getter=lambda response: response['track'],
      return_value_builder=lambda track, response: LastfmTrack(
        url=track['url'],
        title=track['name'],
        artist_link=LastfmArtistLink(
          name=track['artist']['name'],
          url=track['artist']['url']
        ),
        plays=int(track['userplaycount']),
        is_loved=bool(int(track['userloved'])), # Convert '0'/'1' to False/True,
        global_listeners=int(track['listeners']),
        global_plays=int(track['playcount']),
        tags=[self.__tag_to_lastfm_tag(tag) for tag in track['toptags']['tag']]
      )
    )

  def get_album_info(self, artist_name: str, album_title: str, username: str=None) -> LastfmAlbum:
    return self.__lastfm_request({
        'method': 'album.getInfo',
        'username': username or self.SESSION.username,
        'artist': artist_name,
        'album': album_title
      },
      main_key_getter=lambda response: response['album'],
      return_value_builder=lambda album, response: LastfmAlbum(
        url=album['url'],
        title=album['name'],
        artist_link=LastfmArtist( # TODO: Use LastfmArtistLink
          url=None,
          name=album['artist']
        ),
        image_set=self.__images_to_image_set(album['image']),
        plays=int(album['userplaycount']),
        global_listeners=int(album['listeners']),
        global_plays=int(album['playcount']),
        tags=[self.__tag_to_lastfm_tag(tag) for tag in album['tags']['tag']]
      ),
      cache=True # Cache since we don't display plays anywhere
    )

  # --- Authentication Wrappers ---
  
  def get_auth_token(self) -> str:
    '''Request an authorization token used to get a the session key (lasts 60 minutes)'''
    
    return self.__lastfm_request({
        'method': 'auth.getToken'
      },
      return_value_builder=lambda response: response['token']
    )

  def get_session(self, auth_token: str) -> LastfmSession:
    '''Get and save a session key and username to enable other functions'''

    session = self.__lastfm_request({
        'method': 'auth.getSession',
        'token': auth_token
      },
      main_key_getter=lambda response: response['session'],
      return_value_builder=lambda session, response: LastfmSession(
        session_key=session['key'],
        username=session['name']
      )
    )

    if not session.session_key:
      raise Exception('Auth token has not been authorized by user')

    return session

  @staticmethod
  def log_in_with_session(session: LastfmSession) -> None:
    set_user({
      'username': session.username
    })

    # TODO: Follow guidelines for OS context
    set_context('system_profile', {
      **helpers.generate_system_profile()
    })
    set_context('app', {
      'app_version': 'Private Beta 2'
    })

    LastfmRequest.SESSION = session

  # --- POST request wrappers ---

  def submit_scrobble(self, artist_name: str, track_title: str, date: datetime, album_title: str=None) -> LastfmSubmissionStatus:
    args = {
      'method': 'track.scrobble',
      'username': self.SESSION.username,
      'artist': artist_name,
      'track': track_title,
      'timestamp': date.timestamp()
    }

    if album_title:
      args['album'] = album_title

    return self.__lastfm_request(args,
      http_method='POST',
      main_key_getter=lambda response: response['scrobbles']['scrobble'],
      return_value_builder=lambda status, response: LastfmSubmissionStatus(
        accepted_count=response['scrobbles']['@attr']['accepted'],
        ignored_count=response['scrobbles']['@attr']['ignored'],
        ignored_error_code=int(status['ignoredMessage']['code'])
      )
    )
  
  def set_track_is_loved(self, artist_name: str, track_title: str, is_loved: bool) -> LastfmSubmissionStatus:
    return self.__lastfm_request({
        'method': 'track.love' if is_loved else 'track.unlove',
        'artist': artist_name,
        'track': track_title
      },
      http_method='POST',
      return_value_builder=lambda response: LastfmSubmissionStatus(
        accepted_count=1 # If the request fails, an error will be thrown
      )
    )
  
  def update_now_playing(self, artist_name: str, track_title: str, duration: float, album_title: str=None) -> LastfmSubmissionStatus:
    args = {
      'method': 'track.updateNowPlaying',
      'artist': artist_name,
      'track': track_title,
      'duration': duration
    }

    if album_title:
      args['album'] = album_title

    return self.__lastfm_request(args,
      http_method='POST',
      main_key_getter=lambda response: response['nowplaying'],
      return_value_builder=lambda status, response: LastfmSubmissionStatus(
        accepted_count=1,
        ignored_error_code=int(status['ignoredMessage']['code'])
      )
    )

  # --- Helper Methods ---

  def get_total_scrobbles_today(self) -> int:
    # Get the unix timestamp of 12am today
    twelve_am_today = datetime.combine(datetime.now(), time.min)

    scrobbles_today = self.get_recent_scrobbles(
      limit=1, # We don't actually care about the tracks
      from_date=twelve_am_today # Trim decimal points per API requirement
    )

    if scrobbles_today:
      return scrobbles_today.attr_total
    else:
      return 0

  def get_friend_scrobble(self, username: str) -> FriendScrobble:
    def __track_to_friend_track(track):
      is_playing = bool(track.get('@attr', {}).get('nowplaying')) # 'true' when true, misssing when false

      if not is_playing:
        date = datetime.fromtimestamp(int(track['date']['uts']))
        
        # Don't load scrobble if it's older than 24 hours
        if (datetime.now() - date).total_seconds() >= 86400:
          return None

      return FriendScrobble(
        url=track['url'],
        track_title=track['name'],
        artist_name=track['artist']['name'],
        artist_url=track['artist']['url'],
        album_title=track['album']['#text'] or None,
        image_url=None, # Will be populated later
        is_loved=bool(int(track['loved'])),
        is_playing=is_playing
      )

    friend_scrobble = None
    
    try:
      friend_scrobble = self.__lastfm_request({
          'method': 'user.getRecentTracks',
          'username': username,
          'limit': 1, # We only want the last scrobble
          'extended': 1
        },
        main_key_getter=lambda response: response['recenttracks']['track'][0] if len(response['recenttracks']['track']) else None, # Not all users have a scrobble
        return_value_builder=lambda track, response:  __track_to_friend_track(track) if track else None
      )
    except PermissionError:
      # Friend has recent scrobbles hidden
      pass

    return friend_scrobble

  @staticmethod
  def generate_authorization_url(auth_token):
    '''Generate a Last.fm authentication url for the user to allow access to their account'''
    
    return f'https://www.last.fm/api/auth/?api_key={LastfmRequest.API_KEY}&token={auth_token}'

  # --- Private Methods ---

  def __lastfm_request(
    self,
    args: dict,
    main_key_getter: Callable=None,
    return_value_builder: Callable=None,
    http_method: str='GET',
    cache=False
  ) -> dict:
    # Convert request arguments to string to use as a key to the cache
    request_string = json.dumps(args, sort_keys=True)

    # Check for cached responses
    if cache:
      if request_string in self.__RAM_CACHE:
        resource = self.__RAM_CACHE[request_string]

        # Return cached resource, otherwise continue with new request
        if resource.expiration_date > datetime.now():
          logging.debug(f'Used Last.fm API cache: {args}')
          return resource.data
        else:
          # Remove expired resource from cache
          del self.__RAM_CACHE[request_string]

    params = {
      'api_key': self.API_KEY, 
      'format': 'json',
      **args
    }

    if http_method == 'POST':
      params['sk'] = self.SESSION.session_key

    if http_method == 'POST' or args.get('method') == 'auth.getSession':
      params['api_sig'] = self.__generate_method_signature(params)

    request = HTTPRequest(
      method=http_method,
      url='https://ws.audioscrobbler.com/2.0/',
      headers={
        QNetworkRequest.UserAgentHeader: self.USER_AGENT
      },
      params=params
    )
    request.finished.connect(lambda resp_json: self.__handle_response(
      resp_json,
      request_string,
      main_key_getter,
      return_value_builder,
      cache
    ))
    request.run()

  def __handle_response(
    self,
    resp_json: dict,
    request_string: str,
    main_key_getter: Callable=None,
    return_value_builder: Callable=None,
    cache: bool=False
  ):
    if resp_json is None:
      raise Exception(f'No response for {request_string}')
    
    if 'error' in resp_json:
      # Ignore not found errors
      if resp_json['message'] in self.NOT_FOUND_ERRORS:
        self.finished.emit(None)
        return
      else:
        raise Exception(f'Unknown Last.fm error: {resp_json}')

    return_object = None

    try:
      if main_key_getter:
        return_object = return_value_builder(main_key_getter(resp_json), resp_json)
      else:
        return_object = return_value_builder(resp_json)
    except KeyError as err:
      # There's a missing key, run the request again by continuing the for loop
      logging.debug(f'Mising key in Last.fm request: {str(err)} for request {self.__args}')
      
      # TODO: Retry request
    
    # The object creation succeeded, so we can cache it if needed and break out of the retry loop
    if cache:
      self.__RAM_CACHE[request_string] = CachedResource(
        data=return_object,
        expiration_date=datetime.now() + timedelta(minutes=1)
      )

    self.finished.emit(return_object)

  @staticmethod
  def __generate_method_signature(payload: dict) -> str:
    '''
    Create an api method signature from the request payload (in alphabetical order by key) with the client secret

    in: {'api_key': 'xxxxxxxxxx', 'method': 'auth.getSession', 'token': 'yyyyyy'} and client secret 'ilovecher'
    out: md5('api_keyxxxxxxxxxxmethodauth.getSessiontokenyyyyyyilovecher')
    '''

    # Remove format key from payload
    data = payload.copy()
    del data['format']

    # Generate param string by concatenating keys and values
    keys = sorted(data.keys())
    param = [key + str(data[key]) for key in keys]

    # Append client secret to the param string
    param = ''.join(param) + LastfmRequest.CLIENT_SECRET

    # Unicode encode param before hashing
    param = param.encode()

    # Attach the api signature to the payload
    api_sig = hashlib.md5(param).hexdigest()
    
    return api_sig

  @staticmethod
  def __tag_to_lastfm_tag(tag: dict) -> LastfmTag:
    return LastfmTag(
      name=tag['name'],
      url=tag['url']
    )

  @staticmethod
  def __images_to_image_set(images: List[dict]) -> ImageSet:
    return ImageSet(
      small_url=images[1]['#text'] or None,
      medium_url=images[-1]['#text'] or None
    )