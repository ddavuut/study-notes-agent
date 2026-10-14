# Study Notes Agent

Course: Automata, Computability and Complexity  
Presenter: Davud Mustafazade  
Assignment: 15 October 2026

A Python agent that answers study questions, follows a conversation, and calls
`save_note` when a user asks to keep notes. A Streamlit interface shows the tool
result and offers a Markdown download. The terminal interface also exports
notes to the local `notes` folder.

## Quick start on Windows

Extract the project into a **new folder**, keeping your original `first agent`
folder as your learning version. Open the extracted folder in VS Code.

In Terminal > New Terminal:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

The browser initially opens a read-only preview. No API call occurs in preview.
If `py` is unavailable, use your working Python launcher instead. Python 3.12
or 3.13 is a conservative choice for a new deployment. Local dependency
compatibility still needs verification on your specific Python installation.

## Enable live AI privately

1. Copy `secrets.example.toml` to `.streamlit/secrets.toml`.
2. Replace `OPENAI_API_KEY` with your **new, unexposed** API key.
3. Set `DEMO_ACCESS_CODE` to a long random code and `ENABLE_LIVE = "true"`.
4. Save. Restart Streamlit if the changes do not load.
5. In the browser sidebar, enter the demo access code (not your API key).

Never paste the key into Python source, GitHub, chat, a slide, or a screenshot.
The example file contains placeholders only. `.gitignore` excludes the real
secret file, generated notes, and the virtual environment. Gitignore does not
protect a secret that you manually upload or already committed.

```toml
OPENAI_API_KEY = "YOUR_NEW_KEY_HERE"
DEMO_ACCESS_CODE = "YOUR_LONG_RANDOM_DEMO_CODE"
ENABLE_LIVE = "true"
```

## Live demonstration

Send each message after the previous answer:

1. `Explain DFA in three sentences. Do not save it yet.`
2. `Give one example of a language it can recognize.`
3. `Save both explanations as study notes.`

Inspect the tool result and download the new Markdown note. Open it and check
the contents. Ordinary questions should not create notes. The model can still
make a poor tool choice, so test the exact classroom demo before presenting.
AI explanations are not authoritative course material and require review.

## Project files

| File | Purpose |
|---|---|
| `agent_core.py` | Tool schema, argument validation, session state and bounded model/tool loop |
| `app.py` | Streamlit pages, session-local downloads, access code and request limits |
| `agent.py` | Terminal interface and export to local notes folder |
| `tests/test_agent.py` | Offline control-flow and validation tests using a fake client |
| `requirements.txt` | Python dependencies |
| `.streamlit/config.toml` | Interface theme |
| `GUIDE_EN.md` | Step-by-step implementation and public deployment guide |
| `BASLA_TR.md` | Turkish setup instructions |
| `PRESENTATION_NOTES_EN.md` | English talk track and demo checklist |

## Terminal version

```powershell
.\.venv\Scripts\python.exe agent.py
```

Enter your API key privately. Use `new` to clear conversational context and
`exit` to stop. A successful note is also written under `notes/`.

## Offline tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Tests use scripted fake responses and do not call a paid model. They verify
program behavior, not factual quality or real model tool-choice reliability.

## Public deployment

See `GUIDE_EN.md`, section 8. A public GitHub repository makes the code public.
A Streamlit Community Cloud deployment provides the live URL. Both require
your accounts. Publishing is **not yet performed by this package**.

The landing page and project explanation can be public while live API access
requires the class code. Share that code privately with your teacher. If your
teacher requires anonymous live access, agree on a separate usage/billing plan
before removing the gate. API use still costs money even on free hosting.

## Limits and privacy

- Up to 2,000 characters per message and ten turns per conversation.
- At most four model calls per turn, 1,600 output tokens per call, 30-second
  request timeout, and no automatic SDK retries.
- Up to ten notes per web session, with 12,000 characters per note.
- One process allows 60 model requests and locks new code attempts after 30
  failed attempts. These counters reset when the process restarts. They are
  demo guardrails, **not a durable global spend cap or production authentication**.
- A new conversation resets context and turn count. It retains session notes.
  Browser refresh/disconnection can clear session state. Download files to keep them.
- API requests send prompts and relevant context to OpenAI. Responses linking
  uses provider-managed state; this is not an offline or zero-retention design.
- The app offers only `save_note`. It cannot run model-generated code, browse
  the web, or read arbitrary files. Note text renders without unsafe HTML.
- If a request fails after saving, the note remains downloadable. Context resets
  to avoid continuing an ambiguous tool chain. Check notes before repeating a save.

## References

- https://developers.openai.com/api/docs/guides/function-calling
- https://developers.openai.com/api/docs/guides/conversation-state
- https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management

## License

This project is distributed under the MIT License in `LICENSE`.
