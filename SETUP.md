## SetUp Guide

### Clone the Repository  
> git clone https://github.com/shashankg82/OrbitAI.git
> 
> cd OrbitAI

### Create a Virtual Environment  
> python -m venv venv
Activate it:
* In Windows: venv\Scripts\activate
* In macOS/Linux: source venv/bin/activate

### Install Dependencies  
> pip install -r requirements.txt

### Apply Migrations
> python manage.py migrate

### Run the Server
> python manage.py runserver

Now visit: http://127.0.0.1:8000
