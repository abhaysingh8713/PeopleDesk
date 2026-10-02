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
$env:PORTAL_PASSWORD = '<choose-a-private-portal-password>'
python -m streamlit run app.py
```

For a remote MySQL server, set `MYSQL_HOST` to its hostname and create the application user for the connecting host instead of `localhost`. Keep the password in an environment secret; never commit it to source control.

The database must exist before starting the app. On first connection, the app creates the `employees` and `app_migrations` tables. If `validation.csv` is present locally, it is imported once and tracked in `app_migrations`; it is ignored by Git and is not included in the public repository. Rows already in a local MySQL server are not copied automatically.

## Deploy on Streamlit Community Cloud

Push the project to GitHub, then create a Community Cloud app using repository `abhaysingh8713/PeopleDesk`, branch `main`, and entry point `app.py`. In the app's **Settings > Secrets**, add TOML values for the remote MySQL server:

For the PeopleDesk TiDB Cloud Starter instance, use the host and username shown by its **Connect** panel, port `4000`, and database `peopledesk`:

In TiDB SQL Editor, create a separate app user with a new password instead of using the generated admin account:

```sql
CREATE USER 'peopledesk_app'@'%' IDENTIFIED BY 'replace-with-a-new-strong-secret';
GRANT SELECT, INSERT, DELETE, CREATE ON peopledesk.* TO 'peopledesk_app'@'%';
```

Use the exact app username format shown by the TiDB **Connect** panel.

```toml
MYSQL_HOST = "your-tiDB-public-host"
MYSQL_PORT = 4000
MYSQL_DATABASE = "peopledesk"
MYSQL_USER = "your-dedicated-tiDB-app-user"
MYSQL_PASSWORD = "your-new-strong-secret"
MYSQL_SSL_VERIFY = true
PORTAL_PASSWORD = "choose-a-different-private-portal-password"
```

Use a managed MySQL host reachable from Streamlit Community Cloud; `localhost` refers to the hosted app container, not your development PC. TiDB Cloud Starter requires TLS; `MYSQL_SSL_VERIFY = true` enables CA and hostname verification. `PORTAL_PASSWORD` protects employee names, contact details, and salary data from anonymous visitors. Keep both passwords only in Community Cloud Secrets. Rotate the one-time TiDB connection password that was exposed during setup before using it.

The current two records remain in the local MySQL database. Export/import them to TiDB only if they are safe to publish to this password-protected cloud portal; otherwise, start with the empty hosted database.