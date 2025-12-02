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

# Variables globales para mantener contexto
ARGOS_CONTEXT = ""
CONVERSATION_HISTORY = ""

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
    Inicializa ARGOS cargando el contexto desde v1/memory/context.txt.
    """
    global ARGOS_CONTEXT, CONVERSATION_HISTORY
    
    try:
        # Leer el contexto desde v1/memory/context.txt
        if os.path.exists(ARGOS_CONTEXT_FILE):
            with open(ARGOS_CONTEXT_FILE, "r", encoding="utf-8") as f:
                ARGOS_CONTEXT = f.read().strip()
            
            logging.info("Loading ARGOS context...")
            
            # Inicializar conversación con el contexto
            CONVERSATION_HISTORY = ""
            
            # Enviar contexto inicial para que la IA se identifique
            response = sendPrompt("You have been initialized. Confirm your identity.")
            
            logging.info(f"ARGOS initialization response: {response}")
            
            # La IA debería responder como ARGOS
            return True
        else:
            logging.error(f"Context file not found: {ARGOS_CONTEXT_FILE}")
            return False
            
    except Exception as e:
        logging.error(f"Error initializing ARGOS: {e}")
        return False

def sendPrompt(prompt: str) -> str:
    """
    Envía un prompt a ARGOS vía Ollama manteniendo el contexto y devuelve la respuesta.
    """
    global CONVERSATION_HISTORY
    
    try:
        # Construir el prompt completo con contexto + historial + nuevo prompt
        full_prompt = f"{ARGOS_CONTEXT}\n\n"
        
        if CONVERSATION_HISTORY:
            full_prompt += f"Conversation history:\n{CONVERSATION_HISTORY}\n\n"
        
        full_prompt += f"User: {prompt}\nARGOS:"
        
        result = subprocess.run(
            ["ollama", "run", OLLAMA_MODEL],
            input=full_prompt,
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
        )
        
        response = result.stdout.strip()
        
        # Actualizar historial de conversación
        CONVERSATION_HISTORY += f"User: {prompt}\nARGOS: {response}\n"
        
        # Mantener historial limitado (últimos 10 intercambios)
        lines = CONVERSATION_HISTORY.split('\n')
        if len(lines) > 20:  # 10 intercambios * 2 líneas cada uno
            CONVERSATION_HISTORY = '\n'.join(lines[-20:])
        
        return response
        
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

    # Ruta correcta al actions.json
    actions_file = os.path.join(os.path.dirname(__file__), "..", "memory", "actions.json")
    
    if not os.path.exists(actions_file):
        return f"Actions file not found: {actions_file}"

    try:
        with open(actions_file, "r", encoding="utf-8") as f:
            actions_data = json.load(f)
    except Exception as e:
        return f"Error loading actions file: {e}"

    # Obtener las categorías de acciones con su source_file
    core_actions_data = actions_data.get("actions", {}).get("core_argos_actions", {})
    auto_actions_data = actions_data.get("actions", {}).get("auto_updated_actions", {})
    
    # Extraer arrays de acciones y source_files
    core_actions = core_actions_data.get("actions", []) if isinstance(core_actions_data, dict) else core_actions_data
    auto_actions = auto_actions_data.get("actions", []) if isinstance(auto_actions_data, dict) else auto_actions_data
    
    core_source_file = core_actions_data.get("source_file", "") if isinstance(core_actions_data, dict) else ""
    auto_source_file = auto_actions_data.get("source_file", "") if isinstance(auto_actions_data, dict) else ""
    
    # Buscar la acción y determinar su categoría y source_file
    matched_action = None
    source_file = ""
    action_category = ""
    
    # Buscar en core_actions primero
    for action in core_actions:
        if action.get("name") == action_name:
            matched_action = action
            source_file = core_source_file
            action_category = "core_argos_actions"
            break
    
    # Si no se encuentra, buscar en auto_updated_actions
    if not matched_action:
        for action in auto_actions:
            if action.get("name") == action_name:
                matched_action = action
                source_file = auto_source_file
                action_category = "auto_updated_actions"
                break

    if not matched_action:
        return f"Action '{action_name}' not found in actions.json"

    # Ejecutar la función definida en exec_code
    exec_code = matched_action.get("exec_code")
    if not exec_code:
        return f"No exec_code defined for action '{action_name}'"

    try:
        import sys
        import importlib.util
        
        # Construir ruta absoluta al archivo fuente
        if source_file:
            # Convertir ruta relativa a absoluta
            if not os.path.isabs(source_file):
                # source_file es relativo al proyecto A.R.G.O.S
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # Subir desde experimental a A.R.G.O.S
                source_path = os.path.join(project_root, source_file)
            else:
                source_path = source_file
            
            # Importar dinámicamente el módulo
            if os.path.exists(source_path):
                spec = importlib.util.spec_from_file_location("action_module", source_path)
                action_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(action_module)
                
                # Crear safe_globals con las funciones del módulo
                safe_globals = {"__builtins__": {}}
                
                # Agregar todas las funciones públicas del módulo
                for attr_name in dir(action_module):
                    attr_value = getattr(action_module, attr_name)
                    if not attr_name.startswith('_') and callable(attr_value):
                        safe_globals[attr_name] = attr_value
                
                # Si el módulo tiene AVAILABLE_FUNCTIONS, usarlas también
                if hasattr(action_module, 'AVAILABLE_FUNCTIONS'):
                    safe_globals.update(action_module.AVAILABLE_FUNCTIONS)
            else:
                return f"Source file not found: {source_path}"
        else:
            # Fallback al método anterior si no hay source_file
            actions_path = os.path.join(os.path.dirname(__file__), "actions")
            if actions_path not in sys.path:
                sys.path.append(actions_path)
            
            from core_argos_actions import AVAILABLE_FUNCTIONS
            safe_globals = {"__builtins__": {}, **AVAILABLE_FUNCTIONS}
        
        # Ejecutar el código de la acción
        result = eval(exec_code, safe_globals, args)

        # Normalizar la respuesta
        if isinstance(result, dict):
            if "error" in result:
                return f"Action error: {result['error']}"
            elif "success" in result and result["success"]:
                return json.dumps(result, ensure_ascii=False, indent=2)
            else:
                return json.dumps(result, ensure_ascii=False, indent=2)
        elif isinstance(result, str):
            return result
        else:
            return str(result)

    except Exception as e:
        logging.error(f"Error executing action '{action_name}': {e}")
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

    # Si la respuesta contiene "SPEAK:", extraer solo esa parte
    if "SPEAK:" in response:
        # Encontrar la línea que empieza con SPEAK:
        lines = response.split('\n')
        for line in lines:
            if line.strip().startswith("SPEAK:"):
                message = line.strip()[6:].strip()
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

    # Si no hay SPEAK: ni es JSON, buscar si hay contenido útil después de /think
    if "/think" in response.lower():
        # Buscar contenido después de /think
        lines = response.split('\n')
        useful_content = []
        skip_think = False
        
        for line in lines:
            if line.strip().lower().startswith("/think"):
                skip_think = True
                continue
            elif skip_think and line.strip() and not line.strip().startswith("SPEAK:"):
                useful_content.append(line.strip())
        
        if useful_content:
            final_response = ' '.join(useful_content)
            argosSpeak(final_response)
            return "conversation_handled"

    # Si es conversación normal, llamar a argosSpeak
    argosSpeak(response)
    return "conversation_handled"


def restartOfSystem(reason: str = "file modification"):
    """
    Reinicia el sistema ARGOS cuando se modifican archivos .py durante la ejecución.
    
    Args:
        reason: Razón del reinicio (ej: "new action: fetch_webpage")
    
    Proceso:
    1. Termina ejecución actual
    2. Modifica context.txt: "System online" -> "System restarted, [reason]"
    3. Ejecuta main.py con nuevo contexto
    4. Restaura context.txt a su estado normal
    """
    global ARGOS_CONTEXT, CONVERSATION_HISTORY
    
    try:
        logging.info("Starting system restart process...")
        
        # 1. Leer el context.txt actual
        if not os.path.exists(ARGOS_CONTEXT_FILE):
            logging.error(f"Context file not found: {ARGOS_CONTEXT_FILE}")
            return False
        
        with open(ARGOS_CONTEXT_FILE, "r", encoding="utf-8") as f:
            original_context = f.read()
        
        # 2. Crear contexto modificado para reinicio
        restart_context = original_context.replace(
            "System online", 
            f"System restarted, {reason}"
        )
        
        # 3. Guardar contexto modificado
        with open(ARGOS_CONTEXT_FILE, "w", encoding="utf-8") as f:
            f.write(restart_context)
        
        logging.info("Context updated for restart")
        
        # 4. Reinicializar variables globales
        ARGOS_CONTEXT = restart_context
        CONVERSATION_HISTORY = ""
        
        # 5. Enviar contexto de reinicio a la IA
        response = sendPrompt(f"System has been restarted due to: {reason}. Confirm new status.")
        logging.info(f"Restart confirmation response: {response}")
        
        # 6. Restaurar context.txt a su estado original
        with open(ARGOS_CONTEXT_FILE, "w", encoding="utf-8") as f:
            f.write(original_context)
        
        # 7. Actualizar contexto global con el original
        ARGOS_CONTEXT = original_context
        
        logging.info("System restart completed successfully")
        argosSpeak("System restarted successfully, sir. New files are now operative.")
        
        return True
        
    except Exception as e:
        logging.error(f"Error during system restart: {e}")
        
        # En caso de error, intentar restaurar contexto original
        try:
            if 'original_context' in locals():
                with open(ARGOS_CONTEXT_FILE, "w", encoding="utf-8") as f:
                    f.write(original_context)
                ARGOS_CONTEXT = original_context
        except:
            pass
        
        argosSpeak("I encountered an error during system restart, sir.")
        return False


def detectFileModification(file_path: str) -> bool:
    """
    Detecta si un archivo .py ha sido modificado y debe reiniciar el sistema.
    
    Args:
        file_path: Ruta del archivo a verificar
        
    Returns:
        bool: True si el archivo es .py y requiere reinicio
    """
    try:
        if file_path.endswith('.py'):
            logging.info(f"Python file modification detected: {file_path}")
            return True
        return False
    except Exception as e:
        logging.error(f"Error detecting file modification: {e}")
        return False


def handleFileModification(file_path: str) -> str:
    """
    Maneja modificaciones de archivos y reinicia si es necesario.
    
    Args:
        file_path: Ruta del archivo modificado
        
    Returns:
        str: Resultado de la operación
    """
    try:
        if detectFileModification(file_path):
            logging.info(f"Initiating system restart due to modification: {file_path}")
            
            if restartOfSystem():
                return f"System restarted successfully due to {file_path} modification"
            else:
                return f"Failed to restart system after {file_path} modification"
        else:
            return f"File {file_path} modified but no restart required"
            
    except Exception as e:
        logging.error(f"Error handling file modification: {e}")
        return f"Error processing file modification: {e}"