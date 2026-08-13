import os
import sys

from flask import Flask

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from Server.dashboard.dashboard_app import welcometobpbrother
from Server.admin.game_server import game_server

app = Flask(__name__)
app.register_blueprint(welcometobpbrother)
app.register_blueprint(game_server)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)