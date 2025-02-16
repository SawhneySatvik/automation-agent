import speech_recognition as sr
from pydub import AudioSegment
import os
from fastapi import HTTPException

def transcribe_audio(filename: str, targetfile: str = None) -> str:
    audio_file = filename
    if targetfile is None:
        targetfile = audio_file.rsplit(".", 1)[0] + ".txt"
    output_file = targetfile
    if not os.path.exists(audio_file):
        raise HTTPException(status_code=400, detail=f"File not found: {audio_file}")
    if not audio_file.lower().endswith((".mp3", ".wav")):
        raise HTTPException(status_code=400, detail="Unsupported file format. Only MP3 and WAV files are supported.")
    
    if not (output_file.startswith("/data") or output_file.startswith("./data")):
        output_file = f"./data/{output_file}"
    
    # Convert to WAV if not already in WAV format
    if not audio_file.lower().endswith(".wav"):
        print("Converting to WAV format...")
        wav_file = audio_file.rsplit(".", 1)[0] + ".wav"
        audio = AudioSegment.from_file(audio_file)
        audio.export(wav_file, format="wav")
        audio_file = wav_file  # Update file path

    # Transcribe the WAV file
    print("Transcribing audio...")
    r = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio = r.record(source)
    text = r.recognize_google(audio)

    # Write transcription to file
    with open(targetfile, 'w') as f:
        f.write(text)

    return f"Transcription saved to {targetfile}"