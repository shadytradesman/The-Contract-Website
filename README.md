# The Contract Website

## Overview

The Contract Website is an extensive web application for The Contract RPG. Its primary deployment can be found at https://www.TheContractRPG.com/

The goal of the website is to replace the need for a physical print book and elevate the user experience of playing The 
Contract to one commonly offered by online video games. 

That means the game's rules are not only offered in a guidebook, but also displayed contextually and even obscured entirely (for 
example, when calculating rewards and advancement costs), allowing Players to play the game without learning all 
the rules. This offering is common in video games but rare in tabletop games.

Beyond the experiences of learning and playing the game, The Contract Website also eases meta-game organization 
troubles that emerge when playing with large, loosely-organized groups of Players.

Feature overview:

* Rule management
  * Interactive character sheets ease / erase the need to know most of the game's rules to create or play a character.
  * The Custom Gift System allows Players to create and advance equipment and powers for any character concept, automatically generating system text and assigning a power level to anything created.
  * An online guidebook is easily searchable for every page on the site.
* Recordkeeping
  * Registered users can save and share the Contractors, Gifts, and Scenarios they create.
  * All Contractors, Gifts, and Scenarios maintain full edit histories for auditing.
  * Sessions are logged into the site along with their participants, allowing the website to provide a full activity history for each Player and Character, GM, and Scenario.
  * To empower homebrew rules, Players are free to "break the rules" of the game when managing their materials, but the website will flag those differences to other Players and GMs.
* Community
  * Groups of Players can organize into Playgroups. 
  * GMs and Playgroup leaders can advertise their Playgroups and upcoming sessions on "looking-for-game" pages.
  * Each Playgroup gets its own news feed of in-game events and out-of-game activity to keep all the Players informed.
  * Playgroup leaders can manage the membership and permissions of their Playgroups with flexible role-based access controls (RBAC)
  * Direct-messaging and profile customization
  * Hall of fame, graveyard, and community content discovery pages

## Developer's Guide
The Contract Website is built in **Django 3.2.9** using **Python 3.6**. 

In production it uses a **Postgres 12 AWS RDS DB**. When run locally, it uses either a postgres database hydrated from the main site, or a sqlite database that is checked into the repo (default).

The Contract has a front end build system that uses node and webpack to render .less files, javascript, and other static assets.
However, many of the static assets don't utilize this build system.

Media files are served via AWS S3. Memcached is used by the primary webservers as a distributed in-memory cache. 
Asynchronous processing is available utilizing Celery Beat with Redis acting as a message broker. 

Automated bulk emails are sent via Amazon SES. 

### Contributing
If you are an active Player of The Contract and would like to contribute to the website, please reach out to Shady Tradesman 
on Discord, Github, or https://www.thecontractRPG.com for help and guidance on what needs work.

### Getting Started

#### Setting up Environment

*Use Python 3.6*

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

