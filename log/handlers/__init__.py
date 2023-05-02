import time
import asyncio
import os

from config import settings, secrets

try:
    from lipsock import MySSHProxy
except:
    pass

try:
    from atiny.mthread import ThreadWithException
except:
    from ..mthread import ThreadWithException

from .hkafka import init_kafka_handler
from .default import (
    logger, flogger, mlog, INFO, DEBUG, CRITICAL, ERROR, WARNING
)
from .stack import test_stack, test_logger, log_stack


async def add_kafka_handler():
    try:
        collect = secrets.log.collect
        if collect:
            ssh_user = None
            if secrets.log.web.proxy == 'ssh':
                ports = tuple(secrets.log.ssh.listen)
                ip = secrets.log.ssh.ip
                ssh_port = secrets.log.ssh.port
                ssh_user = secrets.log.ssh.user
                remote_port = secrets.log.ssh.remote
                local_ports = tuple(secrets.log.ssh.local)
                pkey_path = secrets.log.ssh.pkey_path
                if not os.path.isfile:
                    raise FileNotFoundError(f'not found private key: {pkey_path} in'
                                            f'{os.getcwd()}')

                ssh = MySSHProxy(
                    ssh_addr=ip,
                    proxy_type='ssh_forward',
                    ssh_port=ssh_port,
                    ssh_user=ssh_user,
                    ssh_user_key=pkey_path,
                    remote_port=remote_port,
                    listen_port=ports,
                    local_port=local_ports
                )

                #asyncio.run(ssh.ssh_forward(False, False))
                #await ssh.ssh_forward(False, False)

                old_loop = asyncio.get_event_loop()
                loop = asyncio.new_event_loop()
                ssh_forward_thread = ThreadWithException(
                    target=ssh.ssh_forward_threaded, args=(
                        loop,
                        True, False
                    )
                )
                ssh_forward_thread.start()

                asyncio.set_event_loop(old_loop)

                t = 0
                while not ssh.running:
                    if t >= 5:
                        break
                        #raise Exception('forward not starting')

                    logger.warning(f'wait run {t}/5 times')
                    t += 1
                    time.sleep(1)

                logger.info(f'####PORT: {ssh.listen_port}, {ports}')
            else:
                ports = (443, )

            for port in ports:
                if port is None:
                    continue

                url = f'{secrets.log.web.url}:{port}'
                kafka_url = url.replace('https://', '').replace('http://', '')
                logger.info(f'{kafka_url=}')

                kafka_handler_test = init_kafka_handler(
                    kafka_url,
                    secrets.log.topic, script=secrets.log.app.name, user=ssh_user,
                    level='test'
                )
                kafka_handler_test.setLevel(INFO)
                test_logger.addHandler(kafka_handler_test)
                test_logger.setLevel(INFO)

                try:
                    test_logger.info(f'TEST KAFKA.logger {port=}')

                    while test_logger.handlers:
                        test_logger.handlers.pop()
                    test_logger.setLevel(CRITICAL)

                    kafka_handler_normal = init_kafka_handler(
                        kafka_url,
                        secrets.log.topic, script=secrets.log.app.name, user=ssh_user,
                        level='normal'
                    )
                    kafka_handler_stack = init_kafka_handler(
                        kafka_url,
                        secrets.log.topic, script=secrets.log.app.name, user=ssh_user,
                        level='stack'
                    )
                    kafka_handler_full = init_kafka_handler(
                        kafka_url,
                        secrets.log.topic, script=secrets.log.app.name, user=ssh_user,
                        level='full'
                    )

                    try:
                        kafka_handler_normal.setLevel(globals().get(secrets.log.level))
                    except Exception:
                        log_stack.info(f'stack setlevel')
                        kafka_handler_normal.setLevel(ERROR)

                    kafka_handler_stack.setLevel(ERROR)
                    kafka_handler_full.setLevel(WARNING)

                    logger.addHandler(kafka_handler_normal)
                    log_stack.addHandler(kafka_handler_stack)
                    flogger.addHandler(kafka_handler_full)

                    break
                except Exception:
                    log_stack.warning(f"can't send init message to kafka: {url}")
            else:
                logger.warning(f'failed for all ports')
                raise Exception(f'failed for all ports: {ports}')
            return loop, ssh_forward_thread

    except Exception:
        log_stack.warning('Kafka initialization failed')
        try:
            ssh_forward_thread.raise_exception()
        except Exception:
            log_stack.warning(f'unkill')

    return None, None


async def del_kafka_ssh(loop=None, ssh_forward_thread=None):
    try:

        logger.warning(f'before {loop=}')
        if loop:

            await loop.shutdown_asyncgens()
            await loop.shutdown_default_executor()
            loop.call_soon_threadsafe(loop.stop)
            loop.call_soon_threadsafe(loop.close)

    except Exception:
        log_stack.warning('loop')

    try:
        if ssh_forward_thread and ssh_forward_thread.join():
            logger.warning(f'raise {ssh_forward_thread=}')
            ssh_forward_thread.raise_exception()

    except Exception:
        log_stack.warning('thread')

    logger.warning(f'after {loop=}')
