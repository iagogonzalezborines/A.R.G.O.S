from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
import pyttsx3

# Initialize the model with the specified LLaMA model
model = OllamaLLM(model="llama3")

# Initialize text-to-speech engine
engine = pyttsx3.init()

# Configure the voice (male voice in English)
engine.setProperty('voice', 'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-US_DAVID_11.0')

# Adjust speech rate and volume (optional)
engine.setProperty('rate', 150)
engine.setProperty('volume', 0.9)

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



Your initial greeting should be: "Hello sir, how are you doing today? Any projects I may assist you with?"
"""

# Invoke the model with the initial setup prompt
initial_response = model.invoke(initial_prompt).strip()
print(initial_response)

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

def speak(text):
    engine.say(text)
    engine.runAndWait()

def simulate_conversation(initial_context, questions):
    context = initial_context
    for question in questions:
        result = chain.invoke({
            "context": context, 
            "question": question
        }).strip()
        print(result)
        speak(result)  # ARGOS speaks the response
        # Update context based on the latest response
        context = f"{context}\n{result}"

# Test the model's response to multiple questions with updated context
initial_context = initial_response  # Use the initial response as context

# List of questions to test
questions = [
    "What is your name?",
    "Today I'm thinking about making some improvements to your functionality, maybe adding voice recognition capabilities. What do you think?",
    "What are you ARGOS? What do you do? What does your name stand for?",
    "How much water should I drink in a day?",
    "What is the capital of France?",
    "Can you code?"
]

simulate_conversation(initial_context, questions)
