from flask import Flask, request, render_template, jsonify, redirect, url_for
from spotipy.oauth2 import SpotifyOAuth
import spotipy
import mysql.connector
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Set up Spotify API
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri='http://localhost:3000',
    scope="playlist-modify-public"
))

# Set up MySQL connection
db = mysql.connector.connect(
    host=os.getenv("MYSQL_HOST"),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    database=os.getenv("MYSQL_DATABASE")
)
cursor = db.cursor()

@app.route('/', methods=['GET'])
def search():
    return render_template('search.html')

@app.route('/search', methods=['GET'])
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

@app.route('/add/<track_id>')
def add_to_playlist(track_id):

    try:
        
        # Check how many musics were put in the db 
        
        # Check if the track is already in the database, retreiving the number of votes
        track_info = sp.track(track_id)
        cursor.execute("SELECT votos FROM tracks WHERE id = %s", (track_info['id'],))
        votos = cursor.fetchone() 
        
        

        # Save track info to MySQL
        if votos is None:
            # Add track to Spotify playlist
            print(track_id)
            sp.playlist_add_items(os.getenv("PLAYLIST_ID"), [track_id])
            cursor.execute("INSERT INTO tracks (id, name, artist, votos) VALUES (%s, %s, %s, 1)",
                       (track_info['id'], track_info['name'], track_info['artists'][0]['name']))
            
        else:
            new_votos = votos[0] + 1
            cursor.execute("UPDATE tracks SET votos = %s WHERE id = %s",
                           (new_votos, track_info['id']))
            
        db.commit()
        return redirect(url_for('search'))
    
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
    
    

if __name__ == '__main__':
    app.run(debug=True)
