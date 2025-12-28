# MiniTube - Video Sharing Platform

link:   https://codesera-youtube-fastapi.netlify.app/

A full-stack YouTube-like video sharing platform built with FastAPI (Python) and React.

## Features

- 🎥 **Video Upload & Streaming** - Upload and watch videos
- 👤 **User Authentication** - Register and login system
- ❤️ **Like System** - Like/unlike videos
- 💬 **Comments** - Add and view comments on videos
- 🗑️ **Delete Videos** - Users can delete their own uploads
- 🎨 **Modern UI** - Dark theme with red accents

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - SQL toolkit and ORM
- **SQLite** - Database
- **Werkzeug** - Password hashing

### Frontend
- **React** - JavaScript library for UI
- **Lucide React** - Icon library
- **Inline CSS** - No external CSS frameworks needed

## Project Structure

```
myYoutube-fastapi/
├── main.py                 # FastAPI backend
├── database.db            # SQLite database (auto-generated)
├── uploads/               # Uploaded videos directory
├── requirements.txt       # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.js        # React main component
│   │   └── index.js      # React entry point
│   ├── public/
│   ├── package.json      # Node dependencies
│   └── node_modules/
└── README.md
```

## Installation & Setup

### Prerequisites
- Python 3.8+
- Node.js 14+
- npm or yarn

### Backend Setup

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd myYoutube-fastapi
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

4. **Run the FastAPI server**
```bash
uvicorn main:app --reload
```

The backend will run on `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory**
```bash
cd frontend
```

2. **Install Node dependencies**
```bash
npm install
```

3. **Start the React development server**
```bash
npm start
```

The frontend will run on `http://localhost:3000`

## API Endpoints

### Authentication
- `POST /register` - Register new user
- `POST /login` - Login user

### Videos
- `GET /videos` - Get all videos
- `GET /video/{video_id}` - Stream video
- `POST /upload` - Upload new video
- `DELETE /video/{video_id}` - Delete video (owner only)

### Interactions
- `POST /like/{video_id}` - Like/unlike video
- `POST /liked/{video_id}` - Check if user liked video
- `GET /comments/{video_id}` - Get video comments
- `POST /comment/{video_id}` - Add comment

## Usage

1. **Register an account** - Click "Sign Up" and create your account
2. **Login** - Use your credentials to login
3. **Upload videos** - Click "Upload" button and fill in details
4. **Watch videos** - Click on any video card to watch
5. **Like & Comment** - Interact with videos by liking and commenting
6. **Delete your videos** - Only video uploaders can delete their own videos

## Database Schema

### Users
- id (Primary Key)
- username (Unique)
- email
- password (Hashed)

### Videos
- id (Primary Key)
- title
- description
- filename
- likes (Default: 0)
- uploader_id (Foreign Key → Users)

### Likes
- id (Primary Key)
- user_id (Foreign Key → Users)
- video_id (Foreign Key → Videos)

### Comments
- id (Primary Key)
- video_id (Foreign Key → Videos)
- user_id (Foreign Key → Users)
- content
- timestamp

## Environment Variables

No environment variables needed for basic setup. The app uses:
- SQLite database: `database.db`
- Upload directory: `./uploads`
- API URL: `http://localhost:8000`

## Development

### Running in Development Mode

**Backend:**
```bash
uvicorn main:app --reload
```

**Frontend:**
```bash
cd frontend
npm start
```

### Building for Production

**Frontend:**
```bash
cd frontend
npm run build
```

The build folder will contain optimized production files.

## Security Notes

⚠️ **This is a demo application. For production use:**
- Implement proper JWT authentication instead of username-as-token
- Add password strength validation
- Implement rate limiting
- Add input sanitization
- Use environment variables for sensitive data
- Implement HTTPS
- Add file size limits for uploads
- Validate video file types on backend
- Add CSRF protection

## Troubleshooting

### CORS Errors
Make sure your FastAPI backend has CORS middleware enabled for `http://localhost:3000`

### Video Upload Fails
- Check that the `uploads/` directory exists
- Verify file size is reasonable
- Ensure you're logged in

### Database Issues
Delete `database.db` and restart the backend to recreate tables

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is open source and available under the [MIT License](LICENSE).

## Author

Your Name - [@yourhandle](https://twitter.com/yourhandle)

## Acknowledgments

- FastAPI documentation
- React documentation
- Lucide React for icons

---

**Made with ❤️ using FastAPI and React**
