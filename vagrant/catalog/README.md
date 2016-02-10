PV Equipment App
----------------

1) Execute application.py on virtual machine using Python

2) Navigate to http://localhost:8000 using browser

3) When run for the first time, a default database will be created with initial
values according to the file database_initdata.py. Only the user with access
to server-side files can manipulate these values (either directly in the database
or by deleting the database and modifying database_initdata.py)

4) When the user is not logged-in, she can browse PV equipment categories and view
the description of various brands on the home page.

5) By clicking on 'log-in' on the home page, the user can log-in using google
credentials.

6) Once logged in, the user will be able to add categories and brands. She will
also be able to edit and delete items that she has added. Only items that
she is authorized to edit will be displayed as modifiable to the user. Protections
are in place to prevent a user from modifying via altering the url directly.

7) A comprehensive summary of data in the database (jsonified) can be viewed by
visiting:

localhost:8000/catalog.json