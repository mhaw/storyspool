import io, uuid, re, tempfile, pathlib
from pydub import AudioSegment
from google.cloud import texttospeech
from flask import current_app
from .store import upload_audio_and_get_url

MAX_CHARS = 4500

def chunk_text(text: str, max_len: int = MAX_CHARS):
    paragraphs = re.split(r"(\n\s*\n)", text)
    chunks, buf = [], ""
    for part in paragraphs:
        if len(buf) + len(part) <= max_len:
            buf += part
        else:
            if buf.strip(): chunks.append(buf.strip())
            buf = part
    if buf.strip(): chunks.append(buf.strip())
    return chunks

def build_ssml(text: str):
    # Simple SSML: wrap paragraphs with small breaks
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    ssml_parts = ["<speak>"]
    for i,p in enumerate(paras):
        ssml_parts.append(f"<p>{p}</p>")
        if i < len(paras)-1:
            ssml_parts.append('<break time="300ms"/>' )
    ssml_parts.append("</speak>")
    return "".join(ssml_parts)

def synthesize_article_to_mp3(meta: dict, urlhash: str|None=None):
    text = meta.get("text","").strip()
    if not text:
        raise ValueError("No article text to synthesize.")
    client = texttospeech.TextToSpeechClient()
    voice = texttospeech.VoiceSelectionParams(
        language_code="-".join(current_app.config["TTS_VOICE"].split("-")[:2]),
        name=current_app.config["TTS_VOICE"]
    )
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=current_app.config["TTS_SPEAKING_RATE"],
        pitch=current_app.config["TTS_PITCH"])
    chunks = chunk_text(text)
    segments = []
    for c in chunks:
        ssml = build_ssml(c)
        res = client.synthesize_speech(input=texttospeech.SynthesisInput(ssml=ssml),
                                       voice=voice, audio_config=audio_config)
        segments.append(AudioSegment.from_file(io.BytesIO(res.audio_content), format="mp3"))
    combined = AudioSegment.silent(duration=250)
    for seg in segments:
        combined += seg + AudioSegment.silent(duration=120)
    tmpdir = tempfile.mkdtemp()
    fn = f"{urlhash or uuid.uuid4().hex}.mp3"
    out_path = pathlib.Path(tmpdir) / fn
    combined.export(out_path, format="mp3")
    gcs_url = upload_audio_and_get_url(out_path, meta, urlhash=urlhash)
    return str(out_path), gcs_url
