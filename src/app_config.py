import os

AUTHORITY = os.getenv("AUTHORITY")

CLIENT_ID = os.getenv("CLIENT_ID")

CLIENT_SECRET = os.getenv("CLIENT_SECRET")

REDIRECT_PATH = "/getAToken"  # Used for forming an absolute URL to redirect URI.

SCOPE = ["User.Read", "User.ReadBasic.All", "User.ReadWrite"]

# Tells the Flask-session extension to store sessions in the filesystem
SESSION_TYPE = "filesystem"

