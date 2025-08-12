# เพิ่มในไฟล์ run_server.py หรือ main.py

from app.api.v1.facebook import router as facebook_router

# เพิ่มในส่วน app.include_router
app.include_router(facebook_router, prefix="/api/v1")

print("✅ Facebook API routes added")
