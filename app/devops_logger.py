import logging
from flask import request
from datetime import datetime

# Setup the logger
devops_logger = logging.getLogger('devsecops')
devops_logger.setLevel(logging.INFO)


file_handler = logging.FileHandler('access.log') 
devops_logger.addHandler(file_handler)

def log_security_event(topic, message):
    """
    Formatted for Common Log Format (CLF)
    Format: IP - - [Time] "TOPIC Message" STATUS
    """

    timestamp = datetime.now().strftime('%d/%b/%Y:%H:%M:%S +0000')
    ip = request.remote_addr if request else "127.0.0.1"
    

    log_line = f'{ip} - - [{timestamp}] "{topic} {message}"'
    
    devops_logger.info(log_line)