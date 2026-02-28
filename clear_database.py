#!/usr/bin/env python3
"""清空数据库脚本"""
import sqlite3
from pathlib import Path

DATABASE_PATH = Path(__file__).parent / 'data' / 'crawler.db'

def clear_database():
    """清空数据库中的所有数据"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # 获取所有表
    tables = cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table';"
    ).fetchall()

    # 删除每个表的数据（除了sqlite_sequence）
    deleted_count = 0
    for table in tables:
        table_name = table[0]
        if table_name != 'sqlite_sequence':
            cursor.execute(f'DELETE FROM {table_name}')
            deleted_count += 1
            print(f"已清空表: {table_name}")

    conn.commit()
    conn.close()
    print(f"\n总计清空了 {deleted_count} 个表的数据")
    print("数据库清空完成!")

if __name__ == '__main__':
    clear_database()
