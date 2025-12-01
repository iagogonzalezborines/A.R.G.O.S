#!/usr/bin/env python3
"""
main.py - ARGOS Main Executable
Punto de entrada principal del sistema ARGOS
"""

import os
import sys
import logging
from controller import listen, sendPrompt, interpreter, argosSpeak

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def start_voice_mode():
    """Modo de operación por voz"""
    from controller import initialize
    
    print("Initializing ARGOS...")
    if not initialize():
        print("ERROR: Failed to initialize ARGOS system")
        return
    
    print("ARGOS: System online. Voice mode activated.")
    argosSpeak("System online. Voice mode activated.")
    
    is_shutdown = False
    
    while not is_shutdown:
        try:
            # Escuchar comando del usuario
            comando = listen()
            if "shutdown" in comando.lower() or "exit" in comando.lower():
                argosSpeak("Shutting down as instructed, sir.")
                is_shutdown = True
                break
                
            # Enviar comando a ARGOS IA
            respuesta = sendPrompt(comando)
            
            # Interpretar respuesta y actuar
            resultado = interpreter(respuesta)
            
            logging.info(f"Interpreter result: {resultado}")
            
        except KeyboardInterrupt:
            argosSpeak("Shutting down, sir.")
            is_shutdown = True
        except Exception as e:
            logging.error(f"Error in voice mode: {e}")
            argosSpeak("I encountered an error, sir.")

def start_text_mode():
    """Modo de operación por texto"""
    from controller import initialize
    
    print("Initializing ARGOS...")
    if not initialize():
        print("ERROR: Failed to initialize ARGOS system")
        return
    
    print("ARGOS: System online. Text mode activated.")
    
    is_shutdown = False
    
    while not is_shutdown:
        try:
            # Obtener comando por texto
            comando = input("You: ").strip()
            if not comando:
                continue
                
            if comando.lower() in ["shutdown", "exit", "quit"]:
                print("ARGOS: Shutting down as instructed, sir.")
                is_shutdown = True
                break
            
            # Enviar comando a ARGOS IA
            respuesta = sendPrompt(comando)
            
            # Interpretar respuesta y actuar
            resultado = interpreter(respuesta)
            
            logging.info(f"Interpreter result: {resultado}")
            
        except KeyboardInterrupt:
            print("\nARGOS: Shutting down, sir.")
            is_shutdown = True
        except Exception as e:
            logging.error(f"Error in text mode: {e}")
            print("ARGOS: I encountered an error, sir.")

def main():
    """
    Función principal del sistema ARGOS
    """
    print("=== ARGOS (Autonomous Response and Guidance Operating System) ===")
    print("Initializing system...\n")
    
    try:
        # Determinar modo de operación
        mode = input("Select mode - (1) Voice Mode, (2) Text Mode: ").strip()
        
        if mode == "1":
            print("Starting Voice Mode...")
            start_voice_mode()
        elif mode == "2":
            print("Starting Text Mode...")
            start_text_mode()
        else:
            print("Invalid mode selected. Starting Text Mode by default...")
            start_text_mode()
            
    except KeyboardInterrupt:
        print("\nARGOS: Shutting down, sir.")
        return 0
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        print(f"FATAL ERROR: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())