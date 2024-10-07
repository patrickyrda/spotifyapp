# OPTIMIZAR PARA USAR MENOS O COMMIT TROCAR SISTEMA EM VEZ DE NUMERO DE MUSICAS POR NUMERO DE VOTOS 
import math
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
            # Here i might need to select only the id directly, dunnow
            self._cursor.execute("SELECT * FROM tracks WHERE votos > (SELECT MIN(votos) FROM tracks) ORDER BY votos DESC LIMIT %s", (self.playlist_limit,))
            favorite_tracks = self._cursor.fetchall()
            return [track[0] for track in favorite_tracks]
    def get_db_genres_proportions_list(self):
        """
        Get a descending list with the name of the genres and their respective vote proportions in the database

        returns
        ----------
        Descending list with the name of the genres and their respective proportions in the database in form of tuples (genre, proportion)
        ----------
        """
        self._cursor.execute("SELECT genre, SUM(votos) / (SELECT SUM(votos) FROM tracks) AS proportion FROM tracks GROUP BY genre ORDER BY proportion DESC")
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
        self._cursor.execute("UPDATE tracks SET in_playlist = 1 WHERE id = %s", (track_uri,))
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
            if not self.is_inside_playlist(track_uri):    
                self.add_track_to_playlist(track_uri)
        
        self.db.commit()
        return "Track added or updated successfully."
    
    def remove_track_general(self, track_uri):
        """
        Remove track from playlist and update its status in the database

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
        """
        Tool to sort the playlist, selecting favorite tracks and when needed selecting tracks to fill the playlist according to their genders

        Returns
        ---------
        Set containing track's uris to be added in the playlist
        ---------
        """
        favorite_tracks = self.get_favorite_tracks()
        print("FAVORITE TRACKS ARE: ")
        print(favorite_tracks)
        tracks_to_add = set()

        # Add favorite tracks to the set
        tracks_to_add.update(favorite_tracks)
        print("First update of tracks_to_add")
        print(tracks_to_add)
        
        size_to_sort = self.playlist_limit - len(tracks_to_add)
        # case when there isnt enough favorite tracks to fill the playlist
        if size_to_sort > 0:
            gender_info = self.get_db_genres_proportions_list()
            print("Gender_info")
            print(gender_info)
            big_genders = sum(1 for genre, proportion in gender_info if proportion >= 0.1)
            print("There are "+str(big_genders)+" big genders")

            # avoid fetching favorites from the database as they were already added 
            if tracks_to_add:
                not_in_clause = " AND id NOT IN (" + ', '.join(['%s'] * len(tracks_to_add)) + ")"
                print("not_in_clause was prepared and is "+not_in_clause)
            else: 
                not_in_clause = ""
                print("not prepared")
            print("Size to sort is "+str(size_to_sort))
            # insert tracks from big genders
            for i in range(big_genders):
                print(i)
                genre, proportion = gender_info[i]
                amount_to_add = int(math.floor(proportion * size_to_sort))
                print("Going to add "+str(amount_to_add)+"musics from gender "+str(genre))

                query = "SELECT id FROM tracks WHERE genre = %s" + not_in_clause + " ORDER BY votos DESC LIMIT %s"
                args = [genre] + list(favorite_tracks) + [amount_to_add]
                print("Prepared query 1:", query)
                print("With args 1:", args)
                self._cursor.execute(query, tuple(args))
                tracks = self._cursor.fetchall()
                print("tracks to add are: ")
                print(tracks)
                tracks_to_add.update(track[0] for track in tracks)
            
            limit = self.playlist_limit - len(tracks_to_add)
            print("Limit is : "+ str(limit))

            if limit > 0:
                not_in_clause = " id NOT IN (" + ', '.join(['%s'] * len(tracks_to_add)) + ")"
                
                query = f"""
                SELECT t.id, t.genre 
                FROM tracks AS t 
                JOIN (
                SELECT genre, SUM(votos) AS gen_sum 
                FROM tracks 
                WHERE {not_in_clause} 
                GROUP BY genre 
                ORDER BY gen_sum DESC
                ) AS g ON t.genre = g.genre 
                ORDER BY g.gen_sum DESC, g.genre
                LIMIT %s;
                """
                print("not_in_clasue "+not_in_clause)
                args = list(tracks_to_add) + [limit]
                print("args : "+str(args))

                self._cursor.execute(query, tuple(args))
                tracks = self._cursor.fetchall()
                print("tracks_to_add are")
                tracks_to_add.update(track[0] for track in tracks)

        return tracks_to_add
    
    def manage_playlist(self):
        """
        ------------
        Manage the Spotify playlist by ensuring it does not exceed the defined limit.
        Adds the top-voted tracks and fills remaining slots based on genre proportions.
        
        """
        # Case when playlist has not yet reached its limit
        if self.get_count_tracks_db() < self.playlist_limit:
            return "Nothing was done since not enough tracks to fill the playlist"
        

        add_set = self.gender_sort()
        print("INSIDE OF MANAGE_PLAYLIST")
        print("add set")
        print(add_set)
        current_tracks = set(self.get_playlist_tracks())
        print("Current tracks")
        print(current_tracks)
       

        for track in current_tracks - add_set:
            print("removing FINAL")
            print(track)
            self.remove_track_general(track)

        # Add new tracks to the playlist
        for track in add_set - current_tracks:
            print("ADDING FINAL")
            print(track)
            self.add_track_to_playlist(track)
        

        return "Finished managing the playlist"
