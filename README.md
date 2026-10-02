# 👥 PeopleDesk – Employee Registration Portal

**PeopleDesk** is a web-based Employee Registration and Management Portal developed using **Python and Streamlit**. It provides an interactive interface for registering employees, managing employee records, viewing workforce statistics, and generating different reports.

The application stores employee information in a **MySQL-compatible database**, with support for **TiDB** as the cloud database platform.

---

## 🚀 Features

### 👤 Employee Registration

* Register new employees
* Full name, email, phone number and gender
* Department and city selection
* Salary management
* Automatic registration date
* Duplicate email prevention
* Input validation

### 📄 Employee Records

* View all registered employees
* Search employees by name
* Filter records by department
* Filter records by city
* Delete individual employee records
* Delete all employee records
* Download filtered records as CSV

### 📊 Dashboard

* Total employee count
* Total departments
* Average salary
* Department-wise employee distribution
* City-wise employee distribution
* Interactive charts using Altair

### 📈 Reports

PeopleDesk provides multiple report types:

* **Summary Report**
* **Department Report**
* **City Report**
* **Salary Report**
* **Individual Salary Slip**

Department and city reports include employee counts and salary statistics. The Salary Report provides total, average, minimum, maximum, and median salary information.

### 🔐 Portal Authentication

The application includes password-based portal authentication before employee data can be accessed. The portal password is configured through environment variables or Streamlit Secrets.

### 🔄 Live Data Refresh

* Automatic database refresh
* Configurable refresh interval
* Manual refresh option
* MySQL connection status
* Last synchronization time

The refresh interval can be configured for **5, 10, 30, or 60 seconds**.

---

## 🛠️ Technologies Used

| Technology                                    | Purpose                                   |
| --------------------------------------------- | ----------------------------------------- |
| **Python**                                    | Application logic and backend programming |
| **Streamlit**                                 | Web application framework and UI          |
| **Pandas**                                    | Data manipulation and analysis            |
| **MySQL**                                     | Employee data storage                     |
| **TiDB**                                      | Cloud/MySQL-compatible database platform  |
| **Altair**                                    | Data visualization                        |
| **Regular Expressions**                       | Email and phone validation                |
| **Streamlit Secrets / Environment Variables** | Secure configuration                      |

---

## 🏗️ System Architecture

```text
                    ┌──────────────────┐
                    │      User        │
                    └────────┬─────────┘
                             │
                             ▼
                 ┌──────────────────────┐
                 │  Streamlit Web App   │
                 │     PeopleDesk       │
                 └──────────┬───────────┘
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
          ▼                 ▼                 ▼
   Registration        Employee Records    Reports
          │                 │                 │
          └─────────────────┼─────────────────┘
                            │
                            ▼
                  ┌──────────────────┐
                  │  Python + SQL    │
                  │  CRUD Operations │
                  └────────┬─────────┘
                           │
                           ▼
                 ┌────────────────────┐
                 │   MySQL / TiDB     │
                 │     Database       │
                 └────────────────────┘
```

---

## 🔄 Application Workflow

```text
Start
  │
  ▼
Portal Login
  │
  ▼
Authentication
  │
  ▼
PeopleDesk Dashboard
  │
  ├── Overview
  │
  ├── Register Employee
  │       │
  │       ▼
  │   Validate Details
  │       │
  │       ▼
  │   Save to Database
  │
  ├── Employee Records
  │       │
  │       ├── Search
  │       ├── Filter
  │       ├── Download CSV
  │       └── Delete
  │
  ├── Dashboard
  │       │
  │       ├── Department Analysis
  │       └── City Analysis
  │
  └── Reports
          │
          ├── Summary
          ├── Department
          ├── City
          ├── Salary
          └── Salary Slip
```

---

## 🗄️ Database Structure

PeopleDesk automatically creates the `employees` table when the application connects to the database.

### Employee Table

| Column           | Type          | Description            |
| ---------------- | ------------- | ---------------------- |
| EmployeeId       | INT           | Unique employee ID     |
| Name             | VARCHAR(150)  | Employee name          |
| Email            | VARCHAR(320)  | Employee email         |
| Phone            | VARCHAR(10)   | Employee phone number  |
| Gender           | VARCHAR(30)   | Employee gender        |
| Department       | VARCHAR(100)  | Employee department    |
| City             | VARCHAR(100)  | Employee city          |
| Salary           | DECIMAL(18,2) | Employee salary        |
| RegistrationDate | DATETIME      | Registration timestamp |

The email field has a **unique constraint**, helping prevent duplicate employee registrations.

---

## 🔧 CRUD Operations

PeopleDesk implements the basic CRUD operations:

```text
CREATE
  ↓
Register Employee

READ
  ↓
View Employee Records

UPDATE
  ↓
Employee data management / extension point

DELETE
  ↓
Delete Individual Employee
Delete All Employees
```

## The current implementation directly provides employee creation, retrieval, and deletion operations through the application interface.

## ✅ Data Validation

The application validates employee information before saving it to the database.

### Email Validation

The application checks whether the email follows a valid email format.

### Phone Validation

The application validates that the phone number contains **10 digits**.

### Required Fields

The following fields are required:

* Full Name
* Email
* Phone Number
* Department
* City

### Duplicate Email

## An employee cannot be registered with an email address that already exists in the database.

## 🔐 Database Configuration

Database credentials are **not hard-coded** into the application.

PeopleDesk reads database configuration from environment variables or Streamlit Secrets.

Example configuration:

```text
MYSQL_HOST
MYSQL_PORT
MYSQL_DATABASE
MYSQL_USER
MYSQL_PASSWORD
MYSQL_SSL_VERIFY
```

The application also supports SSL certificate verification when configured.

> ⚠️ **Important:** Never upload database passwords, API keys, or other credentials to GitHub.

---

## ▶️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/PeopleDesk.git
```

### 2. Open the Project

```bash
cd PeopleDesk
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Database Credentials

Configure your MySQL/TiDB credentials using environment variables or Streamlit Secrets.

### 6. Run the Application

```bash
streamlit run app.py
```

The PeopleDesk application will then open in your web browser.

---

## 📦 Main Dependencies

The application uses Python libraries including:

```text
streamlit
pandas
altair
mysql-connector-python
streamlit-autorefresh
```

Additional dependencies may be required depending on the deployment configuration.

---

## 📁 Project Structure

A typical project structure can be:

```text
PeopleDesk/
│
├── app.py
├── requirements.txt
├── README.md
├── validation.csv
│
└── .streamlit/
    └── secrets.toml
```

> Do not commit `secrets.toml` containing real credentials to GitHub.

---

## 📊 Dashboard Analytics

The dashboard provides a quick overview of workforce information:

* Total employees
* Number of departments
* Average salary
* Department-wise distribution
* City-wise distribution

## The application uses **Altair** to generate bar charts for department and city distributions.

## 📑 Reports

### Summary Report

Provides:

* Total employees
* Total departments
* Total cities
* Average salary
* Complete employee table

### Department Report

Provides:

* Total employees
* Total salary
* Average salary
* Minimum salary
* Maximum salary

### City Report

Provides:

* Total employees
* Total salary
* Average salary

### Salary Report

Provides:

* Total salary
* Average salary
* Minimum salary
* Maximum salary
* Median salary
* Salary distribution

### Salary Slip

Displays individual employee information including:

* Name
* Email
* Phone
* Gender
* Department
* City
* Monthly salary
* Annual salary
* Registration date

---

## 🔄 Legacy Data Migration

PeopleDesk supports a one-time migration of existing employee information from `validation.csv` into the MySQL database.

The application uses an `app_migrations` table to track whether the migration has already been completed, helping prevent repeated imports.

---

## 🎯 Project Objectives

The main objectives of PeopleDesk are:

1. Develop an interactive employee management application.
2. Implement a Streamlit-based web interface.
3. Connect a Python application with a SQL database.
4. Store employee information persistently.
5. Implement employee data validation.
6. Provide workforce analytics and reports.
7. Practice real-world database operations.
8. Build a deployable portfolio project.

---

## 🔮 Future Enhancements

Possible future improvements include:

* 🔐 Role-based authentication
* 👨‍💼 Admin and HR user roles
* ✏️ Dedicated employee edit/update functionality
* 📄 PDF report generation
* 📧 Email notifications
* 📊 More advanced analytics
* 📥 Excel export
* 👤 Employee profile management
* 🕒 Attendance management
* 🏖️ Leave management
* ☁️ Production cloud deployment


---

## 👨‍💻 Developer

**Abhay Singh**
DATA ANALYTICS
B.Tech – CSE (AI&DS)
Lucknow, Uttar Pradesh

---

## 📌 Project Information

**Project Name:** PeopleDesk – Employee Registration Portal
**Version:** 1.0
**Application Type:** Web-based Employee Management System
**Framework:** Streamlit
**Database:** MySQL / TiDB
**Language:** Python

---

## 📄 License

This project is developed for **educational, learning, and portfolio purposes**.
