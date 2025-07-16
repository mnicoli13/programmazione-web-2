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

## Alternative Way :  Run with Docker

If you're having issues running the app locally, you can use Docker:

### 1. Install Docker
Make sure you have Docker installed:
👉 [Download Docker Desktop](https://www.docker.com/get-started)

### 2. Start Docker
Open the Docker Desktop app.
> You don’t need to create an account — just skip the login/registration if prompted

### 3. wsl --update
maybe you have to run this command, if your Windows subsystem is too old
```bash
wsl --update
```
> This updates the Windows Subsystem for Linux, which Docker uses under the hood.
Then you have to restart docker and wait that the Docker Engine is ready


### 4. Build the Docker image
go back to the project and run
```bash
docker-compose build
```

### 5. Start the application
```bash
docker-compose up
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

- if occurs an error like this below you have to correct Documenti in Documents
```bash
failed to evaluate path
"C:\\Users\\nicol\\Documenti\\uni\\progr-web-2\\programmazione-web-2\\mnicoli64"
```


---

## Author
Matteo Nicoli