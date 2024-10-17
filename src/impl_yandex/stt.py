# coding=utf8
from typing import Iterable, Iterator, Literal, List

import grpc
from pydantic import BaseModel

import yandex.cloud.ai.stt.v3.stt_pb2 as stt_pb2
import yandex.cloud.ai.stt.v3.stt_service_pb2_grpc as stt_service_pb2_grpc


# class YSTT_StatusCode(BaseModel):
#     code_type: str
#
#
# class YSTT_Session_UUID(BaseModel):
#     uuid: str
#     user_request_id: str
#
#
# class YSTT_AudioCursors(BaseModel):
#     received_data_ms: int
#     partial_time_ms: int
#     final_time_ms: int
#     final_index: int | None
#     eou_time_ms: int


class YSTT_Word(BaseModel):
    text: str
    start_time_ms: int
    end_time_ms: int


class YSTT_Alternative(BaseModel):
    words: List[YSTT_Word] = list()
    text: str
    end_time_ms: int


class YSTT_Chunks(BaseModel):
    alternatives: List[YSTT_Alternative] = list()
    channel_tag: str


class SttYandexResponse(BaseModel):
    type: Literal['status_code', 'partial', 'final', 'final_refinement', 'eou_update', None]
    partial: YSTT_Chunks | None
    final: YSTT_Chunks | None
    final_refinement: YSTT_Chunks | None
    # session_uuid: YSTT_Session_UUID | None
    # audio_cursors: YSTT_AudioCursors | None
    # response_wall_time_ms: int | None
    # status_code: YSTT_StatusCode | None


class YandexSTTOneSession:
    def __init__(self, api_key: str, iter_bytes: Iterable[bytes]):
        self._api_key: str = api_key
        self._iter_bytes: Iterable[bytes] = iter_bytes

    def convert(self) -> Iterator[stt_pb2.StreamingResponse]:
        # Specify the recognition settings.
        recognize_options = stt_pb2.StreamingOptions(
            recognition_model=stt_pb2.RecognitionModelOptions(
                audio_format=stt_pb2.AudioFormatOptions(
                    raw_audio=stt_pb2.RawAudio(
                        audio_encoding=stt_pb2.RawAudio.LINEAR16_PCM,
                        sample_rate_hertz=8000,
                        audio_channel_count=1
                    )
                ),
                text_normalization=stt_pb2.TextNormalizationOptions(
                    text_normalization=stt_pb2.TextNormalizationOptions.TEXT_NORMALIZATION_ENABLED,
                    profanity_filter=True,
                    literature_text=False
                ),
                language_restriction=stt_pb2.LanguageRestrictionOptions(
                    restriction_type=stt_pb2.LanguageRestrictionOptions.WHITELIST,
                    language_code=['ru-RU']
                ),
                audio_processing_type=stt_pb2.RecognitionModelOptions.REAL_TIME
            )
        )

        # Send a message with recognition settings.
        yield stt_pb2.StreamingRequest(session_options=recognize_options)

        # Read the audio file and send its contents in chunks.
        for data in self._iter_bytes:
            yield stt_pb2.StreamingRequest(chunk=stt_pb2.AudioChunk(data=data))

    # When authorizing with an API key
    # as a service account, provide api_key instead of iam_token.
    # def run(api_key, audio_file_name):
    def gen_raw(self):
        # Establish a server connection.
        cred = grpc.ssl_channel_credentials()
        channel = grpc.secure_channel('stt.api.cloud.yandex.net:443', cred)
        stub = stt_service_pb2_grpc.RecognizerStub(channel)

        # Send data for recognition.
        it: Iterator = stub.RecognizeStreaming(self.convert(), metadata=(
            # Parameters for authorization with an IAM token
            #     ('authorization', f'Bearer {iam_token}'),
            # Parameters for authorization as a service account with an API key
            ('authorization', f'Api-Key {self._api_key}'),
        ))

        # Process the server responses and output the result to the console.
        try:
            for r in it:
                yield r
        except grpc._channel._Rendezvous as err:
            print(f'Error code {err._state.code}, message: {err._state.details}')
            raise err

    def gen(self) -> SttYandexResponse:
        for r in self.gen_raw():
            _type = r.WhichOneof('Event')
            match _type:
                case 'partial':
                    yield SttYandexResponse(
                        type=_type,
                        partial=YSTT_Chunks(
                            channel_tag=r.partial.channel_tag,
                            alternatives=[YSTT_Alternative(
                                text=a.text,
                                end_time_ms=a.end_time_ms,
                                words=[YSTT_Word(
                                    text=w.text, start_time_ms=w.start_time_ms, end_time_ms=w.end_time_ms,
                                ) for w in a.words]
                            ) for a in r.partial.alternatives]
                        )
                    )
                case 'final':
                    yield SttYandexResponse(
                        type=_type,
                        final=YSTT_Chunks(
                            channel_tag=r.partial.channel_tag,
                            alternatives=[YSTT_Alternative(
                                text=a.text,
                                end_time_ms=a.end_time_ms,
                                words=[YSTT_Word(
                                    text=w.text, start_time_ms=w.start_time_ms, end_time_ms=w.end_time_ms,
                                ) for w in a.words]
                            ) for a in r.final.alternatives]
                        )
                    )
                case 'final_refinement':
                    yield SttYandexResponse(
                        type=_type,
                        final_refinement=YSTT_Chunks(
                            channel_tag=r.partial.channel_tag,
                            alternatives=[YSTT_Alternative(
                                text=a.text,
                                end_time_ms=a.end_time_ms,
                                words=[YSTT_Word(
                                    text=w.text, start_time_ms=w.start_time_ms, end_time_ms=w.end_time_ms,
                                ) for w in a.words]
                            ) for a in r.final_refinement.normalized_text.alternatives]
                        )
                    )
                case 'status_code' | 'eou_update' | None:
                    print(f">>> {_type} >>>")
                    # print(r)
                case _:
                    print(f'{_type} ' * 10)
                    print(r)
                    print(f'{_type}-' * 10)
