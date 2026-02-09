import os
import jwt
import json
import logging
from datetime import datetime
from flask import request, current_app

def get_audit_logger():
    """Configures the logger to write to the instance folder."""
    logger = logging.getLogger('audit_log')
    if not logger.handlers:
   
        log_path = os.path.join(current_app.instance_path, 'access.log')
        handler = logging.FileHandler(log_path)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def initialize_logging(app):
    """
    Sets up the application-wide logging system.
    Called once during app creation.
    """

    @app.after_request
    def record_request(response):
        """
        Captures metadata for every request in Common Log Format.
        """
      
        username = "-"
        token = request.cookies.get("access_token")
        
        if token:
            try:
                data = jwt.decode(
                    token, 
                    current_app.config["SECRET_KEY"], 
                    algorithms=["HS256"]
                )
                raw_username = data.get("username", "unknown")

                username = json.dumps(raw_username) 
            except Exception:
                username = "-"


        ip = request.remote_addr or "127.0.0.1"
        timestamp = datetime.now().strftime('%d/%b/%Y:%H:%M:%S +0000')
        request_line = f"{request.method} {request.path} {request.environ.get('SERVER_PROTOCOL')}"
        status = response.status_code
        size = response.calculate_content_length() or 0
        user_agent = request.headers.get('User-Agent', 'unknown')

        log_line = f'{ip} - {username} [{timestamp}] "{request_line}" {status} {size} "{user_agent}"\n'
        
 
        log_path = os.path.join(current_app.instance_path, "access.log")
        try:
            with open(log_path, "a") as f:
                f.write(log_line)
        except Exception as e:

            app.logger.error(f"Failed to write to access log: {e}")
            
        return response
    