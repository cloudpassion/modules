import os
import random
import asyncio


from log import logger


async def print_progress(torrent, trackers, info_hash='unknow'):
    """Periodically poll download progress and `print` it."""
    total = torrent.pieces
    progress_template = "Download progress: {{}}/{} pieces".format(total)
    connections_template = "({} tracker{}, {} peer{})."
    info_hash_template = "info_hash {}"

    if os.name == "nt":
        connections_template += "\n"
    else:
        progress_template = "\r\x1b[K" + progress_template
    try:
        while True:
            if trackers:
                connected_trackers = trackers.connected_trackers
            else:
                connected_trackers = 0

            print(
                progress_template.format(total - torrent.missing_pieces),
                connections_template.format(
                    connected_trackers,
                    "" if connected_trackers == 1 else "s",
                    torrent.connected_peers,
                    "" if torrent.connected_peers == 1 else "s",
                ),
                info_hash_template.format(
                    info_hash,
                ),
                end="",
                flush=True,
            )
            # logger.info(f'pr.1')
            await asyncio.sleep(random.randint(1, 5))
            # logger.info(f'pr.2')
    except asyncio.CancelledError:
        if not torrent.missing_pieces:
            # Print one last time, so that the output reflects the final state.
            print(
                progress_template.format(total),
                info_hash_template.format(
                    info_hash,
                ),
                end="\n", flush=True
            )
        raise
