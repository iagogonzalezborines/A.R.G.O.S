#!/usr/bin/env python3
"""
core_argos_actions.py - Funciones principales para las acciones de ARGOS
"""

import json
import os
import logging
import subprocess
import sys
from typing import Any, Dict, List, Optional


# Rutas de archivos
ACTIONS_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "memory", "actions.json")


def access_actions(action_name: Optional[str] = None, include_internal: bool = False) -> Dict[str, Any]:
    """
    Retrieve the list of available actions or the full definition of a specific action from actions.json.
    
    Args:
        action_name: Name of the action to retrieve; if omitted, return list of all action names
        include_internal: Include internal/hidden actions when listing (default: False)
    
    Returns:
        Dict containing action information or list of actions
    """
    try:
        if not os.path.exists(ACTIONS_FILE):
            return {"error": f"Actions file not found: {ACTIONS_FILE}"}
        
        with open(ACTIONS_FILE, "r", encoding="utf-8") as f:
            actions_data = json.load(f)
        
        # Handle new JSON structure with source_file
        core_actions_data = actions_data.get("actions", {}).get("core_argos_actions", {})
        auto_actions_data = actions_data.get("actions", {}).get("auto_updated_actions", {})
        
        # Extract actions arrays
        core_actions = core_actions_data.get("actions", []) if isinstance(core_actions_data, dict) else core_actions_data
        auto_actions = auto_actions_data.get("actions", []) if isinstance(auto_actions_data, dict) else auto_actions_data
        
        if action_name:
            # Search in core_actions first
            for action in core_actions:
                if action.get("name") == action_name:
                    return action
            # Search in auto_updated_actions
            for action in auto_actions:
                if action.get("name") == action_name:
                    return action
            return {"error": f"Action '{action_name}' not found"}
        else:
            # Return list of all actions from both categories
            action_list = []
            
            # Add core actions
            for action in core_actions:
                if not include_internal or not action.get("internal", False):
                    action_list.append({
                        "name": action.get("name"),
                        "description": action.get("description"),
                        "category": "core_argos_actions"
                    })
            
            # Add auto_updated actions
            for action in auto_actions:
                if not include_internal or not action.get("internal", False):
                    action_list.append({
                        "name": action.get("name"),
                        "description": action.get("description"),
                        "category": "auto_updated_actions"
                    })
            
            return {"actions": action_list}
    
    except Exception as e:
        logging.error(f"Error accessing actions: {e}")
        return {"error": f"Error accessing actions: {e}"}


def read_file(path: str) -> Dict[str, Any]:
    """
    Read the content of a file.
    
    Args:
        path: Path to the file
    
    Returns:
        Dict containing file content or error message
    """
    try:
        # Si no es absoluto, buscar en el directorio A.R.G.O.S
        if not os.path.isabs(path):
            argos_root = get_argos_root()
            path = os.path.join(argos_root, path)
        
        if not os.path.exists(path):
            return {"error": f"File not found: {path}"}
        
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        
        return {
            "success": True,
            "message": "-success",
            "path": path,
            "content": content,
            "size": len(content)
        }
    
    except Exception as e:
        logging.error(f"Error reading file {path}: {e}")
        return {"error": f"Error reading file: {e}"}


def write_file(path: str, content: str) -> Dict[str, Any]:
    """
    Write content to a file (overwrites existing content).
    
    Args:
        path: Path to the file
        content: Content to write
    
    Returns:
        Dict containing operation result
    """
    try:
        # Si no es absoluto, usar el directorio A.R.G.O.S como base
        if not os.path.isabs(path):
            argos_root = get_argos_root()
            path = os.path.join(argos_root, path)
        
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        
        # Verificar si es un archivo .py para triggear restart
        if path.endswith('.py'):
            # Importar la función de restart del controller
            try:
                controller_path = os.path.join(os.path.dirname(__file__), "..")
                if controller_path not in sys.path:
                    sys.path.append(controller_path)
                
                from controller import restartOfSystem
                
                # Obtener el nombre del archivo para el motivo del restart
                file_name = os.path.basename(path)
                restart_reason = f"Python file modified: {file_name}"
                restart_success = restartOfSystem(restart_reason)
                
                return {
                    "success": True,
                    "message": "-success",
                    "path": path,
                    "size": len(content),
                    "restart_triggered": True,
                    "restart_success": restart_success,
                    "restart_reason": restart_reason,
                    "file_completely_replaced": True
                }
            except ImportError as e:
                logging.warning(f"Could not import restartOfSystem: {e}")
        
        return {
            "success": True,
            "message": "-success",
            "path": path,
            "size": len(content),
            "restart_triggered": False
        }
    
    except Exception as e:
        logging.error(f"Error writing file {path}: {e}")
        return {"error": f"Error writing file: {e}"}


def update_actions_json(action_definition: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new action or update an existing one in actions.json.
    
    Args:
        action_definition: Full JSON definition of the action
    
    Returns:
        Dict containing operation result
    """
    try:
        if not os.path.exists(ACTIONS_FILE):
            return {"error": f"Actions file not found: {ACTIONS_FILE}"}
        
        # Validar que el action_definition tiene los campos requeridos
        required_fields = ["name", "description", "exec_type", "exec_code"]
        for field in required_fields:
            if field not in action_definition:
                return {"error": f"Missing required field: {field}"}
        
        with open(ACTIONS_FILE, "r", encoding="utf-8") as f:
            actions_data = json.load(f)
        
        # Handle new JSON structure
        core_actions_data = actions_data.get("actions", {}).get("core_argos_actions", {})
        core_actions = core_actions_data.get("actions", []) if isinstance(core_actions_data, dict) else core_actions_data
        action_name = action_definition.get("name")
        
        # Buscar si la acción ya existe
        existing_index = None
        for i, action in enumerate(core_actions):
            if action.get("name") == action_name:
                existing_index = i
                break
        
        if existing_index is not None:
            # Actualizar acción existente
            core_actions[existing_index] = action_definition
            operation = "updated"
        else:
            # Agregar nueva acción
            core_actions.append(action_definition)
            operation = "created"
        
        # Update the structure preserving source_file
        if isinstance(core_actions_data, dict):
            actions_data["actions"]["core_argos_actions"]["actions"] = core_actions
        else:
            actions_data["actions"]["core_argos_actions"] = core_actions
        
        with open(ACTIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(actions_data, f, indent=4, ensure_ascii=False)
        
        return {
            "success": True,
            "message": "-success",
            "action_name": action_name,
            "operation": operation,
            "total_actions": len(core_actions)
        }
    
    except Exception as e:
        logging.error(f"Error updating actions.json: {e}")
        return {"error": f"Error updating actions: {e}"}


def request_file(file_name: str, reason: str) -> str:
    """
    Request file content from user/program if missing.
    
    Args:
        file_name: Name of the file
        reason: Why the file is needed
    
    Returns:
        String message to speak to user
    """
    return f"Requesting file '{file_name}' because {reason}"


def execute_cmd(command: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Execute a command in CMD at the project root directory and return the output.
    
    Args:
        command: The command to execute in CMD
        timeout: Timeout in seconds (default: 30)
    
    Returns:
        Dict containing command execution result
    """
    try:
        argos_root = get_argos_root()
        
        logging.info(f"Executing command: {command} in {argos_root}")
        
        # Ejecutar comando en CMD desde la raíz del proyecto
        result = subprocess.run(
            command,
            shell=True,
            cwd=argos_root,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8"
        )
        
        # Preparar respuesta
        cmd_output = {
            "success": True,
            "message": "-success",
            "command": command,
            "exit_code": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "working_directory": argos_root
        }
        
        # Enviar resultado a la IA usando sendPrompt del controller
        try:
            # Importar sendPrompt del controller
            controller_path = os.path.join(os.path.dirname(__file__), "..")
            if controller_path not in sys.path:
                sys.path.append(controller_path)
            
            from controller import sendPrompt
            
            # Crear prompt informativo para la IA
            if result.returncode == 0:
                ai_prompt = f"Command '{command}' executed successfully. Output: {result.stdout.strip()}"
            else:
                ai_prompt = f"Command '{command}' failed with exit code {result.returncode}. Error: {result.stderr.strip()}"
            
            # Enviar a la IA
            ai_response = sendPrompt(ai_prompt)
            cmd_output["ai_response"] = ai_response
            
        except ImportError as e:
            logging.warning(f"Could not import sendPrompt: {e}")
            cmd_output["ai_response"] = "Could not send result to AI"
        
        return cmd_output
        
    except subprocess.TimeoutExpired:
        return {
            "error": f"Command '{command}' timed out after {timeout} seconds"
        }
    except Exception as e:
        logging.error(f"Error executing command '{command}': {e}")
        return {
            "error": f"Error executing command: {e}"
        }


def get_argos_root() -> str:
    """
    Get the root A.R.G.O.S folder path.
    
    Returns:
        str: Absolute path to A.R.G.O.S root folder
    """
    # Navegar desde experimental/actions/ hasta A.R.G.O.S/
    current_dir = os.path.dirname(os.path.abspath(__file__))
    argos_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
    return argos_root


def get_file_tree(max_depth: int = 10, include_hidden: bool = False) -> Dict[str, Any]:
    """
    Return the file structure of the A.R.G.O.S folder in JSON format.
    
    Args:
        max_depth: Maximum depth to traverse (default: 10)
        include_hidden: Include hidden files and folders (default: False)
    
    Returns:
        Dict containing file tree structure
    """
    try:
        argos_root = get_argos_root()
        
        def build_tree(path: str, current_depth: int = 0) -> Dict[str, Any]:
            if current_depth >= max_depth:
                return {"type": "directory", "truncated": True}
            
            items = {}
            try:
                for item in os.listdir(path):
                    if not include_hidden and item.startswith('.'):
                        continue
                    
                    item_path = os.path.join(path, item)
                    if os.path.isdir(item_path):
                        items[item] = {
                            "type": "directory",
                            "children": build_tree(item_path, current_depth + 1)
                        }
                    else:
                        items[item] = {
                            "type": "file",
                            "size": os.path.getsize(item_path)
                        }
            except PermissionError:
                return {"type": "directory", "error": "Permission denied"}
            
            return items
        
        tree = build_tree(argos_root)
        
        return {
            "success": True,
            "message": "-success",
            "root_path": argos_root,
            "tree": tree,
            "max_depth": max_depth,
            "include_hidden": include_hidden
        }
    
    except Exception as e:
        logging.error(f"Error building file tree: {e}")
        return {"error": f"Error building file tree: {e}"}


def find_file(filename: str, recursive: bool = True) -> Dict[str, Any]:
    """
    Search for files in the A.R.G.O.S root folder by name or pattern.
    
    Args:
        filename: Name or pattern of the file to search
        recursive: Search recursively in subdirectories (default: True)
    
    Returns:
        Dict containing found files and their paths
    """
    try:
        import fnmatch
        argos_root = get_argos_root()
        found_files = []
        
        def search_directory(path: str):
            try:
                for item in os.listdir(path):
                    if item.startswith('.'):  # Skip hidden files
                        continue
                    
                    item_path = os.path.join(path, item)
                    
                    # Check if file matches pattern
                    if os.path.isfile(item_path) and fnmatch.fnmatch(item, filename):
                        relative_path = os.path.relpath(item_path, argos_root)
                        found_files.append({
                            "name": item,
                            "path": item_path,
                            "relative_path": relative_path,
                            "size": os.path.getsize(item_path)
                        })
                    
                    # Recurse into directories if enabled
                    elif os.path.isdir(item_path) and recursive:
                        search_directory(item_path)
            
            except PermissionError:
                pass  # Skip directories we can't access
        
        search_directory(argos_root)
        
        return {
            "success": True,
            "message": "-success",
            "query": filename,
            "found_count": len(found_files),
            "files": found_files,
            "searched_root": argos_root
        }
    
    except Exception as e:
        logging.error(f"Error searching for file {filename}: {e}")
        return {"error": f"Error searching for file: {e}"}


def create_action(action_definition: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new action by adding it to auto_updated_actions in actions.json,
    writing the function to autoupdated_controller.py, and restarting the system.
    
    Args:
        action_definition: Full JSON definition of the action including exec_code
    
    Returns:
        Dict containing operation result
    """
    try:
        if not os.path.exists(ACTIONS_FILE):
            return {"error": f"Actions file not found: {ACTIONS_FILE}"}
        
        # Validar campos requeridos
        required_fields = ["name", "description", "exec_type", "exec_code"]
        for field in required_fields:
            if field not in action_definition:
                return {"error": f"Missing required field: {field}"}
        
        action_name = action_definition.get("name")
        
        # 1. Actualizar actions.json - agregar a auto_updated_actions
        with open(ACTIONS_FILE, "r", encoding="utf-8") as f:
            actions_data = json.load(f)
        
        # Handle new JSON structure
        auto_actions_data = actions_data.get("actions", {}).get("auto_updated_actions", {})
        auto_actions = auto_actions_data.get("actions", []) if isinstance(auto_actions_data, dict) else auto_actions_data
        
        # Buscar si la acción ya existe
        existing_index = None
        for i, action in enumerate(auto_actions):
            if action.get("name") == action_name:
                existing_index = i
                break
        
        if existing_index is not None:
            auto_actions[existing_index] = action_definition
            operation = "updated"
        else:
            auto_actions.append(action_definition)
            operation = "created"
        
        # Update the structure preserving source_file
        if isinstance(auto_actions_data, dict):
            actions_data["actions"]["auto_updated_actions"]["actions"] = auto_actions
        else:
            actions_data["actions"]["auto_updated_actions"] = auto_actions
        
        with open(ACTIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(actions_data, f, indent=4, ensure_ascii=False)
        
        # Devolver mensaje específico para guiar a la IA
        return {
            "success": True,
            "message": "-success action created proceed to modify file autoupdated_controller.py\n1.- access_actions\n2.- request_file\n3.- write_file",
            "action_name": action_name,
            "operation": operation,
            "next_steps": [
                "access_actions (check if actions.json was updated)",
                "request_file('autoupdated_controller.py', 'to add the new action function')", 
                "write_file('replace with new autoupdated_controller.py', 'with the new function code')"
            ]
        }
        
        # El resto del proceso ahora es manual para que la IA siga los pasos
    
    except Exception as e:
        logging.error(f"Error creating action '{action_name}': {e}")
        return {"error": f"Error creating action: {e}"}


# Diccionario de funciones disponibles para eval()
AVAILABLE_FUNCTIONS = {
    "access_actions": access_actions,
    "read_file": read_file,
    "write_file": write_file,
    "update_actions_json": update_actions_json,
    "request_file": request_file,
    "get_file_tree": get_file_tree,
    "find_file": find_file,
    "execute_cmd": execute_cmd,
    "create_action": create_action,
    "get_argos_root": get_argos_root
}