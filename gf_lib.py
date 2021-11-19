import logging


log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def get_cas_filename(filepath:str):
    filename = ""
    with open(filepath, "rb") as fp:
        data = fp.read()
        filename = data[18:24].decode("ascii")
        filename = filename.strip()
    log.info(f"Found filename: {filename}")
    return filename


