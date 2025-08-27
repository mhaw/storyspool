import io
import pathlib
import re
import tempfile
import uuid

from flask import current_app
from google.cloud import texttospeech
from pydub import AudioSegment  # Uncommented

from .store import upload_audio_and_get_url

# from pydub.playback import play # Added for local testing if needed


MAX_CHARS = 4500


def chunk_text(text: str, max_len: int = MAX_CHARS):
    paragraphs = re.split(r"(\n\s*\n)", text)
    chunks, buf = [], ""
    for part in paragraphs:
        if len(buf) + len(part) <= max_len:
            buf += part
        else:
            if buf.strip():
                chunks.append(buf.strip())
            buf = part
    if buf.strip():
        chunks.append(buf.strip())
    return chunks


def build_ssml(text: str):
    # Simple SSML: wrap paragraphs with small breaks
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    ssml_parts = ["<speak>"]
    for i, p in enumerate(paras):
        ssml_parts.append(f"<p>{p}</p>")
        if i < len(paras) - 1:
            ssml_parts.append('<break time="300ms"/>')
    ssml_parts.append("</speak>")
    return "".join(ssml_parts)


def synthesize_article_to_mp3(meta: dict, urlhash: str | None = None):
    """
    Synthesizes article text to MP3 audio using Google Cloud Text-to-Speech.
    Uploads the generated audio to Google Cloud Storage.
    """
    client = texttospeech.TextToSpeechClient()

    text = meta.get("text", "")
    if not text:
        current_app.logger.warning("No text found in article metadata for TTS.")
        # Return dummy values to allow the rest of the application to function
        tmpdir = tempfile.mkdtemp()
        fn = f"{urlhash or uuid.uuid4().hex}.mp3"
        out_path = pathlib.Path(tmpdir) / fn
        out_path.touch()  # Create a dummy empty file
        gcs_url = f"https://example.com/dummy_audio/{fn}"
        return out_path, gcs_url

    # Set the voice parameters
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )

    # Select the type of audio file you want returned
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    chunks = chunk_text(text, max_len=MAX_CHARS)
    if not chunks:
        current_app.logger.warning("No text chunks generated for TTS.")
        # Return dummy values if no chunks
        tmpdir = tempfile.mkdtemp()
        fn = f"{urlhash or uuid.uuid4().hex}.mp3"
        out_path = pathlib.Path(tmpdir) / fn
        out_path.touch()  # Create a dummy empty file
        gcs_url = f"https://example.com/dummy_audio/{fn}"
        return out_path, gcs_url

    combined_audio = AudioSegment.empty()  # Initialize empty AudioSegment

    for i, chunk in enumerate(chunks):
        current_app.logger.debug(
            f"Synthesizing chunk {i + 1}/{len(chunks)} ({len(chunk)} bytes)."
        )
        synthesis_input = texttospeech.SynthesisInput(text=chunk)
        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        # Append audio content to combined_audio
        combined_audio += AudioSegment.from_mp3(io.BytesIO(response.audio_content))

    # Write the combined audio content to a temporary file.
    tmpdir = tempfile.mkdtemp()
    fn = f"{urlhash or uuid.uuid4().hex}.mp3"
    out_path = pathlib.Path(tmpdir) / fn

    combined_audio.export(out_path, format="mp3")  # Export combined audio
    current_app.logger.info(f"Combined audio content written to file: {out_path}")

    # Upload the audio file to GCS
    gcs_url = upload_audio_and_get_url(out_path, fn)
    current_app.logger.info(f"Audio uploaded to GCS: {gcs_url}")

    return out_path, gcs_url
