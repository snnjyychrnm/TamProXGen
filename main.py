from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from dotenv import load_dotenv
from groq import Groq
from fuzzywuzzy import fuzz
from typing import Optional
import pandas as pd
import os

# Load .env and API Key
load_dotenv()
GROQ_API_KEY = os.getenv("API_KEY")
try:
    client = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    print(f"Error initializing Groq client: {e}")
    client = None

# Load proverb data
try:
    data = pd.read_json("preprocessed_tamil_proverbs.json")
except FileNotFoundError:
    print("Error: preprocessed_tamil_proverbs.json not found.")
    data = pd.DataFrame()
except Exception as e:
    print(f"Error loading proverb data: {e}")
    data = pd.DataFrame()

# App Initialization
app = FastAPI(title="TamProGen API", docs_url=None, redoc_url=None)

# CORS for frontend interaction
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Use specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static and Template Setup
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Request Models
class ProverbQuery(BaseModel):
    input_text: str

class FilterQuery(BaseModel):
    type: Optional[str] = "All"
    keyword: Optional[str] = ""

# HTML Routes (for full-page navigation if needed)
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login", response_class=HTMLResponse)
async def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == "admin" and password == "admin":
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})

@app.get("/signup", response_class=HTMLResponse)
async def signup_get(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.post("/signup", response_class=HTMLResponse)
async def signup_post(request: Request, username: str = Form(...), password: str = Form(...)):
    return RedirectResponse(url="/login", status_code=302)

# Helper Functions
def search_proverb(user_input):
    best_score = 0
    best_match = None
    if data.empty:
        return None
    for _, row in data.iterrows():
        tamil_score = fuzz.partial_ratio(user_input.lower(), row['Proverb (Tamil)'].lower())
        translit_score = fuzz.partial_ratio(user_input.lower(), row['Proverb (Transliteration)'].lower())
        score = max(tamil_score, translit_score)
        if score > best_score:
            best_score = score
            best_match = row
    return best_match if best_score >= 70 else None

def generate_explanation(proverb_text):
    if client is None:
        return "❌ Error: Groq client not initialized. Check API key."
    prompt = f"""You are a Tamil language expert. Explain the following Tamil proverb in detail.

Tamil Proverb: {proverb_text}

Provide your response in this format:
1. Transliteration
2. Meaning in Tamil (brief and full Tamil)
3. Meaning in English
4. Example Usage in Tamil
5. Example Usage in English
6. Literal or Figurative (explain briefly)
"""
    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=1,
            max_tokens=1024,
            top_p=1,
            stream=False
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Error: {e}"

# API: Proverb Search
@app.post("/search/")
def search(query: ProverbQuery):
    matched = search_proverb(query.input_text)
    if matched is not None:
        return {
            "found": True,
            "result": {
                "Proverb_Tamil": matched["Proverb (Tamil)"],
                "Transliteration": matched["Proverb (Transliteration)"],
                "Meaning_Tamil": matched["Meaning (Tamil)"],
                "Meaning_English": matched["Meaning (English)"],
                "Example_Tamil": matched["Example Usage (Tamil)"],
                "Example_English": matched["Example Usage (English)"],
                "Type": matched["Literal/Figurative"]
            }
        }
    else:
        explanation = generate_explanation(query.input_text)
        return {"found": False, "generated": explanation}

# API: Filter Proverbs
@app.post("/filter/")
def filter_proverbs(filters: FilterQuery):
    filtered = data.copy()
    if data.empty:
        return {"results": []}
    if filters.type.lower() != "all":
        filtered = filtered[filtered["Literal/Figurative"].str.lower() == filters.type.lower()]
    if filters.keyword:
        mask = (
            filtered["Proverb (Tamil)"].str.contains(filters.keyword, case=False, na=False) |
            filtered["Proverb (Transliteration)"].str.contains(filters.keyword, case=False, na=False)
        )
        filtered = filtered[mask]
    return {
        "results": filtered[["Proverb (Tamil)", "Meaning (English)", "Literal/Figurative"]].to_dict(orient="records")
    }
