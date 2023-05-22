from .save_file import PyroRewriteSaveFile
from .send_media_group import PyroRewriteSendMediaGroup


class MyPyroMediaRewrite(
    PyroRewriteSaveFile,
    PyroRewriteSendMediaGroup,
):
    pass
