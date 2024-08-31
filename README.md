
# ARGOS: Autonomous Response and Guidance Operating System

## Overview

**ARGOS** (Autonomous Response and Guidance Operating System) is a voice-activated assistant designed to assist with various tasks in a concise and professional manner, inspired by the intelligence and efficiency of JARVIS from Iron Man. ARGOS can perform a wide range of tasks, including browsing the web, fetching weather information, managing markdown notes, and more, all through voice commands.

## Features

- **Voice Recognition**: Listen for commands and respond accordingly.
- **Text-to-Speech (TTS)**: ARGOS speaks with a professional tone using Microsoft's TTS engine.
- **Web Integration**: Search the web or open YouTube via voice commands.
- **Weather Fetching**: Retrieve current weather information for a specified location.
- **Markdown Note Taking**: Automatically write down responses to markdown files and open them in Obsidian.
- **MP3 Playback**: Play MP3 files on command.
- **Custom Language Model Integration**: Leverages the Ollama language model to generate responses.

## Installation

### Prerequisites

- **Python 3.x**
- **Virtual Environment** (recommended)
- **Microsoft Speech SDK** (for TTS)
- **Obsidian** (for note management)
- **Weather API Key**: Sign up at [WeatherAPI](https://www.weatherapi.com/) to get your API key.

### Libraries

Ensure you have the following Python libraries installed:

```sh
pip install requests speechrecognition pyttsx3 pygame langchain_ollama
```

### Clone the Repository

```sh
git clone https://github.com/yourusername/argos.git
cd argos
```

### Configuration

1. **API Key**: Set your weather API key as an environment variable named `WEATHER_API_KEY`.

2. **Paths**: Adjust paths in the code if needed:
   - **Markdown Folder**: Update `MARKDOWN_FOLDER` to your desired location.
   - **Obsidian Executable**: Ensure the path to Obsidian is correct.

## Usage

To start ARGOS, simply run the main script:

```sh
python argos.py
```

ARGOS will initialize and start listening for voice commands. You can interact with ARGOS using natural language commands such as:

- "What's the weather in New York?"
- "Open YouTube."
- "Search for Python tutorials."
- "Write that down."

### Command Examples

- **Home Command**: ARGOS plays an introductory MP3 file and greets you.
- **Weather Command**: ARGOS fetches and reads out the current weather.
- **Markdown Notes**: ARGOS will write down its last response to a markdown file and open it in Obsidian.
- **Shutdown**: ARGOS shuts down gracefully when asked.

## Customization

### Ambient Noise Adjustment

To reduce the time spent adjusting for ambient noise, the `duration` in the `recognizer.adjust_for_ambient_noise()` can be tweaked. By default, it's set to 1 second for quick response.

### Voice & TTS

ARGOS uses the TTS engine with a specific voice. You can change the voice by modifying the `voice` property in the code.

### Obsidian Integration

If you use a different markdown editor, adjust the path to the executable accordingly.

## Troubleshooting

- **Speech Recognition Errors**: Ensure your microphone is properly configured and has minimal background noise.
- **API Errors**: Make sure your `WEATHER_API_KEY` is correct and set as an environment variable.
- **File Not Opening in Obsidian**: Ensure the path to Obsidian is correct and the program is installed properly.

## Contribution

Feel free to fork this repository and contribute. Any help in enhancing ARGOS is welcome!

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Inspired by the JARVIS AI from Iron Man.
- Powered by [Ollama](https://ollama.com/).
- Weather data provided by [WeatherAPI](https://www.weatherapi.com/).

---
