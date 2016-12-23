import sys
import youtube_dl
import os
from requests import get
from requests.exceptions import ConnectionError
from bs4 import BeautifulSoup
import urllib
from tqdm import tqdm
import string
import logging
import begin
from pushbullet import Pushbullet
logger = logging.getLogger()


def rmv_chr(text):
    new_text = ''
    if '-' in text:
        text = text.split('-')[0]
    for letter in text:
        if letter not in (string.ascii_letters or '0123456789'):
            new_text += ' '
        else:
            new_text+= letter
    new_text = " ".join(new_text.split())
    return new_text


def scan_lib():
    music_lib = []
    for root, dir, files in os.walk('/home/drrid/Music/Spotify-Music'):
        for file in files:
            if file.endswith('.ogg'):
                music_lib.append(file[:-4])
    return music_lib


def playlist_generator(genre, song_nbr):
    try:
        #spotify playlists
        urls = ['https://www.youtube.com/results?search_query=',
                'https://open.spotify.com/user/spotify/playlist/16BpjqQV1Ey0HeDueNDSYz',
                'https://open.spotify.com/user/spotify/playlist/63dDpdoVHvx5RkK87g4LKk',
                'https://open.spotify.com/user/spotify/playlist/5FJXhjdILmRA2z5bvz4nzf',
                'https://open.spotify.com/user/spotify/playlist/6PObHFkv7TAGAv5dfxKMl0',
                'https://open.spotify.com/user/spotify/playlist/3nC6qoKzquBYAbhn3e53EA',
                'https://open.spotify.com/user/spotify/playlist/7CQunpJEHecknIyABfS8pP']

        #soup for spotify playlist
        spotify_soup = BeautifulSoup(get(urls[genre]).content, "html.parser")

        #get 28 first songs ... and remove bad characters from them
        titles = [rmv_chr(title.text) for title in spotify_soup.find_all("span", class_="track-name")[0:25]]
        authors = [rmv_chr(author.a.text) for author in spotify_soup.find_all("span", class_="artists-albums")[0:25]]
        songs = [titles[n] + ' ' + authors[n] for n in range(len(titles))]

        #quote songs
        q_songs = [urllib.quote(song) for song in songs]

        #generating youtube urls
        youtube_urls = []
        music_lib = scan_lib()
        n_songs = []
        for i, q_song in enumerate(tqdm(q_songs)):
            if songs[i] not in music_lib:
                youtube_soup = BeautifulSoup(get(urls[0] + q_song).content, "html.parser")
                youtube_url = youtube_soup.find('h3', class_='yt-lockup-title ')
                youtube_urls.append('http://www.youtube.com' + youtube_url.a.get('href'))
                n_songs.append(songs[i])
            if len(youtube_urls) == song_nbr:
                break

        #return list with song names and youtube links.
        return n_songs, youtube_urls

    except ConnectionError:
        logger.exception('Connection Error .. please verify your connection')


def download(song, url, genre):
    #folder selection
    if genre == 1:
        os.chdir('/home/drrid/Music/Spotify-Music/Afternoon Acoustic')
    elif genre == 2:
        os.chdir('/home/drrid/Music/Spotify-Music/Peaceful Piano')
    elif genre == 3:
        os.chdir('/home/drrid/Music/Spotify-Music/Top Hits')
    elif genre == 4:
        os.chdir('/home/drrid/Music/Spotify-Music/Totally Alternative')
    elif genre == 5:
        os.chdir('/home/drrid/Music/Spotify-Music/Epic Wall of Sound')
    elif genre == 6:
        os.chdir('/home/drrid/Music/Spotify-Music/Rainy Day')

    #download options
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': song+'.%(ext)s',
        'noplaylist': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredquality': '192',
            'preferredcodec': 'vorbis',}]}

    #lanch download
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


@begin.start(auto_convert=True)
def main(genre=1,number_of_songs=1):
    """
This script downloads spotify playlists through youtube,
Here are the playlists for now...

    \n1- Afternoon Acoustic
    \n2- Peaceful Piano
    \n3- Today's Top Hits
    \n4- Totally Alternative
    \n5- Epic Wall of Sound
    \n6- Rainy Day            """

    logging.basicConfig(level=logging.WARNING)
    pb = Pushbullet('o.6KLzr08hvmhXgFa3fgdFtP21yzXWreoL')

    songs, urls = playlist_generator(genre, number_of_songs)
    tracks = ''
    for song in songs:
        tracks += song + '\n'
    for i, song in enumerate(songs):
        download(song, urls[i], genre)
    push = pb.push_note('%s Songs Available' % len(songs), tracks)


