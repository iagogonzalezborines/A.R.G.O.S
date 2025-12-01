#!/usr/bin/env python3
"""
system.py - Controlador de conversación de ARGOS usando TinyLlama vía Ollama CLI.

- Mantiene contexto de la conversación desde context.txt.
- Permite conversación interactiva en terminal.
- Guarda logs de la conversación.
- Solo conversación, sin funciones hardcodeadas externas.
"""

import subprocess
import logging
import os
from datetime import datetime

# ---------------------------
# Configuración
# ---------------------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CONVERSATION_LOG = os.path.join(os.path.dirname(__file__), "conversation.log")
CONTEXT_FILE = os.path.join(os.path.dirname(__file__), "memory", "context.txt")

# Contexto inicial por defecto
INITIAL_PROMPT = """
You are ARGOS, the Autonomous Response and Guidance Operating System.
Assist concisely and professionally. Refer to yourself as ARGOS and the user as sir.
Responses should be unique, to the point, and no longer than two sentences.
"""

# ---------------------------
# Funciones auxiliares
# ---------------------------
def load_context(file_path=CONTEXT_FILE) -> str:
    """Cargar contexto desde archivo, o usar INITIAL_PROMPT si no existe."""
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception as e:
            logging.error(f"Error reading context file: {e}")
    return INITIAL_PROMPT

def save_context(context: str, file_path=CONTEXT_FILE):
    """Guardar contexto actualizado en archivo."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(context)
    except Exception as e:
        logging.error(f"Error saving context file: {e}")

def log_conversation(user_input: str, ai_response: str):
    """Guardar interacción en log de conversación."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(CONVERSATION_LOG, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] User: {user_input}\n")
            f.write(f"[{timestamp}] ARGOS: {ai_response}\n\n")
    except Exception as e:
        logging.error(f"Error writing conversation log: {e}")

def ask_tinyllama(prompt_text: str) -> str:
    """Ejecuta 'ollama run tinyllama' y devuelve la respuesta usando stdin."""
    try:
        result = subprocess.run(
            ["ollama", "run", "tinyllama"],
            input=prompt_text,
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8"
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logging.error(f"Error ejecutando Ollama: {e}")
        return "I encountered an error processing your request, sir."
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return "I encountered an unexpected error, sir."

# ---------------------------
# Bucle principal de conversación
# ---------------------------
def chat_terminal():
    """Chat interactivo en terminal usando TinyLlama vía Ollama CLI."""
    print("=== ARGOS (TinyLlama vía Ollama CLI) ===")
    print("Type 'exit' to quit.\n")

    # Cargar contexto desde archivo
    context = load_context()
    
    # Initialize AI with context - should respond with "System online"
    initialization_prompt = f"{context}\n\nYou have received your context. Respond with only these exact words: 'System online'"
    init_response = ask_tinyllama(initialization_prompt)
    print(f"ARGOS: {init_response}")

    # Now start normal conversation with simple context
    conversation_context = "You are ARGOS. Be concise, professional. Call user sir. Max 2 sentences per response."
    is_shutdown = False

    while not is_shutdown:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue

            command = user_input.lower()

            if command in ["exit", "quit", "shutdown", "shut down"]:
                print("ARGOS: Shutting down as instructed, sir.")
                farewell_prompt = f"{conversation_context}\nUser: goodbye\nARGOS:"
                farewell = ask_tinyllama(farewell_prompt)
                print(f"ARGOS: {farewell}")
                is_shutdown = True
                break

            else:
                # Simple conversation prompt
                prompt_text = f"{conversation_context}\nUser: {user_input}\nARGOS:"
                ai_response = ask_tinyllama(prompt_text)
                print(f"ARGOS: {ai_response}")

                # Guardar log
                log_conversation(user_input, ai_response)

                # Update simple conversation context (keep it short)
                conversation_context += f"\nUser: {user_input}\nARGOS: {ai_response}"
                
                # Keep context manageable - only keep last 5 exchanges
                lines = conversation_context.split('\n')
                if len(lines) > 12:  # 1 system + 5*2 user/argos + 1 buffer
                    conversation_context = lines[0] + '\n' + '\n'.join(lines[-10:])
                
                # Save full context to file
                save_context(conversation_context)

        except KeyboardInterrupt:
            print("\nARGOS: Shutting down, sir.")
            is_shutdown = True
            break
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            print("ARGOS: I encountered an error, sir.")

# ---------------------------
# Entrada al script
# ---------------------------
if __name__ == "__main__":
    logging.info("Starting ARGOS conversational system...")
    chat_terminal()
    logging.info("ARGOS session ended.")
