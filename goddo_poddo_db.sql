CREATE DATABASE IF NOT EXISTS `goddo_poddo_db` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `goddo_poddo_db`;

DROP TABLE IF EXISTS `tbl_poem`;
CREATE TABLE `tbl_poem` (
  `STORY_ID` int NOT NULL AUTO_INCREMENT,
  `WRITTEN_BY` int DEFAULT NULL,
  `NAME` varchar(255) DEFAULT NULL,
  `LANGUAGE` varchar(50) DEFAULT NULL,
  `FONT` varchar(50) DEFAULT NULL,
  `PDF_URL` varchar(255) DEFAULT NULL,
  `STORY` text,
  `STATUS` varchar(20) DEFAULT NULL,
  `CREATED_ON` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `UPDATED_ON` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `PRICE` decimal(10,2) DEFAULT NULL,
  PRIMARY KEY (`STORY_ID`),
  KEY `tbl_poem_ibfk_1` (`WRITTEN_BY`),
  CONSTRAINT `tbl_poem_ibfk_1` FOREIGN KEY (`WRITTEN_BY`) REFERENCES `tbl_users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

LOCK TABLES `tbl_poem` WRITE;
INSERT INTO `tbl_poem` VALUES (1,1,'Sunset Melodies','English','Times New Roman','http://example.com/poem.pdf','Golden hues dance in the sky...','published','2025-05-13 15:14:09','2025-05-13 15:14:09',4.99,NULL,NULL,NULL);
UNLOCK TABLES;

DROP TABLE IF EXISTS `tbl_story`;
CREATE TABLE `tbl_story` (
  `STORY_ID` int NOT NULL AUTO_INCREMENT,
  `WRITTEN_BY` int DEFAULT NULL,
  `NAME` varchar(255) DEFAULT NULL,
  `LANGUAGE` varchar(50) DEFAULT NULL,
  `FONT` varchar(50) DEFAULT NULL,
  `PDF_URL` varchar(255) DEFAULT NULL,
  `STORY` text,
  `STATUS` varchar(20) DEFAULT NULL,
  `CREATED_ON` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `UPDATED_ON` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `PRICE` decimal(10,2) DEFAULT NULL,
  PRIMARY KEY (`STORY_ID`),
  KEY `tbl_story_ibfk_1` (`WRITTEN_BY`),
  CONSTRAINT `tbl_story_ibfk_1` FOREIGN KEY (`WRITTEN_BY`) REFERENCES `tbl_users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

LOCK TABLES `tbl_story` WRITE;
INSERT INTO `tbl_story` VALUES (1,1,'The Brave Fox','English','Arial','http://example.com/story.pdf','Once upon a time...','published','2025-05-13 15:12:05','2025-05-13 15:12:05',9.99);
UNLOCK TABLES;

DROP TABLE IF EXISTS `tbl_users`;
CREATE TABLE `tbl_users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `full_name` varchar(100) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `mobile` varchar(15) DEFAULT NULL,
  `password` varchar(255) DEFAULT NULL,
  `role` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

LOCK TABLES `tbl_users` WRITE;
INSERT INTO `tbl_users` VALUES (1,'John Doe','john@example.com','1234567890','scrypt:32768:8:1$NUI155ELanqxL424$a728ffa9696925814f6705df70038c32cd53410fc000501be839f66cd82ff13d81670c04152ec0224d566f1d92447d5e29cf44e6d8647910d3f5d5a59925837a','Writer');
UNLOCK TABLES;
