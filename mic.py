import speech_recognition as sr
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize the recognizer
recognizer = sr.Recognizer()

# Function to listen to the microphone and print recognized text
def listen_and_print():
    mic = sr.Microphone(device_index=3)  # Use the default microphone
    initial_noise_adjustment = True

    with mic as source:
        while True:
            if initial_noise_adjustment:
                logging.info("Adjusting for ambient noise...")
                recognizer.adjust_for_ambient_noise(source, duration=5)  # Adjust for background noise once
                initial_noise_adjustment = False
            
            logging.info("Listening...")
            try:
                # Listen for audio and recognize speech
                audio = recognizer.listen(source, timeout=5)  # Set timeout for listening
                command = recognizer.recognize_google(audio)
                logging.info(f"User said: {command}")
                print(f"Recognized: {command}")
            except sr.UnknownValueError:
                logging.error("Google Speech Recognition could not understand audio")
                print("Sorry, I did not understand that. Please try again.")
            except sr.RequestError as e:
                logging.error(f"Google Speech Recognition request failed; {e}")
                print("Sorry, there was an error with the speech recognition service. Please check your connection.")
            except sr.WaitTimeoutError:
                logging.warning("Listening timed out while waiting for phrase to start. Continuing...")
                print("Listening timed out. Please try speaking again.")
            except Exception as e:
                logging.error(f"An unexpected error occurred: {e}")
                print("An unexpected error occurred. Please try again.")

if __name__ == "__main__":
    listen_and_print()
