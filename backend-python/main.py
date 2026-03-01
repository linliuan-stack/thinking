from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional

from auth import verify_password, get_password_hash, create_access_token, get_current_user
from database import get_db

app = FastAPI(title="Thinking Auth Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class UserRegister(BaseModel):
    username: str
    password: str
    email: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str]
    role: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


@app.get("/api/auth/health")
def health():
    return {"status": "ok", "service": "auth-python"}


@app.post("/api/auth/register", response_model=UserResponse)
def register(user: UserRegister, conn=Depends(get_db)):
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE username = %s", (user.username,))
    if cur.fetchone():
        raise HTTPException(status_code=400, detail="用户名已存在")

    password_hash = get_password_hash(user.password)
    cur.execute(
        "INSERT INTO users (username, password_hash, email, role) VALUES (%s, %s, %s, %s) RETURNING id, username, email, role",
        (user.username, password_hash, user.email, "user"),
    )
    new_user = cur.fetchone()
    conn.commit()

    cur.execute("SELECT id FROM modules")
    modules = cur.fetchall()
    for mod in modules:
        cur.execute(
            "INSERT INTO user_permissions (user_id, module_id, can_access) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
            (new_user["id"], mod["id"], True),
        )
    conn.commit()

    return new_user


@app.post("/api/auth/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), conn=Depends(get_db)):
    cur = conn.cursor()
    cur.execute("SELECT id, username, email, role, password_hash, is_active FROM users WHERE username = %s", (form_data.username,))
    user = cur.fetchone()

    if not user or not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")

    if not user["is_active"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账户已被禁用")

    access_token = create_access_token(data={"sub": user["username"], "role": user["role"]})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"id": user["id"], "username": user["username"], "email": user["email"], "role": user["role"]},
    }


@app.get("/api/auth/me", response_model=UserResponse)
def get_me(current_user=Depends(get_current_user)):
    return current_user


@app.get("/api/auth/users")
def list_users(current_user=Depends(get_current_user), conn=Depends(get_db)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="权限不足")
    cur = conn.cursor()
    cur.execute("SELECT id, username, email, role, is_active, created_at FROM users ORDER BY id")
    return cur.fetchall()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
