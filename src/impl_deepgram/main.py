import os

from deepgram.clients.live import MetadataResponse

# os.environ['DEEPGRAM_API_KEY'] = '6b56fde898752702d32bde0ff8266ff0457007d1'

from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions, Microphone, OpenResponse, \
    SpeechStartedResponse, LiveResultResponse, UtteranceEndResponse, CloseResponse

deepgram: DeepgramClient = DeepgramClient()

dg_connection = deepgram.listen.websocket.v("1")


def on_open(self, open: OpenResponse, **kwargs):
    print(f"on_open [{type(open)}]: {open.type}")


def on_message(self, result: LiveResultResponse, **kwargs):
    def get_sentence():
        sentence = result.channel.alternatives[0].transcript
        if len(sentence) == 0:
            return None
        return sentence

    print(f"on_message [{type(result)}] (sentence): {get_sentence()}")


def on_metadata(self, metadata: MetadataResponse, **kwargs):
    print(f"on_metadata [{type(metadata)}]: {metadata.duration}")


def on_speech_started(self, speech_started: SpeechStartedResponse, **kwargs):
    print(f"on_speech_started [{type(speech_started)}]: {speech_started.timestamp=}")


def on_utterance_end(self, utterance_end: UtteranceEndResponse, **kwargs):
    print(f"on_utterance_end [{type(utterance_end)}]: {utterance_end.last_word_end=}")


def on_error(self, error, **kwargs):
    print(f"on_error [{type(error)}]: {error}")


def on_close(self, close: CloseResponse, **kwargs):
    print(f"on_close [{type(close)}]: {close.type}")


dg_connection.on(LiveTranscriptionEvents.Open, on_open)
dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
dg_connection.on(LiveTranscriptionEvents.Metadata, on_metadata)
dg_connection.on(LiveTranscriptionEvents.SpeechStarted, on_speech_started)
dg_connection.on(LiveTranscriptionEvents.UtteranceEnd, on_utterance_end)
dg_connection.on(LiveTranscriptionEvents.Error, on_error)
dg_connection.on(LiveTranscriptionEvents.Close, on_close)

options: LiveOptions = LiveOptions(
    model="nova-2",
    punctuate=True,
    language="ru-RU",
    encoding="linear16",
    channels=1,
    sample_rate=16000,
    ## To get UtteranceEnd, the following must be set:
    interim_results=True,
    utterance_end_ms="1000",
    vad_events=True,
)
dg_connection.run(options)

if __name__ == '__main__':
    ## create microphone
    microphone = Microphone(dg_connection.send)

    ## start microphone
    microphone.start()

    ## wait until finished
    input("Press Enter to stop recording...\n\n")

    ## Wait for the microphone to close
    microphone.finish()

    ## Indicate that we've finished
    dg_connection.finish()

    print("Finished")
