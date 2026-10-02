# MySQL Setup

The portal stores employee records in MySQL and refreshes the displayed data automatically every 10 seconds by default. The sidebar lets you change the polling interval, disable auto-refresh, or refresh immediately. Install MySQL Server 8.0 or newer, then install the Python dependencies:

```powershell
python -m pip install -r requirements.txt
```

Create the database and a dedicated application user in MySQL Workbench or the MySQL command line. Run these statements as an administrator and replace the password with a strong secret:

```sql
CREATE DATABASE peopledesk CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'peopledesk_app'@'localhost' IDENTIFIED BY 'replace-with-a-strong-password';
GRANT SELECT, INSERT, DELETE, CREATE ON peopledesk.* TO 'peopledesk_app'@'localhost';
```

In the same PowerShell session used to start Streamlit, set the connection settings:

```powershell
$env:MYSQL_HOST = 'localhost'
$env:MYSQL_PORT = '3306'
$env:MYSQL_DATABASE = 'peopledesk'
$env:MYSQL_USER = 'peopledesk_app'
$env:MYSQL_PASSWORD = '<set-this-in-your-local-environment>'
python -m streamlit run app.py
```

For a remote MySQL server, set `MYSQL_HOST` to its hostname and create the application user for the connecting host instead of `localhost`. Keep the password in an environment secret; never commit it to source control.

The database must exist before starting the app. On first connection, the app creates the `employees` and `app_migrations` tables. Existing rows in `validation.csv` are imported once and tracked in `app_migrations`; the CSV remains as a backup, while new records are written directly to MySQL.