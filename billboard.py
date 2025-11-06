from bs4 import BeautifulSoup
import requests

class Billboard:
    URL = "https://www.billboard.com/charts/hot-100/"
    HEADER = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
    }

    def __init__(self, date):
        self.date = date
        self.data = []

    def get_uris(self):
        return [track["spotify_uri"] for track in self.data if track["spotify_uri"]]

    def date_format(self):
        return self.date.strftime("%Y-%m-%d")

    def get_data(self):
        data_url = f"{self.URL}/{self.date_format()}"
        print(data_url)
        response = requests.get(url=data_url, headers=self.HEADER)
        web_content = BeautifulSoup(response.text, 'html.parser')
        billboard_data = web_content.select("div.o-chart-results-list-row-container")


        for i in range(0,10):
            ordinal_number = billboard_data[i].select_one("li span.c-label").get_text(strip=True)
            music_title = billboard_data[i].select_one("h3.c-title").get_text(strip=True)
            artist = billboard_data[i].select_one("li.o-chart-results-list__item span.a-no-trucate").get_text(strip=True)
            self.data.append(
                {
                    "ordinal_number": ordinal_number,
                    "title": music_title,
                    "artist": artist,
                    "spotify_uri": ""
                }
            )




