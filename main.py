import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field

# Database helpers (provided by environment)
try:
    from database import db, create_document, get_documents  # type: ignore
except Exception:
    db = None
    def create_document(collection_name: str, data):  # type: ignore
        return "mock-id"
    def get_documents(collection_name: str, filter_dict=None, limit: int | None = None):  # type: ignore
        return []

app = FastAPI(title="FreeDAIY API", version="1.0.0")

# CORS - allow all during preview
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Health & Test ----------
@app.get("/")
def read_root():
    return {"message": "FreeDAIY API is running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        from database import db as real_db  # type: ignore
        if real_db is not None:
            response["database"] = "✅ Available"
            try:
                names = real_db.list_collection_names()
                response["collections"] = names[:10]
                response["database"] = "✅ Connected & Working"
                response["connection_status"] = "Connected"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:60]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:60]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response


# ---------- Schemas ----------
class LeadCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    company: Optional[str] = None
    current_tools: Optional[str] = Field(None, description="What tools they currently use")
    message: Optional[str] = Field(None, description="What they want to automate / build")


class LeadResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    company: Optional[str] = None


class SubscribeCreate(BaseModel):
    email: EmailStr
    interests: Optional[List[str]] = Field(default_factory=list)


class SubscribeResponse(BaseModel):
    id: str
    email: EmailStr
    interests: List[str] = Field(default_factory=list)


class Post(BaseModel):
    id: str
    title: str
    category: str
    preview: str
    reading_time: str


class Product(BaseModel):
    id: str
    title: str
    description: str
    tag: str
    level: str


class Resource(BaseModel):
    id: str
    title: str
    kind: str
    blurb: str
    tags: List[str]


# ---------- Business Endpoints ----------
@app.post("/leads", response_model=LeadResponse)
async def create_lead(payload: LeadCreate):
    try:
        doc = payload.model_dump()
        inserted_id = create_document("lead", doc)
        return {
            "id": str(inserted_id),
            "name": payload.name,
            "email": payload.email,
            "company": payload.company,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save lead: {e}")


@app.post("/subscribe", response_model=SubscribeResponse)
async def subscribe(payload: SubscribeCreate):
    try:
        doc = payload.model_dump()
        inserted_id = create_document("subscriber", doc)
        return {
            "id": str(inserted_id),
            "email": payload.email,
            "interests": payload.interests or [],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to subscribe: {e}")


@app.get("/posts", response_model=List[Post])
async def list_posts():
    return [
        {
            "id": "post-ai-productivity",
            "title": "Designing calm, hands-free AI flows",
            "category": "AI Productivity",
            "preview": "Principles to build voice-first workflows that reduce clicks and context switching.",
            "reading_time": "6 min",
        },
        {
            "id": "post-n8n-make",
            "title": "Nailing robust automations with n8n + Make.com",
            "category": "Automations",
            "preview": "Patterns for reliability, retries, and observability in production workflows.",
            "reading_time": "7 min",
        },
        {
            "id": "post-self-hosted-ai",
            "title": "Private AI: self-hosting strategies",
            "category": "Self-Hosted AI",
            "preview": "From LLM gateways to vector stores — what to run and where.",
            "reading_time": "8 min",
        },
    ]


@app.get("/products", response_model=List[Product])
async def list_products():
    return [
        {
            "id": "n8n-crm-sync",
            "title": "CRM Sync: Leads → Deals n8n workflow",
            "description": "Auto-creates deals from form leads with enrich + dedupe.",
            "tag": "CRM",
            "level": "Intermediate",
        },
        {
            "id": "ops-daily-digest",
            "title": "Ops Daily Digest",
            "description": "Slack summary of KPIs, incidents, and tasks across tools.",
            "tag": "Operations",
            "level": "Beginner",
        },
        {
            "id": "marketing-utm-cleaner",
            "title": "UTM Cleaner + Attribution",
            "description": "Normalize UTM params and attribute signups across sessions.",
            "tag": "Marketing",
            "level": "Advanced",
        },
    ]


@app.get("/resources", response_model=List[Resource])
async def list_resources():
    return [
        {
            "id": "wf-n8n-intro",
            "title": "n8n Starter Pack",
            "kind": "Workflow",
            "blurb": "Five plug-and-play flows to kickstart automation.",
            "tags": ["Workflow", "n8n", "Starter"],
        },
        {
            "id": "inf-voice-design",
            "title": "Voice UX Principles",
            "kind": "Infographic",
            "blurb": "Design patterns for voice-first productivity.",
            "tags": ["Infographic", "Voice", "UX"],
        },
        {
            "id": "tpl-checklist",
            "title": "Automation Readiness Checklist",
            "kind": "Template",
            "blurb": "Assess your stack before you automate.",
            "tags": ["Template", "Readiness"],
        },
    ]


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
