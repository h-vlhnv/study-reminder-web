# Study Reminder

A web application that helps students manage their assignments and deadlines.

## Description

Study Reminder helps students:
- Add tasks with deadlines
- View list of all tasks
- AI-powered smart task prioritization
- Mark tasks as completed
- Delete tasks
- Track overdue and upcoming deadlines
- Visual deadline indicators

## Product Context

### End Users
University and college students.

### Problem
Students often forget about deadlines and struggle to organize their academic tasks, especially when they have many assignments.

### Solution
A web application that allows convenient task storage, deadline tracking, and AI-powered smart prioritization to help students focus on what matters most.

## Features

### Implemented Features
- ✅ Add task with deadline
- ✅ View list of all tasks
- ✅ Visual deadline indicators (color coding)
- ✅ AI-powered smart prioritization
- ✅ Mark task as completed
- ✅ Delete task

### Planned Features
- ⏳ User registration and authentication
- ⏳ Task categorization by subject
- ⏳ Email notifications about deadlines
- ⏳ Automatic reminders

## Usage

### Run locally

```bash
pip install -r requirements.txt
python app.py
```

Open http://localhost:5000

### Run with Docker

```bash
docker-compose up -d
```

Open http://localhost:5000

## Deployment

### OS Requirements
- Ubuntu 24.04

### Installation

1. Install Docker:
```bash
sudo apt update
sudo apt install docker.io docker-compose
```

2. Clone the project:
```bash
git clone <repository-url>
cd study-reminder-web
```

3. Build and run:
```bash
docker-compose up --build -d
```

4. Open in browser: http://your-ip:5000

## Technology Stack

- Python 3.11
- Flask 3.0
- SQLite
- Docker

## Project Structure

```
study-reminder-web/
├── app.py              # Main application code
├── requirements.txt    # Python dependencies
├── Dockerfile          # Docker configuration
├── docker-compose.yml  # Docker Compose configuration
├── templates/
│   └── index.html      # HTML template
├── README.md           # Documentation
└── LICENSE             # MIT License
```

## License

MIT License - see LICENSE file