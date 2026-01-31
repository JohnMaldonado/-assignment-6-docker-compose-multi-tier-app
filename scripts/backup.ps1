# scripts/backup.ps1
# Backup script for PostgreSQL database

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupFile = "backup_jhon_db_$timestamp.sql"

Write-Host "Starting database backup..." -ForegroundColor Cyan

# Create backup using docker exec
docker exec jhon-postgres pg_dump -U jhon_user jhon_db > "backups/$backupFile"

if ($LASTEXITCODE -eq 0) {
    Write-Host "Backup completed successfully: backups/$backupFile" -ForegroundColor Green
    
    # Compress backup
    Compress-Archive -Path "backups/$backupFile" -DestinationPath "backups/$backupFile.zip"
    Remove-Item "backups/$backupFile"
    
    Write-Host "Backup compressed: backups/$backupFile.zip" -ForegroundColor Green
} else {
    Write-Host "Backup failed!" -ForegroundColor Red
    exit 1
}
