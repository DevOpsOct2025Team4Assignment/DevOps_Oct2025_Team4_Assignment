from flask import send_from_directory
import secrets
import os

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from werkzeug.utils import secure_filename

from app.auth import auth_required
from app.db import query_db

bp = Blueprint("files", __name__, url_prefix="/dashboard")


@bp.route("/")
@auth_required()
def view(user_id: int):
    files = query_db("SELECT * FROM files WHERE user_id = ?", (user_id,))
    user = query_db("SELECT is_admin FROM users WHERE id = ?", (user_id,), single=True)
    is_admin = user["is_admin"] == 1 if user else False
    return render_template("user_dashboard.html", files=files, is_admin=is_admin)


@bp.route("/upload", methods=["POST"])
@auth_required()
def upload(user_id: int):
    if "file" not in request.files:
        flash("No file part")
        return redirect(url_for("files.view"))

    file = request.files["file"]

    if file.filename == "":
        flash("No selected file")
        return redirect(url_for("files.view"))

    if file:
        path = secure_filename(f"{secrets.token_urlsafe(8)}_{file.filename}")
        full_path = os.path.join(current_app.config["FILE_STORE"], path)
        file.save(full_path)
        size_bytes = os.path.getsize(full_path)

        query_db(
            "INSERT INTO files (user_id, display_name, file_path, size_bytes) VALUES (?, ?, ?, ?)",
            (user_id, file.filename, path, size_bytes),
        )
        flash("File uploaded successfully")
        return redirect(url_for("files.view"))

    flash("No file data to upload")
    return redirect(url_for("files.view"))


@bp.route("/download/<int:file_id>", methods=["GET"])
@auth_required()
def download(user_id: int, file_id: int):
    file = query_db(
        "SELECT * FROM files WHERE id = ? AND user_id = ?",
        (file_id, user_id),
        single=True,
    )
    if file is None:
        flash("File not found")
        return redirect(url_for("files.view"))

    return send_from_directory(
        current_app.config["FILE_STORE"],
        file["file_path"],
        download_name=file["display_name"],
        as_attachment=True,
    )


@bp.route("/delete/<int:file_id>", methods=["POST"])
@auth_required()
def delete(user_id: int, file_id: int):
    file = query_db(
        "DELETE FROM files WHERE id = ? AND user_id = ? RETURNING *",
        (file_id, user_id),
        single=True,
    )
    if file is None:
        flash("File not found")
        return redirect(url_for("files.view"))

    os.remove(os.path.join(current_app.config["FILE_STORE"], file["file_path"]))
    flash("File deleted successfully")
    return redirect(url_for("files.view"))
