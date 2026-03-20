import whisper

VIDEO = "A Shocking Accident 1982 from the short story by Graham Greene [get.gt].mp4"
OUTPUT = "subtitles.srt"

print("Loading model (will download ~1.4GB on first run)...")
model = whisper.load_model("medium")

print("Transcribing...")
result = model.transcribe(VIDEO, language="en", verbose=True)

with open(OUTPUT, "w", encoding="utf-8") as f:
    for i, seg in enumerate(result["segments"], 1):
        start = seg["start"]
        end = seg["end"]
        text = seg["text"].strip()
        f.write(f"{i}\n")
        f.write(f"{int(start//3600):02}:{int(start%3600//60):02}:{start%60:06.3f} --> "
                f"{int(end//3600):02}:{int(end%3600//60):02}:{end%60:06.3f}\n".replace(".", ","))
        f.write(f"{text}\n\n")

print(f"\nDetected language: {result.get('language', 'unknown')}")
print(f"Saved to {OUTPUT}")
