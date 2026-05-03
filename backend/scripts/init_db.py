"""
数据库初始化脚本

用法：
    python -m scripts.init_db

初始化内容：
    1. 创建所有表
    2. 创建测试管理员账号（admin / admin123）
    3. 创建测试宿管账号（checker7 / checker123，负责7号楼）
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from passlib.context import CryptContext
from database import engine, SessionLocal, Base
from models import Student, CheckRecord, User


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_user(db, username: str, password: str, role: str, name: str, building: int = None):
    hashed = pwd_context.hash(password)
    user = User(
        username=username,
        password_hash=hashed,
        role=role,
        name=name,
        assigned_building=building,
    )
    db.merge(user)
    print(f"  {'更新' if db.query(User).filter(User.username == username).first() else '创建'}: {username} ({role})")


def init_db():
    print("创建数据表...")
    Base.metadata.create_all(bind=engine)
    print("完成\n")

    db = SessionLocal()
    try:
        print("创建测试账号...")
        create_user(db, "admin", "admin123", "admin", "管理员")
        create_user(db, "checker7", "checker123", "checker", "7号楼宿管", building=7)
        create_user(db, "checker10", "checker123", "checker", "10号楼宿管", building=10)
        create_user(db, "checker11", "checker123", "checker", "11号楼宿管", building=11)
        create_user(db, "checker17", "checker123", "checker", "17号楼宿管", building=17)
        create_user(db, "checker19", "checker123", "checker", "19号楼宿管", building=19)
        db.commit()
        print("\n数据库初始化完成")
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
