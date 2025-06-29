# Local installation

Everything related to authentication is cut out here, and the user works with his “database”.
 
The archive should be copied to the root folder of the Apache or Lightspeed server. In XAMPP this is htdocs.
 
Run these two scripts in your MySQL database (change the credentials to yours):
1_database.sql - will create a MySQL database and a user with full rights
2_table.sql - will create the “database”

In case you need more databases, rename the table name and user name in the 2_table.sql script (they must match) and run it again.
