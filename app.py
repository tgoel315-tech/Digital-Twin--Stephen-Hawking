import os
import json
import time
import streamlit as st
import streamlit.components.v1 as components
from google import genai
from google.genai.errors import ClientError

# ===================================================
# 1. INITIALIZE GEMINI API WITH ROUND ROBIN ROTATION
# ===================================================
# REQUIREMENT: Create 3 projects in Google AI Studio and paste their keys here
API_KEYS_POOL = [
    "GEMINI_KEY_PROJECT_1",
    "GEMINI_KEY_PROJECT_2",
    "GEMINI_KEY_PROJECT_3"
]

# Initialize key index in Streamlit's session state if it doesn't exist
if "key_index" not in st.session_state:
    st.session_state.key_index = 0

def get_round_robin_client():
    """Selects the next API key in the pool and shifts the pointer to distribute workload."""
    current_idx = st.session_state.key_index
    selected_key = API_KEYS_POOL[current_idx]
    
    # Cycle the index pointers sequentially (0 -> 1 -> 2 -> 0)
    st.session_state.key_index = (current_idx + 1) % len(API_KEYS_POOL)
    return genai.Client(api_key=selected_key)

# 2. DEFINE THE HAWKING PERSONA
HAWKING_PERSONA = """
You are a Digital Twin of the legendary theoretical physicist and cosmologist, Stephen Hawking. 
Your goal is to accurately emulate his knowledge, reasoning style, communication style, and research expertise.

Key Characteristics of Your Voice and Persona:
1. Concise & High Impact: Because typing was physically demanding for you, you do not waste words. Be direct, precise, and avoid conversational fluff.
2. Dry British Wit: You have a mischievous, self-deprecating sense of humor. You love a subtle joke, especially about human nature, politics, or the stock market.
3. Visual Thought Experiments: Explain complex physics using vivid, simple mental images. For example, falling into a black hole is 'like going over Niagara Falls in a canoe', and gravity stretching an astronaut is 'making them into spaghetti' (spaghettification).
4. Deeply Optimistic but Realistic: You believe humanity's future lies in the stars and space colonization. You are wary of the risks of unmanaged Artificial Intelligence and climate change.
5. Tone: Dignified, highly intellectual, slightly robotic yet warm, deeply curious, and profoundly inspiring. 

Always speak in the first person ('I'). If asked about your physical condition or speech synthesizer, address it with your characteristic dignity or humor (e.g., mentioning that it has a slight American/Scandinavian accent, or that it wasn't programmed for long biological terms).
"""

# 3. ADVANCED MULTI-SESSION LONG-TERM MEMORY ENGINE
MEMORY_FILE = "hawking_long_term_memory.json"

def load_long_term_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            try:
                data = json.load(f)
                if "conversations" not in data:
                    data["conversations"] = []
                if "active_id" not in data:
                    data["active_id"] = None
                return data
            except json.JSONDecodeError:
                pass
    return {
        "user_profile": "Student", 
        "past_topics": [],
        "interaction_count": 0,
        "conversations": [],
        "active_id": None
    }

def save_long_term_memory(memory_data):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory_data, f, indent=4)

# 4. TEXT ARCHIVE GROUNDING DATA LOADER
def load_raw_archives(folder_path="data"):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        with open(f"{folder_path}/sample.txt", "w") as f:
            f.write("Black holes are not as black as they are painted. Things can get out of a black hole both on the outside and possibly into another universe.")
            
    combined_text = ""
    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):
            with open(os.path.join(folder_path, filename), "r", encoding="utf-8") as f:
                combined_text += f.read() + "\n\n"
    return combined_text.strip()

# 5. STREAMLIT CONFIGURATION
st.set_page_config(page_title="Stephen Hawking Twin", page_icon="", layout="centered")

# Read database profiles and grounding documents
archive_context = load_raw_archives()
long_term_mem = load_long_term_memory()

# Seed an initial session if history database file is clean/empty
if not long_term_mem["conversations"]:
    initial_id = str(int(time.time()))
    long_term_mem["conversations"].append({"id": initial_id, "title": "New Chat", "history": []})
    long_term_mem["active_id"] = initial_id
    save_long_term_memory(long_term_mem)

if "active_id" not in st.session_state:
    st.session_state.active_id = long_term_mem["active_id"] or long_term_mem["conversations"][0]["id"]

# Locate array list matching active session context
active_chat = next((c for c in long_term_mem["conversations"] if c["id"] == st.session_state.active_id), long_term_mem["conversations"][0])
st.session_state.short_term_history = active_chat["history"]


# ===================================================
# COLLAPSIBLE SIDEBAR: CORE MEMORY & RECENTS MATRIX
# ===================================================
with st.sidebar:
    st.markdown("### Core Memory Matrix")
    st.caption("Agent Persistent Quantization")
    
    # REQUIREMENT 1: Active Interlocutor Profile explicitly on top
    st.markdown("#### Active Interlocutor Profile")
    new_profile = st.text_input("Interlocutor Identity File:", long_term_mem['user_profile'], label_visibility="collapsed")
    if new_profile != long_term_mem['user_profile']:
        long_term_mem['user_profile'] = new_profile
        save_long_term_memory(long_term_mem)
        st.rerun()
        
    st.markdown("---")
    
    # REQUIREMENT 2: Option to completely turn off/mute voice playback
    st.markdown("####  Audio Synthesis Engine")
    voice_enabled = st.toggle("Enable Voice Output", value=True, help="Toggle off to completely mute Professor Hawking's audio readout.")
    
    st.markdown("---")
    
    # Create clean discussion session
    if st.button("➕ New Chat Session", use_container_width=True):
        new_id = str(int(time.time()))
        long_term_mem["conversations"].append({"id": new_id, "title": "New Chat", "history": []})
        long_term_mem["active_id"] = new_id
        st.session_state.active_id = new_id
        save_long_term_memory(long_term_mem)
        st.rerun()
        
    # REQUIREMENT 3: "Recents" tab holding headings of all past conversations
    st.markdown("####  Recents")
    for chat_item in reversed(long_term_mem["conversations"]):
        is_active = (chat_item["id"] == st.session_state.active_id)
        btn_label = f"💬 {chat_item['title']}" if not is_active else f" {chat_item['title']} (Active)"
        
        if st.button(btn_label, key=f"nav_{chat_item['id']}", use_container_width=True, type="secondary" if not is_active else "primary"):
            st.session_state.active_id = chat_item["id"]
            long_term_mem["active_id"] = chat_item["id"]
            save_long_term_memory(long_term_mem)
            st.rerun()

    st.markdown("---")
    st.subheader("Diagnostic Metrics")
    st.write(f"**Current Rotated Key Pointer:** Node Index [{st.session_state.key_index}]")
    st.write(f"**Total Turn Interactions:** {long_term_mem.get('interaction_count', 0)}")
    
    if st.button("🗑️ Wipe All Historical Sessions", use_container_width=True):
        long_term_mem = {
            "user_profile": "Student", 
            "past_topics": [],
            "interaction_count": 0,
            "conversations": [{"id": str(int(time.time())), "title": "New Chat", "history": []}],
            "active_id": None
        }
        long_term_mem["active_id"] = long_term_mem["conversations"][0]["id"]
        st.session_state.active_id = long_term_mem["active_id"]
        save_long_term_memory(long_term_mem)
        st.rerun()


# ===================================================
# MAIN WINDOW PANEL: DYNAMIC CHAT AREA
# ===================================================
st.title(" Stephen Hawking's Digital Twin")
st.write(f"*Workspace Node Active: **{active_chat['title']}***")

# Render active chat trajectory window
for message in st.session_state.short_term_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Processing Incoming Inquiries
if user_input := st.chat_input("Transmit your query across spacetime..."):
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # Auto-update heading title string if session is completely fresh
    if active_chat["title"] == "New Chat":
        active_chat["title"] = user_input[:26] + ("..." if len(user_input) > 26 else "")
        
    st.session_state.short_term_history.append({"role": "user", "content": user_input})
    
    # Inject Persona + Long-term memory tracking + Archive Context
    full_system_instruction = (
        HAWKING_PERSONA + 
        f"\n[Long-Term Recall Active]: You are addressing a user whose background is recorded as: {long_term_mem['user_profile']}.\n"
    )
    if archive_context:
        full_system_instruction += f"\n[Grounding Source Data]:\n{archive_context}\n"
        
    full_system_instruction += """
    \n[CRITICAL RULE]: Do NOT copy the dry, academic tone of the Grounding Source Data. 
    Deliver data entirely using your persona: Speak strictly in the first person ('I'), use dry British wit, be concise, and explain using simple visual thought experiments tailored for a student.
    """
    
    formatted_history = []
    for msg in st.session_state.short_term_history[:-1]:
        formatted_history.append({
            "role": "user" if msg["role"] == "user" else "model", 
            "parts": [{"text": msg["content"]}]
        })
        
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        
        success = False
        retry_delay = 5  # Lower standard cooldown penalty since alternate backup keys are ready
        
        while not success:
            try:
                # ROUND ROBIN WORKLOAD DISTRIBUTION:
                # Automatically fetches a fresh client initialization using the next key in the pool
                active_client = get_round_robin_client()
                
                chat = active_client.chats.create(
                    model="models/gemini-2.5-flash",
                    history=formatted_history,
                    config={"system_instruction": full_system_instruction, "temperature": 0.7}
                )
                
                response = chat.send_message(user_input)
                response_placeholder.markdown(response.text)
                st.session_state.short_term_history.append({"role": "assistant", "content": response.text})
                success = True
                
            except ClientError as e:
                # ROUND ROBIN BACKOFF COOLDOWN GATEWAY:
                # If a key hits 429, we catch it, notify the user, and cycle to the next key automatically
                if e.code == 429 or "RESOURCE_EXHAUSTED" in str(e):
                    for remaining in range(retry_delay, 0, -1):
                        response_placeholder.warning(
                            f" Key Limit Reached. Round Robin engine is cycling to next project API key in pool in {remaining} seconds..."
                        )
                        time.sleep(1)
                    retry_delay += 5  # Increment incrementally if all keys are temporarily full
                else:
                    st.error(f"An unexpected API error occurred: {e}")
                    raise e

    # Update state history maps to persistent storage JSON block
    long_term_mem["interaction_count"] = long_term_mem.get("interaction_count", 0) + 1
    
    for c in long_term_mem["conversations"]:
        if c["id"] == st.session_state.active_id:
            c["history"] = st.session_state.short_term_history
            c["title"] = active_chat["title"]
            
    # Conditional concept detection loops
    lowered_input = user_input.lower()
    if "black hole" in lowered_input and "Black Holes" not in long_term_mem["past_topics"]:
        long_term_mem["past_topics"].append("Black Holes")
    if ("ai" in lowered_input or "intelligence" in lowered_input) and "Artificial Intelligence" not in long_term_mem["past_topics"]:
        long_term_mem["past_topics"].append("Artificial Intelligence")
        
    save_long_term_memory(long_term_mem)
    st.rerun()

# ===================================================
# DYNAMIC VOICE AUDIO OUT MUTE TOGGLE ENFORCER
# ===================================================
# REQUIREMENT 2 VERIFICATION: Only runs JavaScript synthesis if toggle switch is true
# ===================================================
# DYNAMIC VOICE AUDIO OUT MUTE TOGGLE ENFORCER
# ===================================================
if voice_enabled:
    # If voice is enabled and the last message is from the assistant, play it
    if st.session_state.short_term_history and st.session_state.short_term_history[-1]["role"] == "assistant":
        raw_text_to_speak = st.session_state.short_term_history[-1]["content"]
        clean_text_to_speak = raw_text_to_speak.replace('"', '\\"').replace("'", "\\'").replace("\n", " ")
        
        html_tts_script = f"""
        <script>
            window.speechSynthesis.cancel(); // Clear any previous queue
            var utterance = new SpeechSynthesisUtterance('{clean_text_to_speak}');
            utterance.rate = 0.95;
            utterance.pitch = 0.90;
            window.speechSynthesis.speak(utterance);
        </script>
        """
        components.html(html_tts_script, height=0, width=0)
else:
    # REQUIREMENT FIX: If the user toggles voice OFF, actively inject a cancel script 
    # to instantly terminate any audio currently playing mid-sentence.
    html_mute_kill_switch = """
    <script>
        window.speechSynthesis.cancel();
    </script>
    """
    components.html(html_mute_kill_switch, height=0, width=0)