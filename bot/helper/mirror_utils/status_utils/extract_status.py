from time import time

from bot import LOGGER, subprocess_lock
from bot.helper.ext_utils.status_utils import (
    get_readable_file_size,
    MirrorStatus,
    get_readable_time,
)
from bot.helper.ext_utils.files_utils import get_path_size
from bot.helper.ext_utils.bot_utils import async_to_sync


class ExtractStatus:
    def __init__(self, listener, size, gid):
        self._size = size
        self._gid = gid
        self._start_time = time()
        self.listener = listener
        self.engine = "7zip"

    def gid(self):
        return self._gid

    def speed_raw(self):
        return self.processed_raw() / (time() - self._start_time)

    def progress_raw(self):
        try:
            return self.processed_raw() / self._size * 100
        except:
            return 0

    def progress(self):
        return f"{round(self.progress_raw(), 2)}%"

    def speed(self):
        return f"{get_readable_file_size(self.speed_raw())}/s"

    def name(self):
        return self.listener.name

    def size(self):
        return get_readable_file_size(self._size)

    def eta(self):
        try:
            seconds = (self._size - self.processed_raw()) / self.speed_raw()
            return get_readable_time(seconds)
        except:
            return "-"

    def status(self):
        return MirrorStatus.STATUS_EXTRACTING

    def processed_bytes(self):
        return get_readable_file_size(self.processed_raw())

    def processed_raw(self):
        if self.listener.newDir:
            return async_to_sync(get_path_size, self.listener.newDir)
        else:
            return async_to_sync(get_path_size, self.listener.dir) - self._size

    def task(self):
        return self

    async def cancel_task(self):
        LOGGER.info(f"Cancelling Extract: {self.listener.name}")
        async with subprocess_lock:
            if (
                self.listener.suproc is not None
                and self.listener.suproc.returncode is None
            ):
                self.listener.suproc.kill()
            else:
                self.listener.suproc = "cancelled"
        await self.listener.onUploadError("extracting stopped by user!")
