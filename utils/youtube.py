import re
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, VideoUnavailable

def _extract_video_id(url_or_id: str) -> str:
    if re.fullmatch(r"[0-9A-Za-z_-]{11}", url_or_id):
        return url_or_id

    m = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})(?:[&?\/]|$)", url_or_id)
    if m:
        return m.group(1)

    m = re.search(r"youtu\.be\/([0-9A-Za-z_-]{11})", url_or_id)
    if m:
        return m.group(1)

    raise ValueError("Invalid YouTube URL or ID.")


def get_youtube_transcript(url_or_id: str, languages=None, as_text=True, separator=" "):
    video_id = _extract_video_id(url_or_id)

    try:
        langs = languages if languages else ['en', 'en-US', 'en-GB', 'en-IN']
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=langs)
        except NoTranscriptFound:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)

        if not transcript:
            raise NoTranscriptFound("Transcript list empty.")

    except TranscriptsDisabled:
        raise RuntimeError("Transcripts are disabled for this video.")
    except NoTranscriptFound:
        raise RuntimeError("No transcript found.")
    except VideoUnavailable:
        raise RuntimeError("Video is unavailable.")
    except Exception as e:
        raise RuntimeError(f"Failed to fetch transcript: {e}")

    if as_text:
        texts = [seg.get("text", "").strip() for seg in transcript if seg.get("text")]
        return re.sub(r"\s+", " ", separator.join(texts)).strip()

    return transcript
