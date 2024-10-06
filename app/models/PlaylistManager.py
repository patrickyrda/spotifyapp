# OPTIMIZAR PARA USAR MENOS O COMMIT TROCAR SISTEMA EM VEZ DE NUMERO DE MUSICAS POR NUMERO DE VOTOS 
class PlaylistManager:
    def __init__(self, spotify_instace, db_instance, playlist_id, playlist_limit):
        """
        Initialize the PlaylistManager instance with Spotify instance, database connection, playlist id and limit playlist limit

        Parameters
        ----------
        spotify_instace : Spotify
            Spotify instance
        db_instance : Database
            Database connection
        playlist_id : str
            Playlist id
        playlist_size : int
            Limit playlist size
        ----------
        """
        self.spotify = spotify_instace
        self.db = db_instance
        self.playlist_id = playlist_id
        self.playlist_limit = playlist_limit
        self._cursor = self.db.cursor()
        # IMPLEMENT THRESHOULDS STRATEGY
    def get_playlist_tracks(self):
        """
        Get list of tracks in the spotify playlist
        
        returns
        ----------
        List containing track uris from musics in the playlist
        ----------     
        """
        print("ERROR HERE")
        results = self.spotify.playlist_items(self.playlist_id)
        print("PASSED ERROR")
        tracks = []
        for item in results['items']:
            track = item['track']
            tracks.append(track['uri'])
        return tracks
        
    def get_playlist_size(self):
        """
        Get playlist size
        
        returns
        ----------
        Playlist size
        ----------
        """
        tracks = self.get_playlist_tracks()
        print(tracks)
        return len(tracks)


    def get_count_tracks_db(self):
        """
        Get count of tracks in the database
        
        returns
        ----------
        Count of tracks in the database
        ----------
        """
        self._cursor.execute("SELECT COUNT(*) FROM tracks")
        count = self._cursor.fetchone()[0]
        return count

   
    # Apply threesholds strategy later
    def get_favorite_tracks(self):
        """
        Get list of track uris with most votes in the database

        returns
        ----------
        List containing track uris with most votes
        ----------
        """
        self._cursor.execute("SELECT count(*) FROM tracks WHERE votos > (SELECT MIN(votos) FROM tracks)")
        number = self._cursor.fetchone()[0] 
        if number == 0:
            # Handle case when all tracks have same amount of votes
            return []
        else:
            self._cursor.execute("SELECT * FROM tracks WHERE votos > (SELECT MIN(votos) FROM tracks) ORDER BY votos DESC LIMIT %s", (self.playlist_limit,))
            favorite_tracks = self._cursor.fetchall()
            return [track[0] for track in favorite_tracks]
    def get_db_genres_proportions_list(self):
        """
        Get a descending list with the name of the genres and their respective proportions in the database

        returns
        ----------
        Descending list with the name of the genres and their respective proportions in the database in form of tuples (genre, proportion)
        ----------
        """
        self._cursor.execute("SELECT genre, COUNT(*) * 100.0 / (SELECT COUNT(*) FROM tracks) AS proportion FROM tracks GROUP BY genre ORDER BY proportion DESC")
        result = self._cursor.fetchall()
        print(result)
        return result
    #this one might be useless
    def get_playlist_spaces_left(self):
        """
        Get playlist spaces left

        returns
        ----------
        Number of tracks that can still be added to playlist
        ----------
        """
        return self.playlist_limit - self.get_playlist_size()

    def add_track_to_playlist(self, track_uri):
        """
        Add track to playlist

        Parameters
        ----------
        track_uri : str
            uri of the track to add
        ----------
        """
        self.spotify.playlist_add_items(self.playlist_id, [track_uri])

    def add_track_to_db(self, id, name, artist, genre):
        """
        Add track to database

        Parameters
        ----------
        id : str
            id of the track
        name : str
            name of the track
        artist : str
            artist of the track
        genre : str
            genre of the track
        ----------
        """
        self._cursor.execute("INSERT INTO tracks (id, name, artist, votos, genre, in_playlist) VALUES (%s, %s, %s, 1, %s, 0)", (id, name, artist, genre))
        self.db.commit()
    def is_inside_playlist(self, track_uri):
        """
        Check if track is inside playlist

        Parameters
        ----------
        track_uri : str
            uri of the track to check
        
        Returns
        true if track is inside playlist false otherwise
        ----------
        """
        tracks = self.get_playlist_tracks()
        return track_uri in tracks
    
    def is_inside_db(self, track_uri):
        """
        Check if track is inside database

        Parameters
        ----------
        track_uri : str
            uri of the track to check
            
        Returns
        true if track is inside database false otherwise
        ----------
        """
        self._cursor.execute("SELECT COUNT(*) FROM tracks WHERE id = %s", (track_uri,))
        count = self._cursor.fetchone()[0]  
        return count > 0 
        
    def add_track_general(self, track_uri):
        """
        Add track to playlist or database depending on if its already in, in this case increment number of votes

        Parameters
        ----------
        track_uri : str
        uri of the track to add
        ----------       
        """
        track_info = self.spotify.track(track_uri)
 
        if self.is_inside_db(track_uri):
            self._cursor.execute("UPDATE tracks SET votos = votos + 1 WHERE id = %s", (track_uri,))
        else: 
            name = track_info['name']
            artist = track_info['artists'][0]['name']
            artist_id = track_info['artists'][0]['id']
            artist_info = self.spotify.artist(artist_id)
            genre = artist_info['genres'][0] if artist_info.get('genres') else 'Unknown'
            # Add track to the database and the Spotify playlist
            self.add_track_to_db(track_uri, name, artist, genre)  
            self._cursor.execute("UPDATE tracks SET in_playlist = 1 WHERE id = %s", (track_uri,))
            if not self.is_inside_playlist(track_uri):    
                self.add_track_to_playlist(track_uri)
        
        self.db.commit()
        return "Track added or updated successfully."
    
    def remove_track_general(self, track_uri):
        """
        Remove track from playlist and database

        Parameters
        ----------  
        track_uri : str
            uri of the track to remove
        ----------
        """
        self._cursor.execute("UPDATE tracks SET in_playlist = 0 WHERE id = %s", (track_uri,))
        self.spotify.playlist_remove_all_occurrences_of_items(self.playlist_id, [track_uri])
        self.db.commit()
        
    # Possible improve by also sorting by artist
    def gender_sort(self):
        
        genre_proportions = self.get_db_genres_proportions_list()
        big_genders = sum(1 for genre, proportion in genre_proportions if proportion >= 0.1)
        favorite_tracks = self.get_favorite_tracks()
        size_to_sort = self.playlist_limit - len(favorite_tracks)
        tracks_to_add = []

        index = 0
        limit = size_to_sort
        
        # Add tracks from big genders
        for i in range(big_genders):
            genre, proportion = genre_proportions[i]
            amount_to_add = min(int(round(proportion * size_to_sort)), limit)
            
            self._cursor.execute("SELECT id FROM tracks WHERE genre = %s ORDER BY votos DESC LIMIT %s", 
                                (genre, amount_to_add))
            tracks = self._cursor.fetchall()
            
            for track in tracks:
                if track[0] not in tracks_to_add and track[0] not in favorite_tracks:
                    tracks_to_add.append(track[0])
                    
            limit = size_to_sort - len(tracks_to_add)  # Update limit after adding tracks
        
        # If there's still space, fill with remaining tracks regardless of genre
        while limit > 0 and index < len(genre_proportions):
            genre, _ = genre_proportions[index]
            
            # MAYBE ADD ASC INSTEAD OF DESC
            self._cursor.execute("SELECT id FROM tracks WHERE genre = %s ORDER BY votos DESC LIMIT %s", 
                                (genre, limit))
            tracks = self._cursor.fetchall()
            
            for track in tracks:
                if track[0] not in tracks_to_add:
                    tracks_to_add.append(track[0])
            
            limit = size_to_sort - len(tracks_to_add)  # Recalculate limit after each addition
            index += 1
        
        # Add favorite tracks at the end, if not already in the list
        for track in favorite_tracks:
            if track not in tracks_to_add:
                tracks_to_add.append(track)
        print("TRACKS TO ADD INSIDE OF GENDER SORT")    
        print(tracks_to_add)
        return tracks_to_add

                

        
    # Redundancy calling favorite_tracks in both methods ^ and down

    def manage_playlist(self):
        """
        ------------
        Manage the Spotify playlist by ensuring it does not exceed the defined limit.
        Adds the top-voted tracks and fills remaining slots based on genre proportions.
        
        """
        
    
        total_tracks_in_db = self.get_count_tracks_db()
        
        # Case when playlist has not yet reached its limit
        if (total_tracks_in_db < self.playlist_limit):
            return "Playlist not full"
        
        current_tracks = self.get_playlist_tracks()
        tracks_to_add = self.get_favorite_tracks()
        print("Favorite tracks inside of manage_playlist")
        print(tracks_to_add)
        # Case when i have enough favorite tracks to fill the playlist 
        if (len(tracks_to_add) == self.playlist_limit):
            for current in current_tracks:
                if current not in tracks_to_add:
                    self.remove_track_general(current)
                else:
                    tracks_to_add.remove(current)   
            for track in tracks_to_add:
                self.add_track_general(track)
            return "Playlist filled with favorite tracks"

        # Case when i don't have enough favorite tracks to fill the playlist, mix input of favorites plus gender_sort
        else:
            print("Case when do not have enough favorites")
            new_tracks = self.gender_sort()
            for current in current_tracks:
                if current not in new_tracks:
                    self.remove_track_general(current)
                else:
                    new_tracks.remove(current)
            for track in new_tracks:
                self.add_track_general(track)
            return "Playlist filled with favorite if there are and gender sorted"

        

    
            

        
        