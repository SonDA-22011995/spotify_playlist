from model import config

class Playlist:
    def __init__(self, name: str, playlist_id: str, description: str, url: str):
        self.name = name
        self.id = playlist_id
        self.description = description
        self.add_items_playlist = config["spotify_api"]["add_items_playlist"]
        self.url = url