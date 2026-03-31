# TaskFlow — To-Do List App teas

A full-stack To-Do List built with **FastAPI + SQLite + HTML/CSS/JS**.  
Deployable on [Railway](https://railway.app) as a single Docker container.

## 🚀 Deploy to Railway

1. Push this repo to GitHub
2. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo**
3. Select this repository — Railway auto-detects the `Dockerfile`
4. Click **Deploy**

Your app will be live at a URL like: `https://taskflow-xxx.up.railway.app`

### Optional: Persistent SQLite with a Railway Volume

By default, Railway's filesystem is ephemeral (resets on redeploy).  
To persist tasks across deployments:

1. In Railway dashboard → your service → **Volumes** → **Add Volume**
2. Mount path: `/data`
3. Add environment variable: `DATABASE_URL=sqlite:////data/todo.db`

---

## 💻 Run Locally

```bash
# 1. Create virtual environment
cd backend
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the server
uvicorn main:app --reload --port 8000
```

Open: **http://localhost:8000**

The API docs are at: **http://localhost:8000/docs**

---

## 🐳 Run with Docker Locally

```bash
# Build the image (from the anti1/ project root)
docker build -t taskflow .

# Run the container
docker run -p 8000:8000 taskflow
```

Open: **http://localhost:8000**

---

## 📁 Project Structure

```
anti1/
├── Dockerfile           ← Docker build config
├── railway.json         ← Railway deployment config
├── .dockerignore        ← Files excluded from Docker image
│
├── backend/
│   ├── main.py          ← FastAPI routes + static file serving
│   ├── database.py      ← SQLAlchemy setup (reads DATABASE_URL env var)
│   ├── models.py        ← Task ORM model (SQLite table)
│   ├── schemas.py       ← Pydantic validation schemas
│   ├── crud.py          ← CRUD database operations
│   └── requirements.txt ← Python dependencies
│
└── frontend/
    ├── index.html       ← App structure
    ├── style.css        ← Dark-mode styling + animations
    └── app.js           ← API calls + DOM interactions
```

## API Endpoints

| Method | Path            | Description          |
|--------|-----------------|----------------------|
| GET    | `/health`       | Health check         |
| GET    | `/tasks`        | Get all tasks        |
| POST   | `/tasks`        | Create task          |
| PUT    | `/tasks/{id}`   | Update task          |
| DELETE | `/tasks/{id}`   | Delete task          |
| GET    | `/docs`         | Swagger API docs     |
# anti6
