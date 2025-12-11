CREATE DATABASE `ideav` /*!40100 DEFAULT CHARACTER SET utf8 */;
USE `ideav`;

CREATE USER 'ideav'@'localhost' IDENTIFIED BY 'ideav';
GRANT ALL PRIVILEGES ON `ideav`.* TO 'ideav'@'localhost';
