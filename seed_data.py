from app import create_app
from app.extensions import db
from app.models import Book, Employee


app = create_app()


BOOKS = [
    {
        "book_code": "BK001",
        "title": "Clean Code",
        "author": "Robert C. Martin",
        "publisher": "Prentice Hall",
        "category": "Programming",
        "isbn": "9780132350884",
        "total_copies": 8,
    },
    {
        "book_code": "BK002",
        "title": "The Pragmatic Programmer",
        "author": "Andrew Hunt",
        "publisher": "Addison-Wesley",
        "category": "Programming",
        "isbn": "9780135957059",
        "total_copies": 6,
    },
    {
        "book_code": "BK003",
        "title": "Python Crash Course",
        "author": "Eric Matthes",
        "publisher": "No Starch Press",
        "category": "Programming",
        "isbn": "9781593279288",
        "total_copies": 10,
    },
    {
        "book_code": "BK004",
        "title": "Effective Python",
        "author": "Brett Slatkin",
        "publisher": "Addison-Wesley",
        "category": "Python",
        "isbn": "9780138172342",
        "total_copies": 4,
    },
    {
        "book_code": "BK005",
        "title": "Fluent Python",
        "author": "Luciano Ramalho",
        "publisher": "O'Reilly Media",
        "category": "Python",
        "isbn": "9781492056355",
        "total_copies": 5,
    },
    {
        "book_code": "BK006",
        "title": "Learning Python",
        "author": "Mark Lutz",
        "publisher": "O'Reilly Media",
        "category": "Python",
        "isbn": "9781449355739",
        "total_copies": 3,
    },
    {
        "book_code": "BK007",
        "title": "The C++ Programming Language",
        "author": "Bjarne Stroustrup",
        "publisher": "Addison-Wesley",
        "category": "C++",
        "isbn": "9780321563842",
        "total_copies": 7,
    },
    {
        "book_code": "BK008",
        "title": "Effective Modern C++",
        "author": "Scott Meyers",
        "publisher": "O'Reilly Media",
        "category": "C++",
        "isbn": "9781491903995",
        "total_copies": 4,
    },
    {
        "book_code": "BK009",
        "title": "Java: The Complete Reference",
        "author": "Herbert Schildt",
        "publisher": "McGraw-Hill",
        "category": "Java",
        "isbn": "9781260440232",
        "total_copies": 5,
    },
    {
        "book_code": "BK010",
        "title": "Head First Java",
        "author": "Kathy Sierra",
        "publisher": "O'Reilly Media",
        "category": "Java",
        "isbn": "9781491910771",
        "total_copies": 3,
    },

    {
        "book_code": "BK011",
        "title": "Introduction to Algorithms",
        "author": "Thomas H. Cormen",
        "publisher": "MIT Press",
        "category": "Algorithms",
        "isbn": "9780262046305",
        "total_copies": 9,
    },
    {
        "book_code": "BK012",
        "title": "Algorithms",
        "author": "Robert Sedgewick",
        "publisher": "Addison-Wesley",
        "category": "Algorithms",
        "isbn": "9780321573513",
        "total_copies": 5,
    },
    {
        "book_code": "BK013",
        "title": "Data Structures and Algorithms in Python",
        "author": "Michael T. Goodrich",
        "publisher": "Wiley",
        "category": "Data Structures",
        "isbn": "9781118290279",
        "total_copies": 6,
    },
    {
        "book_code": "BK014",
        "title": "Data Structures Using C",
        "author": "Reema Thareja",
        "publisher": "Oxford University Press",
        "category": "Data Structures",
        "isbn": "9780198099307",
        "total_copies": 4,
    },
    {
        "book_code": "BK015",
        "title": "Cracking the Coding Interview",
        "author": "Gayle Laakmann McDowell",
        "publisher": "CareerCup",
        "category": "Interview Preparation",
        "isbn": "9780984782857",
        "total_copies": 10,
    },

    {
        "book_code": "BK016",
        "title": "Database System Concepts",
        "author": "Abraham Silberschatz",
        "publisher": "McGraw-Hill",
        "category": "Database",
        "isbn": "9780078022159",
        "total_copies": 7,
    },
    {
        "book_code": "BK017",
        "title": "Fundamentals of Database Systems",
        "author": "Ramez Elmasri",
        "publisher": "Pearson",
        "category": "Database",
        "isbn": "9780133970777",
        "total_copies": 4,
    },
    {
        "book_code": "BK018",
        "title": "Learning SQL",
        "author": "Alan Beaulieu",
        "publisher": "O'Reilly Media",
        "category": "Database",
        "isbn": "9781492057611",
        "total_copies": 5,
    },
    {
        "book_code": "BK019",
        "title": "SQL Cookbook",
        "author": "Anthony Molinaro",
        "publisher": "O'Reilly Media",
        "category": "Database",
        "isbn": "9780596009762",
        "total_copies": 2,
    },
    {
        "book_code": "BK020",
        "title": "Designing Data-Intensive Applications",
        "author": "Martin Kleppmann",
        "publisher": "O'Reilly Media",
        "category": "Database",
        "isbn": "9781449373320",
        "total_copies": 6,
    },

    {
        "book_code": "BK021",
        "title": "Computer Networks",
        "author": "Andrew S. Tanenbaum",
        "publisher": "Pearson",
        "category": "Networking",
        "isbn": "9780132126953",
        "total_copies": 8,
    },
    {
        "book_code": "BK022",
        "title": "Computer Networking: A Top-Down Approach",
        "author": "James Kurose",
        "publisher": "Pearson",
        "category": "Networking",
        "isbn": "9780136681557",
        "total_copies": 5,
    },
    {
        "book_code": "BK023",
        "title": "Network Security Essentials",
        "author": "William Stallings",
        "publisher": "Pearson",
        "category": "Network Security",
        "isbn": "9780134527338",
        "total_copies": 3,
    },
    {
        "book_code": "BK024",
        "title": "Operating System Concepts",
        "author": "Abraham Silberschatz",
        "publisher": "Wiley",
        "category": "Operating Systems",
        "isbn": "9781119456339",
        "total_copies": 9,
    },
    {
        "book_code": "BK025",
        "title": "Modern Operating Systems",
        "author": "Andrew S. Tanenbaum",
        "publisher": "Pearson",
        "category": "Operating Systems",
        "isbn": "9780137618873",
        "total_copies": 4,
    },

    {
        "book_code": "BK026",
        "title": "Computer Organization and Design",
        "author": "David A. Patterson",
        "publisher": "Morgan Kaufmann",
        "category": "Computer Architecture",
        "isbn": "9780128201091",
        "total_copies": 6,
    },
    {
        "book_code": "BK027",
        "title": "Computer Architecture: A Quantitative Approach",
        "author": "John L. Hennessy",
        "publisher": "Morgan Kaufmann",
        "category": "Computer Architecture",
        "isbn": "9780128119051",
        "total_copies": 3,
    },
    {
        "book_code": "BK028",
        "title": "Digital Design",
        "author": "Morris Mano",
        "publisher": "Pearson",
        "category": "Digital Logic",
        "isbn": "9780134549897",
        "total_copies": 5,
    },
    {
        "book_code": "BK029",
        "title": "Artificial Intelligence: A Modern Approach",
        "author": "Stuart Russell",
        "publisher": "Pearson",
        "category": "Artificial Intelligence",
        "isbn": "9780134610993",
        "total_copies": 8,
    },
    {
        "book_code": "BK030",
        "title": "Artificial Intelligence",
        "author": "Elaine Rich",
        "publisher": "McGraw-Hill",
        "category": "Artificial Intelligence",
        "isbn": "9780070522633",
        "total_copies": 2,
    },

    {
        "book_code": "BK031",
        "title": "Deep Learning",
        "author": "Ian Goodfellow",
        "publisher": "MIT Press",
        "category": "Machine Learning",
        "isbn": "9780262035613",
        "total_copies": 7,
    },
    {
        "book_code": "BK032",
        "title": "Hands-On Machine Learning",
        "author": "Aurélien Géron",
        "publisher": "O'Reilly Media",
        "category": "Machine Learning",
        "isbn": "9781098125974",
        "total_copies": 10,
    },
    {
        "book_code": "BK033",
        "title": "Pattern Recognition and Machine Learning",
        "author": "Christopher Bishop",
        "publisher": "Springer",
        "category": "Machine Learning",
        "isbn": "9780387310732",
        "total_copies": 4,
    },
    {
        "book_code": "BK034",
        "title": "Introduction to Machine Learning",
        "author": "Ethem Alpaydin",
        "publisher": "MIT Press",
        "category": "Machine Learning",
        "isbn": "9780262043793",
        "total_copies": 3,
    },
    {
        "book_code": "BK035",
        "title": "Natural Language Processing with Python",
        "author": "Steven Bird",
        "publisher": "O'Reilly Media",
        "category": "NLP",
        "isbn": "9780596516499",
        "total_copies": 5,
    },

    {
        "book_code": "BK036",
        "title": "Flask Web Development",
        "author": "Miguel Grinberg",
        "publisher": "O'Reilly Media",
        "category": "Web Development",
        "isbn": "9781491991732",
        "total_copies": 6,
    },
    {
        "book_code": "BK037",
        "title": "JavaScript: The Good Parts",
        "author": "Douglas Crockford",
        "publisher": "O'Reilly Media",
        "category": "Web Development",
        "isbn": "9780596517748",
        "total_copies": 3,
    },
    {
        "book_code": "BK038",
        "title": "You Don't Know JS",
        "author": "Kyle Simpson",
        "publisher": "O'Reilly Media",
        "category": "JavaScript",
        "isbn": "9781491904244",
        "total_copies": 5,
    },
    {
        "book_code": "BK039",
        "title": "Learning React",
        "author": "Eve Porcello",
        "publisher": "O'Reilly Media",
        "category": "Web Development",
        "isbn": "9781492051725",
        "total_copies": 4,
    },
    {
        "book_code": "BK040",
        "title": "HTML and CSS",
        "author": "Jon Duckett",
        "publisher": "Wiley",
        "category": "Web Development",
        "isbn": "9781118008188",
        "total_copies": 7,
    },

    {
        "book_code": "BK041",
        "title": "Computer Security",
        "author": "William Stallings",
        "publisher": "Pearson",
        "category": "Cyber Security",
        "isbn": "9780134794105",
        "total_copies": 4,
    },
    {
        "book_code": "BK042",
        "title": "The Web Application Hacker's Handbook",
        "author": "Dafydd Stuttard",
        "publisher": "Wiley",
        "category": "Cyber Security",
        "isbn": "9781118026472",
        "total_copies": 3,
    },
    {
        "book_code": "BK043",
        "title": "Practical Malware Analysis",
        "author": "Michael Sikorski",
        "publisher": "No Starch Press",
        "category": "Cyber Security",
        "isbn": "9781593272906",
        "total_copies": 2,
    },
    {
        "book_code": "BK044",
        "title": "Cryptography and Network Security",
        "author": "William Stallings",
        "publisher": "Pearson",
        "category": "Cryptography",
        "isbn": "9780134444284",
        "total_copies": 6,
    },
    {
        "book_code": "BK045",
        "title": "The Art of Computer Programming",
        "author": "Donald E. Knuth",
        "publisher": "Addison-Wesley",
        "category": "Computer Science",
        "isbn": "9780201896831",
        "total_copies": 1,
    },

    {
        "book_code": "BK046",
        "title": "Discrete Mathematics and Its Applications",
        "author": "Kenneth Rosen",
        "publisher": "McGraw-Hill",
        "category": "Mathematics",
        "isbn": "9781259676512",
        "total_copies": 5,
    },
    {
        "book_code": "BK047",
        "title": "Calculus",
        "author": "James Stewart",
        "publisher": "Cengage Learning",
        "category": "Mathematics",
        "isbn": "9781285740621",
        "total_copies": 8,
    },
    {
        "book_code": "BK048",
        "title": "Linear Algebra and Its Applications",
        "author": "David C. Lay",
        "publisher": "Pearson",
        "category": "Mathematics",
        "isbn": "9780321982384",
        "total_copies": 4,
    },
    {
        "book_code": "BK049",
        "title": "Computer Science Illuminated",
        "author": "Nell Dale",
        "publisher": "Jones & Bartlett Learning",
        "category": "Computer Science",
        "isbn": "9781284155618",
        "total_copies": 3,
    },
    {
        "book_code": "BK050",
        "title": "Structure and Interpretation of Computer Programs",
        "author": "Harold Abelson",
        "publisher": "MIT Press",
        "category": "Computer Science",
        "isbn": "9780262510875",
        "total_copies": 2,
    },
]

EMPLOYEES = [
    {
        "employee_code": "EMP001",
        "name": "Aarav Sharma",
        "department": "Information Technology",
        "designation": "Software Engineer",
        "email": "aarav.sharma@example.com",
    },
    {
        "employee_code": "EMP002",
        "name": "Priya Singh",
        "department": "Human Resources",
        "designation": "HR Manager",
        "email": "priya.singh@example.com",
    },
    {
        "employee_code": "EMP003",
        "name": "Rohan Verma",
        "department": "Information Technology",
        "designation": "Backend Developer",
        "email": "rohan.verma@example.com",
    },
    {
        "employee_code": "EMP004",
        "name": "Ananya Gupta",
        "department": "Finance",
        "designation": "Financial Analyst",
        "email": "ananya.gupta@example.com",
    },
    {
        "employee_code": "EMP005",
        "name": "Vikram Mehta",
        "department": "Administration",
        "designation": "Administrative Officer",
        "email": "vikram.mehta@example.com",
    },
    {
        "employee_code": "EMP006",
        "name": "Neha Kapoor",
        "department": "Information Technology",
        "designation": "Frontend Developer",
        "email": "neha.kapoor@example.com",
    },
    {
        "employee_code": "EMP007",
        "name": "Aditya Joshi",
        "department": "Research",
        "designation": "Research Associate",
        "email": "aditya.joshi@example.com",
    },
    {
        "employee_code": "EMP008",
        "name": "Sneha Patel",
        "department": "Marketing",
        "designation": "Marketing Executive",
        "email": "sneha.patel@example.com",
    },
    {
        "employee_code": "EMP009",
        "name": "Karan Malhotra",
        "department": "Information Technology",
        "designation": "DevOps Engineer",
        "email": "karan.malhotra@example.com",
    },
    {
        "employee_code": "EMP010",
        "name": "Isha Agarwal",
        "department": "Human Resources",
        "designation": "HR Executive",
        "email": "isha.agarwal@example.com",
    },
    {
        "employee_code": "EMP011",
        "name": "Rahul Bansal",
        "department": "Operations",
        "designation": "Operations Manager",
        "email": "rahul.bansal@example.com",
    },
    {
        "employee_code": "EMP012",
        "name": "Meera Nair",
        "department": "Research",
        "designation": "Research Scientist",
        "email": "meera.nair@example.com",
    },
    {
        "employee_code": "EMP013",
        "name": "Arjun Rao",
        "department": "Information Technology",
        "designation": "Data Engineer",
        "email": "arjun.rao@example.com",
    },
    {
        "employee_code": "EMP014",
        "name": "Kavya Reddy",
        "department": "Finance",
        "designation": "Accountant",
        "email": "kavya.reddy@example.com",
    },
    {
        "employee_code": "EMP015",
        "name": "Nikhil Sinha",
        "department": "Information Technology",
        "designation": "System Administrator",
        "email": "nikhil.sinha@example.com",
    },
    {
        "employee_code": "EMP016",
        "name": "Simran Kaur",
        "department": "Administration",
        "designation": "Office Administrator",
        "email": "simran.kaur@example.com",
    },
    {
        "employee_code": "EMP017",
        "name": "Manish Kumar",
        "department": "Operations",
        "designation": "Operations Executive",
        "email": "manish.kumar@example.com",
    },
    {
        "employee_code": "EMP018",
        "name": "Pooja Mishra",
        "department": "Marketing",
        "designation": "Marketing Manager",
        "email": "pooja.mishra@example.com",
    },
    {
        "employee_code": "EMP019",
        "name": "Siddharth Jain",
        "department": "Information Technology",
        "designation": "Security Engineer",
        "email": "siddharth.jain@example.com",
    },
    {
        "employee_code": "EMP020",
        "name": "Divya Iyer",
        "department": "Research",
        "designation": "Research Associate",
        "email": "divya.iyer@example.com",
    },
]

def seed_books():
    added = 0

    for data in BOOKS:

        existing = Book.query.filter_by(
            book_code=data["book_code"]
        ).first()

        if existing:
            continue

        book = Book(
            book_code=data["book_code"],
            title=data["title"],
            author=data["author"],
            publisher=data["publisher"],
            category=data["category"],
            isbn=data["isbn"],
            total_copies=data["total_copies"],
            available_copies=data["total_copies"],
        )

        db.session.add(book)
        added += 1

    return added


def seed_employees():
    added = 0

    for data in EMPLOYEES:

        existing = Employee.query.filter_by(
            employee_code=data["employee_code"]
        ).first()

        if existing:
            continue

        employee = Employee(
            employee_code=data["employee_code"],
            name=data["name"],
            department=data["department"],
            designation=data["designation"],
            email=data["email"],
            status="ACTIVE",
        )

        db.session.add(employee)
        added += 1

    return added


with app.app_context():

    books_added = seed_books()
    employees_added = seed_employees()

    db.session.commit()

    print("----------------------------------------")
    print("Dummy data successfully inserted!")
    print(f"Books added:     {books_added}")
    print(f"Employees added: {employees_added}")
    print("----------------------------------------")