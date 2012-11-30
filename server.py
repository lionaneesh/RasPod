import urllib2
import os # for file and path related functions
from sys import argv
import signal # for handling/catching SIGINT
import sqlite3 as lite
import json # playlist handling
from time import time

# -- Tornado modules (for HTTP request handling)

import tornado.ioloop
import tornado.web
import tornado.template

# -- Local Modules

import vlc # libVLC
import settings

def handle_SIGINT(signal, frame) :
    print("Ctrl + C, Detected!")
    print("Exiting Gracefully.")
    rasPod.close()
    exit(0)

def db_connect():
    con = lite.connect(settings.DB_NAME)
    c   = con.cursor()
    return c, con

def db_create(c, con):
    # check if the table exists
    try:
        c.execute("SELECT * FROM playlists")
    except lite.OperationalError:
        print "Creating Table playlists"
        c.execute("CREATE TABLE playlists(name text, song_list text)")
        con.commit()

def add_playlist(name, song_list, c, con):
    c.execute("INSERT INTO playlists(name, song_list) values(?, ?)", (name, json.dumps(song_list)))
    con.commit()

def db_get_playlists(c):
    c.execute("SELECT * FROM playlists")
    playlists = {}

    while 1:
        try:
            data = list(c.fetchone())
        except TypeError:
            break
        playlists[data[0]] = json.loads(data[1])

    return playlists

class RasPod():
    def __init__(self, playlist):
        self.Instance    = vlc.Instance()
        self.media_files = []
        self.MediaPlayer = 0
        self.ListMediaPlayer = 0
        self.playlist    = playlist
        self.MediaPlayer_list = self.Instance.media_list_new()

        if self.MediaPlayer_list == False:
            print "Failed to get media_list object"
            self.close()
            exit(-1)

        self._build_up_playlist()
        self._setup_media_players()

    def _setup_media_players(self):
        self.MediaPlayer     = self.Instance.media_player_new()
        self.ListMediaPlayer = self.Instance.media_list_player_new()
        if self.MediaPlayer and self.ListMediaPlayer:
            self.ListMediaPlayer.set_media_list(self.MediaPlayer_list)
            self.ListMediaPlayer.set_media_player(self.MediaPlayer)
        else:
            print "Failed to load media_player or media_list_player object"
            self.close()
            exit(-1)

    def is_seekable(self):
        return self.MediaPlayer.is_seekable()

    #-- Time/Length/Seek Related -- All functions return time in seconds

    def get_time(self):
        return int(self.MediaPlayer.get_time() / 1000)

    def get_length(self):
        return int(self.MediaPlayer.get_length() / 1000)

    def set_time(self, pos):
        self.MediaPlayer.set_time(pos * 1000);

    def _is_open(self):
        return self.MediaPlayer != 0

    #-- Data Validation --

    def _valid_index(self, id):
        return (id >= 0 and id < len(self.media_files))

    def _is_valid_volume(self, volume):
        return (volume <= 100 and volume >= 0)

    #-- Playlist Related Methods ---

    def get_current_playlist(self):
        return self.media_files

    def get_current_playlist_name(self):
        return self.playlist

    def _build_up_playlist(self):
        self.media_files = playlists[self.playlist]
        vlc.libvlc_media_list_lock(self.MediaPlayer_list)
        for i in range(0, len(self.media_files)):
            filename = unicode(settings.MEDIA_FOLDER, 'utf-8') + unicode(self.media_files[i], 'utf-8')
            if os.access(filename, os.R_OK):
                self.MediaPlayer_list.insert_media(self.Instance.media_new(filename.encode('utf-8', 'ignore')), i)
            else:
                print("%s is not readable.")
        vlc.libvlc_media_list_unlock(self.MediaPlayer_list)

    def load_new_playlist(self, new_playlist):
        self.stop()
        self.close()
        self.__init__(new_playlist)

    #-- Track/Track-id related methods --

    def _get_current_item_id(self):
        if not self._is_open():
            print 'Not Open!'
            return -1

        else:
            self.current_media = vlc.libvlc_media_player_get_media(self.MediaPlayer)

            if not self.current_media:
                return -1

            return self.MediaPlayer_list.index_of_item(self.current_media)

    def play_track_at_id(self, id):
        if self._valid_index(id):
            self.ListMediaPlayer.play_item_at_index(id)

    def get_current_item(self):
        if not self.ListMediaPlayer.is_playing():
            return 'None'
        self.item_id = self._get_current_item_id()
        if not self._valid_index(self.item_id):
            return 'None'
        return self.media_files[self.item_id]

    #-- Actions

    def stop(self):
        """Stop player
        """
        self.ListMediaPlayer.stop()
        self.ListMediaPlayer.pause()

    def play_pause(self):
        """Play/Pause the MediaPlayer
        """
        if self.ListMediaPlayer.is_playing():
            self.ListMediaPlayer.pause()
            self.isPaused = True
        else:
            self.ListMediaPlayer.play()
            self.isPaused = False

    def prev(self):
        self.ListMediaPlayer.previous()

    def next(self):
        self.ListMediaPlayer.next()

    def get_volume(self):
        return self.MediaPlayer.audio_get_volume()

    def set_volume(self, volume):
        return self.MediaPlayer.audio_set_volume(volume)

    def vol_up(self):
        current_vol = self.get_volume()
        if self._is_valid_volume(current_vol) and current_vol < 100:
            self.set_volume(current_vol + 1)

    def vol_down(self):
        current_vol = self.get_volume()
        if self._is_valid_volume(current_vol) and current_vol > 0:
            self.set_volume(current_vol - 1)

    def mute(self):
        self.MediaPlayer.audio_set_volume(0)

    #-- Cleanup --

    def close(self):
        if self.ListMediaPlayer:
            self.ListMediaPlayer.release()
            self.MediaPlayer = 0

        if self.MediaPlayer_list:
            self.MediaPlayer_list.release()
            self.MediaPlayer_list = 0

        if self.MediaPlayer:
            self.MediaPlayer.release()
            self.MediaPlayer = 0

        self.Instance = 0

class Media():
    def __init__(self):
        self.media_f = self.find_media_files()

    def get_media_files(self):
        return self.media_f

    def find_media_files(self):
        """Finds the files with extension .mp3 from the media folder
        defined in settings.py"""
        media_files = []
        for dirpath, dirs, files in os.walk(settings.MEDIA_FOLDER, followlinks=True):
            for filename in files:
                if os.path.splitext(filename)[-1] == ".mp3":
                    media_files.append(
                        self._clip_media(os.path.join(dirpath, filename)))
        return media_files

    def _clip_media(self, filename):
        return filename[len(settings.MEDIA_FOLDER):]

class PlaylistCreator(tornado.web.RequestHandler):
    def initialize(self):
        self.loader = tornado.template.Loader(settings.TEMPLATE_FOLDER)

    def get(self):
        media_files = media.get_media_files()
        self.write(
            self.loader.load("playlist_creator.html").generate(error_message='', media_files=media_files))

    def post(self):
            params = self.request.body.split('&')
            ids = []
            song_list = []
            media_files = media.get_media_files()
            for i in params:
                name = 'playlist%.4f' % time()
                key, value = i.split('=')
                if key.isdigit():
                    ids.append(key)
                elif key == 'playlist_name':
                    if len(value.strip()) > 0:
                        name = value.strip()
                        name = urllib2.unquote(name).decode("utf8").strip()
                        name = name.replace("+", " ")

            if name in playlists:
                self.write(self.loader.load("playlist_creator.html").generate(error_message="The playlist with the specified name already exists, Please chose a different name.", media_files=media_files))
                return
            if len(ids) < 2:
                    self.write(self.loader.load("playlist_creator.html").generate(error_message="Please chose atleast 2 songs to make a playlist.", media_files=media_files))
                    return
            for a in ids:
                if a.isdigit() and int(a) < len(media_files) and int(a) >= 0:
                    song_list.append(media_files[int(a)])

            add_playlist(name, song_list, c, con)
            playlists[name] = song_list
            self.redirect('/')

class SeekingHandler(tornado.web.RequestHandler):
    def initialize(self):
        self.loader = tornado.template.Loader(settings.TEMPLATE_FOLDER)

    def get(self, id):
        rasPod.play_track_at_id(int(id))

class SetSeekHandler(tornado.web.RequestHandler):

    def get(self, pos):
        rasPod.set_time(int(pos))

class SetVolumeHandler(tornado.web.RequestHandler):

    def get(self, volume):
        rasPod.set_volume(int(volume))

class PlaylistsEditor(tornado.web.RequestHandler):
    def delete_playlist(self, playlist):
        log   = "Playlist success fully, deteled."
        print "Trying to delete the %s playlist." % (playlist)

        try:
            c.execute("DELETE FROM playlists WHERE name=?", (playlist,))
            con.commit()

        except lite.OperationalError:
            log = "Failed to detele the playlist."

        else:
            playlists.pop(playlist)

        print log

        self.redirect("/")


    def get(self, playlist, action):
        actions = {
            'delete' : self.delete_playlist
        }

        if action in actions:
            actions[action](playlist)

class PlayerHandler(tornado.web.RequestHandler):

    def get(self, action):
        actions = {
            'play_pause' : rasPod.play_pause,
            'stop'       : rasPod.stop,
            'get_current_track': rasPod.get_current_item,
            'next'       : rasPod.next,
            'prev'       : rasPod.prev,
            'mute'       : rasPod.mute,
            'get_vol'    : rasPod.get_volume,
            'is_seekable': rasPod.is_seekable,
            'get_time'    :  rasPod.get_time,
            'get_length'  :  rasPod.get_length
        }
        out = None
        if action in actions:
            out = actions[action]()
        if out != None:
            self.write(str(out))

class MainHandler(tornado.web.RequestHandler):

    def initialize(self):
        self.loader = tornado.template.Loader(settings.TEMPLATE_FOLDER)

    def get(self, playlist=None):
        if playlist != None and playlist in playlists:
            if rasPod.get_current_playlist_name() != playlist:
                print "Loading %s" % playlist
                rasPod.load_new_playlist(playlist)

        self.write(self.loader.load("index.html").generate(playl=rasPod.get_current_playlist_name(), media_files=rasPod.get_current_playlist(), playlists=playlists))

application = tornado.web.Application(
[
    (r"/player/(.*)", PlayerHandler),
    (r"/jump_to/(.*)", SeekingHandler),
    (r"/create_new_playlist", PlaylistCreator),
    (r"/set_volume/([0-9]{1,3})", SetVolumeHandler),
    (r"/set_seek/([0-9]+)", SetSeekHandler),
    (r"/playlists/(.+)/(.+)", PlaylistsEditor),
    (r"/(.*)", MainHandler)
], static_path=settings.STATIC_FOLDER)

# Main.
if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_SIGINT)
    port = 8888
    playlists = {}

    if len(argv) == 2 and argv[1].isdigit():
        port = int(argv[1])

    application.listen(port)

    # ---- Database Handling -----

    c, con = db_connect()
    db_create(c, con)

    playlists = db_get_playlists(c)

    # -----

    media = Media()
    playlists['all'] = media.get_media_files()
    rasPod = RasPod('all')
    print "RasPod server is running on port %d" % port
    tornado.ioloop.IOLoop.instance().start()