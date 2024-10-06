from flask import Blueprint, request, render_template, jsonify, redirect, url_for
from app.config import Config
from app.services.connection_services import get_spotify_instance, get_db_instance
from app.models.PlaylistManager import PlaylistManager  # Import your PlaylistManager class
import os
import spotipy  # You need to import spotipy for handling its exceptions
import mysql.connector  # Import the mysql.connector module


routes = Blueprint('routes', __name__)


# Set up Spotify API
sp = get_spotify_instance()
db = get_db_instance()

#Limit of musics of the playlist
limit = 10

manager = PlaylistManager(sp, db, Config.PLAYLIST_ID, limit)





@routes.route('/', methods=['GET'])
def search():
    return render_template('search.html')

@routes.route('/search', methods=['GET'])
def ajax_search():
    query = request.args.get('query')
    results = sp.search(q=query, type='track', limit=3)
    tracks = [{
        'id': track['id'],
        'name': track['name'],
        'artist': track['artists'][0]['name'],
        'uri': track['uri'],
        'album_cover': track['album']['images'][0]['url']
    } for track in results['tracks']['items']]
    return jsonify(tracks)

@routes.route('/add/<track_id>')
def add_to_playlist(track_id):

    try:
        # Add track to database and playlist if it doesn't exist or increment votes
        manager.add_track_general(track_id)
    #    take care of when calling this fucnction dont need to be everytime
        manager.manage_playlist()
        
        return redirect(url_for('routes.search'))
    
    except spotipy.exceptions.SpotifyException as e:
        # Handle Spotify API errors
        print(f"Spotify API error occurred: {e}")
        return "An error occurred while interacting with Spotify.", 500
    
    except mysql.connector.Error as e:
        # Handle MySQL database errors
        print(f"Database error occurred: {e}")
        return "An error occurred while interacting with the database.", 500
    
    except Exception as e:
        # Handle any other errors
        print(f"An unexpected error occurred: {e}")
        return "An unexpected error occurred.", 500
    
    

