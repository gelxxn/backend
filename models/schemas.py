from pydantic import BaseModel

class RegisterRequest(BaseModel):
    email: str
    password: str
    display_name: str

class LoginRequest(BaseModel):
    email: str
    password: str

class ProgressRequest(BaseModel):
    vocab_id: str
    level: int
    sub_category: str
    is_completed: bool
    best_score: float