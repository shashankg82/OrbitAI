import os
import fitz  
import pyttsx3
from django.shortcuts import render
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage

# Uploading folder
UPLOAD_DIR = "media/uploads/"
AUDIO_DIR = "media/audio/"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

'''I used voices availabel from Windows system, but my windows edition restricts me
to just add the default 3 voices, when i tried to work with external TTS API like gTTS
it only gives female voice option, and OpenAI TTS and Amazon Polly isn't free.
'''

VOICES = {
    "david": "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-US_DAVID_11.0",
    "hazel": "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-GB_HAZEL_11.0",
    "zira": "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-US_ZIRA_11.0",
}

def pdf_to_audio(request):
    if request.method == "POST" and request.FILES.get("pdf_file"):
        pdf_file = request.FILES["pdf_file"]
        voice_choice = request.POST.get("voice", "david")


        fs = FileSystemStorage(location=UPLOAD_DIR)
        filename = fs.save(pdf_file.name, pdf_file)
        pdf_path = os.path.join(UPLOAD_DIR, filename)

        
        text = ""
        doc = fitz.open(pdf_path)
        for page in doc:
            text += page.get_text("text")
        doc.close()

        if not text.strip():
            return HttpResponse("No text found in PDF.")

        
        audio_filename = filename.replace(".pdf", ".mp3")
        audio_path = os.path.join(AUDIO_DIR, audio_filename)

        engine = pyttsx3.init()
        engine.setProperty("voice", VOICES.get(voice_choice, VOICES["david"]))
        engine.save_to_file(text, audio_path)
        engine.runAndWait()

        audio_url = f"/media/audio/{audio_filename}"

        return render(request, "audiobook/result.html", {
            "audio_url": audio_url,
            "filename": audio_filename
        })

    return render(request, "audiobook/upload.html", {"voices": VOICES})
