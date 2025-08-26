BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "tile" (
	"id"	INTEGER,
	"name"	TEXT,
	"col"	INTEGER,
	PRIMARY KEY("id")
);
INSERT INTO "tile" ("id","name","col") VALUES (0,'vazio',0);
INSERT INTO "tile" ("id","name","col") VALUES (1,'morro',1);
INSERT INTO "tile" ("id","name","col") VALUES (2,'morro',1);
INSERT INTO "tile" ("id","name","col") VALUES (3,'grama',0);
INSERT INTO "tile" ("id","name","col") VALUES (4,'grama2',0);
INSERT INTO "tile" ("id","name","col") VALUES (5,'aa',1);
INSERT INTO "tile" ("id","name","col") VALUES (7,'morro',1);
INSERT INTO "tile" ("id","name","col") VALUES (8,'grama3',0);
INSERT INTO "tile" ("id","name","col") VALUES (9,'grama4',0);
INSERT INTO "tile" ("id","name","col") VALUES (10,'morro4',1);
INSERT INTO "tile" ("id","name","col") VALUES (11,'grama5',0);
INSERT INTO "tile" ("id","name","col") VALUES (12,'morro',1);
INSERT INTO "tile" ("id","name","col") VALUES (13,'morro5',1);
INSERT INTO "tile" ("id","name","col") VALUES (15,'morro',1);
INSERT INTO "tile" ("id","name","col") VALUES (16,'grama6',0);
INSERT INTO "tile" ("id","name","col") VALUES (17,'morro',1);
INSERT INTO "tile" ("id","name","col") VALUES (20,'morro14',1);
INSERT INTO "tile" ("id","name","col") VALUES (21,'grama7',0);
INSERT INTO "tile" ("id","name","col") VALUES (22,'morro',1);
INSERT INTO "tile" ("id","name","col") VALUES (23,'morro6',1);
INSERT INTO "tile" ("id","name","col") VALUES (24,'morro10',1);
INSERT INTO "tile" ("id","name","col") VALUES (25,'morro14',1);
INSERT INTO "tile" ("id","name","col") VALUES (26,'grama8',0);
INSERT INTO "tile" ("id","name","col") VALUES (27,'aa',1);
INSERT INTO "tile" ("id","name","col") VALUES (28,'aa',1);
INSERT INTO "tile" ("id","name","col") VALUES (29,'morro',1);
INSERT INTO "tile" ("id","name","col") VALUES (30,'morro',1);
INSERT INTO "tile" ("id","name","col") VALUES (32,NULL,NULL);
COMMIT;
