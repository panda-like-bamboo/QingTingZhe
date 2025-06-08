import logging
import os
import sys
import json
from typing import List, Dict, Any
from openai import OpenAI

# --- Import settings ---
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SRC_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from app.core.config import settings
except ImportError as e:
    class MockSettings:
        DASHSCOPE_API_KEY = None
        TEXT_MODEL = "qwen-plus"
        APP_NAME = "FallbackApp"
    settings = MockSettings()
    print(f"Warning: Unable to import app.core.config.settings in interrogation_ai.py: {e}", file=sys.stderr)

# --- Configure logging ---
logger = logging.getLogger(settings.APP_NAME)
if not logger.hasHandlers():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

# --- Initialize AI client ---
ai_client = None
if settings.DASHSCOPE_API_KEY:
    try:
        ai_client = OpenAI(
            api_key=settings.DASHSCOPE_API_KEY,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            default_headers={
                "User-Agent": "MyPsychologyApp-InterrogationAI/1.0",
                "Accept": "application/json"
            }
        )
        logger.info("Interrogation AI client initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {e}", exc_info=True)

def format_history_for_prompt(history: List[Dict[str, str]]) -> str:
    """Format conversation history into a prompt string."""
    formatted = ""
    for i, qa in enumerate(history):
        formatted += f"Q{i+1}: {qa.get('q', 'No question text')}\nA{i+1}: {qa.get('a', 'No answer text')}\n\n"
    return formatted.strip()

def suggest_next_question(
    basic_info: Dict[str, Any],
    history: List[Dict[str, str]],
    model_name: str = "qwen-plus",
    num_suggestions: int = 3
) -> List[str]:
    """Generate suggested follow-up questions based on provided information and history."""
    if ai_client is None:
        logger.error("AI client not initialized, cannot generate suggestions.")
        return ["Error: AI service not configured"]

    model_name = settings.TEXT_MODEL if hasattr(settings, 'TEXT_MODEL') else model_name

    system_prompt = f"""You are a top-tier interrogation expert and psychological analyst skilled in strategic questioning.
Your task is to propose {num_suggestions} follow-up questions based on the subject's information and conversation history, each with a distinct strategic intent to guide the interrogation:
1. **Detail-oriented**: Focus on the last answer, requesting specific details like time, place, people, or methods.
2. **Motive/emotion exploration**: Probe the reasons, feelings, or intentions behind the behavior.
3. **Extension/contradiction challenge**: Introduce a related new topic or ask a challenging question to verify consistency.

Return exactly {num_suggestions} questions, each on a single line, without numbering, titles, or additional explanations."""

    history_str = format_history_for_prompt(history)
    basic_info_str = json.dumps(basic_info, ensure_ascii=False, indent=2)

    user_prompt = f"""
**Subject Information:**
```json
{basic_info_str}
```

**Conversation History:**
{history_str if history_str else "(No conversation history)"}

**Task:**
Generate {num_suggestions} distinct follow-up questions as per the system instructions.
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    try:
        logger.debug(f"Calling model '{model_name}' for suggestions...")
        completion = ai_client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_tokens=200 * num_suggestions,
            temperature=0.75,
            n=1
        )
        response_content = completion.choices[0].message.content
        suggestions = [line.strip() for line in response_content.strip().split('\n') if line.strip()]

        if not suggestions:
            logger.warning("Model returned no valid suggestions.")
            return ["AI failed to generate suggestions"]

        logger.info(f"Successfully generated {len(suggestions)} suggestions.")
        return suggestions[:num_suggestions]

    except Exception as e:
        logger.error(f"Error calling AI model: {e}", exc_info=True)
        return [f"Error: Failed to retrieve AI suggestions ({type(e).__name__})"]