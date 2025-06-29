<?php
$connection = mysqli_connect("localhost", "ideav", "ideav", "ideav") or die("Couldn't connect.");
$connection->set_charset("utf8");
mysqli_select_db($connection, "ideav") or die("Couldn't select database.");
define("SALT", "ideav");
