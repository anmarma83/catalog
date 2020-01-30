# Linux Server Configuration
## Catalog Application
A basic steps for installation of Ubuntu Linux on a virtual machine to host a Flask web application. This includes the installation of updates, securing the system from a number of attack vectors and installing/configuring web and database servers.
##Information of accessing
```
### ip address: 3.123.20.102
### ssh prot : 2200
## URL : http://ec2-3-123-20-102.eu-central-1.compute.amazonaws.com
```
# Step by Step Walkthrough
## 1. Launch your Virtual Machine and log in
I accessed the lightsail instance using SSH with the following command:

` ssh -i LightsailDefaultKey-eu-central-1.pem ubuntu@3.123.20.102 `
## 2. Create a new user named grader and grant this user sudo permissions
Created a new user named grader using the following command:

` sudo adduser grader `
#### Followed the instructions in command line and added a secure password. After that I granted sudo permissions to grader user.

## 3. Update all currently installed packages
Updated all currently installed applications:

` sudo apt-get update `

#### and upgraded it with the following command:
` sudo apt-get upgrade `

#### setup Python environment:

` sudo apt-get install python-psycopg2 `
` sudo apt-get install python-flask python-sqlalchemy `
` sudo apt-get install python-pip `
## 4. Configure the local timezone to UTC
#### Changed instance instance time zone to UTC:

` sudo dpkg-reconfigure tzdata `
#### set time sync with NTP:

` sudo apt-get install ntp `
#### Then added additional servers to /etc/ntp.conf file:

`` server ntp.ubuntu.com ``
`` server pool.ntp.org ``
#### And reloaded the NTP service:

` sudo service ntp reload `
## 5. Server needs
#### Apache HTTP Server
#### Installed Apache HTTP Server:

` sudo apt-get install apache2 `
#### mod_wsgi
#### Then I installed mod_wsgi:

` sudo apt-get install libapache2-mod-wsgi `
#### And configured a new Virtual Host by sudo vim /etc/apache2/sites-available/catalog-app.conf with the following content:
```
<VirtualHost *:80>
        ServerName 3.123.20.102
        #ServerAdmin admin@mywebsite.com
        WSGIScriptAlias / /var/www/catalogApp/mycatalog.wsgi
        <Directory /var/www/catalogApp/catalog/>
            Order allow,deny
            Allow from all
        </Directory>
        Alias /static /var/www/catalogApp/catalog/static
        <Directory /var/www/catalogApp/catalog/static/>
            Order allow,deny
            Allow from all
        </Directory>
        ErrorLog ${APACHE_LOG_DIR}/error.log
        LogLevel warn
        CustomLog ${APACHE_LOG_DIR}/access.log combined
</VirtualHost> 
```
#### And enabled the new Virtual Host:

` sudo a2ensite catalog-app `

#### After that I created the .wsgi file by sudo vim /var/www/catalog-app/mycatalog.wsgi with the following content:
```
#!/usr/bin/python
import sys
import logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0, "/var/www/catalogApp/")
from catalog import app as application
application.secret_key = 'Add your secret key' 
```

#### And restarted Apache:

` sudo service apache restart `
### PostgreSQL
#### Installed PostgreSQL:

` sudo apt-get install postgresql postgresql-contrib `
#### To setup, I connected to the postgres user:

` sudo -i -u postgres `
#### Created a new role:

` createuser --interactive `
#### Created database for new user catalog:

` createdb catalog `
#### And set a password for the catalog role:
`
psql
\password catalog
`
#### And followed the commnand line instructions

## Git
#### To install Git:

` sudo apt-get install git-all `
##### Then to setup Catalog project I cloned the Catalog app repository inside the /var/www/ and followed the README instructions. I made additional changes for the project to work with PostgreSQL. I changed /instance/database_setup.py file from

`` SQLALCHEMY_DATABASE_URI = "sqlite:///../catalog/catalog.db" ``
####to

`` SQLALCHEMY_DATABASE_URI = "postgresql://catalog:password@localhost/catalog"  ``
#### And also changed /catalog/project.py file from


# And now this is important step about Securing server
### 1. Adding Key Based login to new user grader
>Changed from root user to new grader user:

>su - grader
>Then added directory .ssh with

>mkdir .ssh
>Added file .ssh/authorized_keys and copied ssh public key contents of udacity_key to authorized_keys, and finally restricted permissions to .ssh and authorized_keys:

>chmod 700 .ssh
>chmod 644 .ssh/authorized_keys
### 2. Forcing Key Based Authentication
>To force key based authentication I edited /etc/ssh/sshd_config file from

>PasswordAuthentication yes
>to

>PasswordAuthentication no
>Then, restarted ssh service:

>sudo service ssh restart
### 3. SSH is hosted on non-default port
>To host SSH on non-default port 22, I edited /etc/ssh/sshd_config file from

>Port 22
>to

>Port 2200
>And finally restarted ssh service:

>sudo service ssh restart
### 4. Configure the Uncomplicated Firewall (UFW)
'''To setup UFW, first I check firewall status with:'''

` sudo ufw status `
#### Then, to deny incoming traffic:

` sudo ufw default deny incoming `
#### And allow outgoing traffic:

` sudo ufw default allow outgoing `
#### And finally start establishing rules. For SSH (port 2200):

` sudo ufw allow 2200/tcp `
#### For HTTP (port 80):

` sudo ufw allow www `
#### And for NTP (port 123):

` sudo ufw allow ntp `
#### And finally to enable UFW:

` sudo ufw enable `
# User management
### 1. Grant sudo permission and prompt for user password at least once
#### To accomplish this task I added a text file named grader to /etc/sudoers.d/ directory with the following content:

`` grader ALL=(ALL) ALL ``
#### This way the user is asked for password at least once per session. The remote user grader is given sudo privileges.

### 2. Disable remote login of the root user
#### To disable root user login, I edited /etc/ssh/sshd_config file, and changed line:

## PermitRootLogin without-password
#### to

## PermitRootLogin no
### Then we need to restart SSH with service ssh restart.
