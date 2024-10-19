from flask import Blueprint, request, render_template, jsonify, redirect, url_for
import os
import spotipy  
import mysql.connector 
from app.services.playlist_instance import manager, sp
from app.tasks import manage_playlist_job

routes = Blueprint('routes', __name__)



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

@routes.route('/add/<track_id>', methods=['POST'])
def add_to_playlist(track_id):

    try:
        # Add track to database and playlist if it doesn't exist or increment votes
        manager.add_track_general(track_id)
        
        manage_playlist_job()

        return jsonify({'status': 'success'}), 200

    except spotipy.exceptions.SpotifyException as e:
        # Handle Spotify API errors
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
    except mysql.connector.Error as e:
        # Handle MySQL database errors
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
    except Exception as e:
        # Handle any other errors
        return jsonify({'status': 'error', 'message': str(e)}), 500
    

