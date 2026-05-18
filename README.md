# Podcraze - E-Commerce Platform

Podcraze is a feature-rich, modern E-commerce web application built with Django. Designed to provide a seamless shopping experience for premium audio products, the platform features robust user authentication, product cataloging, a dynamic shopping cart, order management, payment integration, and a comprehensive custom admin panel for complete store management.

## 🚀 Features

- **User Authentication:** Secure signup, login, password management, and OTP validation integration (via `django-allauth`).
- **Product Management:** Browse categories, view individual product details, and manage inventory.
- **Shopping Cart & Checkout:** Add products to the cart and proceed to checkout securely.
- **Payment Gateway:** Integrated with **Razorpay** for smooth and secure online transactions.
- **Order Management:** Users can view their order history and track order status.
- **Custom Admin Dashboard (`myadmin`):** Comprehensive dashboard to manage products, categories, users, and process order requests.
- **PDF & Excel Reports:** Generate invoices and sales reports using `reportlab` and `xlsxwriter`.
- **Cloud Storage:** Media and static files optimized and hosted via **Cloudinary** and Whitenoise.
- **Docker Ready:** Includes `Dockerfile` and `docker-compose.yml` for effortless containerized deployment.

## 🛠️ Tech Stack

- **Backend:** Python, Django 5.2, Django REST Framework
- **Database:** SQLite (Development) / MySQL (Production readiness)
- **Frontend:** HTML5, CSS3, JavaScript (Django Templates)
- **Payments:** Razorpay API
- **Storage:** Cloudinary
- **Deployment:** Docker, Docker Compose, Whitenoise

---

## ⚙️ Installation & Setup Process

### Prerequisites
Make sure you have the following installed on your system:
- Python (3.10+)
- pip (Python package installer)
- Git
- Docker (Optional, if you prefer containerized deployment)

### Option 1: Local Setup (Without Docker)

1. **Clone the repository**
   ```bash
   git clone <repository_url>
   cd First_Project-Ecommerce/Podcraze
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables Setup**
   The project requires certain environment variables to function correctly. Ensure your `.env` file in the project root (alongside `manage.py`) contains the necessary keys:
   ```env
   SECRET_KEY=your_django_secret_key
   DEBUG=True
   RAZORPAY_KEY_ID=your_razorpay_key_id
   RAZORPAY_KEY_SECRET=your_razorpay_key_secret
   CLOUDINARY_URL=your_cloudinary_url
   # Add your database credentials if using MySQL
   ```

5. **Apply Database Migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create a Superuser (Admin Account)**
   ```bash
   python manage.py createsuperuser
   ```
   Follow the prompts to set your admin username, email, and password.

7. **Run the Development Server**
   ```bash
   python manage.py runserver
   ```
   Open your browser and navigate to `http://127.0.0.1:8000/`.

---

### Option 2: Running with Docker

If you prefer to run the application using Docker, follow these steps:

1. **Build and Run the Containers**
   ```bash
   docker-compose up --build
   ```
   *Note: Ensure your `.env` file is properly configured before running Docker.*

2. **Run Migrations (if not auto-run)**
   Open a new terminal window and execute:
   ```bash
   docker-compose exec web python manage.py migrate
   ```

3. **Create Superuser via Docker**
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

4. **Access the Application**
   The application will be accessible at `http://localhost:8000/`.

---

## 📁 Application Structure

- **`user/`**: Handles all customer-facing features, including product browsing, the shopping cart, checkout, order tracking (`orderview.html`, `order.html`), and user authentication (e.g., `otp_validate.py`).
- **`myadmin/`**: A custom administration panel for store owners to manage the product catalog, monitor sales, and approve/process orders (`adminorder.html`, `order_requests.html`).
- **`Podcraze/`**: The core project directory containing main configurations, global settings, routing, and WSGI/ASGI entry points.
- **`staticfiles/`**: Directory where static assets are collected for production.

---

