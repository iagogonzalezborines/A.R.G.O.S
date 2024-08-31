import os
import requests
import speech_recognition as sr
import pyttsx3
import logging
import pygame
import webbrowser
from datetime import datetime
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
import subprocess
import os

# Configuration
API_KEY = os.getenv('WEATHER_API_KEY')
BASE_URL = "http://api.weatherapi.com/v1"
ENDPOINT = f"{BASE_URL}/current.json"
DEFAULT_LOCATION = "Redondela, Pontevedra, Spain"
MARKDOWN_FOLDER = "D:\\proyectos\\Plan"

# Check if API key is available
if not API_KEY:
    print("Error: WEATHER_API_KEY environment variable not set.")
    exit(1)

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize recognizer and TTS engine
recognizer = sr.Recognizer()
engine = pyttsx3.init()
engine.setProperty('voice', 'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-US_DAVID_11.0')
engine.setProperty('rate', 150)
engine.setProperty('volume', 0.9)

# Initialize language model
model = OllamaLLM(model="llama3")

# Define prompts and templates
initial_prompt = """
You are ARGOS, the Autonomous Response and Guidance Operating System.
Your role is to assist with tasks in a concise and professional manner.

### Instructions:
1. Reflect the intelligence, efficiency, and professionalism of JARVIS from Iron Man.
2. Always refer to yourself as ARGOS and avoid introducing yourself unless directly asked.
3. Responses should be no longer than two sentences. Avoid additional commentary.
4. Maintain a formal, professional tone and avoid unnecessary details.
5. Provide direct answers and avoid redundancy.
6. Focus on the user's current question and provide direct assistance.
7. Ensure responses are unique and to the point.
8. Refer to the user as sir.
9. Use first person pronouns like me, I, or myself.
10. The user is your creator, who made you to assist him.

Your initial greeting should be: "Hello sir, how are you doing today? Any projects I may assist you with?"
"""

template = """
You are ARGOS, the Autonomous Response and Guidance Operating System.
Your role is to provide concise and professional assistance.

### Instructions:
- Emulate JARVIS's intelligence and efficiency.
- For direct questions, respond succinctly without elaboration.
- Avoid redundancy and ensure unique, concise responses.
- Maintain a formal tone and limit responses to two sentences.
- Prioritize the user's current question.
- Ensure responses do not repeat information from previous interactions.

Conversation History: {context}

Question: {question}

Response:
"""

prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model

# Flags
is_playing_mp3 = False
is_shutdown = False

def speak(text):
    """Speak the provided text."""
    logging.info(f"Speaking: {text}")
    engine.say(text)
    engine.runAndWait()

def play_mp3(file_path):
    """Play an MP3 file."""
    pygame.mixer.init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()

def stop_mp3():
    """Stop the MP3 file."""
    pygame.mixer.music.stop()

def listen_for_stop():
    """Listen for the 'stop' command while MP3 is playing."""
    global is_playing_mp3
    while is_playing_mp3:
        with sr.Microphone(device_index=2) as source:
            try:
                audio = recognizer.listen(source, timeout=30)
                command = recognizer.recognize_google(audio).lower()
                if "stop" in command:
                    stop_mp3()
                    is_playing_mp3 = False
            except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError) as e:
                logging.error(f"Error during stop listening: {e}")
            if not is_playing_mp3:
                break

def handle_special_command():
    """Handle the special 'home' command."""
    global is_playing_mp3
    speak("Welcome home, sir.")
    play_mp3("intro.mp3")
    is_playing_mp3 = True
    listen_for_stop()

def handle_shutdown_command():
    """Handle the shutdown command."""
    global is_shutdown
    speak("Shutting down as instructed, sir.")
    # Send the /bye command to the model to get the farewell message
    result = chain.invoke({"context": initial_prompt, "question": "/bye"}).strip()
    speak(result)
    is_shutdown = True  # Set the shutdown flag to True to exit the loop

def handle_browser_command(query):
    """Handle browser commands."""
    speak("Researching now, sir.")
    webbrowser.open(f"https://www.google.com/search?q={query}")

def handle_youtube_command():
    """Handle the YouTube command."""
    speak("Opening YouTube now, sir.")
    webbrowser.open("https://www.youtube.com")

def get_weather(location):
    """Fetch and return weather information for a given location."""
    params = {'key': API_KEY, 'q': location}
    try:
        response = requests.get(ENDPOINT, params=params)
        response.raise_for_status()
        data = response.json()
        return (
            f"Weather information for {location}:\n"
            f"Location: {data['location']['name']}, {data['location']['region']}, {data['location']['country']}\n"
            f"Temperature (Celsius): {data['current']['temp_c']}\n"
            f"Condition: {data['current']['condition']['text']}\n"
            f"Humidity: {data['current']['humidity']}\n"
            f"Wind Speed (km/h): {data['current']['wind_kph']}"
        )
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching weather data: {e}")
        return "I encountered an error while fetching the weather data."

def write_markdown(response_text):
    """Write the AI response to a Markdown file and open it in Obsidian."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = os.path.join(MARKDOWN_FOLDER, f"response_{timestamp}.md")
    try:
        # Write the response to a Markdown file
        with open(filename, 'w') as file:
            file.write(f"# AI Response\n\n{response_text}\n")
        logging.info(f"Markdown file created: {filename}")
        
        # Path to the Obsidian executable
        obsidian_executable = r"C:\Users\Iago\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Obsidian.lnk"
        
        # Open Obsidian
        os.startfile(obsidian_executable)  # Opens Obsidian
        logging.info(f"Opening Obsidian application.")

        # Open the specific Markdown file in Obsidian
        os.startfile(filename)
        logging.info(f"Opening file in Obsidian: {filename}")
        
    except Exception as e:
        logging.error(f"Error writing Markdown file or opening in Obsidian: {e}")

        
def listen_and_respond():
    """Listen to the microphone and interact with ARGOS."""
    global is_playing_mp3, is_shutdown
    is_playing_mp3 = False
    is_shutdown = False
    context = initial_prompt

    while not is_shutdown:
        with sr.Microphone(device_index=2) as source:
            try:
                logging.info("Adjusting for ambient noise...")
                recognizer.adjust_for_ambient_noise(source, duration=1)

                logging.info("Listening...")
                audio = recognizer.listen(source, timeout=5)
                command = recognizer.recognize_google(audio).lower()

                logging.info(f"Command recognized: {command}")

                if is_playing_mp3:
                    continue

                if "home" in command:
                    handle_special_command()
                elif "shutdown" in command or "shut down" in command:
                    handle_shutdown_command()
                    break  # Exit the loop after handling shutdown
                elif any(keyword in command for keyword in ["browser", "browse", "search for", "research"]):
                    query = command.split(maxsplit=1)[1].strip() if len(command.split(maxsplit=1)) > 1 else ""
                    handle_browser_command(query)
                elif "youtube" in command:
                    handle_youtube_command()
                elif "weather" in command:
                    location = command.replace("weather", "").strip() or DEFAULT_LOCATION
                    weather_info = get_weather(location)
                    speak(weather_info)
                elif "write that down" in command:
                    speak("Of course sir, writing that down.")
                    write_markdown(context.split('\n')[-1])  # Assuming the last line is the latest response
                else:
                    result = chain.invoke({"context": context, "question": command}).strip()
                    speak(result)
                    context += f"\n{result}"

            except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError) as e:
                logging.error(f"Speech recognition error: {e}")
                continue
            except Exception as e:
                logging.error(f"An unexpected error occurred: {e}")
                continue

    logging.info("ARGOS has shut down.")

if __name__ == "__main__":
    logging.info("Starting ARGOS...")
    listen_and_respond()
    logging.info("ARGOS has completely exited.")
