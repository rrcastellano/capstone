# EVChargeLog (Django Capstone)

**EVChargeLog** is a robust web application designed to help Electric Vehicle (EV) owners track, manage, and analyze their charging sessions. Built with **Django**, it offers a dashboard with key performance indicators (KPIs), monthly cost/consumption trends, and savings estimates compared to gasoline vehicles.

This project is a port and evolution of an earlier Flask prototype, re-engineered to leverage Django's "batteries-included" philosophy for better scalability, security, and maintainability.

## Distinctiveness and Complexity

This project satisfies the distinctiveness and complexity requirements by implementing a feature-rich, data-intensive application that goes significantly beyond simple CRUD operations.

1.  **Complex Data Aggregation**: Unlike a standard blog or e-commerce site, EVChargeLog performs real-time data analysis. The Dashboard view aggregates thousands of recharge records into monthly groups, calculating derived metrics such as:
    *   **Consumption (kWh/100km)**: Derived from odometer readings and charged energy.
    *   **Savings Analysis**: Compares electricity costs against user-defined gasoline prices and consumption rates.
    *   **Distance Driven**: Calculated by diffing odometer readings between sessions.
    All this logic is handled in Python (`views.py`) and served via efficient APIs to the frontend.

2.  **Robust Bulk Import System**: One of the most complex features is the generic CSV importer (`bulk_recharge`). It doesn't just read a standard format; it implements a heuristic parser that:
    *   Detects file encoding (UTF-8, Latin-1) and handles BOMs.
    *   Normalizes newline characters to support files from different OSs.
    *   Automatically validates headers and maps data to the `Recharge` model.

3.  **Comprehensive Internationalization (i18n)**: The application is fully localized for **Portuguese (pt-br)**, **English (en-us)**, and **Spanish (es)**.
    *   **Locale-Aware Formatting**: Custom template filters (`custom_filters.py`) were created to format currency (e.g., `R$ 1.000,00` vs `$ 1,000.00`) and dates (`dd/mm/yyyy` vs `mm/dd/yyyy`) dynamically based on the active language.
    *   **Middleware**: Uses `Django's LocaleMiddleware` to persist language preferences across sessions.

4.  **Custom Administration**: The Django Admin was customized (`admin.py`) to provide business insights directly to site operators, adding computed columns like "Recharge Count" for users and a full search interface for Contact logs.

5.  **Mobile-Responsive Design**: The UI is built with Bootstrap 5 and custom CSS (`styles.css`) to ensure a seamless experience on mobile devices, including fluid typography (`clamp()`), responsive tables that hide non-essential columns on small screens, and touch-optimized touch targets.

## File Contents

-   **`capstone/`**: Main project configuration directory.
    -   `settings.py`: Configured for PostgreSQL, WhiteNoise (static files), and Internationalization.
    -   `urls.py`: Main URL routing including i18n patterns.

-   **`core/`**: The main application app.
    -   **`models.py`**: Defines the database schema:
        -   `Recharge`: Stores charging session data (date, kWh, cost, odometer, etc.).
        -   `Settings`: Stores user-specific preferences (gas price, car consumption).
        -   `ContactLog`: Stores "Contact Us" form submissions.
    -   **`views.py`**: Contains all business logic. Handles Dashboard aggregation, Auth views (Login/Register), generic CSV importing, and REST-like logic for managing recharges.
    -   **`admin.py`**: Customizes the Django Admin interface to show calculated fields and filters.
    -   **`forms.py`**: Defines Django Forms with `gettext_lazy` for translation support.
    -   **`urls.py`**: App-specific routing.
    -   **`templatetags/custom_filters.py`**: Custom filters for locale-aware number and date formatting.

-   **`core/templates/core/`**: HTML Templates.
    -   `dashboard.html`: The main analytics view with Chart.js integration.
    -   `manage_recharges.html`: A responsive table view for CRUD operations on data.
    -   `bulk_recharge.html`: Interface for CSV uploading with custom file input UI.
    -   `layout.html`: Base template with dynamic language switcher and responsive navbar.
    -   (and others: `index.html`, `register.html`, `contact.html`, `account.html`, `recharge.html`)

-   **`core/static/core/`**: Static assets.
    -   `js/dashboard_charts.js`: Renders the interactive charts using data stamped into the HTML.
    -   `css/styles.css`: Custom styling and mobile responsiveness rules (media queries).
    -   `img/`: Favicons and country flags.

-   **`deployment/` scripts**:
    -   `build.sh`: Shell script for Render.com deployment (installs deps, collects static, migrates).
    -   `create_superuser_prod.py`: Python script to auto-generate a superuser in production environments without SSH.

## How to Run

1.  **Clone the repository**:
    ```bash
    git clone <repository_url>
    cd capstone
    ```

2.  **Create and activate a virtual environment**:
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # Linux/Mac
    source venv/bin/activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Database Setup**:
    The project is configured to use PostgreSQL by default (via `dj_database_url`), but falls back to a local configuration. Ensure you have a database created or adjust `settings.py` to use SQLite if you prefer simplicity for testing.
    ```bash
    python manage.py migrate
    ```

5.  **Create a Superuser** (Optional):
    ```bash
    python manage.py createsuperuser
    ```

6.  **Run the Server**:
    ```bash
    python manage.py runserver
    ```
    Access the application at `http://127.0.0.1:8000`.

## Additional Information

-   **Deployment**: This project sends with a `build.sh` file specifically for **Render.com** deployment. It acts as a production-ready example of how to deploy Django apps.
-   **Security**: All user-specific data is isolated. Users can only view and edit their own recharges and settings.
