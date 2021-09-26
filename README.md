# JoinedUp-backend

[![](JoinedUp.gif)]

## Backend (Flask)

$ git clone [https://github.com/TomNewton1/JoinedUp-backend.git](https://github.com/TomNewton1/JoinedUp-backend.git)

change in to project directory

$ cd JoinedUp-backend

start virtual environment

$ source venv/bin/activate

install requirements

$ pip install -r requirements.txt

run the server (this will run on port 5000)

$ flask run

## Frontend (React)

The frontend repository can be found at: https://github.com/TomNewton1/JoinedUp-frontend

In a seperate directory clone the repository

$ git clone [https://github.com/TomNewton1/JoinedUp-frontend.git](https://github.com/TomNewton1/JoinedUp-frontend.git)

change in to project directory

$ cd JoinedUp-frontend

$ npm install 

$ npm start

the server will run on port 3000

### Notes/changes to make (since submission):
- Forgot to validate country code is submited correctly. Would do this by creating an array of country codes and checking if country code submitted is in the array. On the frontend I would provide a dropdown menu of country codes instead of a text input field.  
