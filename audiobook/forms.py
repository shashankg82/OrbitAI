from django import forms


VOICE_CHOICES = [
    ("en-uk-male", "British Male"),
    ("en-uk-female", "British Female"),
    ("en-us-male", "American Male"),
    ("en-us-female", "American Female"),
]

class PDFUploadForm(forms.Form):
    pdf_file = forms.FileField(label="Upload PDF")
    voice_choice = forms.ChoiceField(choices=VOICE_CHOICES, label="Select Voice")