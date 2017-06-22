## Dockerizing Flask With Compose and Machine - From Localhost to the Cloud

Featuring:

- Docker v1.9.0
- Docker Compose v1.5.0
- Docker Machine v0.5.0

**Check out the awesome blog post here > https://realpython.com/blog/python/dockerizing-flask-with-compose-and-machine-from-localhost-to-the-cloud/**

Cheers!


## HOW TO RUN THE APP

#Description

The application is developed using Flask (A Python web development framework), PostgresSQL as backend on virtualbox engine

Prerequisites:
- Docker latest
- Docker Compose latest
- Docker Machine latest

Verify the installation:
$ docker-machine --version
docker-machine version 0.5.0 (04cfa58) (version might be different)
$ docker-compose --version
docker-compose version: 1.5.0 (version might be different)

Next clone the project using `git clone https://github.com/sirimala/elt.git`

cd to newly cloned repository

Directory structure may look similar this

.
├── docker-compose.yml
├── nginx
│   ├── Dockerfile
│   └── sites-enabled
│       └── flask_project
├── README.md
└── web
    ├── app.bak.py
    ├── app.py
    ├── config.py
    ├── create_db.py
    ├── Dockerfile
    ├── __init__.py
    ├── logs
    │   └── login.log
    ├── models.py
    ├── requirements.txt
    ├── settings.py
    ├── static
    │   ├── css
    │   │   ├── bootstrap.min.css
    │   │   └── main.css
    │   ├── img
    │   ├── javascripts
    │   │   ├── app.js
    │   │   ├── bootstrap.min.js
    │   │   ├── bootstrap-select.js
    │   │   ├── crossdomain.xml
    │   │   ├── feedback.js
    │   │   ├── jquery.min.js
    │   │   ├── quiz.js
    │   │   ├── recorder.js
    │   │   ├── RecordRTCInterface.js
    │   │   ├── RecordRTC.js
    │   │   ├── render_qb.js
    │   │   └── Wami.swf
    │   ├── js
    │   │   ├── bootstrap.min.js
    │   │   └── main.js
    │   ├── json
    │   │   ├── E1-Reading.json
    │   │   ├── E2-Listening.json
    │   │   ├── E3-Speaking.json
    │   │   ├── E4-Writing.json
    │   │   ├── QP_template.json
    │   │   ├── Test21
    │   │   │   ├── E3-Speaking.json
    │   │   │   └── QP_template.json
    │   │   ├── Test22
    │   │   │   ├── E3-Speaking.json
    │   │   │   └── QP_template.json
    │   │   └── unique1
    │   │       ├── E3-Speaking.json
    │   │       └── QP_template.json
    │   ├── stylesheets
    │   │   ├── bootstrap.min.css
    │   │   ├── bootstrap-select.css
    │   │   ├── bootstrap-theme.min.css
    │   │   └── quizdata.json
    │   └── video
    │       └── Intro-SpeakingSection.mp4
    └── templates
        ├── admin.html
        ├── _base.html
        ├── base.html
        ├── create.html
        ├── index.html
        ├── login.html
        ├── quiz.html
        ├── register.html
        ├── registration.html
        ├── set_password.html
        └── testresult.html

Docker Machine
To start Docker Machine, first make sure you’re in the project root and then simply run:

$ docker-machine create -d virtualbox dev;
Running pre-create checks...
Creating machine...
Waiting for machine to be running, this may take a few minutes...
Machine is running, waiting for SSH to be available...
Detecting operating system of created instance...
Provisioning created instance...
Copying certs to the local machine directory...
Copying certs to the remote machine...
Setting Docker configuration on the remote daemon...
To see how to connect Docker to this machine, run: docker-machine env dev
The create command setup a “machine” (called dev) for Docker development. In essence, it downloaded boot2docker and started a VM with Docker running. Now just point the Docker client at the dev machine via:

$ eval "$(docker-machine env dev)"
Run the following command to view the currently running Machines:

$ docker-machine ls
NAME      ACTIVE   DRIVER       STATE     URL                         SWARM
dev       *        virtualbox   Running   tcp://192.168.99.100:2376
Next, let’s fire up the containers with Docker Compose and get the Flask app and Postgres database up and running.

Docker Compose
Take a look at the docker-compose.yml file:

web:
  restart: always
  build: ./web
  expose:
    - "8000"
  links:
    - postgres:postgres
  volumes:
    - /usr/src/app/static
  env_file: .env
  command: /usr/local/bin/gunicorn -w 2 -b :8000 app:app

nginx:
  restart: always
  build: ./nginx/
  ports:
    - "80:80"
  volumes:
    - /www/static
  volumes_from:
    - web
  links:
    - web:web

data:
  restart: no
  image: postgres:latest
  volumes:
    - /var/lib/postgresql
  command: true

postgres:
  restart: always
  image: postgres:latest
  volumes_from:
    - data
  ports:
    - "5432:5432"
Here, we’re defining four services – web, nginx, postgres, and data.

First, the web service is built via the instructions in the Dockerfile within the “web” directory – where the Python environment is setup, requirements are installed, and the Flask app is fired up on port 8000. That port is then forwarded to port 80 on the host environment – e.g., the Docker Machine. This service also adds environment variables to the container that are defined in the .env file.
The nginx service is used for reverse proxy to forward requests either to the Flask app or the static files.
Next, the postgres service is built from the the official PostgreSQL image from Docker Hub, which install Postgres and runs the server on the default port 5432.
Finally, notice how there is a separate volume container that’s used to store the database data, data. This helps ensure that the data persists even if the Postgres container is completely destroyed.
Now, to get the containers running, build the images and then start the services:

$ docker-compose build
$ docker-compose up -d
Grab a cup of coffee. Or two. Check out the Real Python courses. This will take a while the first time you run it.

We also need to create the database table:

$ docker-compose run web /usr/local/bin/python create_db.py

Open your browser and navigate to the IP address associated with Docker Machine ($ docker-machine ip dev):

Now you can see the working website

Cheets!!!

Nice!

To see which environment variables are available to the web service, run:

$ docker-compose run web env
To view the logs:

$ docker-compose logs
You can also enter the Postgres Shell – since we forward the port to the host environment in the docker-compose.yml file – to add users/roles as well as databases via:

$ psql -h 192.168.99.100 -p 5432 -U postgres --password
Once done, stop the processes via docker-compose stop.