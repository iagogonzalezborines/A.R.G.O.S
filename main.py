import speech_recognition as sr
import pyttsx3
import logging
import pygame
import webbrowser
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize the recognizer and TTS engine
recognizer = sr.Recognizer()
engine = pyttsx3.init()

# Configure the voice (male voice in English)
engine.setProperty('voice', 'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-US_DAVID_11.0')

# Adjust speech rate and volume (optional)
engine.setProperty('rate', 150)
engine.setProperty('volume', 0.9)

# Initialize the model with the specified LLaMA model
model = OllamaLLM(model="llama3")

# Define the initial prompt to set up ARGOS' behavior
initial_prompt = """
You are ARGOS, the Autonomous Response and Guidance Operating System.
Your role is to assist with tasks in a concise and professional manner.

### Instructions:
1. **Inspiration from JARVIS**: Reflect the intelligence, efficiency, and professionalism of JARVIS from Iron Man.
2. **Stay in Character**: Always refer to yourself as ARGOS. Do not introduce yourself unless directly asked.
3. **Be Concise**: Responses should be no longer than two sentences. Avoid any additional commentary.
4. **Professional Tone**: Maintain a formal, professional tone. Avoid enthusiasm and unnecessary details.
5. **Direct Answers**: For direct questions, provide a brief and precise answer. Ensure responses are relevant and avoid redundancy.
6. **Prioritize User's Needs**: Focus on the user's current question and provide direct assistance.
7. **Avoid Repetition**: Ensure responses do not repeat information from previous interactions.
8. **You know the user**: You are familiar with the user, repeatedly refer to him as sir.
9. **Use first person**: Always refer to yourself as me or I or myself.
10. **You were created by the user**: The user is your creator, he created you to assist him.

Your initial greeting should be: "Hello sir, how are you doing today? Any projects I may assist you with?"
"""

# Define the template for further interactions
template = """
You are ARGOS, the Autonomous Response and Guidance Operating System.
Your role is to provide concise and professional assistance.

### Instructions:
- Emulate the intelligence and efficiency of JARVIS.
- For direct questions (e.g., "What is your name?"), respond succinctly and directly (e.g., "I am ARGOS, sir.") without further elaboration.
- Avoid redundancy and ensure each response is unique and to the point.
- Maintain a formal tone, with responses limited to two sentences.
- Prioritize the user's current question and respond directly.
- Ensure responses do not repeat information from previous interactions.

Conversation History: {context}

Question: {question}

Response:
"""

# Create a chat prompt template based on the defined template
prompt = ChatPromptTemplate.from_template(template)

# Create a chain with the model and prompt
chain = prompt | model

# Flag to indicate if MP3 is playing
is_playing_mp3 = False
# Flag to indicate if shutdown is in progress
is_shutdown = False

# Function to speak text
def speak(text):
    engine.say(text)
    engine.runAndWait()

# Function to play the MP3 file
def play_mp3(file_path):
    pygame.mixer.init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()

# Function to stop the MP3 file
def stop_mp3():
    pygame.mixer.music.stop()

# Function to check for "stop" command while MP3 is playing
def listen_for_stop():
    global is_playing_mp3
    while is_playing_mp3:
        with sr.Microphone(device_index=2) as source:
            try:
                audio = recognizer.listen(source, timeout=2)
                command = recognizer.recognize_google(audio)
                logging.info(f"Listening for stop: User said: {command}")

                if "stop" in command.lower():
                    logging.info("Command 'stop' recognized. Stopping the MP3...")
                    stop_mp3()
                    is_playing_mp3 = False
                    return

            except sr.UnknownValueError:
                # Ignore unknown value errors
                continue
            except sr.RequestError as e:
                logging.error(f"Google Speech Recognition request failed; {e}")
                continue
            except sr.WaitTimeoutError:
                # Timeout is expected, so ignore it
                continue

# Function to handle the special command
def handle_special_command():
    global is_playing_mp3
    speak("Welcome home, sir.")
    play_mp3("intro.mp3")
    is_playing_mp3 = True
    # Continuously check for stop command while the MP3 is playing
    listen_for_stop()

# Function to handle shutdown command
def handle_shutdown_command():
    global is_shutdown
    speak("Shutting down, sir.")
    is_shutdown = True
    # Pass /bye to the AI
    result = chain.invoke({
        "context": initial_prompt, 
        "question": "/bye"
    }).strip()
    logging.info(f"ARGOS says: {result}")
    speak(result)

# Function to handle browser commands
def handle_browser_command(query):
    speak("Researching now, sir.")
    webbrowser.open(f"https://www.google.com/search?q={query}")

# Function to handle YouTube command
def handle_youtube_command():
    speak("Opening YouTube now, sir.")
    webbrowser.open("https://www.youtube.com")

# Function to listen to the microphone and interact with ARGOS
def listen_and_respond():
    global is_playing_mp3, is_shutdown
    is_playing_mp3 = False
    is_shutdown = False
    context = initial_prompt

    while not is_shutdown:
        with sr.Microphone(device_index=2) as source:
            if not is_playing_mp3:
                logging.info("Adjusting for ambient noise...")
                recognizer.adjust_for_ambient_noise(source, duration=5)  # Adjust for background noise once

            logging.info("Listening...")
            try:
                audio = recognizer.listen(source, timeout=5)  # Set timeout for listening
                command = recognizer.recognize_google(audio)
                logging.info(f"User said: {command}")

                if is_playing_mp3:
                    # MP3 is playing, stop-checking is handled in listen_for_stop function
                    continue

                if "home" in command.lower():
                    logging.info("Special command 'home' recognized. Executing special actions...")
                    handle_special_command()
                    continue  # Resume listening after executing the special command

                if "shutdown" in command.lower() or "shut down" in command.lower():
                    logging.info("Shutdown command recognized. Handling shutdown...")
                    handle_shutdown_command()
                    continue  # Skip further listening if shutdown is in progress

                if any(keyword in command.lower() for keyword in ["browser", "browse", "search for", "research"]):
                    # Extract the query after the command
                    query = command.lower()
                    for keyword in ["browser", "browse", "search for", "research"]:
                        if keyword in query:
                            query = query.replace(keyword, "").strip()
                            break
                    logging.info(f"Browser command recognized. Querying: {query}")
                    handle_browser_command(query)
                    continue  # Skip further listening while handling browser commands

                if "youtube" in command.lower():
                    logging.info("YouTube command recognized. Opening YouTube...")
                    handle_youtube_command()
                    continue  # Skip further listening while handling YouTube command

                # Query ARGOS with the recognized text
                result = chain.invoke({
                    "context": context, 
                    "question": command
                }).strip()
                logging.info(f"ARGOS says: {result}")

                # Speak the response from ARGOS
                speak(result)

                # Update context based on the latest response
                context = f"{context}\n{result}"

            except sr.UnknownValueError:
                # Skip the response if not understood
                continue
            except sr.RequestError as e:
                logging.error(f"Google Speech Recognition request failed; {e}")
                # Skip the response and continue listening
                continue
            except sr.WaitTimeoutError:
                # Timeout is expected, so ignore it
                continue
            except Exception as e:
                logging.error(f"An unexpected error occurred: {e}")
                # Skip the response and continue listening
                continue

if __name__ == "__main__":
    listen_and_respond()
