# Windows 11 Setup Guide (Beginner Friendly)

This guide takes you from a ZIP file to a running Password Strength Checker, step by step, using **PowerShell**.

> **Honesty note:** the application and its tests were built and verified on Linux. The Windows commands below are standard
> PowerShell, but they have **not been executed on a Windows 11 machine** by the author. If any step behaves differently,
> use the troubleshooting section (Step 14) and tell the team what you saw.

**How to read each step.** Every command is followed by: **Where** (which folder), **What it does**, **Expect** (what you should see), **If it fails**.

**Words you will see:** *terminal* = a window where you type commands. *PowerShell* = the Windows terminal. *Folder* = directory. *Virtual environment (venv)* = a private box of Python packages for this project only.

**Tip:** copy a command, right-click in PowerShell to paste, press **Enter**. Run commands one at a time.

---

## 1. Required software

You need: **Python 3.10 to 3.13**, **Git**, and (recommended) **Visual Studio Code**. PostgreSQL is only needed in Step 12 and is optional.

### 1.1 Check Python
```powershell
python --version
```
- **Where:** any PowerShell window (press **Win**, type `PowerShell`, press Enter).
- **What:** shows the installed Python version.
- **Expect:** `Python 3.12.x` (any 3.10 - 3.13 is fine).
- **If it fails** ("not recognized", or the Microsoft Store opens): install Python from https://www.python.org/downloads/windows/ . On the first installer screen **tick "Add python.exe to PATH"**, then click *Install Now*. Close PowerShell, open a new one, run the command again.

### 1.2 Check Git
```powershell
git --version
```
- **Expect:** `git version 2.xx.x.windows.x`.
- **If it fails:** install from https://git-scm.com/download/win (accept the defaults), then open a **new** PowerShell.

### 1.3 Check VS Code (optional)
Open the Start menu and search "Visual Studio Code". If missing, install from https://code.visualstudio.com/ . It gives you an editor and a built-in terminal.

---

## 2. Extract the ZIP file

1. Create a folder for projects, for example `C:\Projects`.
2. Move `one-service-four-ways.zip` there.
3. Right-click the ZIP → **Extract All…** → check the destination ends with `C:\Projects` → **Extract**.

- **Expect:** a folder `C:\Projects\one-service-four-ways` that contains `app`, `db`, `README.md`, etc.
- **If it fails / looks wrong:** do not run anything from *inside* the ZIP (double-clicking it only previews). Make sure you extracted it. If you see `one-service-four-ways\one-service-four-ways`, use the **inner** folder, the one that contains `app`.

---

## 3. Open the project in a terminal or VS Code

**Option A: VS Code (recommended).** Open VS Code → **File → Open Folder…** → choose `C:\Projects\one-service-four-ways` → **Select Folder** → (if asked) *Yes, I trust the authors*. Then **Terminal → New Terminal**. A PowerShell panel opens at the bottom, already in the project folder.

**Option B: File Explorer.** Open the project folder, right-click an empty area → **Open in Terminal**.

- **Expect:** a prompt like `PS C:\Projects\one-service-four-ways>`.
- **If the terminal says it is not PowerShell** (e.g. `Command Prompt`): in VS Code click the **▾** next to **+** in the terminal panel and choose *PowerShell*.

## 4. Navigate to the correct folder

```powershell
cd C:\Projects\one-service-four-ways
dir
```
- **Where:** any PowerShell window.
- **What:** `cd` moves into the folder; `dir` lists what is inside.
- **Expect:** a list including `app`, `db`, `tests`, `README.md`, `.env.example`.
- **If it fails** ("cannot find path"): the folder is somewhere else. Type `cd ` (with a space), drag the project folder from File Explorer into the PowerShell window, press Enter.

> You will use two locations: the **project root** (`...\one-service-four-ways`) and the **app folder** (`...\one-service-four-ways\app`). Each step says which.

---

## 5. Create a Python virtual environment

```powershell
python -m venv .venv
```
- **Where:** project root.
- **What:** creates a private Python environment in a new folder called `.venv`.
- **Expect:** nothing printed, takes 5-20 seconds, a `.venv` folder appears.
- **If it fails:** run `python --version` again (Step 1.1). If you have several Pythons, try `py -3.12 -m venv .venv`.

## 6. Activate the virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
```
- **Where:** project root.
- **What:** switches this terminal to use the project's private Python.
- **Expect:** the prompt now starts with **`(.venv)`**, e.g. `(.venv) PS C:\Projects\one-service-four-ways>`.
- **If it fails** with *"running scripts is disabled on this system"*: run this once, then retry the activate command:
  ```powershell
  Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
  ```
  Type `Y` and Enter if asked. This only affects your own user account.

**Important:** every time you open a **new** terminal you must activate again (this step). If you do not see `(.venv)`, you are not activated.

## 7. Install the required Python packages

```powershell
python -m pip install --upgrade pip
pip install -r app\requirements-dev.txt
```
- **Where:** project root, with `(.venv)` showing.
- **What:** updates pip, then installs Flask, SQLAlchemy, psycopg2-binary, python-dotenv and pytest. (Gunicorn is skipped on Windows on purpose; it is for Linux servers.)
- **Expect:** many "Collecting…/Downloading…" lines ending with `Successfully installed Flask-… SQLAlchemy-… pytest-… …`.
- **If it fails:**
  - *"No matching distribution"/psycopg2 error*: check `python --version` is 3.10 - 3.13, run `python -m pip install --upgrade pip`, retry.
  - *Network/SSL errors*: check your internet or try another network.
  - *'pip' is not recognized*: you are not activated (Step 6); use `python -m pip install -r app\requirements-dev.txt`.

---

## 8. Configure environment variables

For the first run **you do not need to change anything**: with no database configured, the app runs in local mode and the footer shows `Environment: local`. If you want a `.env` file anyway:

```powershell
Copy-Item .env.example .env
notepad .env
```
- **Where:** project root.
- **What:** copies the example settings to a private `.env` file and opens it in Notepad.
- **Expect:** Notepad shows lines such as `ENV_NAME=local` and an empty `DB_HOST=`. Leave `DB_HOST` **empty** to run without PostgreSQL. Save (Ctrl+S) and close.
- **If it fails** ("cannot find path .env.example"): you are not in the project root (Step 4).

**Never** share or commit `.env`; it can contain the team's database password. It is already listed in `.gitignore`.

To try another footer value quickly (this only lasts for the current terminal):
```powershell
$env:ENV_NAME = "docker"
```

---

## 9. Run the application locally without PostgreSQL

```powershell
cd app
python -m flask --app app run --port 8000
```
- **Where:** first command moves from the project root into `app`; the second runs there, with `(.venv)` showing.
- **What:** starts Flask's built-in development server (Windows cannot run Gunicorn).
- **Expect:**
  ```
   * Serving Flask app 'app'
   * Running on http://127.0.0.1:8000
  Press CTRL+C to quit
  ```
  The terminal now stays busy. That is normal; the server is running.
- **If it fails:**
  - *"Could not import 'app'" / "No module named app"*: you are not inside the `app` folder. Run `dir` and look for `app.py`.
  - *"No module named flask"*: you are not activated (Step 6) or skipped Step 7.
  - *"Address already in use"*: see Step 14, port 8000.

## 10. Open the application in the browser

Open **Chrome or Edge** and go to **http://127.0.0.1:8000** (or http://localhost:8000).

- **Expect:** the dark "PassCheck" page. Type `abc` and click **Check strength** → **Weak**. Then `Hello#Pass9` → **Strong**, and `Xq7!mPz2#Lw9vTr4` → **Very Strong**. The footer shows `Environment: local`.
- **If the page does not load:** make sure the terminal from Step 9 is still running and shows no red error.

Optional quick API check, in a **second** PowerShell window (activation not needed):
```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/ready
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/check -ContentType "application/json" -Body '{"password":"Hello#Pass9"}'
```
- **Expect:** `/health` shows `status ok` and `host`; `/ready` shows `database not_configured` (this is correct in local mode); the check shows `label Strong`.

---

## 11. Run the 18 unit tests

Stop the server first (Step 13), or open a second terminal and activate it (Step 6).

```powershell
cd C:\Projects\one-service-four-ways\app
python -m pytest -q
```
- **Where:** the `app` folder, with `(.venv)` showing.
- **What:** runs the automated tests. They need no PostgreSQL and use a temporary SQLite file where a database is needed.
- **Expect:** `..................  [100%]` and **`18 passed`** (in about a second).
- **If it fails:**
  - *"No module named pytest"*: you did not install `requirements-dev.txt` (Step 7).
  - *"no tests ran"*: you are not in the `app` folder.
  - *Any `FAILED` line*: copy the whole output and send it to the team. Do not edit the tests to make them pass.

---

## 12. Configure and test PostgreSQL (optional, when available)

**12.1 Install.** Download PostgreSQL 16 for Windows from https://www.postgresql.org/download/windows/ . Keep port **5432**. Choose and **remember a password for the `postgres` administrator account**. (This is not the team's `passcheck` password.)

**12.2 Create the database and user.** Replace `YOUR_PRIVATE_PASSWORD` with the team's privately chosen password. Never write it in chat, GitHub or the README.
```powershell
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -h localhost
```
- **Where:** any PowerShell.
- **Expect:** asks `Password for user postgres:` (typing is invisible), then a `postgres=#` prompt.
- **If it fails:** *"connection refused"* → the PostgreSQL service is not running (Step 14). *"path not found"* → your version number differs; open `C:\Program Files\PostgreSQL` to see the folder name.

At the `postgres=#` prompt type these two lines (end each with `;`), then `\q` to leave:
```sql
CREATE USER passcheck WITH PASSWORD 'YOUR_PRIVATE_PASSWORD';
CREATE DATABASE passcheck OWNER passcheck;
\q
```
- **Expect:** `CREATE ROLE` then `CREATE DATABASE`.

**12.3 Create the `stats` table.**
```powershell
cd C:\Projects\one-service-four-ways
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U passcheck -h localhost -d passcheck -f db\init.sql
```
- **Expect:** password prompt, then `CREATE TABLE` and `DO`.
- **If it fails:** *"password authentication failed"* → wrong password; *"database does not exist"* → redo 12.2.

**12.4 Tell the app about the database.** Open `.env` (`notepad .env`) and set:
```
ENV_NAME=local
DB_HOST=localhost
DB_PORT=5432
DB_NAME=passcheck
DB_USER=passcheck
DB_PASSWORD=YOUR_PRIVATE_PASSWORD
```
Save and close.

**12.5 Run the app again** (Step 9) and check readiness:
```powershell
Invoke-RestMethod http://127.0.0.1:8000/ready
```
- **Expect:** `database ok`. If you get an error with status **503**, the app cannot reach PostgreSQL (Step 14).

Use the web page a few times, then look at the saved statistics:
```powershell
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U passcheck -h localhost -d passcheck -c "SELECT * FROM stats;"
```
- **Expect:** rows with columns `id | env | label | length_bucket | ts`. **There is no password column**, and the values must never contain what you typed.

**12.6 Run the PostgreSQL integration tests** (the `.env` from 12.4 is picked up automatically):
```powershell
cd C:\Projects\one-service-four-ways
python -m pytest tests -q -v
```
- **Expect:** `2 passed`. If `DB_HOST` is empty they show `2 skipped`, which is correct when there is no database.

---

## 13. Stop and restart the application

- **Stop:** click the terminal that is running the server and press **Ctrl + C**. Expect the prompt to return.
- **Restart:** make sure you are in the `app` folder with `(.venv)` showing, then press the **Up arrow** key to recall the run command (or retype it) and press Enter:
  ```powershell
  python -m flask --app app run --port 8000
  ```
- After editing `.env`, **restart** the server; settings are read at start-up.

---

## 14. Troubleshooting

| Problem | Cause and fix |
|---|---|
| `python` is not recognized | Python is not installed or PATH was not ticked. Reinstall (Step 1.1) and open a **new** terminal. |
| `Activate.ps1 cannot be loaded… scripts is disabled` | Run `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`, then activate again. |
| No `(.venv)` in the prompt | Not activated. Run `.\.venv\Scripts\Activate.ps1` from the project root. |
| `ModuleNotFoundError: No module named 'flask'` (or sqlalchemy, pytest…) | Not activated or Step 7 skipped. Activate, then `pip install -r app\requirements-dev.txt`. |
| `No module named 'gunicorn'` | Expected on Windows; Gunicorn is for Linux only. Use the `flask run` command. |
| `flask` is not recognized | Use `python -m flask …` exactly as shown. |
| `Could not import "app"` / `Error: Failed to find Flask application` | You are not in the `app` folder. `cd` there and check `dir` shows `app.py`. |
| `Address already in use` / `Port 8000 is in use` | Another copy is running. Find it: `netstat -ano \| findstr :8000` (last number = PID), stop it: `taskkill /PID <PID> /F`. Or close the old terminal. |
| `psycopg2` fails to install | Use Python 3.10 - 3.13, upgrade pip, retry. |
| `/ready` returns 503, or `OperationalError … connection refused` | PostgreSQL is not running or the settings are wrong. Press **Win**, type `Services`, find **postgresql-x64-16**, click **Start**. Re-check `DB_HOST`, `DB_PORT`. |
| `password authentication failed for user "passcheck"` | `DB_PASSWORD` in `.env` differs from the password you used in `CREATE USER`. |
| `database "passcheck" does not exist` | Redo Step 12.2. |
| Page loads but shows `recorded: false` / nothing saved | Database not configured/reachable, or `init.sql` not applied. Check `/ready` and Step 12.3. The check itself still works. |
| Browser shows an old page after changes | Hard refresh: **Ctrl + F5**. |
| `18 passed` not shown | Make sure you ran the tests from the `app` folder. |
| `git` is not recognized | Install Git (Step 1.2) and open a **new** terminal. |

---

## 15. Prepare the application files for GitHub

Check that secrets and junk are excluded:
```powershell
cd C:\Projects\one-service-four-ways
git status
```
- **Where:** project root (inside your Git repository; see 16.1 if you have not cloned yet).
- **What:** lists what Git would add.
- **Expect:** you see `app/`, `db/`, `tests/`, `README.md`, `.gitignore`, `.env.example`, etc. You must **NOT** see `.env`, `.venv/`, or `__pycache__/`.
- **If `.env` or `.venv` appears:** stop. Do not commit. Check that `.gitignore` exists in the project root and contains `.env` and `.venv/`. If you accidentally committed `.env`, tell the team immediately and **change the database password**.

Also double-check no real password is written inside any file you will upload: `.env.example` must only contain `CHANGE_ME_...`.

## 16. Create a branch and submit a pull request

**16.1 One-time setup (first time using Git on this PC).**
```powershell
git config --global user.name "Your Name"
git config --global user.email "your-github-email@example.com"
```
- **What:** labels your commits. **Expect:** no output.

**Get the team repository** (URL from your team; replace it):
```powershell
cd C:\Projects
git clone https://github.com/TEAM-OR-USER/REPO-NAME.git
```
- **Expect:** `Cloning into 'REPO-NAME'…`. **If it fails:** check the URL and that you are invited to the repository; GitHub may ask you to sign in in the browser.

Copy the **contents** of `one-service-four-ways` (the folders `app`, `db`, `tests`, `vm`, `docker`, `k8s`, `hybrid` and the files `README.md`, `.gitignore`, `.env.example`, `WINDOWS_SETUP_GUIDE.md`, `TEAMMATE_HANDOFF.md`) into the cloned repository folder. **Do not copy** `.venv`, `.env`, or `__pycache__`. (Note: the hidden files `.gitignore` and `.env.example` must be copied too: in File Explorer enable **View → Show → Hidden items**.)

**16.2 Create a branch** (never work directly on `main`):
```powershell
cd C:\Projects\REPO-NAME
git checkout -b feature/application
```
- **Expect:** `Switched to a new branch 'feature/application'`.

**16.3 Review, commit.**
```powershell
git status
git add .
git status
git commit -m "Add Password Strength Checker application, tests and docs"
```
- **Expect:** the second `git status` shows green "new file" lines (and still **no** `.env`/`.venv`); the commit prints `NN files changed`.
- **If it fails:** *"Please tell me who you are"* → do 16.1 setup. *"nothing to commit"* → files were not copied into the cloned folder.

**16.4 Push the branch.**
```powershell
git push -u origin feature/application
```
- **Expect:** lines ending with `Branch 'feature/application' set up to track…`, plus a link for creating a pull request.
- **If it fails:** *authentication* → sign in when the browser opens, or use a GitHub Personal Access Token; *permission denied* → ask to be added as a collaborator.

**16.5 Open the pull request.** Go to the repository page on GitHub. Click the yellow **Compare & pull request** button, write a short title (e.g. "Add application") and description (what you added; mention tests: `18 passed`), choose a teammate under **Reviewers**, then click **Create pull request**. A teammate reviews and clicks **Merge pull request**.

**16.6 Next changes:** switch to `main`, update it, then start a new branch:
```powershell
git checkout main
git pull
git checkout -b feature/my-next-change
```

Teammates then add their deployment files only in `vm/`, `docker/`, `k8s/` or `hybrid/`, each on their own branch, and update the status table in `README.md` only after their stage is verified.
