import pyttsx3

engine = pyttsx3.init()

# Listar todas las voces disponibles
voices = engine.getProperty('voices')
for index, voice in enumerate(voices):
    print(f"Voice {index}:")
    print(f" - ID: {voice.id}")
    print(f" - Name: {voice.name}")
    print(f" - Languages: {voice.languages}")
    print(f" - Gender: {voice.gender}")
    print(f" - Age: {voice.age}\n")
