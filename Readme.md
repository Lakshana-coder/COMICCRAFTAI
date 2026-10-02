# ComicCraft

ComicCraft is an AI-powered web application that turns a user's
story idea into a five-panel comic.

## Features

- FastAPI backend
- Jinja2 frontend
- Gemini-powered story outline
- Gemini-powered narration and dialogue
- AI image generation
- Five connected comic panels
- PDF export
- JSON API
- Swagger API documentation
- Image testing endpoint

## Project Flow

User Input
    ↓
Gemini Outline
    ↓
Five Panel Story Structure
    ↓
Gemini Story
    ↓
Narration + Dialogue
    ↓
Image Generation
    ↓
Comic Layout
    ↓
PDF Export

## Requirements

- Python 3.11+
- Google Gemini API key
- Hugging Face token
- Internet connection

## Installation

Create a virtual environment.

### Windows

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1