from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from sqlalchemy import or_

from app.extensions import db
from app.models import Employee, BookTransaction


employees_bp = Blueprint(
    "employees",
    __name__,
    url_prefix="/employees"
)


# ============================================================
# EMPLOYEE LIST
# ============================================================

@employees_bp.route("/")
def list_employees():

    search_query = request.args.get(
        "q",
        ""
    ).strip()

    query = Employee.query

    # Database-side search
    if search_query:

        search = f"%{search_query}%"

        query = query.filter(
            or_(
                Employee.employee_code.ilike(search),
                Employee.name.ilike(search),
                Employee.department.ilike(search),
                Employee.designation.ilike(search),
                Employee.email.ilike(search),
                Employee.phone.ilike(search)
            )
        )

    employees = query.order_by(
        Employee.name.asc()
    ).all()

    return render_template(
        "employees/list.html",
        employees=employees,
        search_query=search_query
    )


# ============================================================
# EMPLOYEE OVERVIEW
# Read-only page used by dashboard
# ============================================================

@employees_bp.route("/overview")
def employees_overview():

    search_query = request.args.get(
        "q",
        ""
    ).strip()

    query = Employee.query

    # Database-side search
    if search_query:

        search = f"%{search_query}%"

        query = query.filter(
            or_(
                Employee.employee_code.ilike(search),
                Employee.name.ilike(search),
                Employee.department.ilike(search),
                Employee.designation.ilike(search),
                Employee.email.ilike(search),
                Employee.phone.ilike(search)
            )
        )

    employees = query.order_by(
        Employee.name.asc()
    ).all()

    return render_template(
        "employees/overview.html",
        employees=employees,
        search_query=search_query
    )


# ============================================================
# ADD EMPLOYEE
# ============================================================

@employees_bp.route(
    "/add",
    methods=["GET", "POST"]
)
def add_employee():

    if request.method == "POST":

        employee_code = request.form.get(
            "employee_code",
            ""
        ).strip()

        name = request.form.get(
            "name",
            ""
        ).strip()

        department = request.form.get(
            "department",
            ""
        ).strip()

        designation = request.form.get(
            "designation",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        status = request.form.get(
            "status",
            "ACTIVE"
        ).strip()


        # ----------------------------------------------------
        # REQUIRED FIELDS
        # ----------------------------------------------------

        if not employee_code or not name:

            flash(
                "Employee code and name are required.",
                "danger"
            )

            return render_template(
                "employees/add.html"
            )


        # ----------------------------------------------------
        # DUPLICATE EMPLOYEE CODE
        # ----------------------------------------------------

        existing_employee = Employee.query.filter_by(
            employee_code=employee_code
        ).first()

        if existing_employee:

            flash(
                "An employee with this code already exists.",
                "danger"
            )

            return render_template(
                "employees/add.html"
            )


        # ----------------------------------------------------
        # CREATE EMPLOYEE
        # ----------------------------------------------------

        employee = Employee(
            employee_code=employee_code,
            name=name,
            department=department or None,
            designation=designation or None,
            email=email or None,
            phone=phone or None,
            status=status
        )

        db.session.add(employee)
        db.session.commit()


        flash(
            "Employee added successfully.",
            "success"
        )

        return redirect(
            url_for("employees.list_employees")
        )


    return render_template(
        "employees/add.html"
    )


# ============================================================
# EDIT EMPLOYEE
# ============================================================

@employees_bp.route(
    "/<int:employee_id>/edit",
    methods=["GET", "POST"]
)
def edit_employee(employee_id):

    employee = Employee.query.get_or_404(
        employee_id
    )

    if request.method == "POST":

        employee_code = request.form.get(
            "employee_code",
            ""
        ).strip()

        name = request.form.get(
            "name",
            ""
        ).strip()

        department = request.form.get(
            "department",
            ""
        ).strip()

        designation = request.form.get(
            "designation",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        status = request.form.get(
            "status",
            "ACTIVE"
        ).strip()


        # ----------------------------------------------------
        # REQUIRED FIELDS
        # ----------------------------------------------------

        if not employee_code or not name:

            flash(
                "Employee code and name are required.",
                "danger"
            )

            return render_template(
                "employees/edit.html",
                employee=employee
            )


        # ---------------- ------------------------------------
        # DUPLICATE EMPLOYEE CODE
        # ----------------------------------------------------

        existing_employee = Employee.query.filter(
            Employee.employee_code == employee_code,
            Employee.id != employee.id
        ).first()

        if existing_employee:

            flash(
                "Another employee with this code already exists.",
                "danger"
            )

            return render_template(
                "employees/edit.html",
                employee=employee
            )


        # ----------------------------------------------------
        # UPDATE EMPLOYEE
        # ----------------------------------------------------

        employee.employee_code = employee_code
        employee.name = name
        employee.department = department or None
        employee.designation = designation or None
        employee.email = email or None
        employee.phone = phone or None
        employee.status = status

        db.session.commit()


        flash(
            "Employee updated successfully.",
            "success"
        )

        return redirect(
            url_for("employees.list_employees")
        )


    return render_template(
        "employees/edit.html",
        employee=employee
    )


# ============================================================
# DELETE EMPLOYEE
# ============================================================

@employees_bp.route(
    "/<int:employee_id>/delete",
    methods=["POST"]
)
def delete_employee(employee_id):

    employee = Employee.query.get_or_404(
        employee_id
    )


    # ----------------------------------------------------
    # BLOCK DELETE IF EMPLOYEE HAS AN ACTIVE TRANSACTION
    # ----------------------------------------------------

    active_transaction = BookTransaction.query.filter_by(
        employee_id=employee.id
    ).first()

    if active_transaction:

        flash(
            f"Cannot delete '{employee.name}' because "
            f"they currently have a book issued to them "
            f"that has not been returned.",
            "danger"
        )

        return redirect(
            url_for("employees.list_employees")
        )


    # ----------------------------------------------------
    # DELETE EMPLOYEE
    # ----------------------------------------------------

    db.session.delete(employee)
    db.session.commit()


    flash(
        "Employee deleted successfully.",
        "success"
    )

    return redirect(
        url_for("employees.list_employees")
    )