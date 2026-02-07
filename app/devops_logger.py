import logging
import os


devops_logger = logging.getLogger('devsecops')
devops_logger.setLevel(logging.INFO)


file_handler = logging.FileHandler('devsecops_audit.log')
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(topic)s | %(message)s')
file_handler.setFormatter(formatter)

devops_logger.addHandler(file_handler)

def log_security_event(topic, message):
    """Logs events like login failures, admin actions, or unauthorized access."""
    devops_logger.info(message, extra={'topic': topic})

