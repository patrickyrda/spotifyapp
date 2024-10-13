
from app.services.playlist_instance import manager
import threading

def manage_playlist_job():
    
    print("MANAGING PLAYLIST")
    threading.Thread(target=manager.manage_playlist).start()

  
