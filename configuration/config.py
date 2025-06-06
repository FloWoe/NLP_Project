import google.generativeai as genai
from elevenlabs import ElevenLabs, save
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path="configuration/config.env")

GOOGLE_TRANSLATE_API_KEY = os.getenv("GOOGLE_TRANSLATE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")