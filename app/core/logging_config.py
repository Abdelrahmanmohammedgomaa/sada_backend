import logging


logging.basicConfig(level=logging.INFO)

app_logger = logging.getLogger("app")
error_logger = logging.getLogger("error")
upload_logger = logging.getLogger("upload")
