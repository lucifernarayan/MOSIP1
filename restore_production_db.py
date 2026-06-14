"""
restore_production_db.py
-------------------------
Restores the `mosip.dump` database backup into the PostgreSQL database.
Works for both local installations and running Docker Compose containers.

Prerequisites:
- Run `python download_pg16.py` first to download pg_restore if it's not in your system PATH.
"""

import os
import subprocess
import sys
from backend.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

def restore_db():
    print("[MOSIP] Preparing database restoration...")
    
    # Check for dump file
    dump_file = "mosip.dump"
    if not os.path.exists(dump_file):
        print(f"[ERR] Database dump file '{dump_file}' not found in the root directory.")
        sys.exit(1)
        
    # Find pg_restore executable
    pg_restore_path = None
    for local_bin_dir in ["pg17_bin", "pg16_bin"]:
        local_restore = os.path.join(local_bin_dir, "pg_restore.exe")
        if os.path.exists(local_restore):
            pg_restore_path = local_restore
            break
    else:
        # Check system PATH
        import shutil
        system_restore = shutil.which("pg_restore")
        if system_restore:
            pg_restore_path = system_restore

    if not pg_restore_path:
        print("[ERR] pg_restore was not found.")
        print("Please run: python download_pg16.py")
        sys.exit(1)
        
    print(f"[MOSIP] Using pg_restore binary at: {pg_restore_path}")
    print(f"[MOSIP] Restoring database '{DB_NAME}' on {DB_HOST}:{DB_PORT} as user '{DB_USER}'...")
    
    # Prepare environment with password to avoid interactive prompt
    env = os.environ.copy()
    if DB_PASSWORD:
        env["PGPASSWORD"] = DB_PASSWORD
        
    # Command arguments
    # --clean drops database objects before recreating them
    # --no-owner skips restoration of object ownership
    # --no-privileges skips restoration of access privileges
    cmd = [
        pg_restore_path,
        "-h", DB_HOST,
        "-p", str(DB_PORT),
        "-U", DB_USER,
        "-d", DB_NAME,
        "--clean",
        "--no-owner",
        "--no-privileges",
        "-v",
        dump_file
    ]
    
    try:
        process = subprocess.run(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        print("[MOSIP] Database restoration completed successfully.")
        print(process.stdout)
    except subprocess.CalledProcessError as e:
        print("[ERR] pg_restore failed with exit code:", e.returncode)
        print("Error Details:")
        print(e.stderr)
        sys.exit(1)

if __name__ == "__main__":
    restore_db()
