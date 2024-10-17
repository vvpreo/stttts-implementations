import os

from impl_yandex.stt import YandexSTTOneSession
from micreader import MicReader

if __name__ == '__main__':
    mr = MicReader()

    ystt = YandexSTTOneSession(
        api_key=os.environ['YANDEX_API_KEY'],
        iter_bytes=mr.listen()
    )

    mr.start()

    responses = list()

    for r in ystt.gen():
        responses.append(r)

    print("ALL " * 80)
    print("ALL " * 80)
    print("ALL " * 80)
    for r in responses:
        print(r)
