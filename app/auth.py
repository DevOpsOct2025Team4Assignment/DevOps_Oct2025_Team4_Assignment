from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import (
    Blueprint,
    current_app,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)
from werkzeug.security import check_password_hash

from app.db import query_db

bp = Blueprint("auth", __name__)


@bp.route("/")
def index():
    return redirect(url_for("auth.login"))


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username")
    password = request.form.get("password")

    user = query_db("SELECT * FROM users WHERE username = ?", (username,), single=True)

    if user and check_password_hash(user["password_hash"], password):
        user_role = "admin" if user["is_admin"] == 1 else "user"

        payload = {
            "sub": f"{user['id']}",
            "username": username,
            "role": user_role,
            "exp": datetime.now(timezone.utc) + timedelta(hours=2),
        }

        token = jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")

        # Determine where to send the user
        target = "admin.dashboard" if user_role == "admin" else "files.view"
        response = make_response(redirect(url_for(target)))
        response.set_cookie("access_token", token, httponly=True, samesite="Lax")
        return response

    flash("Invalid username or password")
    return redirect(url_for("auth.login"))


@bp.route("/logout")
def logout():
    response = make_response(redirect(url_for("auth.login")))
    response.delete_cookie("access_token")
    flash("You have been logged out.")
    return response


def auth_required(*, admin=False):
    """
    If admin=True, it checks for the 'admin' role in the JWT payload.
    """

    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = request.cookies.get("access_token")

            if not token:
                return redirect(url_for("auth.login"))

            try:
                # Verify signature and expiration
                data = jwt.decode(
                    token, current_app.config["SECRET_KEY"], algorithms=["HS256"]
                )

                # Role check logic
                if admin and data.get("role") != "admin":
                    print("Access denied: Admins only.")
                    flash("Access denied: Admins only.")
                    return redirect(url_for("auth.login"))

                sub = data.get("sub")
                if sub is None:
                    flash("Invalid access token.")
                    return redirect(url_for("auth.login"))

                return f(int(sub), *args, **kwargs)
            except Exception as e:
                print(e)
                # Catches expired tokens or invalid signatures
                return redirect(url_for("auth.login"))

        return decorated

    return decorator
