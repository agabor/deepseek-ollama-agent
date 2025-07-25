# Simple Coding Agent for Ollama

A lightweight coding assistant that interfaces with Ollama's DeepSeek-Coder-v2:16b model, providing Aider-like functionality with basic file read/write operations.

## Requirements

Create a `requirements.txt` file:

```
requests>=2.31.0
rich>=13.0.0
pathlib
```

## Installation

1. **Install Ollama** (if not already installed):
   ```bash
   # On macOS
   brew install ollama
   
   # On Linux
   curl -fsSL https://ollama.com/install.sh | sh
   
   # On Windows, download from https://ollama.com/download
   ```

2. **Start Ollama service**:
   ```bash
   ollama serve
   ```

3. **Pull the DeepSeek Coder model**:
   ```bash
   ollama pull deepseek-coder-v2:16b
   ```

4. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Optional: Create custom model with Modelfile**:
   ```bash
   # Save the Modelfile as 'Modelfile'
   ollama create coding-assistant -f Modelfile
   ```
   
   Then modify the `model_name` in the Python script to `"coding-assistant"`.

## Usage

Run the coding agent:

```bash
python coding_agent.py
```

### Commands

- **Regular chat**: Just type your coding questions or requests
- **`/clear`**: Clear conversation history
- **`/help`**: Show available commands
- **`exit`, `quit`, `bye`**: End the session

### Example Interactions

```
You: Create a simple React component for a header with navigation

🤖 Assistant: I'll create a React header component with navigation for you.

📖 Read file: src/components/Header.tsx
💾 Wrote file: src/components/Header.tsx

I've created a Header component with navigation...
```

```
You: Add dark mode toggle to the header component

🤖 Assistant: I'll add a dark mode toggle to your header component.

📖 Read file: src/components/Header.tsx
💾 Wrote file: src/components/Header.tsx

I've updated the Header component to include a dark mode toggle...
```

## Features

- **File Operations**: Read and write files with full path support
- **Rich Terminal UI**: Syntax highlighting and formatted output
- **Conversation Memory**: Maintains context throughout the session
- **Error Handling**: Graceful handling of file system errors
- **Progress Indicators**: Visual feedback for AI processing

## Architecture

The agent works by:

1. **Parsing tool calls** from the AI response using regex
2. **Executing file operations** (read/write) on the local filesystem  
3. **Providing results** back to the AI for context
4. **Maintaining conversation** history for coherent interactions

## Customization

You can customize the agent by:

- **Modifying the system prompt** in `_build_system_prompt()`
- **Adding new tools** by extending the tool parsing and execution methods
- **Changing model parameters** in the Modelfile
- **Adjusting the base URL** for remote Ollama instances

## Limitations

- Only supports `read_file` and `write_to_file` tools
- No git integration or version control
- No syntax validation or linting
- No multi-file refactoring capabilities
- Limited to text-based file operations

This is a minimal implementation focused on basic file operations. For more advanced features, consider extending the tool set or using full-featured alternatives like Aider.
