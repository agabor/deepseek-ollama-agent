#!/usr/bin/env python3
"""
Simple Coding Agent for Ollama with DeepSeek-Coder-v2:16b
Similar interface to Aider but with basic file operations only.
"""

import json
import re
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests
from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.panel import Panel

console = Console()

class OllamaCodingAgent:
    def __init__(self, model_name: str = "deepseek-coder-v2:16b", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url
        self.conversation_history: List[Dict] = []
        self.system_prompt = self._build_system_prompt()
        
    def _build_system_prompt(self) -> str:
        return """You are a helpful coding assistant. You can read and write files to help with coding tasks.

Available tools:
1. <read_file><path>filepath</path></read_file> - Read the contents of a file
2. <write_to_file><path>filepath</path><content>file content</content></write_to_file> - Write content to a file

When using tools:
- Always use the exact XML format shown above
- Use relative paths from the current working directory
- For write_to_file, include the complete file content
- Only use these two tools, no others

When you need to read or write files, use the appropriate tool. Always explain what you're doing before using a tool."""

    def _call_ollama(self, messages: List[Dict]) -> str:
        """Make a request to Ollama API"""
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model_name,
                    "messages": messages,
                    "stream": False
                },
                timeout=60
            )
            response.raise_for_status()
            return response.json()["message"]["content"]
        except requests.exceptions.RequestException as e:
            console.print(f"[red]Error calling Ollama: {e}[/red]")
            return ""

    def _extract_tool_calls(self, text: str) -> List[Tuple[str, Dict]]:
        """Extract tool calls from the response text"""
        tools = []
        
        # Extract read_file calls
        read_pattern = r'<read_file>\s*<path>(.*?)</path>\s*</read_file>'
        for match in re.finditer(read_pattern, text, re.DOTALL):
            tools.append(("read_file", {"path": match.group(1).strip()}))
        
        # Extract write_to_file calls
        write_pattern = r'<write_to_file>\s*<path>(.*?)</path>\s*<content>(.*?)</content>\s*</write_to_file>'
        for match in re.finditer(write_pattern, text, re.DOTALL):
            tools.append(("write_to_file", {
                "path": match.group(1).strip(),
                "content": match.group(2).strip()
            }))
        
        return tools

    def _execute_read_file(self, path: str) -> str:
        """Execute read_file tool"""
        try:
            file_path = Path(path)
            if not file_path.exists():
                return f"Error: File '{path}' does not exist"
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            console.print(f"[green]📖 Read file: {path}[/green]")
            return f"File content of '{path}':\n```\n{content}\n```"
        except Exception as e:
            error_msg = f"Error reading file '{path}': {str(e)}"
            console.print(f"[red]{error_msg}[/red]")
            return error_msg

    def _execute_write_file(self, path: str, content: str) -> str:
        """Execute write_to_file tool"""
        try:
            file_path = Path(path)
            # Create directories if they don't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            console.print(f"[green]💾 Wrote file: {path}[/green]")
            return f"Successfully wrote to '{path}'"
        except Exception as e:
            error_msg = f"Error writing file '{path}': {str(e)}"
            console.print(f"[red]{error_msg}[/red]")
            return error_msg

    def _execute_tools(self, tools: List[Tuple[str, Dict]]) -> List[str]:
        """Execute all extracted tools"""
        results = []
        for tool_name, params in tools:
            if tool_name == "read_file":
                result = self._execute_read_file(params["path"])
                results.append(result)
            elif tool_name == "write_to_file":
                result = self._execute_write_file(params["path"], params["content"])
                results.append(result)
        return results

    def _clean_response_text(self, text: str) -> str:
        """Remove tool calls from response text for display"""
        # Remove read_file calls
        text = re.sub(r'<read_file>\s*<path>.*?</path>\s*</read_file>', '', text, flags=re.DOTALL)
        # Remove write_to_file calls
        text = re.sub(r'<write_to_file>\s*<path>.*?</path>\s*<content>.*?</content>\s*</write_to_file>', '', text, flags=re.DOTALL)
        return text.strip()

    def chat(self, user_input: str) -> str:
        """Process user input and return response"""
        # Add user message to history
        self.conversation_history.append({"role": "user", "content": user_input})
        
        # Prepare messages for Ollama
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(self.conversation_history)
        
        # Get response from Ollama
        response = self._call_ollama(messages)
        if not response:
            return "Sorry, I couldn't process your request."
        
        # Extract and execute tools
        tools = self._extract_tool_calls(response)
        tool_results = []
        
        if tools:
            tool_results = self._execute_tools(tools)
            
            # Add tool results to conversation if any tools were executed
            if tool_results:
                tool_context = "\n\n".join(tool_results)
                # Add assistant response and tool results to history
                self.conversation_history.append({"role": "assistant", "content": response})
                self.conversation_history.append({"role": "user", "content": f"Tool results:\n{tool_context}"})
                
                # Get follow-up response from Ollama
                messages = [{"role": "system", "content": self.system_prompt}]
                messages.extend(self.conversation_history)
                follow_up_response = self._call_ollama(messages)
                
                if follow_up_response:
                    self.conversation_history.append({"role": "assistant", "content": follow_up_response})
                    return follow_up_response
        
        # Add assistant response to history
        self.conversation_history.append({"role": "assistant", "content": response})
        
        # Return cleaned response (without tool calls)
        return self._clean_response_text(response) or response

    def start_interactive_session(self):
        """Start interactive chat session"""
        console.print(Panel.fit(
            "[bold blue]🤖 Ollama Coding Agent[/bold blue]\n"
            f"Model: {self.model_name}\n"
            "Type 'exit', 'quit', or 'bye' to end the session.\n"
            "Type '/clear' to clear conversation history.\n"
            "Type '/help' for available commands.",
            border_style="blue"
        ))
        
        while True:
            try:
                user_input = Prompt.ask("\n[bold green]You[/bold green]").strip()
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    console.print("[yellow]👋 Goodbye![/yellow]")
                    break
                
                if user_input == '/clear':
                    self.conversation_history = []
                    console.print("[yellow]🧹 Conversation history cleared.[/yellow]")
                    continue
                
                if user_input == '/help':
                    help_text = """
Available commands:
- `/clear` - Clear conversation history
- `/help` - Show this help message
- `exit`, `quit`, `bye` - End the session

Available tools (used automatically by the AI):
- Read files: The AI can read file contents
- Write files: The AI can create or modify files
                    """
                    console.print(Panel(help_text.strip(), title="Help", border_style="cyan"))
                    continue
                
                if not user_input:
                    continue
                
                console.print("\n[bold cyan]🤖 Assistant[/bold cyan]")
                with console.status("[bold green]Thinking..."):
                    response = self.chat(user_input)
                
                if response:
                    console.print(Markdown(response))
                
            except KeyboardInterrupt:
                console.print("\n[yellow]👋 Goodbye![/yellow]")
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

def check_ollama_connection(base_url: str = "http://localhost:11434") -> bool:
    """Check if Ollama is running"""
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False

def check_model_exists(model_name: str, base_url: str = "http://localhost:11434") -> bool:
    """Check if the specified model exists in Ollama"""
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return any(model["name"] == model_name for model in models)
    except:
        pass
    return False

def main():
    model_name = "deepseek-coder-v2:16b"
    base_url = "http://localhost:11434"
    
    # Check Ollama connection
    if not check_ollama_connection(base_url):
        console.print(f"[red]❌ Cannot connect to Ollama at {base_url}[/red]")
        console.print("Make sure Ollama is running with: [cyan]ollama serve[/cyan]")
        sys.exit(1)
    
    # Check if model exists
    if not check_model_exists(model_name, base_url):
        console.print(f"[yellow]⚠️  Model '{model_name}' not found.[/yellow]")
        console.print(f"Please install it with: [cyan]ollama pull {model_name}[/cyan]")
        sys.exit(1)
    
    # Start the agent
    agent = OllamaCodingAgent(model_name, base_url)
    agent.start_interactive_session()

if __name__ == "__main__":
    main()
