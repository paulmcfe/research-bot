# 🔬 ResearchBot Frontend

A sleek, modern chat interface for your AI research assistant. Built with pure vanilla HTML, CSS, and JavaScript – no bloated frameworks here!

## ✨ Features

- **Dark mode by default** – Easy on the eyes, stylish by nature
- **Real-time chat** – Send messages and get AI responses instantly
- **Responsive design** – Looks great on phones, tablets, and desktops
- **Accessible** – Screen reader friendly with proper ARIA labels
- **Loading indicators** – Know when ResearchBot is thinking
- **Auto-resizing input** – Write long messages without awkward scrollbars

## 🚀 Getting Started

### Prerequisites

Make sure your backend is running first! The frontend expects the API at `http://localhost:8000`.

```bash
# From the project root, start the backend:
uvicorn api.index:app --reload
```

### Running the Frontend

**Option 1: Python's built-in server (recommended)**

```bash
cd frontend
python -m http.server 3000
```

Then open [http://localhost:3000](http://localhost:3000) in your browser.

**Option 2: VS Code Live Server**

If you have the Live Server extension, right-click `index.html` and select "Open with Live Server".

**Option 3: Just open the file**

Double-click `index.html` in your file browser. Note: This might have CORS issues depending on your browser settings.

## 🎨 Customization

The color scheme uses CSS variables defined in `styles.css`. Feel free to tweak them:

```css
:root {
    --primary: hsl(217 91% 60%);      /* Blue accents */
    --background: hsl(215 28% 17%);   /* Dark background */
    --text: hsl(210 20% 98%);         /* Light text */
    --accent: hsl(160 84% 39%);       /* Green highlights */
}
```

## 📁 File Structure

```
frontend/
├── index.html    # Main HTML structure
├── styles.css    # All the pretty styling
├── script.js     # Chat logic and API calls
└── README.md     # You are here! 👋
```

## 🔧 Configuration

Need to point to a different backend? Update the API URL in `script.js`:

```javascript
const API_BASE_URL = 'http://localhost:8000';
```

## 🐛 Troubleshooting

**"Unable to connect to the server"**
- Is your backend running? Check with `curl http://localhost:8000`
- Make sure CORS is enabled on the backend (it is by default)

**Styles look broken**
- Make sure all three files (`index.html`, `styles.css`, `script.js`) are in the same folder
- Clear your browser cache with Ctrl+Shift+R (or Cmd+Shift+R on Mac)

---

Happy researching! 🎉
