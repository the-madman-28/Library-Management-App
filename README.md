# Library Management System

A multi-tenant web-based Library Management System built with **Flask, SQLAlchemy, and PostgreSQL**. The application allows libraries to manage books, employees, active book issues, returns, overdue books, and permanent transaction history through a responsive web interface.

Each registered library operates within its own isolated data scope, so users can only access records belonging to their library.

## Features

### Authentication
- Library registration with the first library user
- User login and logout
- Password hashing with Werkzeug
- Active/inactive user accounts
- Email validation during registration
- Role field for library users

### Multi-Tenant Library Management
- Separate library/organization records
- Users belong to a specific library
- Books belong to a specific library
- Employees belong to a specific library
- Transactions and transaction history belong to a specific library
- Routes enforce the current user's library scope

### Dashboard
- Total books
- Available copies
- Total employees
- Currently issued books
- Overdue books
- All-time transaction count
- Quick access to major library operations

### Book Management
- Add books
- Edit book information
- View all books
- View available books
- Track total and available copies
- Book code and ISBN support
- Category, author, publisher and title information

### Employee Management
- Add employees
- Edit employee information
- View employees
- Employee code, name, department and designation
- Email and phone information
- Active/inactive employee status

### Book Transactions
- Issue books to employees
- Return books
- Track issue and due dates
- Automatically update available copies
- Display currently issued books
- Identify overdue books

### Transaction History
- Permanent transaction history
- Returned transactions remain available after return
- Stores book and employee details at the time of the transaction
- Separates active transactions from historical records

## Business Rules

### Book deletion
- A book that has never been issued can be deleted.
- A book whose previous issues have all been returned can be deleted.
- A book with an active/unreturned issue cannot be deleted.

### Employee deletion
- An employee who has never borrowed a book can be deleted.
- An employee whose previous transactions have all been returned can be deleted.
- An employee who currently has issued books cannot be deleted.

Historical returned transactions are preserved and do not prevent deletion.

## Technology Stack

### Backend
- Python
- Flask
- Flask-SQLAlchemy
- Flask-Migrate
- Flask-Login
- SQLAlchemy
- Alembic
- Werkzeug

### Frontend
- HTML5
- CSS3
- JavaScript
- Jinja2
- Bootstrap 5.3.3
- Bootstrap Icons

### Database
- PostgreSQL
- Neon PostgreSQL for hosted environments

### Deployment
- Vercel
- Neon
- GitHub

## Project Structure

```text
Library-Management-App/
│
├── app/
│   ├── models/
│   │   ├── book.py
│   │   ├── book_transaction.py
│   │   ├── employee.py
│   │   ├── library.py
│   │   ├── transaction_history.py
│   │   ├── user.py
│   │   └── __init__.py
│   │
│   ├── routes/
│   │   ├── auth.py
│   │   ├── books.py
│   │   ├── employees.py
│   │   ├── main.py
│   │   ├── transactions.py
│   │   └── __init__.py
│   │
│   ├── static/
│   │   ├── css/
│   │   └── js/
│   │
│   ├── templates/
│   │   ├── books/
│   │   ├── employees/
│   │   ├── transactions/
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   └── index.html
│   │
│   ├── extensions.py
│   └── __init__.py
│
├── migrations/
│   ├── versions/
│   ├── alembic.ini
│   ├── env.py
│   └── script.py.mako
│
├── config.py
├── requirements.txt
├── run.py
├── vercel.json
├── .gitignore
└── README.md
```

## Database Design

The current application uses these main database tables:

| Table | Purpose |
|---|---|
| `libraries` | Stores registered libraries/organizations |
| `users` | Stores users belonging to libraries |
| `books` | Stores library book information and availability |
| `employees` | Stores employees/borrowers belonging to libraries |
| `book_transactions` | Stores currently active book issues |
| `transaction_history` | Stores permanent transaction history |

Active transactions are removed when a book is returned, while the corresponding transaction history remains permanently available.

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/the-madman-28/Library-Management-App.git
cd Library-Management-App
```

### 2. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql+psycopg://username:password@host:5432/database_name
```

Do not commit `.env` to Git.

### 5. Run the application

```powershell
flask run
```

The application is normally available at:

```text
http://127.0.0.1:5000
```

You can also start it with:

```powershell
python run.py
```

## Database Migrations

The project uses **Flask-Migrate/Alembic** for database schema migrations.

After configuring the database:

```powershell
flask db upgrade
```

When making model changes during development:

```powershell
flask db migrate -m "describe the change"
flask db upgrade
```

Migration files are stored in:

```text
migrations/versions/
```

## Environment Separation

The application can use different PostgreSQL databases for different environments.

```text
Development
    ↓
Development PostgreSQL database

Production
    ↓
Neon PostgreSQL
    ↓
Vercel
```

Database credentials and application secrets should be supplied through environment variables and never committed to the repository.

## Deployment

The project contains a `vercel.json` configuration for deploying the Flask application to Vercel.

The production architecture is:

```text
GitHub
   ↓
Vercel
   ↓
Flask Application
   ↓
Neon PostgreSQL
```

Configure these environment variables in the Vercel project:

```text
DATABASE_URL
SECRET_KEY
```

The production database should be kept separate from local development databases.

## Development Workflow

```text
Develop locally
      ↓
Run Flask application
      ↓
Verify database changes
      ↓
Run migration when required
      ↓
Commit changes
      ↓
Push to GitHub
      ↓
Deploy to Vercel
      ↓
Verify production
```

## Future Improvements

Possible future improvements include:

- Email-based OTP password recovery
- Forgot-password and password reset workflow
- Role-based access control and dedicated administration
- Library/user management for organization administrators
- Advanced search and filtering
- Pagination for large datasets
- Email notifications for overdue books
- Automated due-date reminders
- Improved audit logging
- Enhanced reporting and analytics
- Production-grade rate limiting and additional security hardening
- Additional monitoring and operational tooling

## Project Status

The core Library Management System is implemented with authentication, multi-tenant library isolation, book management, employee management, issuing and returning books, overdue tracking, permanent transaction history, database migrations, and Vercel/Neon deployment configuration.
