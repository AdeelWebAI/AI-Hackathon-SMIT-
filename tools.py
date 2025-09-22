import asyncio
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from langchain_core.tools import tool

# ---------------- MongoDB Setup ----------------
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "hackathon_db")

if not MONGO_URI:
    raise ValueError("❌ MONGO_URI is missing in .env file")

client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]

students = db["students"]
activity = db["activity_logs"]

# ---------------- Tools ----------------

@tool
async def add_student(name: str, student_id: str, department: str, email: str):
    """Insert a new student document into MongoDB."""
    doc = {
        "student_id": student_id,
        "name": name,
        "department": department,
        "email": email,
        "created_at": datetime.utcnow(),
        "last_active": datetime.utcnow(),
    }
    await students.insert_one(doc)
    return {"status": "success", "student": doc}


@tool
async def get_student(student_id: str):
    """Fetch a student by ID from MongoDB and show as the example formate.
    id: 76
    name: adeel
    department: computer science 
    email: adeel@gmail.com
    """
    return await students.find_one({"student_id": student_id}, {"_id": 0})


@tool
async def update_student(student_id: str, field: str, new_value: str):
    """Update a single field for a student document."""
    result = await students.update_one({"student_id": student_id}, {"$set": {field: new_value}})
    return {"matched": result.matched_count, "modified": result.modified_count}


@tool
async def delete_student(student_id: str):
    """Delete a student document by ID."""
    result = await students.delete_one({"student_id": student_id})
    return {"deleted": result.deleted_count}


@tool
async def list_students(limit: int = 20):
    """List student documents with a limit."""
    cursor = students.find({}, {"_id": 0}).limit(limit)
    return [doc async for doc in cursor]


@tool
async def get_total_students():
    """Return total number of students."""
    return await students.count_documents({})


@tool
async def get_students_by_department():
    """Return student that have are quered department from user."""
    pipeline = [{"$group": {"_id": "$department", "count": {"$sum": 1}}}]
    return await students.aggregate(pipeline).to_list(length=None)


@tool
async def get_recent_onboarded_students(limit: int = 5):
    """Return recently onboarded students, sorted by created_at."""
    cursor = students.find({}, {"_id": 0}).sort("created_at", -1).limit(limit)
    return [doc async for doc in cursor]


@tool
async def get_active_students_last_7_days():
    """Return count of students active in the last 7 days."""
    cutoff = datetime.utcnow() - timedelta(days=7)
    return await students.count_documents({"last_active": {"$gte": cutoff}})