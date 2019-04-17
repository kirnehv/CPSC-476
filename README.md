# Project 2
A set of microservices for a blog platform with individual databases.

Microservices: Users, Articles, Tags, Comments

## Dependencies
* [Python](https://www.python.org/downloads/)
* [pip](https://pypi.org/project/pip/#files)
   - `pip install flask`
   - `pip install flask_basicauth`
   - `pip install flask_cli`
* [RubyGems](https://rubygems.org/pages/download) - Package manager for Ruby 
* [cURL](https://curl.haxx.se/download.html) - tranfer data with URLs
* [Nginx](http://nginx.org/en/download.html) - Web Server/Reverse Proxy

## Run
* Nginx Configuration
   - Place `nginx-enabled` in `/etc/nginx/sites-enabled/`
   - Start Nginx `sudo service nginx restart`
* Point terminal path to directory of downloaded files
* Install foreman `gem install foreman`
* Run `foreman start` to execute the Procfile
* Example cURL commands in the [Documentation](https://github.com/kirnehv/CPSC-476/blob/master/API%20documentation.pdf)

## Authors
* Arianne Arcebal - hharin@csu.fullerton.edu
* Henrik Vahanian - henrikv@csu.fullerton.edu
* Kiren Syed - kirensyed@csu.fullerton.edu

## Resources
* [CPSC476](https://docs.google.com/document/d/1A4VBDnFb12M3QB-M6Kmv4MrU9PMjoCbJr0l5s0zuDTU/edit)
* [Responses](https://www.programcreek.com/python/example/51515/flask.Response)
* [Hashing](https://pythonprogramming.net/password-hashing-flask-tutorial/)
* [Date and Time](https://tecadmin.net/get-current-date-time-python/)
