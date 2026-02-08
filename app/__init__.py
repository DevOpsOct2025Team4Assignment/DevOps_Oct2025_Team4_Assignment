import os
from typing import Any, Mapping
from datetime import datetime # Added this import
import jwt
from dotenv import load_dotenv
from flask import Flask, request, session
from app.devops_logger import log_security_event

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


    @app.after_request
    def log_standard_access(response):
        if request.path.startswith('/admin'):
            
            user_identifier = "-"
            token = request.cookies.get("access_token")

            if token:
                try:

                    data = jwt.decode(
                        token, 
                        app.config["SECRET_KEY"], 
                        algorithms=["HS256"]
                    )
                    user_id = data.get("sub")
                    username = data.get("username", "Unknown")
                    user_identifier = f"User:{username}(ID:{user_id})"
                except Exception:
                    user_identifier = "INVALID_TOKEN"

            ip = request.remote_addr or "127.0.0.1"
            timestamp = datetime.now().strftime('%d/%b/%Y:%H:%M:%S +0000')
            request_line = f"{request.method} {request.path} {request.environ.get('SERVER_PROTOCOL')}"
            status = response.status_code
            size = response.calculate_content_length() or 0
            
            
            user_agent = request.headers.get('User-Agent', 'unknown')
            
            clf_line = f'{ip} - {user_identifier} [{timestamp}] "{request_line}" {status} {size} "{user_agent}"'
            
            
            with open("access.log", "a") as f:
                f.write(clf_line + "\n")
            
        return response 

    return app 