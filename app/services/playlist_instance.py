from .connection_services import get_db_instance, get_spotify_instance
from app.models.PlaylistManager import PlaylistManager
from app.config import Config


sp = get_spotify_instance()
db = get_db_instance()

limit = 10

manager = PlaylistManager(sp, db, Config.PLAYLIST_ID, limit)
