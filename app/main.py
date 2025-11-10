from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.routers import auth, doctor, employee, patient  # ✅ import all routers

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Healthcare Automation Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        # Added dev port 3001 to support alternative dev server
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Register all routers
app.include_router(auth.router)
app.include_router(doctor.router)
app.include_router(patient.router)
app.include_router(employee.router)

@app.get("/")
def root():
    return {"message": "Healthcare backend is running!"}
