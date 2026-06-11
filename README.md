# Minecraft_Ai_Builder_project
# 🧱 Minecraft AI Builder

A Minecraft-inspired 3D building game powered by a trained ML model. Type natural language commands like *"build a castle"* or *"make a wooden house next to a tower"* and watch the AI construct it in real time inside a 3D world.

---

## 🎮 Features

- 3D first-person world built with **Panda3D**
- **AI-powered building** — understands natural language prompts
- Supports structures: house, tower, pyramid, wall, castle, bridge, village, town and more
- **Compound prompts** — e.g. *"build a bridge and a house next to it"*
- Size modifiers — tiny, small, big, huge
- Style/material modifiers — modern, medieval, wooden, desert, jungle
- Drag and reposition built structures
- AI companion character that reacts to builds
- Block types: grass, dirt, stone, sand, wood, glass, brick

---

## 🚀 Getting Started

### Prerequisites
- Python 3.13
- Windows (the run script is `.bat`)

### Installation & Run

**First time setup:**
```bash
run.bat
```
This will automatically install dependencies and train the ML model if `model.pkl` doesn't exist.

**Manual setup:**
```bash
pip install -r requirements.txt
python setup.py       # trains and saves the ML model
python main.py        # launches the game
```

---

## 🕹️ Controls

| Key | Action |
|-----|--------|
| W A S D | Move |
| Mouse | Look around |
| Left Click | Place block |
| Right Click | Remove block |
| T | Open AI chat |
| Escape | Release mouse |

---

## 💬 Example AI Prompts

```
build a house
make a huge castle
create a wooden bridge
build a medieval tower next to a small house
make a desert pyramid
build a village
```

---

## 📁 Project Structure

```
├── main.py              # Game engine & main loop
├── ai_builder.py        # AI prompt parser & structure builder
├── chat_ui.py           # In-game chat interface
├── companion.py         # AI companion character
├── train_model.py       # ML model training script
├── generate_data.py     # Training data generation
├── setup.py             # First-run setup script
├── run.bat              # One-click launcher (Windows)
├── requirements.txt     # Python dependencies
├── settings.prc         # Panda3D settings
└── skybox/              # Skybox textures
```

---

## 🧠 How the AI Works

The AI uses a **scikit-learn ML model** (`model.pkl`) trained on labeled building prompts. It classifies:
- **Intent** — what structure to build (house, tower, castle, etc.)
- **Size** — tiny / small / normal / big / huge
- **Material** — wood, stone, sand, glass, brick

It also handles **compound prompts** by splitting on keywords like *"and"*, *"next to"*, *"beside"*, *"with"* to build multiple structures at once.

---

## 📦 Dependencies

```
panda3d
scikit-learn
numpy
```

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
