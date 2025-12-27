import requests
import json
from typing import List, Dict, Any, Optional

class LLMProvider:
    def __init__(self, api_key: str, base_url: str, provider_type: str = "openai"):
        self.api_key = api_key
        # Ensure base_url doesn't have trailing slash for consistency
        self.base_url = base_url.rstrip('/') if base_url else ""
        self.provider_type = provider_type.lower()

    def generate(self, messages: List[Dict], model: str, max_tokens: int = 4096, temperature: float = 0.3) -> Dict:
        raise NotImplementedError("Subclasses must implement generate")

class OpenAICompatibleProvider(LLMProvider):
    """
    Handles OpenAI, DeepSeek, OpenRouter, and AI Builders (default).
    Expects /chat/completions endpoint.
    """
    def generate(self, messages: List[Dict], model: str, max_tokens: int = 4096, temperature: float = 0.3) -> Dict:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # OpenRouter specific header for identifying the app
        if "openrouter" in self.base_url:
            headers["HTTP-Referer"] = "http://localhost:5173"
            headers["X-Title"] = "StoryFlow"

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # Only strict OpenAI supports 'json_object' reliably. 
        # Others (DeepSeek, Custom Proxies) might error 400/500 if this is sent.
        if self.provider_type == "openai":
             payload["response_format"] = {"type": "json_object"}

        try:
            # Assume /chat/completions is needed if not present, but usually base_url convention varies.
            # If base_url ends in /v1, we usually add /chat/completions.
            # Let's try to be smart or expect the user to provide the root.
            url = f"{self.base_url}/chat/completions"
            
            print(f"DEBUG: Sending to {url} with model {model}")
            # Increased timeout to 180s for long contexts
            response = requests.post(url, json=payload, headers=headers, timeout=180)
            
            if response.status_code != 200:
                # Log detailed error to file for debugging
                try:
                    import datetime
                    with open("debug_api_errors.txt", "a", encoding="utf-8") as f:
                        f.write(f"\n--- API Error {datetime.datetime.now()} ---\n")
                        f.write(f"URL: {url}\nModel: {model}\nStatus: {response.status_code}\n")
                        f.write(f"Response: {response.text}\n--------------------------\n")
                except: pass

                # Try to parse error
                try:
                    err = response.json()
                    raise Exception(f"API Error {response.status_code}: {err}")
                except:
                    raise Exception(f"API Error {response.status_code}: {response.text}")
            
            return response.json()
            
        except Exception as e:
            print(f"LLM Request Failed: {e}")
            raise e

class AnthropicProvider(LLMProvider):
    """
    Handles Anthropic Claude API.
    Expects /messages endpoint.
    """
    def generate(self, messages: List[Dict], model: str, max_tokens: int = 4096, temperature: float = 0.3) -> Dict:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        # Convert OpenAI "system" role to Anthropic top-level "system" parameter
        system_prompt = ""
        filtered_messages = []
        for msg in messages:
            if msg['role'] == 'system':
                system_prompt += msg['content'] + "\n"
            else:
                filtered_messages.append(msg)

        payload = {
            "model": model,
            "messages": filtered_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system_prompt.strip()
        }

        url = f"{self.base_url}/messages"
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=180)
            if response.status_code != 200:
                 raise Exception(f"Anthropic API Error {response.status_code}: {response.text}")
            
            # Convert Anthropic response to OpenAI-like format for compatibility
            data = response.json()
            content = data['content'][0]['text']
            
            return {
                "choices": [{
                    "message": {
                        "content": content
                    },
                    "finish_reason": data.get("stop_reason")
                }],
                "usage": data.get("usage", {})
            }
        except Exception as e:
            raise e

def get_llm_provider(provider_type: str, api_key: str, base_url: str) -> LLMProvider:
    """Factory to return the correct provider instance."""
    p_type = provider_type.lower()
    
    if p_type == 'anthropic':
        # Default Anthropic URL if not provided
        url = base_url if base_url else "https://api.anthropic.com/v1"
        return AnthropicProvider(api_key, url, p_type)
    
    # Default to OpenAI Compatible (Works for OpenAI, DeepSeek, OpenRouter, AI Builders)
    # If base_url is missing, default to OpenAI? Or AI Builders?
    # Let's default to AI Builders since that's the current default
    url = base_url if base_url else "https://space.ai-builders.com/backend/v1"
    return OpenAICompatibleProvider(api_key, url, p_type)
