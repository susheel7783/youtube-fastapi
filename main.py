from fastapi import FastAPI, Form, UploadFile, Depends,HTTPException,File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from werkzeug.security import generate_password_hash, check_password_hash
import os, shutil, uuid, datetime

DATABASE_URL = "sqlite:///database.db"
engine= create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

UPLOAD_DIR="./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    email = Column(String)
    password = Column(String)

class Video(Base):
    __tablename__ = 'videos'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    description = Column(Text)
    filename = Column(String)
    likes = Column(Integer, default=0)
    uploader_id = Column(Integer, ForeignKey('users.id'))
    uploader = relationship("User")



class Like(Base):
    __tablename__ = 'likes'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    video_id = Column(Integer, ForeignKey('videos.id'))
    
class Comment(Base):
    __tablename__ = 'comments'
    id = Column(Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey('videos.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    user=relationship("User")


Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()  


def get_user_by_token(token: str, db: Session):
    return db.query(User).filter(User.username == token).first()

@app.post("/register")
def register(
    username: str = Form(...),
    email: str = Form(...), 
    password: str   = Form(...),
    db: Session = Depends(get_db)
):
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    hashed_pw = generate_password_hash(password)
    user = User(username=username, email=email, password=hashed_pw)
    db.add(user)
    db.commit()
    return {"message": "User registered successfully"}



@app.post("/login")
def login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()
    if not user or not check_password_hash(user.password, password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    return {"access_token": user.username, "token_type": "bearer"}  # Using username as token for simplicity   

@app.post("/upload")
def upload_video(
    title: str = Form(...),
    description: str = Form(...),
    token: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)       
):
    if not title.strip() or not description.strip():
        raise HTTPException(status_code=400, detail="Title and description cannot be empty")
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")
    
    user = get_user_by_token(token, db)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid token")
    
    file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}_{file.filename}")
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    video= Video(
        title=title,
        description=description,
        filename=file_path,
        uploader_id=user.id
    )
    db.add(video)
    db.commit()
    db.refresh(video)
    return {"message": "Video uploaded successfully", "id": video.id}    


@app.get("/videos")
def list_videos(db: Session = Depends(get_db)):
    videos = db.query(Video).all()
    return [
        {
            "id": video.id,
            "title": video.title,
            "description": video.description,
            "likes": video.likes,
            "uploader": video.uploader.username 
        }   
        for video in videos 
    ]    

@app.get("/video/{video_id}")
def stream_video(video_id: int, db: Session = Depends(get_db)):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return FileResponse(video.filename, media_type="video/mp4")



@app.post("/like/{video_id}")
def like_video(
    video_id: int,
    token: str = Form(...),
    db: Session = Depends(get_db)
):
    user = get_user_by_token(token, db)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid token")
    
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    existing_like = db.query(Like).filter(Like.user_id == user.id, Like.video_id == video_id).first()
    if existing_like:
        db.delete(existing_like)
        video.likes -= 1
        liked=False
    else:
        like=Like(user_id=user.id, video_id=video_id)
        db.add(like)
        video.likes += 1
        liked=True
    db.commit()
    return {"likes": video.likes, "liked": liked}


@app.post("/liked/{video_id}")
def check_liked(
    video_id: int,
    token: str = Form(...),
    db: Session = Depends(get_db)
):
    user = get_user_by_token(token, db)
    if not user:
        return {"liked": False}
    liked= db.query(Like).filter(Like.user_id == user.id, Like.video_id == video_id).first() is not None
    return {"liked": liked}

@app.get("/comments/{video_id}")
def get_comments(video_id: int, db: Session = Depends(get_db)):
    comments = db.query(Comment).filter(Comment.video_id == video_id).all()

    return [
        {
            "id": c.id,
            "user": c.user.username,
            "content": c.content,
            "timestamp": c.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        }
        for c in comments
    ]
    
   
@app.post("/comment/{video_id}")
def add_comment(
    video_id: int,
    token: str = Form(...),
    content: str = Form(...),   
    db: Session = Depends(get_db)
):
    user = get_user_by_token(token, db)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid token")
    
    if not content.strip():
        raise HTTPException(status_code=400, detail="Comment cannot be empty")
    
    
    comment = Comment(
        video_id=video_id,
        user_id=user.id,
        content=content
    )
    db.add(comment)
    db.commit()
    return {"message": "Comment added successfully"}


@app.delete("/video/{video_id}")    
def delete_video(
    video_id: int,
    token: str = Form(...),
    db: Session = Depends(get_db)
):
    user = get_user_by_token(token, db)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid token")
    
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    if video.uploader_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this video")
    
    try:
        os.remove(video.filename)
    except FileNotFoundError:
        pass
        
    db.delete(video)
    db.commit()
    return {"message": "Video deleted successfully"}