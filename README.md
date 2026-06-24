# Trắc Nghiệm với Django

A Django-based multiple-choice quiz platform inspired by popular Vietnamese educational platforms like **Azota.com**, **Wayground.com**, and **Tracnghiem.net**.

## What This Is

This is an online quiz/test management system that allows teachers to create, manage, and administer multiple-choice tests, and enables students to take quizzes, join virtual classrooms, and view their results. The platform features role-based access control (students, teachers, and admins), classroom management with enrollment workflows, support for importing quizzes from Word documents, and real-time answer tracking with score calculations.

---

## Stack

- **Language(s):** Python (backend), JavaScript (frontend), HTML, CSS
- **Framework / runtime:** Django 5.2.15 + MySQL
- **Notable libraries:**
  - `django-allauth` — User authentication (login, signup, password reset)
  - `python-docx` — Parse Word documents to generate quizzes
  - `pandas`, `numpy`, `openpyxl` — Data manipulation (export scores, handle spreadsheets)
  - `mysqlclient` — MySQL database driver
  - `lxml` — XML parsing for document handling

---

## How It's Organized

```
web1/                          # Main Django project directory
  manage.py                    # Django management script
  web1/                        # Django project settings package
    settings.py               # Configuration (database, apps, middleware)
    urls.py                   # URL routing (allauth + app1)
    wsgi.py, asgi.py         # ASGI/WSGI entry points for deployment
  
  app1/                        # Main application (business logic)
    models.py                 # Database models (User, Quiz, Classroom, etc.)
    views.py                  # View handlers (teacher/student rooms, quiz management)
    urls.py                   # App-specific URL routing
    forms.py                  # Custom Django forms (login, signup)
    admin.py                  # Django admin configuration
    migrations/              # Database migration history
    
    templates/               # HTML templates
      account/              # Allauth login/signup pages
      app1/                 # Quiz, classroom, and result pages
    
    static/                  # CSS, JS, images for the app
  
  staticfiles/               # Collected static files for production
  templates/                 # Project-level templates

requirements.txt             # Python package dependencies
```

### How It Fits Together

**Request flow:** 
1. User visits the home page (`/`) or logs in via allauth (`/accounts/login/`).
2. Based on role, the `login_redirect_view` routes them to either the teacher room (`/teacher-room/`) or student room (`/student-room/`).
3. **Teachers** can:
   - Create classes and manage enrollments
   - Upload Word files to auto-generate quizzes
   - Edit quiz questions/answers and publish them
   - Monitor student responses and export results
4. **Students** can:
   - Join classes by class code
   - View available quizzes and enter exam rooms by code
   - Take quizzes with shuffled answer choices
   - View their scores and review correct answers

**Data flow:**
- Quiz data is stored in the `Quiz`, `Question`, and `Choice` models
- Student responses go into `StudentAnswer` (tracks which choice they selected and whether it was correct)
- Classroom membership is managed via `Classroom` and `ClassEnrollment` models with approval workflow
- User roles (teacher/student) are stored in the custom `User` model

---

## How to Run It

### Prerequisites
- Python 3.8+
- MySQL Server running locally
- Virtual environment (recommended)

### Setup Steps

1. **Clone and enter the project:**
   ```bash
   git clone https://github.com/Anhpro1234/tracnghiem_voi_django.git
   cd tracnghiem_voi_django
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure the database:**
   - Ensure MySQL is running
   - Update `web1/web1/settings.py` with your MySQL credentials:
     ```python
     DATABASES = {
         'default': {
             'ENGINE': 'django.db.backends.mysql',
             'NAME': 'web1',
             'USER': 'root',            # Change to your MySQL user
             'PASSWORD': 'tunatuna',    # Change to your MySQL password
             'HOST': 'localhost',
         }
     }
     ```
   - Create the database in MySQL:
     ```sql
     CREATE DATABASE web1;
     ```

5. **Run migrations:**
   ```bash
   cd web1
   python manage.py migrate
   ```

6. **Create a superuser (admin):**
   ```bash
   python manage.py createsuperuser
   ```

7. **Start the development server:**
   ```bash
   python manage.py runserver
   ```
   - Visit `http://localhost:8000/` to see the home page
   - Admin panel: `http://localhost:8000/admin/`

### Key Environment Variables (Optional)
- `DJANGO_SETTINGS_MODULE` — Defaults to `web1.settings` (see `manage.py`)
- Database credentials are hard-coded in `settings.py` (consider using environment variables for production)

---

## Features

### For Teachers
- **Create & manage classes** — Generate unique class codes for students to join
- **Approve enrollments** — Manage student requests to join classes
- **Import quizzes from Word** — Auto-parse `.docx` files to create questions and answers
  - Recognizes question format: `Câu 1: ...` and answer format: `A) ...`, `B) ...`, etc.
  - Mark correct answers with an asterisk: `*A) Correct Answer`
- **Edit quizzes** — Adjust questions and answers after import
- **Publish & deactivate quizzes** — Control which quizzes are active
- **Export results** — Download CSV of student scores
- **View student lists** — See enrolled students and remove them if needed

### For Students
- **Join classes** — Enter class code to request classroom membership
- **View available quizzes** — See public and class-specific quizzes
- **Take quizzes** — Multiple-choice interface with shuffled answers
- **View scores** — Get immediate feedback and see correct answers
- **Export class lists** — (For teachers) Export CSV of student rosters

### For Administrators
- Django admin panel to manage users, subjects, quizzes, and results
- Full database visibility and CRUD operations

---

## Project Structure Details

### Models (`models.py`)
- **User** — Custom user model with roles (ADMIN, TEACHER, STUDENT)
- **Subject** — Course/subject categories (e.g., Math, English)
- **Classroom** — Virtual classroom with teacher and enrolled students
- **ClassEnrollment** — Workflow to approve/deny student join requests
- **Quiz** — A quiz/exam with a unique room ID and active status
- **Question** — Individual quiz question
- **Choice** — Multiple-choice answers (each marked as correct or not)
- **StudentAnswer** — Stores which choice each student selected and if it was correct

### Views (`views.py`)
- `home` — Public homepage with featured public quizzes
- `teacher_room` — Teacher dashboard (manage classes, quizzes, enrollments)
- `student_room` — Student dashboard (join classes, enter exams)
- `upload_create_quiz` — Word file upload and parsing
- `edit_quiz` — Modify questions and answers
- `take_quiz` — Quiz-taking interface
- `view_result` — Score display and answer review
- `export_class_students` / `export_quiz_results` — CSV export endpoints

### Database (MySQL)
- Configured in `settings.py` with `django.db.backends.mysql`
- Default credentials: `root` / `tunatuna` (change for production!)

---

## Deployment Notes

- **DEBUG mode is ON** in `settings.py` — Disable for production
- **Secret key is exposed** — Generate a new one before deploying
- **Allowed hosts** includes `ngrok-free.app`, `localhost`, `127.0.0.1` — Update for your domain
- **Database credentials are hard-coded** — Use environment variables or `.env` file in production
- Static files need to be collected: `python manage.py collectstatic`

---

## Try Asking

- **How do I import a quiz from a Word document?** — See the Word parsing logic in `upload_create_quiz` view; questions must be formatted as `Câu 1:` and answers as `A) ...`.
- **How does the classroom enrollment workflow work?** — Teachers approve/reject student join requests in `teacher_room`; once approved, students appear in `view_class_students`.
- **Can I customize the quiz timing or question types beyond multiple-choice?** — Currently only supports multiple-choice; adding short-answer or essay questions would require extending the `Question` and `Choice` models.

---

## License

No license specified. Contact the repository owner for usage rights.

---

## Contributors

- **Anhpro1234** (Repository Owner)

---

## Support & Contact

For issues, feature requests, or questions, please open an issue on GitHub or contact the repository maintainer.
