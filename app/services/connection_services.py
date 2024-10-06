# spotify_service.py

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import mysql.connector
from app.config import Config

def get_spotify_instance():
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=Config.SPOTIPY_CLIENT_ID,
        client_secret=Config.SPOTIPY_CLIENT_SECRET,
        redirect_uri=Config.SPOTIPY_REDIRECT_URI,
        scope="playlist-modify-public playlist-modify-private"
    ))
    return sp

def get_db_instance():
    db = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DATABASE
    )
    return db
