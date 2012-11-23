import os

here = os.path.abspath(os.path.dirname(__file__))

MEDIA_FOLDER = os.path.join(here, "static", "Media/")
TEMPLATE_FOLDER = os.path.join(here, "templates")
STATIC_FOLDER = os.path.join(here, "static")
DB_NAME = os.path.join(here, "playlists.db")