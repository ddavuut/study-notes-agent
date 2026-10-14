"""Run: py -m streamlit run app.py"""
import hashlib
import hmac
import os
import threading
import time

import streamlit as st
from openai import OpenAI
from agent_core import AgentState, MODEL, MAX_TURNS, run_turn, friendly_error

st.set_page_config(page_title="Study Notes Agent", page_icon="📚", layout="wide")


def setting(name, default=""):
    if name in os.environ:
        return os.environ[name]
    try:
        return str(st.secrets.get(name, default))
    except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        return default


class Budget:
    """Shared by sessions in this process. Restarts reset it; not a billing cap."""
    def __init__(self):
        self.lock = threading.Lock()
        self.calls = 0
        self.failures = 0

    def reserve(self):
        with self.lock:
            if self.calls >= 60:
                raise RuntimeError("This demo has reached its server request allowance.")
            self.calls += 1

    def access(self, entered, expected):
        with self.lock:
            if self.failures >= 30:
                return False
            if hmac.compare_digest(entered.encode(), expected.encode()):
                return True
            self.failures += 1
            return False


@st.cache_resource
def shared_budget():
    return Budget()


if "agent" not in st.session_state:
    st.session_state.agent = AgentState()
    st.session_state.messages = []
    st.session_state.authorized_for = ""
    st.session_state.last_request = 0.0

st.markdown("""<style>
.stApp {background:#f6f7fb;}
.block-container {max-width:1160px;padding-top:2rem;}
h1 {letter-spacing:-1.8px;}
[data-testid="stSidebar"] {background:#eef1f8;}
[data-testid="stChatMessage"] {border:1px solid #e0e5ef;border-radius:14px;}
</style>""", unsafe_allow_html=True)

key = setting("OPENAI_API_KEY")
code = setting("DEMO_ACCESS_CODE")
enabled = setting("ENABLE_LIVE", "false").lower() == "true"
configured = bool(key and code and enabled)
fingerprint = hashlib.sha256((code + key).encode()).hexdigest()

with st.sidebar:
    st.subheader("Study Notes Agent")
    st.caption("A course project by Davud Mustafazade")
    page = st.radio("Workspace", ["Chat", "How it works", "Demo guide"])
    st.divider()
    if configured and st.session_state.authorized_for != fingerprint:
        with st.form("unlock"):
            entered = st.text_input("Class demo access code", type="password")
            unlock = st.form_submit_button("Enable live AI")
        if unlock:
            if shared_budget().access(entered, code):
                st.session_state.authorized_for = fingerprint
                st.rerun()
            else:
                st.error("Access code not accepted, or attempt limit reached.")
    authorized = configured and st.session_state.authorized_for == fingerprint
    st.caption("Live AI enabled" if authorized else "Read-only preview")
    st.caption(f"Model: {MODEL}")
    st.caption(f"Conversation turns: {st.session_state.agent.turns}/{MAX_TURNS}")
    if st.button("New conversation", use_container_width=True):
        st.session_state.agent.last_response_id = None
        st.session_state.agent.turns = 0
        st.session_state.messages = []
        st.rerun()
    st.caption("New conversation clears chat context, but keeps this session's notes.")

st.title("Understand it. Keep the notes.")
st.write("Ask a study question, follow up, and ask the agent to save what matters.")

if page == "How it works":
    st.subheader("The model chooses; Python performs the action")
    st.markdown("""
1. You send a goal and the app supplies tool descriptions and conversation context.
2. GPT-4.1 mini returns text or a structured `save_note` call.
3. Python validates the arguments and creates a Markdown note in your session.
4. The app sends the tool result back, linked by `call_id`.
5. The model uses that result to answer. Each turn has at most four model calls.

The chat input repeats user turns. The separate agent loop handles tool calls
within one turn. The model cannot execute arbitrary Python or browse files.
""")
    st.code('result = save_note(arguments["content"], state)', language="python")
    st.info("Notes stay in your browser session on this server. Download them to keep a copy. Refreshing or disconnecting can clear the session. Messages are sent to OpenAI for processing. Do not enter secrets.")
    st.markdown("[OpenAI function calling](https://developers.openai.com/api/docs/guides/function-calling) · [Streamlit session state](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state)")
elif page == "Demo guide":
    st.subheader("Three prompts for the live demonstration")
    st.code("Explain DFA in three sentences. Do not save it yet.")
    st.code("Give one example of a language it can recognize.")
    st.code("Save both explanations as study notes.")
    st.write("Check the visible tool result, open the note preview, and download the Markdown file.")
    st.subheader("Limits to explain")
    st.write("AI text may contain mistakes. This app has no web search. It remembers a limited conversation, not permanent knowledge. Live AI requires an API balance and the class access code.")
else:
    left, right = st.columns([2.1, 1], gap="large")
    with right:
        st.subheader("Your notes")
        if not st.session_state.agent.notes:
            st.caption("Saved notes appear here when you request them.")
        for note in st.session_state.agent.notes:
            with st.expander(note["filename"]):
                st.markdown(note["content"])
                st.download_button("Download Markdown", note["content"], note["filename"],
                                   mime="text/markdown", key=note["filename"])
    with left:
        if not authorized:
            st.info("This is a read-only preview. The owner enables live AI and shares an access code for the class demo.")
            with st.expander("Example interaction — written example, not a live AI response", expanded=True):
                st.markdown("**You:** Explain a DFA, then save the explanation.\n\n**Tool:** `save_note(content=...)`\n\n**Result:** A Markdown note becomes available to download.\n\n**Agent:** Confirms the result after Python reports success.")
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["text"])
                for event in message.get("events", []):
                    result = event["result"]
                    if result.get("ok"):
                        st.success(f"Tool: {event['tool']} · Created {result['filename']}")
                    else:
                        st.warning(f"Tool: {event['tool']} · {result.get('error', 'Failed')}")
                if message.get("model"):
                    st.caption(f"Response model: {message['model']}")
        prompt = st.chat_input("Ask a question or say ‘save that explanation’", disabled=not authorized)
        if prompt is not None:
            if not prompt.strip():
                st.warning("Please enter a message.")
            elif time.monotonic() - st.session_state.last_request < 3:
                st.warning("Please wait a few seconds between requests.")
            elif len(prompt) > 2000:
                st.warning("Keep your message under 2,000 characters.")
            else:
                st.session_state.last_request = time.monotonic()
                st.session_state.messages.append({"role": "user", "text": prompt})
                try:
                    client = OpenAI(api_key=key, timeout=30.0, max_retries=0)
                    with st.spinner("Working on your request…"):
                        reply = run_turn(client, prompt, st.session_state.agent, shared_budget().reserve)
                    st.session_state.messages.append({"role": "assistant", "text": reply.text,
                                                       "events": reply.events, "model": reply.model})
                except Exception as error:
                    # Notes survive a failure after the save. Clear context to avoid
                    # retrying an ambiguous tool chain and creating duplicate notes.
                    st.session_state.agent.last_response_id = None
                    st.session_state.messages.append({"role": "assistant", "text":
                        friendly_error(error) + " Check Your notes before retrying. Conversation context was reset."})
                st.rerun()

st.caption("Automata, Computability and Complexity · 15 October 2026")
