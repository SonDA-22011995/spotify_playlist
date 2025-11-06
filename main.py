import pyinputplus as pyip
from utils import save_data
from model import playlists
from billboard import Billboard
from playlist import Playlist
from typing import Optional
from spotify import Spotify

playlist: Optional[Playlist] = None
spotify = Spotify(playlists)


def login():
    spotify.request_user_authorization()

    callback_url = pyip.inputURL(prompt="""
Enter the URL you were redirected to:
""")
    spotify.set_code(callback_url=callback_url)
    spotify.set_token()
    spotify.set_user_profile()

def travel_to_playlist():
    global playlist
    date = pyip.inputDate(
        prompt="""
Which year do you want to travel to? Type the date in the format YYYY-MM-DD
""",
        formats=["%Y-%m-%d"]
    )

    name = date.strftime("%Y-%m-%d")
    description = f"Playlist {name} on spotify"
    if spotify.is_exists_playlist(name):
        playlist = spotify.get_playlist(name=name)
    else:
        response = spotify.create_playlist(name=name, description=description)
        playlist = Playlist(
            name=name,playlist_id=response["id"],
            description=description,
            url= response["external_urls"]["spotify"]
        )
        spotify.append_playlist(
            [
                response["id"],
                name,
                description,
                response["external_urls"]["spotify"]
            ]
        )
        billboard = Billboard(date)
        billboard.get_data()
        for track in billboard.data:
            response = spotify.search_for_item(title=track["title"], artist=track["artist"])
            items = response.get("tracks", {}).get("items", [])
            if not items:
                track["spotify_uri"] = None
            else:
                track["spotify_uri"] = items[0]["uri"]

        uris = billboard.get_uris()
        playlist_id = playlist.id
        spotify.add_item_to_playlist(uris=uris, playlist_id=playlist_id)

    print(f"Please visit the link {playlist.url} to listen to music")


is_run = True

while is_run:
    if not spotify.access_token:
        choice = pyip.inputChoice(
            prompt="""
    Please choose one option below:
    1: Login
    0: Exist
    """,
            choices= ["0","1"],
        )
    else:
        choice = "1"

    match choice:
        case "0":
            is_run = False
            save_data(file_path="./data/playlist.csv", csv_data=spotify.playlists)
            print("Good bye see ya")
        case "1":
            login()

            if getattr(spotify,"user_profile",""):
                print(f"""
Login successfully user {spotify.get_user_profile_name()}
""")
                travel_to_playlist()



