MASTER CONTEXT FOR FASTBOARD HACKATHON PROJECT

**Project Goal:** Build "FastBoard," a real-time, collaborative whiteboard web application.
**Core Technologies:**
  - **Backend:** Python with FastAPI. We will use the `uvicorn` server for development.
  - **Frontend:** Pure FastHTML, served from the FastAPI backend. All dynamic UI updates must be driven by FastHTML over WebSockets where possible.
  - **Styling:** Tailwind CSS, loaded via CDN in the main HTML template.
  - **Real-Time Collaboration:** Achieved using Python WebSockets (`websockets` library) integrated with FastAPI.
  - **Client-Side Logic:** Minimal vanilla JavaScript is ONLY for HTML Canvas manipulation (drawing pixels) and WebSocket communication. All other interactivity should be handled by FastHTML.

**Data Structures (JSON):** All WebSocket messages must be JSON strings and follow this schema:
  - **Drawing Action:** `{"type": "draw", "clientId": "...", "payload": {"tool": "pen/eraser", "color": "#RRGGBB", "size": integer, "points": [{"x": number, "y": number}, ...]}}`
  - **Text Action:** `{"type": "text", "clientId": "...", "payload": {"content": "...", "x": number, "y": number, "font": "...", "color": "..."}}`
  - **Clear Board:** `{"type": "clear", "clientId": "..."}`
  - **Cursor Position:** `{"type": "cursor", "clientId": "...", "payload": {"x": number, "y": number}}`
  - **User Count:** `{"type": "user_count", "payload": {"count": integer}}`

**AI Feature ("AI Assist"):**
  - **Goal:** A button that sends the current canvas state to the backend. The backend sends it to an AI vision model (like GPT-4o) to interpret the drawing.
  - **Process:**
    1. Client-side JS captures the canvas as a Base64 encoded PNG string.
    2. This string is sent to a dedicated FastAPI REST endpoint (e.g., `/ai-assist`).
    3. The backend makes a call to the OpenAI API. The API key is stored in a `.env` file and loaded using `python-dotenv`.
    4. The AI's task is to interpret the image and return a structured response, such as Mermaid.js diagram code or a Markdown list.
    5. The FastAPI endpoint returns this structured text.
    6. The client displays the response in a modal overlay.

**Coding Style & Principles:**
  - Adhere strictly to PEP 8 for all Python code.
  - Use type hints for all Python function definitions.
  - Functions should have a single responsibility.
  - Use clear, descriptive variable and function names.
  - All user-facing text should be professional and clear.
  - Comment complex logic, especially in the WebSocket handling and canvas drawing code.

**File Structure:**
  - `main.py`: The main FastAPI application file.
  - `requirements.txt`: Project dependencies.
  - `.env`: For the `OPENAI_API_KEY`.
  - `templates/`: Contains the main `index.html` template.
  - `static/`: For any static assets, like a CSS file or client-side `board.js`.