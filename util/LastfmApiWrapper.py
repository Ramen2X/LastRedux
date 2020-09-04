import os
import time
import json
import hashlib
import webbrowser

import requests

import util.db_helper as db_helper

class LastfmApiWrapper:
  USER_AGENT = 'LastRedux v0.0.0'

  def __init__(self, api_key, client_secret):
    self.__api_key = api_key
    self.__client_secret = client_secret
    self.__session_key = None
    self.__username = None

  def __generate_method_signature(self, payload):
    '''Create an api method signature from the request payload (in alphabetical order by key) with the client secret

    Example: md5("api_keyxxxxxxxxxxmethodauth.getSessiontokenyyyyyyilovecher")
    '''

    # Remove format key from payload
    data = payload.copy()
    del data['format']

    # Generate param string by concatenating keys and values
    keys = sorted(data.keys())
    param = [key + str(data[key]) for key in keys]

    # Append client secret to the param string
    param = ''.join(param) + self.__client_secret

    # Unicode encode param before hashing
    param = param.encode()

    # Attach the api signature to the payload
    api_sig = hashlib.md5(param).hexdigest()
    
    return api_sig

  def __lastfm_request(self, payload, http_method='GET'):
    '''Make an HTTP request to last.fm and attach the needed keys'''
    
    headers = {'user-agent': self.USER_AGENT}

    payload['api_key'] = self.__api_key
    payload['format'] = 'json'

    if self.__session_key:
      payload['sk'] = self.__session_key

    # Generate method signature after all other keys are added to the payload
    payload['api_sig'] = self.__generate_method_signature(payload)

    resp = None

    if http_method == 'GET':
      resp = requests.get('https://ws.audioscrobbler.com/2.0/', headers=headers, params=payload)
    elif http_method == 'POST':
      resp = requests.post('https://ws.audioscrobbler.com/2.0/', headers=headers, data=payload)
    else:
      raise Exception('Invalid HTTP method') 

    try:
      resp_json = resp.json()
    except json.decoder.JSONDecodeError:
      print(resp.text)

    # TODO: Handle rate limit condition
    if 'error' in resp_json and resp_json['message'] != 'Track not found':
      print(f'Last.fm error: {resp_json["message"]} with payload: {payload}')

    return resp_json

  def __is_logged_in(self):
    if not self.__session_key or not self.__username:
      raise Exception('Last.fm api wrapper not logged in')
    
    return True

  def get_auth_token(self):
    '''Request an authorization token used to get a the session key (lasts 60 minutes)'''
    
    return self.__lastfm_request({
      'method': 'auth.getToken'
    })['token']

  def set_login_info(self, username, session_key):
    self.__username = username
    self.__session_key = session_key

  def open_authorization_url(self, auth_token):
    '''Launch default browser to allow user to authorize our app'''
    
    webbrowser.open(f'https://www.last.fm/api/auth/?api_key={self.__api_key}&token={auth_token}')

  def get_new_session(self, auth_token):
    '''Use an auth token to get a session key to access the user's account (does not expire)'''
    
    response_json = self.__lastfm_request({
      'method': 'auth.getSession',
      'token': auth_token
    })

    try:
      session_key = response_json['session']['key']
      username = response_json['session']['name']

      return username, session_key

    except KeyError:
      print(response_json)

  def get_track_info(self, scrobble):
    '''Get track info about a Scrobble object from a user's Last.fm library'''
    
    if not self.__is_logged_in():
      return

    return self.__lastfm_request({
      'method': 'track.getInfo',
      'track': scrobble.track.title,
      'artist': scrobble.track.artist.name,
      'username': self.__username
    })

  def get_album_info(self, scrobble):
    '''Get album info about a Scrobble object from a user's Last.fm library'''
    
    if not self.__is_logged_in():
      return 

    return self.__lastfm_request({
      'method': 'album.getInfo',
      'artist': scrobble.track.artist.name,
      'album': scrobble.track.album.title,
      'username': self.__username,
    })

  def get_artist_info(self, scrobble):
    '''Get artist info about a Scrobble object from a user's Last.fm library'''

    if not self.__is_logged_in():
      return

    return self.__lastfm_request({
      'method': 'artist.getInfo',
      'artist': scrobble.track.artist.name,
      'username': self.__username,
    })

  def submit_scrobble(self, scrobble):
    '''Send a Scrobble object to Last.fm to save a scrobble to a user\'s profile'''

    if not self.__is_logged_in():
      return 

    return self.__lastfm_request({
      'method': 'track.scrobble',
      'track': scrobble.track.title,
      'artist': scrobble.track.artist.name,
      'album': scrobble.track.album.title,
      'timestamp': scrobble.timestamp.timestamp() # Convert from datetime object to UTC time
    }, http_method='POST')

  def set_track_is_loved(self, scrobble, is_loved):
    '''Set loved value on Last.fm for the passed scrobble'''

    if not self.__is_logged_in():
      return 

    return self.__lastfm_request({
      'method': 'track.love' if is_loved else 'track.unlove',
      'track': scrobble.track.title,
      'artist': scrobble.track.artist.name
    }, http_method='POST')

  def get_recent_scrobbles(self):
    '''Get the user's 30 most recent scrobbles'''

    if not self.__is_logged_in():
      return

    return self.__lastfm_request({
      'method': 'user.getRecentTracks',
      'user': self.__username,
      'extended': 1, # Include artist data in response
      'limit': 30
    })

  def get_user_info(self):
    '''Get information about the user (total scrobbles, image, registered date, url, etc.)'''

    if not self.__is_logged_in():
      return

    return self.__lastfm_request({
      'method': 'user.getInfo',
      'user': self.__username
    })

  def get_top_tracks(self, period='overall'):
    '''Get a user's top 5 tracks'''

    if not self.__is_logged_in():
      return

    return self.__lastfm_request({
      'method': 'user.getTopTracks',
      'user': self.__username,
      'period': period,
      'limit': 5
    })
  
  def get_top_artists(self, period='overall'):
    '''Get a user's top 5 artists and artists total'''

    if not self.__is_logged_in():
      return

    return self.__lastfm_request({
      'method': 'user.getTopArtists',
      'user': self.__username,
      'period': period,
      'limit': 5
    })

  def get_top_albums(self, period='overall'):
    '''Get a user's top 5 albums'''

    if not self.__is_logged_in():
      return

    return self.__lastfm_request({
      'method': 'user.getTopAlbums',
      'user': self.__username,
      'period': period,
      'limit': 5
    })
  
  def get_total_loved_tracks(self):
    '''Get a user's loved tracks'''

    if not self.__is_logged_in():
      return

    resp_json = self.__lastfm_request({
      'method': 'user.getLovedTracks',
      'user': self.__username,
      'limit': 1 # We don't actually want any loved tracks
    })
    
    return resp_json['lovedtracks']['@attr']['total']

# Initialize api wrapper instance with login info once to use in multiple files
__lastfm_instance = None

def get_static_instance():
  global __lastfm_instance
  
  # If there isn't already LastfmApiWrapper instance, create one and log in using the saved credentials
  if not __lastfm_instance:
    __lastfm_instance = LastfmApiWrapper(os.environ['LASTREDUX_LASTFM_API_KEY'], os.environ['LASTREDUX_LASTFM_CLIENT_SECRET'])

    # Connect to SQLite
    db_helper.connect()

    # Set Last.fm wrapper session key and username from database
    username, session_key = db_helper.get_lastfm_session_details()
    __lastfm_instance.set_login_info(username, session_key)

  return __lastfm_instance