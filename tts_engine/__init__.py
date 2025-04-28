"""
TTS Engine package for Orpheus text-to-speech system.

This package contains the core components for audio generation:
- inference.py: Token generation and API handling
- speechpipe.py: Audio conversion pipeline
"""

# Make key components available at package level
from .inference import (
    generate_speech_from_api,
    generate_speech_streaming,
    ACTIVE_REQUESTS,
    AVAILABLE_VOICES,
    DEFAULT_VOICE,
    VOICE_TO_LANGUAGE,
    AVAILABLE_LANGUAGES,
    list_available_voices
)
