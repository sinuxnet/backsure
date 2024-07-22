import os
import subprocess
import boto3
import schedule
import time
from datetime import datetime


def backup_and_upload():
    # SQL Server connection details from environment variables
    sql_server = os.getenv('SQL_SERVER', 'localhost')
    sql_port = os.getenv('SQL_PORT', '1433')
    sql_user = os.getenv('SQL_USER', 'your_sql_user')
    sql_password = os.getenv('SQL_PASSWORD', 'your_sql_password')
    sql_database_name = os.getenv('SQL_DATABASE_NAME', 'your_database')

    # MinIO connection details from environment variables
    minio_endpoint = os.getenv('MINIO_ENDPOINT', 'your_minio_endpoint')
    minio_access_key = os.getenv('MINIO_ACCESS_KEY', 'your_minio_access_key')
    minio_secret_key = os.getenv('MINIO_SECRET_KEY', 'your_minio_secret_key')
    minio_bucket_name = os.getenv('MINIO_BUCKET_NAME', 'your_minio_bucket')
    minio_file_path = os.getenv('MINIO_FILE_PATH', 'backups')

    # Backup file details
    backup_dir = '/backup'
    backup_filename = f'{sql_database_name}_backup_{datetime.now().strftime("%Y%m%d%H%M%S")}.bak'
    backup_filepath = os.path.join(backup_dir, backup_filename)

    # Create the backup directory if it does not exist
    os.makedirs(backup_dir, exist_ok=True)

    # Create a backup of the database
    backup_command = f"sqlcmd -S {sql_server},{sql_port} -U {sql_user} -P {sql_password} -Q \"BACKUP DATABASE [{sql_database_name}] TO DISK = N'{backup_filepath}' WITH NOFORMAT, NOINIT, NAME = N'{sql_database_name}-Full Database Backup', SKIP, NOREWIND, NOUNLOAD, STATS = 10\""
    subprocess.run(backup_command, shell=True, check=True)

    # Initialize MinIO client
    s3_client = boto3.client('s3',
                             endpoint_url=minio_endpoint,
                             aws_access_key_id=minio_access_key,
                             aws_secret_access_key=minio_secret_key)

    # Upload the backup file to MinIO
    with open(backup_filepath, 'rb') as backup_file:
        s3_client.upload_fileobj(backup_file, minio_bucket_name, f"{minio_file_path}/{backup_filename}")

    print(f"Backup {backup_filename} uploaded to MinIO bucket {minio_bucket_name} successfully.")

def schedule_backups():
    # Schedule the backup every 10 minutes
    schedule.every(10).minutes.do(backup_and_upload)

    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(1)