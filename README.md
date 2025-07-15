# Programmazione Web 2

This repository contains the Django project for the university course *Programmazione Web 2*.

## Getting Started
Follow these steps to set up the project on your local machine.

### 1. Clone the Repository
```bash
git clone https://github.com/mnicoli13/programmazione-web-2.git
cd programmazione-web-2/mnicoli64
```

### 2. Set Up a Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate  # On Windows
# source venv/bin/activate  # On macOS/Linux
```

### 3. Upgrade pip and Install Dependencies
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Run the Development Server
```bash
python manage.py runserver
```

Then just open your browser and go to `http://127.0.0.1:8000/`.

---

## Notes
- Ensure you have Python 3.10+ installed.
- If using macOS or Linux, replace the `venv\Scripts\activate` command with `source venv/bin/activate`.
- If you encounter migration or database issues, run:
```bash
python manage.py makemigrations
python manage.py migrate
```

---

## Author
Matteo Nicoli