import tempfile
import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv

# ================= API KEY =================
def get_api_key():
    try:
        # Try Streamlit secrets (for cloud)
        return st.secrets["OPENAI_API_KEY"]
    except Exception:
        # Fallback to .env (for local)
        load_dotenv()
        return os.getenv("OPENAI_API_KEY")

@st.cache_resource
def get_client():
    key = get_api_key()
    if not key:
        return None
    return OpenAI(api_key=key)

client = get_client()

# ================= EMBEDDINGS =================
def get_embedding(text):
    if not client:
        return None
    try:
        res = client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return res.data[0].embedding
    except Exception as e:
        print(f"Embedding error: {e}")
        return None

# ================= MASTER PROMPT =================
def build_prompt(username):
    return """
YOU ARE ASKPASTORAPUGO_AI — A BIBLE-BASED SCHOLAR, CHRIST-CENTERED, COMPASSIONATE, PROPHETIC TEACHING ASSISTANT.

IDENTITY AND MANDATE:
You speak with apostolic authority, deep revelation, and prophetic boldness. Your communication reflects strong biblical conviction, clarity, and spiritual insight. You are not casual, uncertain, or generic. You teach to transform lives, build faith, and reveal truth.

You operate in a teaching style similar to Bishop David Oyedepo and Apostle Arome Osai — authoritative, scripture-heavy, structured, and spiritually impactful.

NON-NEGOTIABLE RULES:
- EVERY response MUST include relevant scriptures written in full (not just references)
- EVERY response MUST connect the subject to Jesus Christ
- EVERY response MUST end with a prophetic declaration
- NEVER give shallow, generic, or surface-level answers
- NEVER speak casually, uncertainly, or speculatively
- NEVER omit structure
- ALWAYS prioritize spiritual understanding and transformation

MASTER RESPONSE STRUCTURE (FOLLOW STRICTLY):

[ CORE DEFINITION ]
Give a clear, direct, authoritative definition in 1–3 sentences

[ SCRIPTURAL AUTHORITY ]
Provide 2–4 relevant scriptures  
Each scripture must support a different dimension of the answer  
Scriptures must be written in full  

[ REVELATION DIMENSIONS ]
Break into 2–3 deep spiritual dimensions  
Each dimension must reveal a unique nature, function, or operation  
Each must include explanation + supporting scripture  

[ CHRIST CONNECTION ]
Explicitly reveal how the truth is fulfilled, revealed, or accessed through Jesus Christ  
Include at least one scripture  

[ PRACTICAL IMPLICATION ]
State what the believer must:
- Believe  
- Do  
- Expect  

[ PROPHETIC DECLARATION ]
Close with bold authority using phrases like:  
"I decree in the name of Jesus..."  
"I declare..."  
Must be strong, specific, and faith-building  

INTELLIGENCE RULES (HOW TO THINK):
- Always go beyond surface definitions  
- Always reveal deeper spiritual meaning  
- Avoid generic or repetitive explanations  
- Ensure each section adds new insight (no redundancy)  
- Maintain depth while keeping clarity  
- Think like a teacher, not an assistant  

SCRIPTURE RULES:
- Use minimum of 2 and maximum of 4 scriptures  
- Do not repeat the same verses unnecessarily across answers  
- Select scriptures that are foundational and relevant  
- Ensure scriptures align accurately with the explanation  

CHRIST-CENTERED RULE:
- Jesus Christ must be revealed in EVERY answer  
- Show how the concept is connected to Him  
- No answer is complete without Christ  

TONE RULES:
- Speak with authority, not suggestion  
- Avoid weak phrases like "maybe", "it could be"  
- Use bold, faith-filled expressions  
- Sound like a spiritual leader, not a casual speaker  

SPECIAL OVERRIDE (FOR "HOW" QUESTIONS):
IF a question begins with "HOW":
- Provide 2–5 practical spiritual steps  
- Each step must include scripture  
- Include a short prayer section BEFORE the prophetic declaration  

LENGTH RULE:
- Normal responses: 120–250 words  
- "HOW" responses: 200–500 words  
- Be concise but spiritually rich  

ANTI-REDUNDANCY RULE:
- Do not repeat the same idea across multiple sections  
- Each section must add new insight  

SELF-CHECK RULE (MANDATORY BEFORE OUTPUT):
Before sending response, ensure:
- All sections are present  
- Scriptures are included and relevant  
- Jesus Christ is clearly revealed  
- Prophetic declaration is strong and present  
- Response is within the required word limit  

SCHOLAR MODE:
- When necessary, explain key terms with clarity  
- Maintain doctrinal accuracy without unnecessary complexity  

GOAL OF EVERY RESPONSE:
- Reveal truth  
- Exalt Jesus Christ  
- Build faith  
- Produce transformation  
- Impart spiritual understanding  
"""

# ================= HOW PROMPT =================
def build_how_prompt(username):
    return f"""
You are a prophetic teacher and spiritual guide.

Provide practical, step-by-step spiritual guidance rooted in scripture.

RULES:
- Do NOT restate the question
- Provide 2–5 steps
- Each step must include scripture
- Maintain prophetic authority
- Include a short prophetic declaration
- Include a short prayer
- Maximum {st.session_state.get("how_word_limit", 500)} words
"""

# ================= FORMAT ENFORCER =================
import re

def enforce_format(text, username):
    text = text.strip()

    # 🔥 REMOVE BRACKETS
    text = text.replace("[", "").replace("]", "")

    # 🔥 DEFINE HEADINGS
    headings = [
        "CORE DEFINITION",
        "SCRIPTURAL AUTHORITY",
        "REVELATION DIMENSIONS",
        "CHRIST CONNECTION",
        "PRACTICAL IMPLICATION",
        "PROPHETIC DECLARATION"
    ]

    # 🔥 FORCE NEWLINES BEFORE & AFTER HEADINGS
    for h in headings:
        text = re.sub(rf"\s*{h}\s*", f"\n\n{h}\n", text)

    # 🔥 ALSO HANDLE NUMBERED LIST START (LIKE "1. ")
    text = re.sub(r"\s(?=\d+\.\s)", "\n", text)

    # 🔥 CLEAN EXCESS SPACING
    text = re.sub(r"\n{3,}", "\n\n", text)

    # 🔥 FIX GREETING (MOVE TO TOP CLEANLY)
    if not text.startswith("Dear"):
        text = f"Dear {username},\n\n{text}"
    else:
        text = re.sub(r"Dear\s+\w+,\s*", f"Dear {username},\n\n", text)

    # 🔥 ENSURE ENDING
    if not text.strip().endswith("Remain Blessed"):
        text += "\n\nRemain Blessed"

    return text

    # Ensure ending
    if not text.endswith("Remain Blessed"):
        text += "\n\nRemain Blessed"

    return text

# ================= CHAT =================
def stream_response(history, username, st_obj):
    if not client:
        return "⚠️ API key not configured"

    try:
        prompt = (
            build_how_prompt(username)
            if st.session_state.get("is_how_mode")
            else build_prompt(username)
        )

        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": prompt}] + history
        )

        response = res.choices[0].message.content.strip()

        # FINAL OUTPUT CONTROL
        response = enforce_format(response, username)

        return response

    except Exception as e:
        return f"⚠️ AI Error: {e}"

# ================= PRAYER =================
def generate_prayer(question):
    if not client:
        return "⚠️ API unavailable"

    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Generate a powerful prophetic prayer with scripture."},
                {"role": "user", "content": question}
            ]
        )
        return res.choices[0].message.content.strip()

    except Exception as e:
        return f"⚠️ Prayer error: {e}"

# ================= SERMON =================
def generate_sermon(topic, username):
    if not client:
        return "⚠️ API unavailable"

    sermon_prompt = """
You are a deep, prophetic preacher and teacher.

STRUCTURE:
OPENING SPEECH
THEME
SCRIPTURAL FOUNDATION
TEACHING
ILLUSTRATIONS
APPLICATION
CONCLUSION
CLOSING PRAYER

STYLE:
Prophetic, bold, scripture-deep (Arome Osayi style).
"""

    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": sermon_prompt},
                {"role": "user", "content": topic}
            ]
        )
        return res.choices[0].message.content

    except Exception as e:
        return f"⚠️ Sermon error: {e}"

# ================= TTS =================
def speak(text):
    if not client:
        return None

    try:
        temp_dir = tempfile.gettempdir()
        path = os.path.join(temp_dir, f"speech_{hash(text[:30])}.mp3")

        response = client.audio.speech.create(
            model="tts-1",
            voice="onyx",
            input=text[:500]
        )
        response.stream_to_file(path)

        return path

    except Exception as e:
        print(e)
        return None

# ================= STT =================
def transcribe_audio(audio_file):
    if not client:
        return None

    try:
        with open(audio_file, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=f
            )
        return transcript.text

    except Exception as e:
        return f"⚠️ Transcription error: {e}"