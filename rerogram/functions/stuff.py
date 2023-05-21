from log import logger, log_stack


async def progress(current, total):
    try:
        logger.info(f"{current * 100 / total:.1f}%")
    except Exception as exc:
        pass
