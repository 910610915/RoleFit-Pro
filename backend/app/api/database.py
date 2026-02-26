from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy import create_engine, text
from typing import Optional
import os
import io
import json
import shutil
from datetime import datetime

from app.core.config import settings
from app.core.database import sync_engine

router = APIRouter(prefix="/db", tags=["Database"])

# SQLite to other database type mappings
SQLITE_TO_MYSQL = {
    'INTEGER': 'INT',
    'TEXT': 'TEXT',
    'REAL': 'DOUBLE',
    'BLOB': 'BLOB',
    'BOOLEAN': 'TINYINT(1)',
    'DATETIME': 'DATETIME',
}

SQLITE_TO_POSTGRESQL = {
    'INTEGER': 'INTEGER',
    'TEXT': 'TEXT',
    'REAL': 'DOUBLE PRECISION',
    'BLOB': 'BYTEA',
    'BOOLEAN': 'BOOLEAN',
    'DATETIME': 'TIMESTAMP',
}


def get_table_schema(table_name: str) -> list:
    """Get table schema"""
    with sync_engine.connect() as conn:
        result = conn.execute(text(f"PRAGMA table_info({table_name})"))
        return result.fetchall()


def get_table_data(table_name: str, limit: Optional[int] = None) -> list:
    """Get table data"""
    query = f"SELECT * FROM {table_name}"
    if limit:
        query += f" LIMIT {limit}"
    
    with sync_engine.connect() as conn:
        result = conn.execute(text(query))
        columns = result.keys()
        rows = result.fetchall()
        
        data = []
        for row in rows:
            row_dict = {}
            for i, col in enumerate(columns):
                value = row[i]
                # Convert datetime to string
                if isinstance(value, datetime):
                    value = value.isoformat()
                # Convert bytes to base64
                elif isinstance(value, bytes):
                    value = value.hex()
                row_dict[col] = value
            data.append(row_dict)
        
        return data


def convert_type(sqlite_type: str, target_db: str) -> str:
    """Convert SQLite type to target database type"""
    sqlite_type = sqlite_type.upper()
    
    if target_db == 'mysql':
        return SQLITE_TO_MYSQL.get(sqlite_type, sqlite_type)
    elif target_db == 'postgresql':
        return SQLITE_TO_POSTGRESQL.get(sqlite_type, sqlite_type)
    
    return sqlite_type


def generate_create_table_sql(table_name: str, schema: list, target_db: str) -> str:
    """Generate CREATE TABLE SQL"""
    columns = []
    for col in schema:
        col_name = col[1]
        col_type = col[2]
        not_null = col[3]
        default_value = col[4]
        primary_key = col[5]
        
        # Convert type
        sql_type = convert_type(col_type, target_db)
        
        col_sql = f"  {col_name} {sql_type}"
        
        if primary_key:
            col_sql += " PRIMARY KEY"
        if not_null and not primary_key:
            col_sql += " NOT NULL"
        if default_value is not None:
            if target_db == 'mysql':
                col_sql += f" DEFAULT {default_value}"
            elif target_db == 'postgresql':
                if default_value == 'NULL':
                    col_sql += " DEFAULT NULL"
                else:
                    col_sql += f" DEFAULT {default_value}"
        
        columns.append(col_sql)
    
    return f"CREATE TABLE {table_name} (\n{', '.join(columns)}\n);"


def generate_insert_sql(table_name: str, data: list, target_db: str) -> list:
    """Generate INSERT SQL statements"""
    if not data:
        return []
    
    columns = list(data[0].keys())
    column_str = ', '.join(columns)
    
    statements = []
    for row in data:
        values = []
        for col in columns:
            value = row[col]
            if value is None:
                values.append('NULL')
            elif isinstance(value, bool):
                values.append('1' if value else '0')
            elif isinstance(value, (int, float)):
                values.append(str(value))
            elif isinstance(value, str):
                # Escape single quotes
                escaped = value.replace("'", "''")
                values.append(f"'{escaped}'")
            else:
                values.append(f"'{str(value)}'")
        
        values_str = ', '.join(values)
        statements.append(f"INSERT INTO {table_name} ({column_str}) VALUES ({values_str});")
    
    return statements


@router.get("/export/sqlite")
def export_sqlite():
    """Export database as SQLite file"""
    db_path = "./hardware_benchmark.db"
    
    if not os.path.exists(db_path):
        raise HTTPException(status_code=404, detail="Database file not found")
    
    return FileResponse(
        path=db_path,
        filename=f"rolefit_pro_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
        media_type="application/x-sqlite3"
    )


@router.get("/export/mysql")
def export_mysql():
    """Export database as MySQL compatible SQL"""
    output = io.StringIO()
    
    # Get all tables
    with sync_engine.connect() as conn:
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"))
        tables = [row[0] for row in result.fetchall()]
    
    output.write("-- RoleFit Pro Database Export\n")
    output.write(f"-- Generated: {datetime.now().isoformat()}\n")
    output.write(f"-- Target: MySQL\n\n")
    output.write("SET FOREIGN_KEY_CHECKS=0;\n\n")
    
    for table_name in tables:
        # Get schema
        schema = get_table_schema(table_name)
        
        # Generate CREATE TABLE
        create_sql = generate_create_table_sql(table_name, schema, 'mysql')
        output.write(f"\n-- Table: {table_name}\n")
        output.write(f"DROP TABLE IF EXISTS {table_name};\n")
        output.write(create_sql + "\n")
        
        # Get data
        data = get_table_data(table_name)
        
        # Generate INSERT
        if data:
            insert_statements = generate_insert_sql(table_name, data, 'mysql')
            for stmt in insert_statements:
                output.write(stmt + "\n")
    
    output.write("\nSET FOREIGN_KEY_CHECKS=1;\n")
    
    # Return as downloadable file
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/plain",
        headers={
            "Content-Disposition": f"attachment; filename=rolefit_pro_mysql_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        }
    )


@router.get("/export/postgresql")
def export_postgresql():
    """Export database as PostgreSQL compatible SQL"""
    output = io.StringIO()
    
    # Get all tables
    with sync_engine.connect() as conn:
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"))
        tables = [row[0] for row in result.fetchall()]
    
    output.write("-- RoleFit Pro Database Export\n")
    output.write(f"-- Generated: {datetime.now().isoformat()}\n")
    output.write(f"-- Target: PostgreSQL\n\n")
    
    for table_name in tables:
        # Get schema
        schema = get_table_schema(table_name)
        
        # Generate CREATE TABLE
        create_sql = generate_create_table_sql(table_name, schema, 'postgresql')
        output.write(f"\n-- Table: {table_name}\n")
        output.write(f"DROP TABLE IF EXISTS {table_name} CASCADE;\n")
        output.write(create_sql + "\n")
        
        # Get data
        data = get_table_data(table_name)
        
        # Generate INSERT
        if data:
            insert_statements = generate_insert_sql(table_name, data, 'postgresql')
            for stmt in insert_statements:
                output.write(stmt + "\n")
    
    # Return as downloadable file
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/plain",
        headers={
            "Content-Disposition": f"attachment; filename=rolefit_pro_postgresql_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        }
    )


@router.post("/import")
async def import_database(file: UploadFile = File(...)):
    """Import database from uploaded file (SQLite .db or .sql file)"""
    # Get current database path
    db_path = os.path.abspath("./hardware_benchmark.db")
    backup_path = db_path + f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        # Create backup of current database
        if os.path.exists(db_path):
            shutil.copy2(db_path, backup_path)
        
        # Check file extension
        filename = file.filename.lower()
        
        if filename.endswith('.db') or filename.endswith('.sqlite'):
            # Import SQLite file - replace the database file
            contents = await file.read()
            with open(db_path, 'wb') as f:
                f.write(contents)
            return {
                "success": True,
                "message": f"SQLite数据库导入成功！原数据库已备份到: {os.path.basename(backup_path)}",
                "backup_file": os.path.basename(backup_path)
            }
        
        elif filename.endswith('.sql'):
            # Import SQL file - execute SQL statements
            contents = await file.read()
            sql_content = contents.decode('utf-8')
            
            # Connect and execute SQL
            with sync_engine.connect() as conn:
                # Split by semicolon and execute each statement
                statements = sql_content.split(';')
                for i, stmt in enumerate(statements):
                    stmt = stmt.strip()
                    if stmt and not stmt.startswith('--'):
                        try:
                            conn.execute(text(stmt))
                        except Exception as e:
                            # Continue on error but log it
                            print(f"Statement {i} error: {e}")
                
                conn.commit()
            
            return {
                "success": True,
                "message": "SQL文件导入成功！请重启服务以加载新数据。",
            }
        
        else:
            raise HTTPException(status_code=400, detail="不支持的文件格式。请上传 .db, .sqlite 或 .sql 文件")
    
    except Exception as e:
        # Restore from backup if import failed
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, db_path)
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")
