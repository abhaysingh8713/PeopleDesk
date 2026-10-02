import streamlit as st
import altair as alt
import pandas as pd
from streamlit.errors import StreamlitSecretNotFoundError
from streamlit_autorefresh import st_autorefresh
import os
from datetime import datetime
import re

LEGACY_CSV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "validation.csv")
MYSQL_DATABASE_ENV = "MYSQL_DATABASE"

def get_mysql_setting(name, default=""):
    environment_value = os.getenv(name)
    if environment_value:
        return environment_value
    try:
        return str(st.secrets.get(name, default))
    except StreamlitSecretNotFoundError:
        return default

def open_mysql_connection():
    host = get_mysql_setting("MYSQL_HOST", "localhost").strip()
    database = get_mysql_setting(MYSQL_DATABASE_ENV, "peopledesk").strip()
    user = get_mysql_setting("MYSQL_USER").strip()
    password = get_mysql_setting("MYSQL_PASSWORD")
    if not user or not password:
        raise RuntimeError("Set MYSQL_USER and MYSQL_PASSWORD as environment variables or Streamlit secrets to connect to MySQL.")
    try:
        import mysql.connector
    except ImportError as error:
        raise RuntimeError("Install the project dependencies with `pip install -r requirements.txt`.") from error
    return mysql.connector.connect(
        host=host,
        port=int(get_mysql_setting("MYSQL_PORT", "3306")),
        database=database,
        user=user,
        password=password,
        connection_timeout=5,
        charset="utf8mb4"
    )

def initialize_database(connection):
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            EmployeeId INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            Name VARCHAR(150) NOT NULL,
            Email VARCHAR(320) NOT NULL,
            Phone VARCHAR(10) NOT NULL,
            Gender VARCHAR(30) NOT NULL,
            Department VARCHAR(100) NOT NULL,
            City VARCHAR(100) NOT NULL,
            Salary DECIMAL(18, 2) NOT NULL,
            RegistrationDate DATETIME NOT NULL,
            UNIQUE KEY uq_employees_email (Email)
        ) CHARACTER SET utf8mb4
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS app_migrations (
            MigrationName VARCHAR(100) NOT NULL PRIMARY KEY,
            AppliedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ) CHARACTER SET utf8mb4
    """)
    connection.commit()

    if not os.path.exists(LEGACY_CSV_FILE):
        return

    migration_name = "import_validation_csv_v1"
    cursor.execute("SELECT 1 FROM app_migrations WHERE MigrationName = %s", (migration_name,))
    if cursor.fetchone():
        return

    legacy_df = pd.read_csv(LEGACY_CSV_FILE)
    for _, employee in legacy_df.iterrows():
        email = str(employee.get("Email", "")).strip().lower()
        if not email:
            continue
        registration_date = pd.to_datetime(employee.get("Registration Date"), errors="coerce")
        registration_date = datetime.now() if pd.isna(registration_date) else registration_date.to_pydatetime()
        cursor.execute("SELECT 1 FROM employees WHERE Email = %s", (email,))
        if cursor.fetchone():
            continue
        cursor.execute("""
            INSERT INTO employees
                (Name, Email, Phone, Gender, Department, City, Salary, RegistrationDate)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (str(employee.get("Name", "")), email,
              re.sub(r"\D", "", str(employee.get("Phone", ""))),
              str(employee.get("Gender", "")), str(employee.get("Department", "")),
              str(employee.get("City", "")), float(employee.get("Salary", 0) or 0), registration_date))

    cursor.execute("INSERT INTO app_migrations (MigrationName) VALUES (%s)", (migration_name,))
    connection.commit()

def get_employee_records():
    connection = None
    try:
        connection = open_mysql_connection()
        initialize_database(connection)
        cursor = connection.cursor()
        cursor.execute("""
            SELECT EmployeeId, Name, Email, Phone, Gender, Department, City, Salary,
                     RegistrationDate AS `Registration Date`
                 FROM employees
            ORDER BY EmployeeId DESC
        """)
        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        st.session_state["mysql_connected"] = True
        st.session_state["mysql_last_sync"] = datetime.now()
        return pd.DataFrame.from_records(rows, columns=columns)
    except Exception as error:
        st.session_state["mysql_connected"] = False
        if connection is not None:
            connection.rollback()
        st.error(f"MySQL is unavailable: {error}")
        return None
    finally:
        if connection is not None:
            connection.close()

def insert_employee_record(employee):
    connection = None
    try:
        connection = open_mysql_connection()
        initialize_database(connection)
        cursor = connection.cursor()
        cursor.execute("SELECT 1 FROM employees WHERE Email = %s", (employee["Email"],))
        if cursor.fetchone():
            return "duplicate"
        cursor.execute("""
            INSERT INTO employees
                (Name, Email, Phone, Gender, Department, City, Salary, RegistrationDate)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (employee["Name"], employee["Email"], employee["Phone"], employee["Gender"],
              employee["Department"], employee["City"], employee["Salary"], datetime.now()))
        connection.commit()
        return "saved"
    except Exception as error:
        if connection is not None:
            connection.rollback()
        st.error(f"Could not save employee to MySQL: {error}")
        return None
    finally:
        if connection is not None:
            connection.close()

# Helper function to validate email
def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# Helper function to validate phone
def validate_phone(phone):
    """Validate phone number (10 digits)"""
    return len(re.sub(r'\D', '', phone)) == 10

def render_bar_chart(series, color):
    chart_data = series.rename_axis("Category").reset_index(name="Employees")
    chart = (
        alt.Chart(chart_data)
        .mark_bar(color=color, cornerRadiusEnd=4)
        .encode(
            x=alt.X("Category:N", sort="-y", title=None, axis=alt.Axis(labelAngle=0)),
            y=alt.Y("Employees:Q", title=None),
            tooltip=[alt.Tooltip("Category:N", title="Category"), alt.Tooltip("Employees:Q", title="Count")]
        )
        .properties(height=250)
        .configure(background="transparent")
        .configure_view(fill="transparent", stroke=None)
        .configure_axis(domain=False, labelColor="#708078", gridColor="#edf0ea")
    )
    st.altair_chart(chart, width="stretch", theme=None)

def delete_employee(employee_id):
    connection = None
    try:
        connection = open_mysql_connection()
        initialize_database(connection)
        connection.cursor().execute("DELETE FROM employees WHERE EmployeeId = %s", (employee_id,))
        connection.commit()
        st.success("Employee deleted successfully!")
        st.rerun()
    except Exception as error:
        if connection is not None:
            connection.rollback()
        st.error(f"Could not delete employee from MySQL: {error}")
    finally:
        if connection is not None:
            connection.close()

def delete_all_employees():
    connection = None
    try:
        connection = open_mysql_connection()
        initialize_database(connection)
        connection.cursor().execute("DELETE FROM employees")
        connection.commit()
        st.success("All employee records were deleted.")
        st.rerun()
    except Exception as error:
        if connection is not None:
            connection.rollback()
        st.error(f"Could not delete employee records from MySQL: {error}")
    finally:
        if connection is not None:
            connection.close()

def format_employee_option(df, employee_id):
    employee = df.loc[df["EmployeeId"] == employee_id].iloc[0]
    return f"{employee['Name']} · {employee['Email']}"

# ---------------- PAGE CONFIG ---------------- #

st.set_page_config(
    page_title="PeopleDesk | Workforce Portal",
    page_icon="🟢",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
:root { --ink: #18352d; --muted: #708078; --leaf: #c9ef83; --paper: #f4f6f1; --line: #e2e8df; }
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background: var(--paper); color: var(--ink); }
[data-testid="stHeader"] { background: rgba(244,246,241,.92); }
[data-testid="stSidebar"] { background: #173d33; border-right: 0; }
[data-testid="stSidebar"] * { color: #edf5eb; }
.brand-lockup { display: flex; align-items: center; gap: .65rem; padding: .25rem 0 .85rem; }
.brand-mark { display: grid; place-items: center; width: 38px; height: 38px; flex: 0 0 38px; border-radius: 9px; background: #c9ef83; color: #173d33 !important; font: 800 1.1rem 'Manrope', sans-serif; }
.brand-copy { display: flex; flex-direction: column; gap: .12rem; }
.brand-name { color: #fff !important; font: 600 1.08rem 'Manrope', sans-serif; }
.brand-name strong { color: #c9ef83 !important; font-weight: 800; }
.brand-tagline { color: #b6c8bf !important; font-size: .62rem; font-weight: 600; }
[data-testid="stSidebar"] [data-testid="stRadio"] label { padding: .55rem .7rem; border-radius: 8px; }
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover { background: rgba(255,255,255,.08); }
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,.16); }
h1, h2, h3 { font-family: 'Manrope', sans-serif !important; color: var(--ink); letter-spacing: 0 !important; }
h1 { font-size: 2rem !important; font-weight: 800 !important; }
[data-testid="stMetric"] { background: #fff; border: 1px solid var(--line); border-radius: 10px; padding: 1rem 1.1rem; }
[data-testid="stMetricLabel"] { color: var(--muted); font-weight: 600; }
[data-testid="stMetricValue"] { color: var(--ink); font-family: 'Manrope', sans-serif; }
[data-testid="stForm"] { background: #fff; border: 1px solid var(--line); border-radius: 10px; padding: 1.2rem; }
[data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 8px; overflow: hidden; }
.stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] button { border-radius: 7px; font-weight: 700; }
.stButton > button[kind="primary"], [data-testid="stFormSubmitButton"] button { background: #1c5142; border-color: #1c5142; color: white; }
.portal-hero { background: #173d33; border-radius: 12px; padding: 1.7rem 2rem; color: white; margin: .2rem 0 1.3rem; position: relative; overflow: hidden; }
.portal-hero:after { content: ''; position: absolute; width: 190px; height: 190px; right: 7%; top: -110px; border: 1px solid rgba(201,239,131,.36); border-radius: 50%; box-shadow: 0 0 0 24px rgba(201,239,131,.06), 0 0 0 48px rgba(201,239,131,.04); }
.portal-hero .eyebrow { text-transform: uppercase; letter-spacing: 1.4px; color: var(--leaf); font-size: .72rem; font-weight: 700; }
.portal-hero h1 { color: white; margin: .35rem 0 !important; font-size: 2.1rem !important; }
.portal-hero p { color: #c5d6cd; margin: 0; max-width: 640px; }
.section-label { color: var(--muted); text-transform: uppercase; font-size: .72rem; font-weight: 700; letter-spacing: 1px; margin: .5rem 0 .8rem; }
@media (max-width: 700px) { .portal-hero { padding: 1.25rem; } .portal-hero h1 { font-size: 1.65rem !important; } }
</style>
""", unsafe_allow_html=True)

# ---------------- SIDEBAR ---------------- #

st.sidebar.markdown(
    '<div class="brand-lockup" aria-label="PeopleDesk logo">'
    '<div class="brand-mark">PD</div>'
    '<div class="brand-copy"><div class="brand-name">People<strong>Desk</strong></div>'
    '<div class="brand-tagline">PEOPLE OPERATIONS</div></div></div>',
    unsafe_allow_html=True
)
st.sidebar.divider()

menu = st.sidebar.radio(
    "Go To",
    [
        "🏠 Overview",
        "👨‍💼 Register Employee",
        "📄 Employee Records",
        "📊 Dashboard",
        "📈 Reports",
        "ℹ️ About"
    ]
)

st.sidebar.divider()
st.sidebar.markdown("### Live data")
auto_refresh = st.sidebar.toggle(
    "Auto-refresh",
    value=True,
    help="Fetch the latest employee data from MySQL automatically."
)
refresh_seconds = st.sidebar.select_slider(
    "Refresh interval",
    options=[5, 10, 30, 60],
    value=10,
    format_func=lambda seconds: f"{seconds} sec",
    disabled=not auto_refresh
)
st.sidebar.button("Refresh now", icon=":material/refresh:", width="stretch")
if auto_refresh:
    st_autorefresh(interval=refresh_seconds * 1000, key="people_desk_live_refresh")

df = get_employee_records()
if st.session_state.get("mysql_connected"):
    st.sidebar.markdown("**● MySQL connected**")
    last_sync = st.session_state.get("mysql_last_sync")
    if last_sync:
        st.sidebar.caption(f"Last sync: {last_sync:%H:%M:%S}")
else:
    st.sidebar.markdown("**● MySQL connection unavailable**")

# ---------------- OVERVIEW ---------------- #

if menu == "🏠 Overview":

    df = df if df is not None else pd.DataFrame()
    employee_count = len(df)
    department_count = df["Department"].nunique() if "Department" in df.columns else 0
    city_count = df["City"].nunique() if "City" in df.columns else 0
    average_salary = df["Salary"].mean() if employee_count and "Salary" in df.columns else 0

    st.markdown("""
    <div class="portal-hero">
      <div class="eyebrow">People operations · Overview</div>
      <h1>Your people, in one place.</h1>
      <p>A clear view of your workforce, with the tools to manage every employee record.</p>
    </div>
    """, unsafe_allow_html=True)

    metric_columns = st.columns(4)
    metric_columns[0].metric("Employees", f"{employee_count:,}")
    metric_columns[1].metric("Departments", f"{department_count:,}")
    metric_columns[2].metric("Cities", f"{city_count:,}")
    metric_columns[3].metric("Average salary", f"₹{average_salary:,.0f}")

    st.markdown('<div class="section-label">Workforce snapshot</div>', unsafe_allow_html=True)
    chart_column, recent_column = st.columns([1.05, 1])
    with chart_column:
        st.subheader("Team distribution")
        if employee_count and "Department" in df.columns:
            render_bar_chart(df["Department"].value_counts(), "#8dbc5a")
        else:
            st.info("Register your first employee to see team distribution.")
    with recent_column:
        st.subheader("Recently added")
        if employee_count:
            recent_columns = [column for column in ["Name", "Department", "City", "Registration Date"] if column in df.columns]
            st.dataframe(df[recent_columns].tail(5).iloc[::-1], hide_index=True, width="stretch")
        else:
            st.info("Your latest employee records will appear here.")
    st.caption("Live workforce data from MySQL.")

# ---------------- REGISTER PAGE ---------------- #

elif menu == "👨‍💼 Register Employee":

    st.title("📝 Employee Registration Form")

    st.write("Add a team member to your workforce directory.")

    st.divider()

    with st.form("employee_form"):

        col1, col2 = st.columns(2)

        # LEFT COLUMN

        with col1:

            name = st.text_input("👤 Full Name")

            email = st.text_input("📧 Email")

            phone = st.text_input("📱 Phone Number")

        # RIGHT COLUMN

        with col2:

            department = st.selectbox(
                "🏢 Department",
                [
                    "Select",
                    "HR",
                    "IT",
                    "Finance",
                    "Sales",
                    "Marketing"
                ]
            )

            salary = st.number_input(
                "💰 Salary",
                min_value=0
            )

            city = st.selectbox(
                "🏙 City",
                [
                    "Select",
                    "Lucknow",
                    "Delhi",
                    "Mumbai",
                    "Hyderabad",
                    "Bengaluru"
                ]
            )

        gender = st.radio(
            "Gender",
            ["Male", "Female", "Other"],
            horizontal=True
        )

        submit = st.form_submit_button(
            "🚀 Register Employee"
        )

    if submit:
        # Validation
        errors = []
        
        if not name or name.strip() == "":
            errors.append("Full Name is required")
        elif len(name) < 3:
            errors.append("Full Name must be at least 3 characters")
            
        if not email or email.strip() == "":
            errors.append("Email is required")
        elif not validate_email(email):
            errors.append("Invalid email format (e.g., user@example.com)")
            
        if not phone or phone.strip() == "":
            errors.append("Phone Number is required")
        elif not validate_phone(phone):
            errors.append("Phone must be a valid 10-digit number")
            
        if department == "Select":
            errors.append("Please select a Department")
            
        if city == "Select":
            errors.append("Please select a City")
            
        existing_df = df
        if existing_df is None:
            errors.append("Connect to MySQL before registering an employee")
        elif "Email" in existing_df.columns:
            if email.strip().casefold() in existing_df["Email"].astype(str).str.strip().str.casefold().values:
                errors.append("An employee with this email address is already registered")
        
        # Show all errors
        if errors:
            for error in errors:
                st.error(f"❌ {error}")
        else:
            # Create employee data dictionary
            employee_data = {
                "Name": name.strip(),
                "Email": email.strip().lower(),
                "Phone": re.sub(r"\D", "", phone),
                "Gender": gender,
                "Department": department,
                "City": city,
                "Salary": salary,
                "Registration Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            save_result = insert_employee_record(employee_data)
            if save_result == "saved":
                st.success("✅ Employee registered successfully!")
                st.balloons()
            elif save_result == "duplicate":
                st.error("An employee with this email address is already registered")

# ---------------- EMPLOYEE RECORDS ---------------- #

elif menu == "📄 Employee Records":

    st.title("📄 Employee Records")

    if df is not None and len(df) > 0:
        st.success(f"✅ Total Employees: {len(df)}")
        
        # Search and Filter Section
        st.divider()
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_name = st.text_input("🔍 Search by Name", "")
        with col2:
            departments = df["Department"].dropna().astype(str).unique().tolist() if "Department" in df.columns else []
            filter_dept = st.selectbox("Filter by Department", ["All"] + departments)
        with col3:
            cities = df["City"].dropna().astype(str).unique().tolist() if "City" in df.columns else []
            filter_city = st.selectbox("Filter by City", ["All"] + cities)
        
        # Apply filters
        filtered_df = df.copy()
        if search_name and "Name" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["Name"].str.contains(search_name, case=False, na=False)]
        if filter_dept != "All" and "Department" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["Department"] == filter_dept]
        if filter_city != "All" and "City" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["City"] == filter_city]
        
        st.divider()
        st.dataframe(filtered_df, width="stretch")
        
        # Download CSV
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name="employee_records.csv",
            mime="text/csv"
        )
        
        # Delete Employee Section
        st.divider()
        st.subheader("🗑️ Delete Employee")
        
        if len(filtered_df) > 0:
            employee_to_delete = st.selectbox(
                "Select employee to delete:",
                filtered_df["EmployeeId"].tolist(),
                format_func=lambda employee_id: format_employee_option(df, employee_id)
            )
            
            if st.button("Delete Selected Employee", key="delete_btn"):
                delete_employee(employee_to_delete)
        
        # Reset/Delete All option
        with st.expander("Danger zone"):
            confirm_delete = st.checkbox("I understand this permanently deletes every employee record")
            if st.button("Delete All Data", key="delete_all", disabled=not confirm_delete):
                delete_all_employees()
    else:
        st.info("📋 No employee records available yet.")
        st.caption("Add an employee to start building your directory.")

# ---------------- DASHBOARD ---------------- #

elif menu == "📊 Dashboard":

    st.title("📊 Dashboard")

    if df is not None:
        col1, col2, col3 = st.columns(3)
        
        col1.metric("👨 Employees", len(df))
        col2.metric("🏢 Departments", df["Department"].nunique() if "Department" in df.columns else 0)
        col3.metric("💰 Average Salary", f"₹{int(df['Salary'].mean()) if len(df) and 'Salary' in df.columns else 0}")
        
        st.divider()
        
        # Department Distribution
        st.subheader("📊 Department-wise Distribution")
        if "Department" in df.columns:
            dept_count = df["Department"].value_counts()
            render_bar_chart(dept_count, "#8dbc5a")
        
        # City Distribution
        st.subheader("🏙 City-wise Distribution")
        if "City" in df.columns:
            city_count = df["City"].value_counts()
            render_bar_chart(city_count, "#4d9d88")
    else:
        col1, col2, col3 = st.columns(3)

        col1.metric("Employees", "0")

        col2.metric("Departments", "0")

        col3.metric("Average Salary", "₹0")
        
        st.info("No data available yet.")

# ---------------- REPORTS ---------------- #

elif menu == "📈 Reports":

    st.title("📈 Reports")

    if df is not None and len(df) > 0:
        # Report Type Selection
        report_type = st.radio(
            "Select Report Type:",
            ["Summary Report", "Department Report", "City Report", "Salary Report", "Salary Slip"],
            horizontal=True
        )
        
        st.divider()
        
        if report_type == "Summary Report":
            st.subheader("📊 Summary Report")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Employees", len(df))
            with col2:
                st.metric("Total Departments", df["Department"].nunique())
            with col3:
                st.metric("Total Cities", df["City"].nunique())
            with col4:
                avg_salary = int(df["Salary"].mean()) if "Salary" in df.columns else 0
                st.metric("Avg Salary", f"₹{avg_salary}")
            
            st.divider()
            st.dataframe(df, width="stretch")
        
        elif report_type == "Department Report":
            st.subheader("🏢 Department-wise Report")
            dept_report = df.groupby("Department").agg({
                "Name": "count",
                "Salary": ["sum", "mean", "min", "max"]
            }).round(0)
            dept_report.columns = ["Total Employees", "Total Salary", "Avg Salary", "Min Salary", "Max Salary"]
            st.dataframe(dept_report, width="stretch")
            
            render_bar_chart(df["Department"].value_counts(), "#8dbc5a")
        
        elif report_type == "City Report":
            st.subheader("🏙️ City-wise Report")
            city_report = df.groupby("City").agg({
                "Name": "count",
                "Salary": ["sum", "mean"]
            }).round(0)
            city_report.columns = ["Total Employees", "Total Salary", "Avg Salary"]
            st.dataframe(city_report, width="stretch")
            
            render_bar_chart(df["City"].value_counts(), "#4d9d88")
        
        elif report_type == "Salary Report":
            st.subheader("💰 Salary Report")
            salary_stats = {
                "Total Salary": f"₹{df['Salary'].sum()}",
                "Average Salary": f"₹{int(df['Salary'].mean())}",
                "Min Salary": f"₹{df['Salary'].min()}",
                "Max Salary": f"₹{df['Salary'].max()}",
                "Median Salary": f"₹{int(df['Salary'].median())}"
            }
            
            for key, value in salary_stats.items():
                st.info(f"{key}: {value}")
            
            st.divider()
            st.subheader("Salary Distribution")
            render_bar_chart(df["Salary"].value_counts().sort_index(), "#d29a55")
        
        elif report_type == "Salary Slip":
            st.subheader("💼 Individual Salary Slip")
            selected_employee = st.selectbox(
                "Select Employee:",
                df["EmployeeId"].tolist(),
                format_func=lambda employee_id: format_employee_option(df, employee_id)
            )

            emp_data = df.loc[df["EmployeeId"] == selected_employee].iloc[0]
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Name:** {emp_data['Name']}")
                st.write(f"**Email:** {emp_data['Email']}")
                st.write(f"**Phone:** {emp_data['Phone']}")
            with col2:
                st.write(f"**Gender:** {emp_data['Gender']}")
                st.write(f"**Department:** {emp_data['Department']}")
                st.write(f"**City:** {emp_data['City']}")
            
            st.divider()
            st.write(f"**Monthly Salary:** ₹{emp_data['Salary']}")
            st.write(f"**Annual Salary:** ₹{emp_data['Salary'] * 12}")
            st.write(f"**Registration Date:** {emp_data['Registration Date']}")
    else:
        st.warning("No data available to generate reports. Please register employees first.")

# ---------------- ABOUT ---------------- #

elif menu == "ℹ️ About":

    st.title("ℹ️ About Project")

    st.write("""
### Employee Registration Portal

A complete employee management system built using Python and Streamlit for registering, managing, and analyzing employee data.

#### Technologies Used
- **Python** - Backend programming
- **Streamlit** - Web framework
- **Pandas** - Data manipulation and analysis
- **Regular Expressions** - Email & Phone validation

#### Features

✅ **Employee Registration**
- Full Name, Email, Phone, Gender
- Department & City selection
- Salary management
- Duplicate email prevention
- Form validation with clear error handling

✅ **Employee Records**
- View all employee records in table format
- Search by employee name
- Filter by Department and City
- Download data as CSV file
- Delete individual or all records

✅ **Dashboard**
- Real-time employee statistics
- Department-wise distribution chart
- City-wise distribution chart
- Average salary calculation
- Department and city count metrics

✅ **Advanced Reports**
- Summary Report - Overview of all employees
- Department Report - Department-wise analytics
- City Report - City-wise analytics
- Salary Report - Salary statistics and distribution
- Salary Slip - Individual employee salary slip

✅ **Data Management**
- MySQL storage for employee records
- One-time import of records from the existing CSV
- Data persistence across sessions
- CSV export functionality

#### Validation Features
- Email format validation
- Phone number (10-digit) validation
- Mandatory field validation

#### Data Storage
Employee records are stored in the configured MySQL database. The existing validation.csv file is imported once when the MySQL connection is first configured.
""")

    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Quick Stats")
        if df is not None:
            st.metric("Total Employees", len(df))
            st.metric("Departments", df["Department"].nunique())
            st.metric("Cities", df["City"].nunique())
        else:
            st.info("No data available yet")
    
    with col2:
        st.subheader("👥 Developer Info")
        st.write("""
**Project:** Employee Registration Portal  
**Version:** 1.0  
**Developer:** Abhay Singh  
""")