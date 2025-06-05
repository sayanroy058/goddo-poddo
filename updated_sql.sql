CREATE DATABASE  IF NOT EXISTS `goddo_poddo_db` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `goddo_poddo_db`;
-- MySQL dump 10.13  Distrib 8.0.36, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: goddo_poddo_db
-- ------------------------------------------------------
-- Server version	8.3.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `tbl_poem`
--

DROP TABLE IF EXISTS `tbl_poem`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
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
  `LIKED_BY` text,
  `SHARED_BY` text,
  `COMMENTED_BY` text,
  PRIMARY KEY (`STORY_ID`),
  KEY `tbl_poem_ibfk_1` (`WRITTEN_BY`),
  CONSTRAINT `tbl_poem_ibfk_1` FOREIGN KEY (`WRITTEN_BY`) REFERENCES `tbl_users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tbl_poem`
--

LOCK TABLES `tbl_poem` WRITE;
/*!40000 ALTER TABLE `tbl_poem` DISABLE KEYS */;
INSERT INTO `tbl_poem` VALUES (1,1,'Sunset Melodies','English','Times New Roman','http://example.com/poem.pdf','Golden hues dance in the sky...','published','2025-05-13 15:14:09','2025-05-13 15:14:09',4.99,NULL,NULL,NULL);
/*!40000 ALTER TABLE `tbl_poem` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tbl_story`
--

DROP TABLE IF EXISTS `tbl_story`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
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
  `LIKED_BY` text,
  `SHARED_BY` text,
  `COMMENTED_BY` text,
  PRIMARY KEY (`STORY_ID`),
  KEY `tbl_story_ibfk_1` (`WRITTEN_BY`),
  CONSTRAINT `tbl_story_ibfk_1` FOREIGN KEY (`WRITTEN_BY`) REFERENCES `tbl_users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tbl_story`
--

LOCK TABLES `tbl_story` WRITE;
/*!40000 ALTER TABLE `tbl_story` DISABLE KEYS */;
INSERT INTO `tbl_story` VALUES (1,1,'The Brave Fox','English','Arial','http://example.com/story.pdf','Once upon a time...','published','2025-05-13 15:12:05','2025-05-13 15:12:05',9.99,NULL,NULL,NULL);
/*!40000 ALTER TABLE `tbl_story` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tbl_users`
--

DROP TABLE IF EXISTS `tbl_users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tbl_users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `full_name` varchar(100) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `mobile` varchar(15) DEFAULT NULL,
  `password` varchar(255) DEFAULT NULL,
  `role` varchar(20) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT '1',
  `is_approved` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tbl_users`
--

LOCK TABLES `tbl_users` WRITE;
/*!40000 ALTER TABLE `tbl_users` DISABLE KEYS */;
INSERT INTO `tbl_users` VALUES (1,'John Doe','john@example.com','1234567890','scrypt:32768:8:1$NUI155ELanqxL424$a728ffa9696925814f6705df70038c32cd53410fc000501be839f66cd82ff13d81670c04152ec0224d566f1d92447d5e29cf44e6d8647910d3f5d5a59925837a','Writer',1,0),(2,'Alice Johnson','alice@example.com','1234567890','scrypt:32768:8:1$P2Y9A8rBIqwra7T1$286ce972977112641151c90280942c9d4acccf08988a7d125b5b9bb2206d5f7570d808e62f3ff1863a3c6303c53688ff574945a5423c1d653f281055c51d02b3','writer',1,0);
/*!40000 ALTER TABLE `tbl_users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping events for database 'goddo_poddo_db'
--

--
-- Dumping routines for database 'goddo_poddo_db'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-06-03 23:54:45
