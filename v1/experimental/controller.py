#!/usr/bin/env python3
"""
controller.py - ARGOS Controller con funciones esenciales
"""

import json
import logging
import os
import subprocess
from typing import Any, Dict

try:
    import pyttsx3
    import speech_recognition as sr

    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False
    logging.warning("Voice libraries not available")

# ---------------------------
# Configuración
# ---------------------------
ACTIONS_FILE = os.path.join(os.path.dirname(__file__), "actions.json")
MEMORY_FILE = os.path.join(os.path.dirname(__file__), "memory.txt")
CONTEXT_FILE = os.path.join(os.path.dirname(__file__), "context.txt")
# Ruta al context.txt en v1/memory/
ARGOS_CONTEXT_FILE = os.path.join(os.path.dirname(__file__), "..", "memory", "context.txt")
# Configuración del modelo AI
OLLAMA_MODEL = "svjack/qwen3-4b-instruct-2507-heretic"  # Modelo ARGOS

# Inicializar componentes de voz
if VOICE_AVAILABLE:
    recognizer = sr.Recognizer()
    tts_engine = pyttsx3.init()
    tts_engine.setProperty("rate", 150)
    tts_engine.setProperty("volume", 0.9)


# ---------------------------
# Funciones principales
# ---------------------------

def initialize() -> bool:
    """
    Inicializa ARGOS enviando el contexto desde v1/memory/context.txt a la IA.
    """
    try:
        # Leer el contexto desde v1/memory/context.txt
        if os.path.exists(ARGOS_CONTEXT_FILE):
            with open(ARGOS_CONTEXT_FILE, "r", encoding="utf-8") as f:
                context_content = f.read().strip()
            
            logging.info("Loading ARGOS context...")
            
            # Enviar contexto a la IA - debería responder "System online" naturalmente
            response = sendPrompt(context_content)
            
            logging.info(f"ARGOS initialization response: {response}")
            
            # La IA debería responder "System online" por sí misma según el contexto
            if "system online" in response.lower():
                return True
            else:
                logging.warning(f"Unexpected initialization response: {response}")
                return True  # Continuar de todas formas
        else:
            logging.error(f"Context file not found: {ARGOS_CONTEXT_FILE}")
            return False
            
    except Exception as e:
        logging.error(f"Error initializing ARGOS: {e}")
        return False

def sendPrompt(prompt: str) -> str:
    """
    Envía un prompt a ARGOS vía Ollama y devuelve la respuesta.
    """
    try:
        result = subprocess.run(
            ["ollama", "run", OLLAMA_MODEL],
            input=prompt,
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logging.error(f"Error communicating with ARGOS: {e}")
        return "I encountered an error processing your request, sir."
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return "I encountered an unexpected error, sir."


def executeAction(action: Dict[str, Any]) -> str:
    """
    Ejecuta una acción definida en actions.json.
    """
    action_name = action.get("name")
    args = action.get("args", {})

    # Cargar acciones desde actions.json
    if not os.path.exists(ACTIONS_FILE):
        return f"Actions file not found: {ACTIONS_FILE}"

    try:
        with open(ACTIONS_FILE, "r", encoding="utf-8") as f:
            actions_data = json.load(f)
    except Exception as e:
        return f"Error loading actions file: {e}"

    core_actions = actions_data.get("core_argos_actions", [])
    matched_action = next((a for a in core_actions if a.get("name") == action_name), None)

    if not matched_action:
        return f"Action '{action_name}' not found in actions.json"

    # Ejecutar la función definida en exec_code
    exec_code = matched_action.get("exec_code")
    if not exec_code:
        return f"No exec_code defined for action '{action_name}'"

    try:
        # Ejecutar el código de la acción en un entorno limitado
        result = eval(exec_code, {"__builtins__": None}, args)

        # Normalizar la respuesta
        if isinstance(result, str):
            return result
        try:
            return json.dumps(result, ensure_ascii=False)
        except Exception:
            return str(result)

    except Exception as e:
        return f"Error executing action '{action_name}': {e}"


def listen() -> str:
    """
    Obtiene audio del micrófono y lo convierte a texto.
    """
    if not VOICE_AVAILABLE:
        return "Voice input not available"

    with sr.Microphone() as source:
        try:
            logging.info("Adjusting for ambient noise...")
            recognizer.adjust_for_ambient_noise(source, duration=1)

            logging.info("Listening...")
            audio = recognizer.listen(source, timeout=5)

            command = recognizer.recognize_google(audio)
            logging.info(f"Command recognized: {command}")

            return command

        except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError) as e:
            logging.error(f"Speech recognition error: {e}")
            return "I didn't catch that, sir. Could you repeat?"
        except Exception as e:
            logging.error(f"Error in listen function: {e}")
            return "I encountered an error while listening, sir."


def argosSpeak(text: str) -> None:
    """
    Convierte la respuesta de ARGOS de texto a audio.
    """
    if VOICE_AVAILABLE:
        try:
            logging.info(f"Speaking: {text}")
            tts_engine.say(text)
            tts_engine.runAndWait()
        except Exception as e:
            logging.error(f"Error in speak function: {e}")
            print(f"ARGOS: {text}")  # Fallback to text
    else:
        print(f"ARGOS: {text}")


def interpreter(argos_response: str) -> str:
    """
    Interpreta la respuesta de ARGOS y decide si ejecutar acción o hablar.
    """
    response = argos_response.strip()

    # Si la respuesta contiene "SPEAK:", es un mensaje para el usuario
    if response.startswith("SPEAK:"):
        message = response[6:].strip()
        argosSpeak(message)
        return "spoke_to_user"

    # Si la respuesta es JSON, es una acción
    try:
        action = json.loads(response)
        if isinstance(action, dict) and "type" in action:
            if action["type"] == "action":
                result = executeAction(action)
                return f"action_executed: {result}"
            else:
                # Otros tipos de acciones (memory_write, etc.)
                return f"handled_{action['type']}"
    except json.JSONDecodeError:
        pass

    # Si es conversación normal, llamar a argosSpeak
    argosSpeak(response)
    return "conversation_handled"
