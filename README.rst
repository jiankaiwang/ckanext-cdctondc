
.. image:: https://travis-ci.org/jiankaiwang/ckanext-cdctondc.svg?branch=master
    :target: https://travis-ci.org/jiankaiwang/ckanext-cdctondc

=============
ckanext-cdctondc
=============

The repository implements the API of CDC Open Data Portal connects to NDC Open Data Portal. The all synchronization operations is in one button.

* The synchronization operation is shown on the page of each datasets.

.. image:: images/first_commit.png

* The synchronization button would be shown in red while it failed.

.. image:: images/failure.png

* The synchronization button would be shown in green while it succeeded.

.. image:: images/success.png

------------
Requirements
------------

* Developed on CKAN 2.5.x
* Require external packages
	* psycopg2 : https://pypi.python.org/pypi/psycopg2
	* py2psql : https://github.com/jiankaiwang/seed/blob/master/python/py2psql.py
        * TEXTCODING : https://github.com/jiankaiwang/seed/blob/master/python/TEXTCODING.py

------------
Installation
------------

To install ckanext-cdctondc:

1. Activate your CKAN virtual environment, for example::

     . /usr/lib/ckan/default/bin/activate

2. Clone the ckanext-cdctondc from github, for example::

     cd /usr/lib/ckan/default/src/
     git clone https://github.com/jiankaiwang/ckanext-cdctondc.git

3. Install the ckanext-cdctondc Python package into your virtual environment::

     cd /usr/lib/ckan/default/src/ckanext-cdctondc
     pip install .

4. Add ``cdctondc`` to the ``ckan.plugins`` setting in your CKAN
   config file (by default the config file is located at
   ``/etc/ckan/default/production.ini``).

5. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu::

     sudo service apache2 reload

   If you've deployed CKAN with uwsgi::
     
     uwsgi --ini-paste /etc/ckan/default/production.ini
 
   If you've create a ckan.service::

     sudo systemctl restart ckan.service

---------------
Config Settings
---------------

1. Make sure adding cdctondc to the ckan.plugins. For example::

     ckan.plugins = cdctondc

2. Document any optional config settings here. For example::

     sudo vim /etc/ckan/default/production.ini

     ckan.cdctondc.psqlUrl = postgresql://(dbuser):(dbpass)@(dbhost)/(dbname)
     ckan.cdctondc.apikey = (This is the api key received from NDC.)
     ckan.cdctondc.apiUrl = API URL (for example, http://data.nat.gov.tw/api/v1/rest/dataset)

------------------------
Development Installation
------------------------

To install ckanext-cdctondc for development, activate your CKAN virtualenv and
do::

    git clone https://github.com/jiankaiwang/ckanext-cdctondc.git
    cd ckanext-cdctondc
    python setup.py develop
    pip install -r dev-requirements.txt


----------------------------------------
Releasing a New Version of ckanext-cdctondc
----------------------------------------

1. Update the version number in the ``setup.py`` file.
   See `PEP 440 <http://legacy.python.org/dev/peps/pep-0440/#public-version-identifiers>`_
   for how to choose version numbers.

2. Create a source distribution of the new version::

     python setup.py sdist

3. Upload the source distribution to PyPI::

     python setup.py sdist upload

4. Tag the new release of the project on GitHub with the version number from
   the ``setup.py`` file. For example if the version number in ``setup.py`` is
   0.0.2 then do::

       git tag 0.0.2
       git push --tags
