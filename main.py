# FastAPI: Modern, fast web framework for building APIs with Python
# Used here to create the video sharing platform's backend server
from fastapi import FastAPI, Form, UploadFile, Depends, HTTPException, File

# CORSMiddleware: Handles Cross-Origin Resource Sharing
# Allows frontend applications from different domains to communicate with this API
from fastapi.middleware.cors import CORSMiddleware

# FileResponse: Used to send files (videos) as HTTP responses
# Enables video streaming to clients
from fastapi.responses import FileResponse

# SQLAlchemy components for database operations:
# - create_engine: Creates database connection
# - Column, Integer, String, ForeignKey, Text, DateTime: Define table column types
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Text, DateTime

# declarative_base: Base class for ORM models
# Provides the foundation for creating database table classes
from sqlalchemy.ext.declarative import declarative_base

# sessionmaker: Creates database session factory
# relationship: Defines relationships between tables
# Session: Type hint for database sessions
from sqlalchemy.orm import sessionmaker, relationship, Session

# Werkzeug security functions:
# - generate_password_hash: Encrypts passwords before storing
# - check_password_hash: Verifies password against stored hash
from werkzeug.security import generate_password_hash, check_password_hash

# Standard library imports:
# - os: File system operations (create directories, remove files)
# - shutil: High-level file operations (copy uploaded files)
# - uuid: Generate unique identifiers for uploaded files
# - datetime: Handle timestamps for comments
import os, shutil, uuid, datetime

# Database configuration
# SQLite database file path - stores all application data
DATABASE_URL = "sqlite:///database.db"

# Create database engine with SQLite-specific configuration
# check_same_thread=False allows multiple threads to use the same connection
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Session factory for creating database sessions
# bind=engine connects sessions to our database
SessionLocal = sessionmaker(bind=engine)

# Base class for all ORM models
# All database table classes will inherit from this
Base = declarative_base()

# Directory path for storing uploaded video files
UPLOAD_DIR = "./uploads"

# Create uploads directory if it doesn't exist
# exist_ok=True prevents error if directory already exists
os.makedirs(UPLOAD_DIR, exist_ok=True)


# User model - represents the 'users' table in database
# Stores user account information
class User(Base):
    # Table name in the database
    __tablename__ = 'users'
    
    # Primary key - unique identifier for each user
    id = Column(Integer, primary_key=True)
    
    # Username - must be unique across all users
    username = Column(String, unique=True)
    
    # Email address of the user
    email = Column(String)
    
    # Hashed password (never store plain text passwords)
    password = Column(String)


# Video model - represents the 'videos' table in database
# Stores information about uploaded videos
class Video(Base):
    # Table name in the database
    __tablename__ = 'videos'
    
    # Primary key - unique identifier for each video
    id = Column(Integer, primary_key=True)
    
    # Video title displayed to users
    title = Column(String)
    
    # Longer description of the video content
    description = Column(Text)
    
    # File path where the video file is stored on disk
    filename = Column(String)
    
    # Number of likes the video has received (defaults to 0)
    likes = Column(Integer, default=0)
    
    # Foreign key linking to the user who uploaded this video
    uploader_id = Column(Integer, ForeignKey('users.id'))
    
    # Relationship to access the User object who uploaded this video
    uploader = relationship("User")


# Like model - represents the 'likes' table in database
# Tracks which users liked which videos (many-to-many relationship)
class Like(Base):
    # Table name in the database
    __tablename__ = 'likes'
    
    # Primary key - unique identifier for each like
    id = Column(Integer, primary_key=True)
    
    # Foreign key linking to the user who liked
    user_id = Column(Integer, ForeignKey('users.id'))
    
    # Foreign key linking to the video that was liked
    video_id = Column(Integer, ForeignKey('videos.id'))


# Comment model - represents the 'comments' table in database
# Stores user comments on videos
class Comment(Base):
    # Table name in the database
    __tablename__ = 'comments'
    
    # Primary key - unique identifier for each comment
    id = Column(Integer, primary_key=True)
    
    # Foreign key linking to the video being commented on
    video_id = Column(Integer, ForeignKey('videos.id'))
    
    # Foreign key linking to the user who wrote the comment
    user_id = Column(Integer, ForeignKey('users.id'))
    
    # The actual comment text
    content = Column(Text)
    
    # When the comment was created (automatically set to current UTC time)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationship to access the User object who wrote this comment
    user = relationship("User")


# Create all tables in the database based on the models defined above
# Only creates tables that don't already exist
Base.metadata.create_all(bind=engine)

# Initialize FastAPI application instance
# This is the main application object
app = FastAPI()

# Add CORS middleware to allow cross-origin requests
# This enables frontend apps on different domains/ports to access the API
app.add_middleware(
    CORSMiddleware,
    # allow_origins=["*"]: Accept requests from any domain (use specific domains in production)
    allow_origins=["*"],
    # allow_credentials=True: Allow cookies and authentication headers
    allow_credentials=True,
    # allow_methods=["*"]: Allow all HTTP methods (GET, POST, DELETE, etc.)
    allow_methods=["*"],
    # allow_headers=["*"]: Allow all headers in requests
    allow_headers=["*"],
)


# Dependency function that provides database sessions to route handlers
# Automatically manages session lifecycle (creation and cleanup)
def get_db():
    # Create a new database session
    db = SessionLocal()
    try:
        # Yield the session to the route handler
        yield db
    finally:
        # Always close the session when done, even if an error occurs
        db.close()


# Helper function to authenticate users by their token
# Returns the User object if token is valid, None otherwise
def get_user_by_token(token: str, db: Session):
    # Simple authentication: token is the username
    # In production, use proper JWT tokens or session IDs
    return db.query(User).filter(User.username == token).first()


# Registration endpoint - creates new user accounts
# POST /register
@app.post("/register")
def register(
    # username: Required form field for username
    username: str = Form(...),
    # email: Required form field for email address
    email: str = Form(...),
    # password: Required form field for password (will be hashed)
    password: str = Form(...),
    # db: Database session injected by dependency
    db: Session = Depends(get_db)
):
    # Check if username already exists in database
    if db.query(User).filter(User.username == username).first():
        # Return 400 error if username is taken
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Hash the password using Werkzeug's secure hashing
    # Never store plain text passwords
    hashed_pw = generate_password_hash(password)
    
    # Create new User object with provided data
    user = User(username=username, email=email, password=hashed_pw)
    
    # Add user to database session
    db.add(user)
    
    # Commit the transaction to save to database
    db.commit()
    
    # Return success message
    return {"message": "User registered successfully"}


# Login endpoint - authenticates users and returns access token
# POST /login
@app.post("/login")
def login(
    # username: Required form field
    username: str = Form(...),
    # password: Required form field (plain text, will be verified against hash)
    password: str = Form(...),
    # db: Database session injected by dependency
    db: Session = Depends(get_db)
):
    # Query database for user with provided username
    user = db.query(User).filter(User.username == username).first()
    
    # Check if user exists and password matches the stored hash
    if not user or not check_password_hash(user.password, password):
        # Return 400 error if credentials are invalid
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    # Return access token (using username as token for simplicity)
    # In production, generate proper JWT tokens
    return {"access_token": user.username, "token_type": "bearer"}


# Video upload endpoint - allows users to upload videos
# POST /upload
@app.post("/upload")
def upload_video(
    # title: Required video title
    title: str = Form(...),
    # description: Required video description
    description: str = Form(...),
    # token: Authentication token to identify uploader
    token: str = Form(...),
    # file: The video file being uploaded
    file: UploadFile = File(...),
    # db: Database session injected by dependency
    db: Session = Depends(get_db)
):
    # Validate that title and description are not empty
    if not title.strip() or not description.strip():
        raise HTTPException(status_code=400, detail="Title and description cannot be empty")
    
    # Validate that a file was actually uploaded
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")
    
    # Authenticate the user using their token
    user = get_user_by_token(token, db)
    if not user:
        # Return error if token is invalid
        raise HTTPException(status_code=400, detail="Invalid token")
    
    # Generate unique filename using UUID to prevent collisions
    # Format: {random_uuid}_{original_filename}
    file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}_{file.filename}")
    
    # Save the uploaded file to disk
    with open(file_path, "wb") as f:
        # Copy file contents from upload to disk
        shutil.copyfileobj(file.file, f)

    # Create Video record in database
    video = Video(
        title=title,
        description=description,
        filename=file_path,  # Store file path for later retrieval
        uploader_id=user.id  # Link video to uploader
    )
    
    # Add video to database session
    db.add(video)
    
    # Commit transaction to save to database
    db.commit()
    
    # Refresh to get the auto-generated ID
    db.refresh(video)
    
    # Return success message with video ID
    return {"message": "Video uploaded successfully", "id": video.id}


# List all videos endpoint - returns video metadata
# GET /videos
@app.get("/videos")
def list_videos(db: Session = Depends(get_db)):
    # Query all videos from database
    videos = db.query(Video).all()
    
    # Return list of video information as JSON
    return [
        {
            "id": video.id,  # Video unique identifier
            "title": video.title,  # Video title
            "description": video.description,  # Video description
            "likes": video.likes,  # Number of likes
            "uploader": video.uploader.username  # Username of uploader
        }
        # Iterate through all videos
        for video in videos
    ]


# Video streaming endpoint - serves video files
# GET /video/{video_id}
@app.get("/video/{video_id}")
def stream_video(video_id: int, db: Session = Depends(get_db)):
    # Query database for video with specified ID
    video = db.query(Video).filter(Video.id == video_id).first()
    
    # Return 404 if video doesn't exist
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Return the video file as HTTP response
    # media_type="video/mp4" tells browser it's a video file
    return FileResponse(video.filename, media_type="video/mp4")


# Like/unlike video endpoint - toggles like status
# POST /like/{video_id}
@app.post("/like/{video_id}")
def like_video(
    # video_id: ID of video to like/unlike (from URL path)
    video_id: int,
    # token: Authentication token
    token: str = Form(...),
    # db: Database session
    db: Session = Depends(get_db)
):
    # Authenticate user
    user = get_user_by_token(token, db)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid token")
    
    # Find the video in database
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Check if user has already liked this video
    existing_like = db.query(Like).filter(Like.user_id == user.id, Like.video_id == video_id).first()
    
    if existing_like:
        # User already liked - remove the like (unlike)
        db.delete(existing_like)
        # Decrement like count
        video.likes -= 1
        liked = False
    else:
        # User hasn't liked - add new like
        like = Like(user_id=user.id, video_id=video_id)
        db.add(like)
        # Increment like count
        video.likes += 1
        liked = True
    
    # Save changes to database
    db.commit()
    
    # Return updated like count and current like status
    return {"likes": video.likes, "liked": liked}


# Check if user liked a video - returns like status
# POST /liked/{video_id}
@app.post("/liked/{video_id}")
def check_liked(
    # video_id: ID of video to check (from URL path)
    video_id: int,
    # token: Authentication token
    token: str = Form(...),
    # db: Database session
    db: Session = Depends(get_db)
):
    # Try to authenticate user
    user = get_user_by_token(token, db)
    if not user:
        # If not authenticated, user hasn't liked the video
        return {"liked": False}
    
    # Check if a Like record exists for this user and video
    liked = db.query(Like).filter(Like.user_id == user.id, Like.video_id == video_id).first() is not None
    
    # Return whether user has liked this video
    return {"liked": liked}


# Get all comments for a video
# GET /comments/{video_id}
@app.get("/comments/{video_id}")
def get_comments(video_id: int, db: Session = Depends(get_db)):
    # Query all comments for the specified video
    comments = db.query(Comment).filter(Comment.video_id == video_id).all()

    # Return list of comments with user and timestamp info
    return [
        {
            "id": c.id,  # Comment unique identifier
            "user": c.user.username,  # Username of commenter
            "content": c.content,  # Comment text
            "timestamp": c.timestamp.strftime("%Y-%m-%d %H:%M:%S"),  # Formatted timestamp
        }
        # Iterate through all comments
        for c in comments
    ]


# Add comment to a video
# POST /comment/{video_id}
@app.post("/comment/{video_id}")
def add_comment(
    # video_id: ID of video to comment on (from URL path)
    video_id: int,
    # token: Authentication token
    token: str = Form(...),
    # content: Comment text
    content: str = Form(...),
    # db: Database session
    db: Session = Depends(get_db)
):
    # Authenticate user
    user = get_user_by_token(token, db)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid token")
    
    # Validate that comment is not empty
    if not content.strip():
        raise HTTPException(status_code=400, detail="Comment cannot be empty")
    
    # Create new Comment object
    comment = Comment(
        video_id=video_id,  # Link to video
        user_id=user.id,  # Link to user
        content=content  # Comment text
    )
    
    # Add comment to database
    db.add(comment)
    
    # Save changes
    db.commit()
    
    # Return success message
    return {"message": "Comment added successfully"}


# Delete video endpoint - removes video and associated data
# DELETE /video/{video_id}
@app.delete("/video/{video_id}")
def delete_video(
    # video_id: ID of video to delete (from URL path)
    video_id: int,
    # token: Authentication token
    token: str = Form(...),
    # db: Database session
    db: Session = Depends(get_db)
):
    # Authenticate user
    user = get_user_by_token(token, db)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid token")
    
    # Find the video in database
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Check if user is the uploader (authorization check)
    if video.uploader_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this video")
    
    try:
        # Try to delete the video file from disk
        os.remove(video.filename)
    except FileNotFoundError:
        # If file doesn't exist, continue anyway (data cleanup)
        pass
    
    # Delete video record from database
    db.delete(video)
    
    # Save changes
    db.commit()
    
    # Return success message
    return {"message": "Video deleted successfully"}
