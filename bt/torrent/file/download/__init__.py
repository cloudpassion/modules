from log import logger, log_stack

from .surge import TorrentSurgeDownload
# from .krbt import TorrentKrbtDownload

from .progress.console import print_progress


class TorrentDownload(
    TorrentSurgeDownload,
    # TorrentKrbtDownload,
):

    async def download(
            self,
            missing_pieces,
            to_bytes=False, to_file=False,
            variant='surge',
            progress_func=print_progress,
    ):
        if not missing_pieces:
            logger.info(f'no missing_pieces, {self.info_hash=}')
            return

        if not to_bytes and not to_file:
            logger.info(f'need set to_bytes or to_file')
            return

        try:
            if variant == 'surge':
                return await self._surge_download(
                    missing_pieces,
                    to_bytes, to_file,
                    progress_func=progress_func,
                )

            if variant == 'krbt':
                return await self._krbt_download(
                    missing_pieces,
                    to_bytes, to_file,
                    progress_func=progress_func,
                )
        except Exception:
            log_stack.error('ret')
            return

    pass


