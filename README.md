# One Service, Four Ways – Password Strength Checker

## Project Overview
This project implements a Password Strength Checker service using four deployment approaches:

1. Virtual Machine (VM)
2. Docker
3. Kubernetes
4. Hybrid Deployment

The application checks password strength and provides feedback while collecting anonymous usage statistics. Actual passwords are never stored.

## Stage 1 – Virtual Machine (Ubuntu)

### Environment
- Operating System: Ubuntu 24.04.3 LTS
- Web Server: Nginx
- Application Server: Gunicorn
- Backend: Python / Flask
- Database: PostgreSQL 16

### Architecture
The application runs inside an Ubuntu Virtual Machine. Nginx receives HTTP requests and forwards them to the Flask application running through Gunicorn. PostgreSQL stores anonymous password-checking statistics.

### VM Download
The complete Stage 1 virtual machine is available here:

**[Download Stage 1 VM](PASTE_GOOGLE_DRIVE_LINK_HERE)**

The VM export includes:
- `PassCheck-Stage1.ovf`
- `PassCheck-Stage1-disk1.vmdk`
- `PassCheck-Stage1.mf`

### How to Import the VM
1. Download all three VM files.
2. Keep the files in the same folder.
3. Open VMware Workstation.
4. Select **File → Open**.
5. Select `PassCheck-Stage1.ovf`.
6. Follow the import wizard.
7. Start the imported virtual machine.

### Accessing the Application
After starting the VM, open the application using its configured IP address:

`http://VM-IP-ADDRESS`

The network configuration might need adjustment depending on the host computer.

## Application Endpoints

| Endpoint | Description |
|---|---|
| `/` | Main application page |
| `/api/check` | Password strength checking API |
| `/health` | Application health check |
| `/ready` | Database readiness check |

## Security Notes
- Actual passwords are never stored in the database.
- Only anonymous statistics are collected.
- Database credentials must be configured locally and must not be committed to GitHub.

## Team
One Service, Four Ways – Password Strength Checker

