# Creating Study Notes Agent: complete walkthrough

Davud Mustafazade · Automata, Computability and Complexity · 15 October 2026

## 1. What is an AI agent?

An AI agent receives a goal, uses context to select an action, and uses the result of that action to continue. Agents differ in how much autonomy they have. This project is a bounded, tool-using study assistant: it can explain a topic and request one allowed action, `save_note`. Python executes that action. The model does not execute Python itself.

## 2. How this agent works

The user enters a goal. The app sends the goal, instructions, tool schema and conversation reference to the OpenAI Responses API. GPT-4.1 mini returns either text or a function call. A function call includes a tool name, JSON arguments and a call ID. Python validates the call and creates a note. The app returns the result as `function_call_output` using the same `call_id`. The model uses the result to compose its answer.

There are two loops: the interface accepts multiple user turns, while the controller handles tool calls inside one turn. Each turn permits at most four model requests. The last request disables tools to encourage a final answer. The last completed response ID supplies context on the next user turn. Instructions are supplied on each model request.

## 3. Prepare the project

Install Python and open a terminal in the extracted `study-notes-agent` folder. The dependencies were checked here with Python 3.12. Use Python 3.12 for deployment.

In Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Using the virtual environment's executable directly avoids PowerShell activation-policy problems.

## 4. Configure private secrets

Create `.streamlit/secrets.toml` locally and copy the structure of `secrets.example.toml`. Replace the example values privately with a new API key and a separate class access code. Set `ENABLE_LIVE = true` to permit live AI. The API account must have available credit. Never upload the real secrets file to GitHub or send the API key in a chat. A previously exposed key should be revoked and replaced.

The class access code is not the API key. It protects the owner-funded classroom demo. Visitors can still open a read-only preview without it.

## 5. Define the allowed action

Read `save_note` in `agent_core.py`. It accepts content and the current session state, checks that the text is not empty or too long, creates a filename using UTC time plus a random suffix, and stores the note in session memory. It returns a structured success result containing the filename. Each session can hold up to ten notes.

The browser's **Download Markdown** button creates the user's persistent local copy. A web note is not a permanent cloud file. The terminal wrapper instead writes new notes to the local `notes` folder.

## 6. Describe the tool to the model

`TOOLS` contains a function schema named `save_note`. Its JSON object has one required string property, `content`; additional properties are disallowed. Strict mode constrains the model's function arguments. Runtime checks are still necessary: `execute_tool` rejects unknown tools, invalid JSON, extra properties and invalid content. It caches tool results by call ID to avoid repeating the same call's action.

This schema tells the model what it can request. It does not itself run the function.

## 7. Call the model and handle tool results

Read `run_turn` in `agent_core.py`:

1. Validate the user message and turn count.
2. Reserve a request from the demo allowance before calling the API.
3. Call `client.responses.create` with the model, instructions, input and tools.
4. Reject an incomplete response rather than executing partial arguments.
5. If the response contains text and no function calls, return it.
6. Otherwise execute the allowed calls and produce matching `function_call_output` messages.
7. Send the outputs back with `previous_response_id` and continue within the bound.

The actual model identifier displayed in the interface comes from `response.model`. The model does not need to be asked to identify itself.

## 8. Preserve conversation state

`AgentState` stores the last completed response ID, turn count, notes and executed tool results. Each Streamlit session has its own instance. This supports requests such as “save that explanation.” **New conversation** clears the conversation reference and chat but keeps already created notes in that session.

The API reference supplies provider-side conversational context. This is not offline memory or a promise of zero data retention. Prompts and generated content are sent to OpenAI; do not enter private secrets.

## 9. Add the web interface

`app.py` provides a chat page, educational explanation and demo guide. The sidebar accepts the class code, and successful tool calls show their result in the chat. The notes column offers previews and downloads. The server reads the API key from environment variables or private Streamlit secrets.

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open the local URL printed by Streamlit. Enter your class access code in the sidebar. If you see only the read-only preview, check all three secret settings and restart the app.

## 10. Verify the behavior

First run the deterministic offline tests:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Then perform a real API test:

1. `Explain DFA in three sentences. Do not save it yet.` — expect a response without a note.
2. `Give one example of a language it can recognize.` — expect a follow-up about DFAs.
3. `Save both explanations as study notes.` — expect a successful tool result and a new note.
4. Preview and download the Markdown file; open it to inspect its content.
5. Ask for another note and check the filenames are different.

Model behavior is probabilistic. A passed offline test proves the controller's behavior for its simulated responses; it does not guarantee every future model choice. See `TEST_REPORT.md` for exactly what has been checked.

## 11. Publish the project

Create a public GitHub repository, such as `study-notes-agent`. Upload the Python source, requirements, tests, guides, license, `secrets.example.toml` and `.streamlit/config.toml`. Do not upload `.streamlit/secrets.toml`, `.env`, virtual environments, caches or personal notes. The included `.gitignore` helps with Git, but manually uploaded files still require care.

In Streamlit Community Cloud, connect GitHub, create an app from that repository and choose `app.py` as the entrypoint. Select Python 3.12 in advanced settings. Add the three actual secret values in the private secrets settings. Deploy, then inspect the build logs if necessary.

Open the resulting public URL in a private browser window. Verify the preview without a code, then unlock with the class code and repeat the three-prompt test. Give the teacher the app URL, repository URL and access code privately. If the teacher requires unrestricted anonymous live use, discuss that requirement; this package intentionally uses controlled live access to owner-funded API calls.

Deployment is not completed merely by preparing this package. Record and submit the actual URLs after those steps succeed. For the last presentation slide, you may add the real URLs after verification; do not insert invented links.

## 12. Explain the course connection

The controller can be described with finite control states: waiting, requesting, executing, completed and failed. A tool call sends control from requesting to executing, then back to requesting with the result. Text completes the turn; errors stop it. The request bound prevents an indefinite tool loop.

This is an analogy to finite-state control, not a claim that the complete AI system is a DFA. External model computation, conversation data and note storage are separate concerns.

For note length n, validating and retaining content requires O(n) work and O(n) stored content. The number of model requests per turn is bounded by k ≤ 4. That bound does not make model inference constant-cost: latency and token use depend on input, context, output and the service. Bounded execution does not establish factual correctness.

## 13. Limits and failure behavior

The interface permits ten turns per conversation, ten notes per session, a short request cooldown, and sixty reserved model requests per server process. Restarting resets the process budget, so it is not a hard account billing cap. The access-attempt limit also resets with the process. These are classroom demo controls, not production authentication or distributed rate limiting.

AI answers can be wrong and there is no web search tool. Session notes may disappear after disconnecting; download them. If a save succeeds but the model's final request fails, the note remains available and the app clears ambiguous conversation context. Check notes before retrying.

## 14. Present the assignment

Use the accompanying 12-slide presentation and speaker notes. Allow about 6–8 minutes plus a live demo. Cover the definition, action/result loop, architecture, creation steps, deployment, demo, course connection and limitations. Demonstrate both a text-only turn and a tool-using turn. Keep the real API key out of the projected screen.

## Official references

- OpenAI function calling: https://developers.openai.com/api/docs/guides/function-calling
- OpenAI conversation state: https://developers.openai.com/api/docs/guides/conversation-state
- Streamlit session state: https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state
- Streamlit deployment: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app
- Streamlit secrets management: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management
