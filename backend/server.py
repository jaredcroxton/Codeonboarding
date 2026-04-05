from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT config
JWT_SECRET = os.environ.get('JWT_SECRET', 'accorplus-academy-secret-key-change-in-production')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 72

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

security = HTTPBearer(auto_error=False)


# ─── Models ───────────────────────────────────────────────────────────

class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str


# Auth models
class UserRegister(BaseModel):
    email: str
    password: str
    name: str
    role: str = "team_member"  # team_member | manager

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    email: str
    name: str
    role: str
    created_at: str

class AuthResponse(BaseModel):
    token: str
    user: UserResponse


# Progress models
class ProgressUpdate(BaseModel):
    module_key: str  # e.g. "0-1" for dest 0, module 1
    programme: str = "onboarding"  # onboarding | leadership

class QuizResult(BaseModel):
    module_key: str
    programme: str = "onboarding"
    score: int
    total: int
    answers: Dict[str, Any] = {}

class UserProgress(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    completed_modules: Dict[str, bool] = {}
    quiz_results: List[Dict[str, Any]] = []
    leadership_completed: Dict[str, bool] = {}
    leadership_quiz_results: List[Dict[str, Any]] = []
    total_time_minutes: int = 0
    last_activity: str = ""

class LeaderboardEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str
    completed_modules: int
    total_modules: int
    quiz_accuracy: float
    completion_pct: float


# ─── Auth Helpers ─────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str, email: str, role: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    payload = decode_token(credentials.credentials)
    user = await db.users.find_one({"id": payload["sub"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


# ─── Status Routes (existing) ────────────────────────────────────────

@api_router.get("/")
async def root():
    return {"message": "Hello World"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    return status_checks


# ─── Auth Routes ──────────────────────────────────────────────────────

@api_router.post("/auth/register", response_model=AuthResponse)
async def register(input: UserRegister):
    existing = await db.users.find_one({"email": input.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    user_doc = {
        "id": user_id,
        "email": input.email,
        "password_hash": hash_password(input.password),
        "name": input.name,
        "role": input.role,
        "created_at": now
    }
    await db.users.insert_one(user_doc)

    # Initialize progress record
    await db.progress.insert_one({
        "user_id": user_id,
        "completed_modules": {},
        "quiz_results": [],
        "leadership_completed": {},
        "leadership_quiz_results": [],
        "total_time_minutes": 0,
        "last_activity": now
    })

    token = create_token(user_id, input.email, input.role)
    return AuthResponse(
        token=token,
        user=UserResponse(id=user_id, email=input.email, name=input.name, role=input.role, created_at=now)
    )

@api_router.post("/auth/login", response_model=AuthResponse)
async def login(input: UserLogin):
    user = await db.users.find_one({"email": input.email}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not verify_password(input.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_token(user["id"], user["email"], user["role"])
    return AuthResponse(
        token=token,
        user=UserResponse(
            id=user["id"], email=user["email"], name=user["name"],
            role=user["role"], created_at=user["created_at"]
        )
    )

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(user=Depends(get_current_user)):
    return UserResponse(
        id=user["id"], email=user["email"], name=user["name"],
        role=user["role"], created_at=user["created_at"]
    )


# ─── Progress Routes ─────────────────────────────────────────────────

@api_router.get("/progress", response_model=UserProgress)
async def get_progress(user=Depends(get_current_user)):
    progress = await db.progress.find_one({"user_id": user["id"]}, {"_id": 0})
    if not progress:
        raise HTTPException(status_code=404, detail="Progress not found")
    return progress

@api_router.post("/progress/complete-module")
async def complete_module(input: ProgressUpdate, user=Depends(get_current_user)):
    now = datetime.now(timezone.utc).isoformat()
    field = "completed_modules" if input.programme == "onboarding" else "leadership_completed"

    await db.progress.update_one(
        {"user_id": user["id"]},
        {
            "$set": {
                f"{field}.{input.module_key}": True,
                "last_activity": now
            }
        },
        upsert=True
    )
    return {"status": "ok", "module_key": input.module_key, "programme": input.programme}

@api_router.post("/progress/quiz-result")
async def save_quiz_result(input: QuizResult, user=Depends(get_current_user)):
    now = datetime.now(timezone.utc).isoformat()
    field = "quiz_results" if input.programme == "onboarding" else "leadership_quiz_results"

    result_doc = {
        "module_key": input.module_key,
        "score": input.score,
        "total": input.total,
        "answers": input.answers,
        "timestamp": now
    }
    await db.progress.update_one(
        {"user_id": user["id"]},
        {
            "$push": {f"{field}": result_doc},
            "$set": {"last_activity": now}
        },
        upsert=True
    )
    return {"status": "ok", "score": input.score, "total": input.total}

@api_router.post("/progress/add-time")
async def add_time(minutes: int, user=Depends(get_current_user)):
    now = datetime.now(timezone.utc).isoformat()
    await db.progress.update_one(
        {"user_id": user["id"]},
        {
            "$inc": {"total_time_minutes": minutes},
            "$set": {"last_activity": now}
        }
    )
    return {"status": "ok"}


# ─── Leaderboard Route ───────────────────────────────────────────────

@api_router.get("/leaderboard", response_model=List[LeaderboardEntry])
async def get_leaderboard():
    """Get top learners ranked by completion percentage and quiz accuracy."""
    users = await db.users.find({}, {"_id": 0, "id": 1, "name": 1}).to_list(1000)
    progress_list = await db.progress.find({}, {"_id": 0}).to_list(1000)

    progress_map = {p["user_id"]: p for p in progress_list}
    total_possible = 19  # total modules across all destinations

    entries = []
    for u in users:
        prog = progress_map.get(u["id"], {})
        completed = prog.get("completed_modules", {})
        quizzes = prog.get("quiz_results", [])

        completed_count = sum(1 for v in completed.values() if v)
        completion_pct = round((completed_count / total_possible) * 100, 1) if total_possible > 0 else 0

        total_score = sum(q.get("score", 0) for q in quizzes)
        total_questions = sum(q.get("total", 0) for q in quizzes)
        quiz_accuracy = round((total_score / total_questions) * 100, 1) if total_questions > 0 else 0

        entries.append(LeaderboardEntry(
            name=u["name"],
            completed_modules=completed_count,
            total_modules=total_possible,
            quiz_accuracy=quiz_accuracy,
            completion_pct=completion_pct
        ))

    entries.sort(key=lambda e: (-e.completion_pct, -e.quiz_accuracy))
    return entries[:50]


# ─── Manager Routes ──────────────────────────────────────────────────

@api_router.get("/manager/team-stats")
async def get_team_stats(user=Depends(get_current_user)):
    if user["role"] != "manager":
        raise HTTPException(status_code=403, detail="Manager access required")

    users = await db.users.find({"role": "team_member"}, {"_id": 0}).to_list(1000)
    progress_list = await db.progress.find({}, {"_id": 0}).to_list(1000)
    progress_map = {p["user_id"]: p for p in progress_list}

    total_possible = 19
    active_count = 0
    total_completion = 0
    total_quiz_score = 0
    total_quiz_questions = 0
    team_members = []

    for u in users:
        prog = progress_map.get(u["id"], {})
        completed = prog.get("completed_modules", {})
        quizzes = prog.get("quiz_results", [])
        completed_count = sum(1 for v in completed.values() if v)
        completion_pct = round((completed_count / total_possible) * 100, 1) if total_possible > 0 else 0

        if completed_count > 0:
            active_count += 1
        total_completion += completion_pct

        for q in quizzes:
            total_quiz_score += q.get("score", 0)
            total_quiz_questions += q.get("total", 0)

        team_members.append({
            "id": u["id"],
            "name": u["name"],
            "email": u["email"],
            "completed_modules": completed_count,
            "completion_pct": completion_pct,
            "last_activity": prog.get("last_activity", ""),
            "total_time_minutes": prog.get("total_time_minutes", 0)
        })

    avg_completion = round(total_completion / len(users), 1) if users else 0
    quiz_accuracy = round((total_quiz_score / total_quiz_questions) * 100, 1) if total_quiz_questions > 0 else 0

    return {
        "active_learners": active_count,
        "total_learners": len(users),
        "avg_completion": avg_completion,
        "quiz_accuracy": quiz_accuracy,
        "team_members": sorted(team_members, key=lambda x: -x["completion_pct"])
    }


# ─── App Setup ────────────────────────────────────────────────────────

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
