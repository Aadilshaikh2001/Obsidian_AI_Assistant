"""
Voice Processor

Handles voice recording, Whisper transcription, and user editing workflow.
"""

import os
import tempfile
import threading
import time
import wave
from typing import Optional

import numpy as np
import sounddevice as sd
import soundfile as sf
import whisper

from rich.console import Console
from rich.panel import Panel
from rich.text import Text


class VoiceProcessor:
    """
    Handles voice recording and transcription using Whisper.
    """

    def __init__(self, model_name: str = "base", language: str = "en"):
        """
        Initialize the voice processor.

        Args:
            model_name: Whisper model size (tiny, base, small, medium, large)
            language: Language code for transcription (e.g., "en", "es", None for auto)
        """
        self.model_name = model_name
        self.language = language
        self.console = Console()
        self.model = None
        self._recording = False
        self._audio_data = None
        self._sample_rate = 16000  # Whisper expects 16kHz

    def _load_wav_direct(self, filepath: str) -> np.ndarray:
        """
        Load WAV file using Python's built-in wave module (no ffmpeg required).

        Args:
            filepath: Path to WAV file

        Returns:
            Audio array as float32, normalized to [-1, 1]
        """
        with wave.open(filepath, 'rb') as wav_file:
            frames = wav_file.readframes(wav_file.getnframes())
            audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0

            # Convert stereo to mono
            if wav_file.getnchannels() > 1:
                audio = audio.reshape(-1, wav_file.getnchannels())
                audio = audio.mean(axis=1)

            # Normalize if audio is too quiet (Whisper works better with louder audio)
            peak = np.max(np.abs(audio))
            if peak > 0 and peak < 0.1:
                # Scale up quiet audio for better Whisper transcription
                audio = audio / peak * 0.8

            return audio

    def _load_model(self):
        """Load Whisper model if not already loaded."""
        if self.model is None:
            self.console.print(
                f"[dim]Loading Whisper {self.model_name} model...[/dim]"
            )
            self.model = whisper.load_model(self.model_name)
        return self.model

    def record_audio(self, duration: Optional[int] = None) -> str:
        """
        Record audio from microphone.

        Args:
            duration: Recording duration in seconds (None = unlimited, press Enter to stop)

        Returns:
            Path to recorded audio file
        """
        self._load_model()

        self.console.print(
            "\n[bold cyan]🎤 Start speaking...[/bold cyan]"
        )
        self.console.print(
            "[dim]Press Enter to stop recording...[/dim]\n"
        )

        # Setup audio recording
        self._recorded_chunks = []
        self._recording = True

        def callback(indata, frames, time_info, status):
            if self._recording and len(indata) > 0:
                self._recorded_chunks.append(indata.copy())

        # Start recording in background
        stream = sd.InputStream(
            samplerate=self._sample_rate,
            channels=1,
            dtype="float32",
            callback=callback,
        )

        with stream:
            start_time = time.time()

            def check_timeout():
                while self._recording:
                    if duration and (time.time() - start_time) >= duration:
                        self._recording = False
                        return
                    time.sleep(0.05)

            timeout_thread = threading.Thread(target=check_timeout, daemon=True)
            timeout_thread.start()

            # Wait for user to press Enter or timeout
            try:
                # Use a timeout so we don't block forever
                if duration:
                    # For duration mode, just wait for the duration
                    time.sleep(duration)
                    self._recording = False
                else:
                    # For manual mode, wait for Enter
                    input()
                    self._recording = False
            except EOFError:
                self._recording = False

            timeout_thread.join(timeout=2)

        # Combine recording chunks into single array
        if self._recorded_chunks:
            self._audio_data = np.concatenate(self._recorded_chunks, axis=0).flatten()
            self.console.print(
                f"[dim]Recorded {len(self._audio_data) / self._sample_rate:.2f} seconds of audio[/dim]"
            )
        else:
            self._audio_data = None
            self.console.print(
                "[yellow]No audio recorded[/yellow]"
            )

        # Save to temp file
        return self._save_audio()

    def _save_audio(self) -> str:
        """Save recorded audio to temp WAV file with normalization."""
        if self._audio_data is None:
            raise ValueError("No audio data recorded")

        # Normalize audio if it's too quiet for better Whisper transcription
        audio = self._audio_data.copy()
        peak = np.max(np.abs(audio))
        if peak > 0 and peak < 0.1:
            # Scale up quiet audio for better Whisper transcription
            audio = audio / peak * 0.8

        # Create temp file
        fd, path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)

        # Write WAV file
        sf.write(path, audio, self._sample_rate)

        return path

    def transcribe_audio(self, audio_path: str) -> str:
        """
        Transcribe audio file using Whisper.

        Args:
            audio_path: Path to audio file

        Returns:
            Transcribed text
        """
        self._load_model()

        self.console.print(
            "[dim]Transcribing audio...[/dim]"
        )

        # Load audio using wave module (no ffmpeg required)
        audio = self._load_wav_direct(audio_path)

        # Transcribe with Whisper
        result = self.model.transcribe(
            audio,
            language=self.language if self.language else None,
            word_timestamps=False,
            verbose=False,
        )

        return result["text"].strip()

    def edit_transcription(self, text: str) -> Optional[str]:
        """
        Display transcription and allow user to edit.

        Args:
            text: Original transcription

        Returns:
            Final text to send, or None if cancelled
        """
        self.console.print()

        # Show transcription in panel
        self.console.print(
            Panel(
                text,
                title="[bold]Transcription[/bold]",
                border_style="cyan",
                padding=(1, 2),
            )
        )

        # Ask user what to do
        self.console.print()
        self.console.print(
            "[bold]What would you like to do?[/bold]"
        )
        self.console.print(
            "  [Y]es - Send to AI"
        )
        self.console.print(
            "  [E]dit text"
        )
        self.console.print(
            "  [C]ancel"
        )
        self.console.print()

        while True:
            try:
                self.console.print(
                    "[bold]Select option (Y/E/C):[/bold] ",
                    end="",
                    flush=True,
                )
                choice = input().strip().lower()

                if choice == "y":
                    return text
                elif choice == "e":
                    return self._inline_edit(text)
                elif choice == "c":
                    return None
                else:
                    self.console.print(
                        "[yellow]Please choose Y, E, or C[/yellow]"
                    )
            except EOFError:
                return None

    def _inline_edit(self, text: str) -> Optional[str]:
        """
        Allow user to edit transcription inline.

        Args:
            text: Original transcription

        Returns:
            Edited text, or None if cancelled
        """
        self.console.print()
        self.console.print(
            "[bold]Edit your transcription:[/bold]"
        )
        self.console.print(
            "[dim]Type your changes and press Enter.[/dim]"
        )
        self.console.print(
            "[dim]Press Ctrl+C to cancel.[/dim]\n"
        )

        # Show current text with prompt
        self.console.print(f"[dim]>[/dim] {text}", highlight=False)

        try:
            edit_input = input()
            if edit_input.strip():
                return edit_input.strip()
            return text  # Return original if empty
        except KeyboardInterrupt:
            self.console.print()
            return None

    def record_and_get_text(
        self, duration: Optional[int] = None
    ) -> Optional[str]:
        """
        Complete voice-to-text flow: record → transcribe → edit.

        Args:
            duration: Optional recording duration

        Returns:
            Final text to send, or None if cancelled/error
        """
        try:
            # Record audio
            audio_path = self.record_audio(duration)

            # Transcribe
            transcription = self.transcribe_audio(audio_path)

            if not transcription:
                self.console.print(
                    "[bold red]No speech detected.[/bold red]"
                )
                self._cleanup_temp(audio_path)
                return None

            # Edit if needed
            final_text = self.edit_transcription(transcription)

            # Cleanup
            self._cleanup_temp(audio_path)

            return final_text

        except Exception as e:
            self.console.print(
                f"[bold red]Error:[/bold red] {e}"
            )
            return None

    def _cleanup_temp(self, audio_path: str):
        """Delete temporary audio file."""
        try:
            if os.path.exists(audio_path):
                os.remove(audio_path)
        except Exception:
            pass


def get_voice_processor() -> VoiceProcessor:
    """Get or create the voice processor singleton."""
    import yaml
    import os

    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        "config.yaml"
    )
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            config = yaml.safe_load(f) or {}
    else:
        config = {"voice": {}}

    voice_config = config.get("voice", {})

    return VoiceProcessor(
        model_name=voice_config.get("model", "base"),
        language=voice_config.get("language", "en"),
    )
