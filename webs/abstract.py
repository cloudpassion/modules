import redis
from sanic import Sanic


class AbstractServer:

    app: Sanic
    redis_conn: redis.Redis
