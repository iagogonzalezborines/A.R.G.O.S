import subprocess

def ollama_chat(user_input: str, context_text: str) -> str:
    """
    Ejecuta tinyllama en modo run para interacción conversacional mínima.
    """
    try:
        # Prepara el prompt combinando contexto + usuario
        prompt = f"{context_text}\nUser: {user_input}\nAI:"
        # Ejecuta ollama run tinyllama con input
        result = subprocess.run(
            ["ollama", "run", "tinyllama", "--stdin"],
            input=prompt,
            capture_output=True,
            text=True,  # asegura UTF-8
            encoding="utf-8",
            check=True
        )
        output = result.stdout.strip()
        return output
    except subprocess.CalledProcessError as e:
        return f"[ERROR] Ollama call failed: {e}"
