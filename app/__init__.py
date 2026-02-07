import os
from typing import Any, Mapping

from dotenv import load_dotenv
from flask import Flask

load_dotenv()


def create_app(test_config: Mapping[str, Any] | None = None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev"),
        DATABASE=os.path.join(app.instance_path, "database.sqlite"),
        FILE_STORE=os.path.join(app.instance_path, "files"),
    )

    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.from_mapping(test_config)

    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["FILE_STORE"], exist_ok=True)

    from . import admin, auth, files, db

    db.init_app(app)
    app.register_blueprint(auth.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(files.bp)

    from .utils import format_size

    app.jinja_env.filters["format_size"] = format_size

    return app
