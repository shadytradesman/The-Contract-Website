# The Contract Website

## Overview

The Contract Website is a web app that enables users to build and manage powers in conjunction with the game The Contract. System administrators can edit the database through an administrator's panel which will give end users access to web forms that they can use to create custom powers for their role-playing characters. 

The website is built in Django 2.2.12 using Python 3.6 It is deployed via Elastic Beanstalk on AWS. When run locally, it uses a sqlite database. 

The front end is very simple. Bootstrap, no react... yet 🙃

## Getting Started

#### Setting up Environment
First of all, clone the repositorty. The team suggests either Mac or Linux for development, or Windows Subsystem Linux.

Then you will want to start a virtual environment: ```python3 -m venv my-environment```

You should be sure to start your environment in the root directory of the repository. This should start your environment which should be listed ahead of your shell path.

If you do not see that, or if you restart your shell and lose your virtual environment session, you can restart it by sourcing the "activate" file. 

```find . -name "activate"```

```source <path to activate file>```


Next up, install the required libraries by issuing the following command:

``` pip install -r requirements.txt ```

Next, install npm through whatever package manager is on your system. This is for MacOS:

``brew install node``

Navigate to hgapp/ (same directory as packages.json) and install all the node required files.

``npm install``

Finally, build the static content of the site:

``npm run build``

#### Running the Server

Next, in your terminal, run ```python manage.py runserver```. 

If you are running from Pycharm, simply create a run configuration that contains that command.

#### Contributing Code

If you have permissions to the repo, switch to a new branch

```git checkout -b <branchname>```

Use the following naming convention for your branch names:
[bugfix|improvement|feature|documentation]/[name]

Examples:
	
 * bugfix/paragraph-display
 * improvement/new-index-visuals
 * documentation/readme-update

Next, add the files you've changed.

```git add -u```

Then go ahead and commit

```git commit```

Type a detailed message. Make sure to leave the second line empty and limit your first line to ~60 characters. 

Next push up to the remote branch.

```git push --set-upstream origin <branch name>```

Finally, go to the repository home page on Github and open a pull request. Add shadytradesman as a reviewer.
