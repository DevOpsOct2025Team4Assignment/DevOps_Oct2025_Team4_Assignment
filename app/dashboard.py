from flask import (
    Blueprint,
    render_template,
)

from app.auth import auth_required
from app.db import query_db

bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@bp.route("/")
@auth_required()
def index(user_id: int):
    files = query_db("SELECT * FROM files WHERE user_id = ?", (user_id,))
    return render_template("user_dashboard.html", files=files)
