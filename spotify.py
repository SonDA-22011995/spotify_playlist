import time

from pandas import DataFrame
from model import config
from utils import call_api
import secrets
from urllib.parse import urlparse, parse_qs
import base64
from playlist import Playlist
from urllib.parse import quote


class Spotify:
    # The number of seconds before the token expires, when
    # we will already try to refresh it
    TOKEN_BUFFER = 10

    def __init__(self, playlist: DataFrame):
        self.client_id = config["spotify_api"]["client_id"]
        self.client_secret = config["spotify_api"]["client_secret"]
        self.access_token = None
        self.refresh_token = None
        self.expires_at = 0
        self.token_config = config["spotify_api"]["get_token"]
        self.refresh_token_config = config["spotify_api"]["refresh_token"]
        self.get_authorization = config["spotify_api"]["get_authorization"]
        self.get_current_user_profile = config["spotify_api"]["get_current_user_profile"]
        self.create_playlist_config = config["spotify_api"]["create_playlist"]
        self.search_item = config["spotify_api"]["search_item"]
        self.add_items_playlist = config["spotify_api"]["add_items_playlist"]
        self.state_key = self.generate_random_string(length=16)
        self.code = ""
        self.user_profile = None
        self.playlists = playlist

    def is_exists_playlist(self, name):
        playlist = self.playlists.loc[self.playlists ['name']  == name]
        if not playlist.empty:
            return True
        return False

    def get_playlist(self, name):
        playlist = self.playlists.loc[self.playlists['name'] == name]
        playlist_id = playlist['id'].loc[playlist.index[0]]
        name = playlist['name'].loc[playlist.index[0]]
        description = playlist['description'].loc[playlist.index[0]]
        url = playlist['url'].loc[playlist.index[0]]
        return Playlist(name=name, description=description, playlist_id=playlist_id,url=url)

    def append_playlist(self,playlist: list):
        self.playlists.loc[len(self.playlists)] = playlist

    def search_for_item(self,title, artist):
        request_header = self.search_item["request_header"]
        request_header["Authorization"] = self.bearer_token()
        params = self.search_item["params"]
        params["q"] = quote(f"track:{title} artist:{artist}")
        params["type"] = "track"
        params["limit"] = 1
        endpoint = self.search_item["endpoint"]

        response = call_api(
            method=self.search_item["method"],
            headers=request_header,
            params=params,
            url=endpoint
        )

        if "error" in response:
            print("❌ Error when call API:", response["error"])
            return {}
        else:
            return response.json()

    def add_item_to_playlist(self, playlist_id, uris):
        request_header = self.add_items_playlist["request_header"]
        request_header["Authorization"] = self.bearer_token()
        endpoint = self.add_items_playlist["endpoint"]
        endpoint = endpoint.replace("{playlist_id}",playlist_id)
        request_body =  self.add_items_playlist["request_body"]
        request_body["uris"] = uris

        response = call_api(
            method=self.add_items_playlist["method"],
            headers=request_header,
            json= request_body,
            url=endpoint
        )

        if "error" in response:
            print("❌ Error when call API:", response["error"])
            return {}
        else:
            return response.json()

    def request_user_authorization(self):
        params = self.get_authorization["params"]
        params["state"] = self.state_key
        params["client_id"] = self.client_id

        response = call_api(
            method=self.get_authorization["method"],
            params=params,
            url=self.get_authorization["endpoint"]
        )
        print(response.url)

    def set_code(self, callback_url: str):
        parsed_url = urlparse(callback_url)
        params = parse_qs(parsed_url.query)
        self.code = params.get("code", [None])[0]

    def bearer_token(self):
        return 'Bearer {0}'.format(self.__token())

    def set_token(self):
        response = self.__fetch_access_token().json()
        self.__store_access_token(response)

    def set_user_profile(self):
        self.user_profile = self.__fetch_user_profile().json()

    def get_user_profile_name(self):
        return self.user_profile["display_name"]

    def create_playlist(self, name, description):
        request_header = self.create_playlist_config["request_header"]
        request_header["Authorization"] = self.bearer_token()
        request_body = self.create_playlist_config["request_body"]
        request_body["name"] = name
        request_body["description"] = description
        endpoint = self.create_playlist_config["endpoint"]
        endpoint = endpoint.replace("{user_id}",self.user_profile["id"])

        response = call_api(
            method=self.create_playlist_config["method"],
            headers=request_header,
            json=request_body,
            url=endpoint
        )

        if "error" in response:
            print("❌ Error when call API:", response["error"])
            return {}
        else:
            return response.json()

    def __token(self):
        if self.__needs_refresh():
            self.__update_access_token()
        return self.access_token

    def __needs_refresh(self):
        has_access_token = self.access_token is not None
        current_time_window = int(time.time()) + self.TOKEN_BUFFER
        has_valid_token = current_time_window < self.expires_at
        return not (has_access_token and has_valid_token)

    def __store_access_token(self, data):
        self.access_token = data.get('access_token', None)
        self.refresh_token = data.get('refresh_token', None)
        current_time = int(time.time())
        self.expires_at = current_time + data.get('expires_in', 0)

        # Fetches a new access token and stores it and its expiry date

    def __authorization_encode_base64(self):
        raw = f"{self.client_id}:{self.client_secret}"
        return f"Basic {base64.b64encode(raw.encode()).decode()}"

    def __fetch_access_token(self):
        request_header = self.token_config["request_header"]
        request_header["Authorization"] = self.__authorization_encode_base64()
        request_body = self.token_config["request_body"]
        request_body["code"] = self.code

        response = call_api(
            method=self.token_config["method"],
            headers=request_header,
            data= request_body,
            url=self.token_config["endpoint"]
        )

        if "error" in response:
            print("❌ Error when call API:", response["error"])
            return {}
        else:
            return response

    def __refresh_access_token(self):
        request_header = self.refresh_token_config["request_header"]
        request_header["Authorization"] = self.__authorization_encode_base64()
        request_body = self.refresh_token_config["request_body"]
        request_body["refresh_token"] = self.refresh_token
        request_body["client_id"] = self.client_id

        response = call_api(
            method=self.token_config["method"],
            headers=request_header,
            data= request_body,
            url=self.token_config["endpoint"]
        )

        if "error" in response:
            print("❌ Error when call API:", response["error"])
            return {}
        else:
           return response

    def __fetch_user_profile(self):
        request_header = self.get_current_user_profile["request_header"]
        request_header["Authorization"] = self.bearer_token()

        response = call_api(
            method=self.get_current_user_profile["method"],
            headers=request_header,
            url=self.get_current_user_profile["endpoint"]
        )

        if "error" in response:
            print("❌ Error when call API:", response["error"])
            return {}
        else:
            return response

    def __update_access_token(self):
        response = self.__refresh_access_token().json()
        self.__store_access_token(response)

    def generate_random_string(self,length: int) -> str:
        return secrets.token_hex(60)[:length]