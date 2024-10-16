import queue
import threading

import sounddevice
from devbooster import InterruptHandler

BYTES_PER_FRAME = 2


class MicReaderAbstract(InterruptHandler, threading.Thread):
    def __init__(self,
                 sample_rate_hertz: int = 8000,
                 invocations_per_second: int = 50,
                 ):
        InterruptHandler.__init__(self)
        threading.Thread.__init__(self)
        self.sample_rate_hertz: int = sample_rate_hertz
        self.invocations_per_second: int = invocations_per_second

    def run(self):
        def callback(indata, frames, time, status):
            if status:
                print(status)
            # Преобразуем данные в байты и отправляем на сервер
            buf = indata.tobytes()
            self._put_to_q(buf)

        dtype = f'int{int(BYTES_PER_FRAME * 8)}'
        print(f'dtype={dtype}')

        print(self.sample_rate_hertz)
        print(BYTES_PER_FRAME)
        print(self.invocations_per_second)

        blocksize = int(self.sample_rate_hertz * BYTES_PER_FRAME / self.invocations_per_second)
        print(f'blocksize={blocksize}')


        with sounddevice.InputStream(
                samplerate=self.sample_rate_hertz,
                channels=1,
                dtype=dtype,
                blocksize=blocksize,
                callback=callback,
        ):
            print("Capturing audio stream...")
            while self.not_interrupted():
                sounddevice.sleep(int(1000 / self.invocations_per_second))  # Поддерживаем поток открытым
            print("Stopped capturing audio.")
            sounddevice.stop()

    def _put_to_q(self, data: bytes):
        raise NotImplementedError()

    def listen(self):
        raise NotImplementedError()


class MicReader(MicReaderAbstract):
    def __init__(self, sample_rate_hertz: int = 8000, invocations_per_second=50):
        super().__init__(sample_rate_hertz, invocations_per_second)
        self._queue: queue.Queue[bytes] = queue.Queue()

    def _put_to_q(self, data: bytes):
        self._queue.put_nowait(data)

    def listen(self):
        try:
            while next_chunk := self._queue.get(timeout=1):
                yield next_chunk
        except queue.Empty:
            pass
