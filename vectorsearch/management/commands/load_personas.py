from django.core.management.base import BaseCommand
import json
from vectorsearch.models import Persona

class Command(BaseCommand):
    help = 'Load Personas from orbitai.json'

    def handle(self, *args, **kwargs):
        with open("orbitai.json") as f:
            personas = json.load(f)
        for p in personas:
            Persona.objects.create(
                name=p["name"],
                gender=p["gender"],
                age=p["age"],
                bio=p["bio"],
                job_role=p["job_role"],
                hobbies=p["hobbies"],
                smoker=p["smoker"],
                location=p["location"],
                embedding=p["embedding"]
            )
        self.stdout.write(self.style.SUCCESS('Successfully loaded personas'))