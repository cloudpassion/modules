from .throttling import register_throttling_middleware
from .logging import register_logging_middleware
from .rkn import register_rkn_middleware
# from .lesson_acl import register_lesson_acl_middleware
from .post_query_answer import register_pqa_middleware
from .forwarder import register_forwarder_middleware
from .database import register_database_middleware


def register_middlewares(dp):
    register_forwarder_middleware(dp)
    register_pqa_middleware(dp)
    # register_lesson_acl_middleware(dp)
    register_rkn_middleware(dp)
    register_logging_middleware(dp)
    register_throttling_middleware(dp)
    register_database_middleware(dp)
