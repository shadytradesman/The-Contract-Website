# The Contract Website

## Overview

The Contract Website is a web app that enables users to build and manage powers in conjunction with the game The Contract. 

The website is built in Django 3.2.9 using Python 3.6 It is deployed via Elastic Beanstalk on AWS and uses a Postgres 12 RDS DB.
When run locally, it uses either a postgres database hydrated from the main site, or a sqlite database that is check in 
to the repo (default).

The Contract has a front end build system that uses node and webpack to render .less files, javascript, and other static assets.
However, most of the static assets don't utilize this build system.

## Getting Started

#### Setting up Environment

1. First of all, clone the repo. The team suggests either Mac or Linux for development, or Windows Subsystem Linux.
2. Then you will want to start a virtual environment: ```python3 -m venv my-environment``` You should be sure to start 
your environment in the root directory of the repository. This should start your environment which should be listed 
ahead of your terminal prompt. EG `(my-environment) Shadys-MBP:hgapp shady$`
3. If your environment is not active, or if you restart your shell and lose your virtual environment session, you can 
restart it by sourcing the "activate" file. `find . -name "activate"` and `source <path to activate file>`
4. Next up, install the required python libraries by issuing the following command: ` pip install -r requirements.txt `
5. Next, install npm through whatever package manager is on your system. This is for MacOS: `brew install node`
6. Navigate to the directory containing `packages.json` (it's in `hgapp/`) and install all the node required files. 
`npm install`
7. Finally, build the static assets of the site: `npm run build` (You will need to run this manually any time you edit a 
static source file in the static/src/ directory.)
8. Collect the static files for serving locally `python manage.py collectstatic`. Go ahead and confirm that you 
would like to overwrite any existing files.

#### Running the Server

1. Next, in your terminal, run `python manage.py runserver`.
1. If you are running from Pycharm, simply create a run configuration that contains that command.

#### Running tests

1. Use `python manage.py test` while your virtual environment is active

#### Using the included sqlite DB

1. For convenience, there is a checked-in sqlite DB that comes prepopulated with test data. 
1. You may need to run migrations for it to work. `python manage.py migrate`
1. The admin's credentials are `admin:nobnobnob`. There are also a bunch of test users (user1, user2, user3, etc) with 
the password `nobnobnob` 

## Contributing

Please do! We have open github issues, but we recommend reaching out to Shady Tradesman before contributing so he can help
you find appropriate bug / feature / cleanup work.
