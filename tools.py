import asyncio
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ---------------- MongoDB Setup ----------------
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "hackathon_db")  # default if not provided

if not MONGO_URI:
    raise ValueError("❌ MONGO_URI is missing in .env file")

client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]

# Collections
students = db["students"]
activity = db["activity_logs"]

# ---------------- Student Management ----------------
async def add_student(name: str, student_id: str, department: str, email: str):
    """Add a new student document"""
    doc = {
        "student_id": student_id,
        "name": name,
        "department": department,
        "email": email,
        "created_at": datetime.utcnow(),
        "last_active": datetime.utcnow(),
    }
    await students.insert_one(doc)
    return "✅ Student added successfully"


async def get_student(student_id: str):
    """Fetch a student by ID"""
    student = await students.find_one({"student_id": student_id}, {"_id": 0})
    if student:
        return f"👤 Student found: {student['name']} ({student['student_id']}), Dept: {student['department']}, Email: {student['email']}"
    return "⚠️ Student not found"


async def update_student(student_id: str, field: str, new_value: str):
    """Update a student field"""
    result = await students.update_one({"student_id": student_id}, {"$set": {field: new_value}})
    if result.modified_count:
        return "✅ Student updated successfully"
    return "⚠️ Student not found or no changes made"


async def delete_student(student_id: str):
    """Delete a student by ID"""
    res = await students.delete_one({"student_id": student_id})
    if res.deleted_count:
        return "✅ Student deleted successfully"
    return "⚠️ Student not found"


async def list_students(limit: int = 20):
    """List students with limit"""
    cursor = students.find().limit(limit)
    docs = [doc async for doc in cursor]
    if not docs:
        return "⚠️ No students found"
    result = "📋 Student List:\n"
    for d in docs:
        result += f"- {d['name']} ({d['student_id']}), Dept: {d['department']}, Email: {d['email']}\n"
    return result.strip()

# ---------------- Analytics ----------------
async def get_total_students():
    """Total number of students"""
    count = await students.count_documents({})
    return f"📊 Total students: {count}"


async def get_students_by_department():
    """Count students grouped by department"""
    pipeline = [{"$group": {"_id": "$department", "count": {"$sum": 1}}}]
    result = await students.aggregate(pipeline).to_list(length=None)
    if not result:
        return "⚠️ No departments found"
    msg = "🏫 Students by Department:\n"
    for r in result:
        msg += f"- {r['_id']}: {r['count']}\n"
    return msg.strip()


async def get_recent_onboarded_students(limit: int = 5):
    """Get recently onboarded students"""
    cursor = students.find().sort("created_at", -1).limit(limit)
    docs = [doc async for doc in cursor]
    if not docs:
        return "⚠️ No recent students found"
    result = "🆕 Recently Onboarded Students:\n"
    for d in docs:
        result += f"- {d['name']} ({d['student_id']}) - {d['department']}\n"
    return result.strip()


async def get_active_students_last_7_days():
    """Count students active in last 7 days"""
    cutoff = datetime.utcnow() - timedelta(days=7)
    count = await students.count_documents({"last_active": {"$gte": cutoff}})
    return f"📅 Active students in last 7 days: {count}"
