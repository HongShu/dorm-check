"""
Excel 学生数据导入脚本

用法：
    python -m scripts.import_students data/students.xlsx
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from services.importer import import_students_from_excel


def main():
    if len(sys.argv) < 2:
        print("用法: python -m scripts.import_students <excel文件路径>")
        sys.exit(1)

    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        sys.exit(1)

    db = SessionLocal()
    try:
        result = import_students_from_excel(db, file_path)
        print(f"导入完成: 共 {result['imported']} 条")
        print("按楼栋分布:")
        for b, cnt in sorted(result["by_building"].items()):
            print(f"  {b}号楼: {cnt} 人")
    finally:
        db.close()


if __name__ == "__main__":
    main()
