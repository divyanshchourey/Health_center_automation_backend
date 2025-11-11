from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.routers import auth, doctor, employee, patient

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Healthcare Automation Backend")

origins = [
    "https://health-automation-landing.web.app",
    "https://health-automation-landing.firebaseapp.com",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(doctor.router)
app.include_router(patient.router)
app.include_router(employee.router)

@app.get("/")
def root():
    return {"message": "Healthcare backend is running!"}