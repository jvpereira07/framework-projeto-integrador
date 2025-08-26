BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "BehaviorTree" (
	"id"	INTEGER,
	"name"	TEXT NOT NULL,
	"structure"	TEXT NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "Creature" (
	"id"	INTEGER,
	"maxHp"	INTEGER NOT NULL,
	"regenHp"	INTEGER NOT NULL,
	"maxMana"	INTEGER NOT NULL,
	"regenMana"	INTEGER NOT NULL,
	"maxStamina"	INTEGER NOT NULL,
	"regenStamina"	INTEGER NOT NULL,
	"damage"	INTEGER NOT NULL,
	"critical"	INTEGER NOT NULL,
	"defense"	INTEGER NOT NULL,
	"speed"	INTEGER NOT NULL,
	"name"	TEXT NOT NULL,
	"behaviors"	INTEGER NOT NULL,
	"aceleration"	INTEGER NOT NULL,
	"sizex"	INTEGER NOT NULL,
	"sizey"	INTEGER NOT NULL,
	"idTextura"	INTEGER NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "Projectile" (
	"id"	INTEGER,
	"speed"	REAL,
	"damage"	REAL,
	"penetration"	REAL,
	"sizex"	INTEGER,
	"sizey"	INTEGER,
	"time"	REAL,
	"behavior"	TEXT,
	"idTextura"	INTEGER,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "itens" (
	"id"	INTEGER,
	"item_type"	TEXT,
	"name"	TEXT,
	"texture"	TEXT,
	"description"	TEXT,
	"heal"	REAL,
	"mana"	REAL,
	"stamina"	REAL,
	"effect"	TEXT,
	"defense"	REAL,
	"resistance"	REAL,
	"regen"	REAL,
	"speed"	REAL,
	"attack"	REAL,
	"critical"	REAL,
	"mana_regen"	REAL,
	"classe"	TEXT,
	"condition"	TEXT,
	"special"	TEXT,
	"slot"	TEXT,
	"damage"	REAL,
	"range"	REAL,
	"move"	REAL,
	"ability"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT)
);
INSERT INTO "BehaviorTree" ("id","name","structure") VALUES (1,'Rato','[["structure", "Sequence"], ["block_start", "{"], ["condition", "timer-andar"], ["action", "andar"], ["block_end", "}"]]');
INSERT INTO "BehaviorTree" ("id","name","structure") VALUES (3,'Rato','[["structure", "Sequence"], ["block_start", "{"], ["condition", "sem-condicao"], ["action", "andar"], ["block_end", "}"]]');
INSERT INTO "BehaviorTree" ("id","name","structure") VALUES (4,'Bombastic','[["structure", "Sequence"], ["block_start", "{"], ["condition", "sem-condicao"], ["action", "andar"], ["action", "animBombastic"], ["block_end", "}"]]');
INSERT INTO "Creature" ("id","maxHp","regenHp","maxMana","regenMana","maxStamina","regenStamina","damage","critical","defense","speed","name","behaviors","aceleration","sizex","sizey","idTextura") VALUES (1,1000,5,300,2,200,1,150,10,50,20,'Leonardo',3,1,32,32,4);
INSERT INTO "Creature" ("id","maxHp","regenHp","maxMana","regenMana","maxStamina","regenStamina","damage","critical","defense","speed","name","behaviors","aceleration","sizex","sizey","idTextura") VALUES (2,1500,7,500,3,250,2,200,15,75,25,'Orc',1,1,32,32,2);
INSERT INTO "Creature" ("id","maxHp","regenHp","maxMana","regenMana","maxStamina","regenStamina","damage","critical","defense","speed","name","behaviors","aceleration","sizex","sizey","idTextura") VALUES (3,800,3,200,1,150,1,100,5,30,15,'Elf',1,1,32,32,3);
INSERT INTO "Creature" ("id","maxHp","regenHp","maxMana","regenMana","maxStamina","regenStamina","damage","critical","defense","speed","name","behaviors","aceleration","sizex","sizey","idTextura") VALUES (4,1000,1,100,1,100,1,10,10,1,12,'Bombastic',4,1,96,96,5);
INSERT INTO "Projectile" ("id","speed","damage","penetration","sizex","sizey","time","behavior","idTextura") VALUES (1,1.0,18.0,1.0,32,32,600.0,'teste',1);
INSERT INTO "Projectile" ("id","speed","damage","penetration","sizex","sizey","time","behavior","idTextura") VALUES (2,0.1,18.0,100.0,32,32,60.0,'teste',6);
INSERT INTO "itens" ("id","item_type","name","texture","description","heal","mana","stamina","effect","defense","resistance","regen","speed","attack","critical","mana_regen","classe","condition","special","slot","damage","range","move","ability") VALUES (1,'Consumable','Poção de cura','9','Restaura 100 pontos de vida',100.0,0.0,0.0,'',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'',NULL,NULL,NULL,NULL,NULL);
INSERT INTO "itens" ("id","item_type","name","texture","description","heal","mana","stamina","effect","defense","resistance","regen","speed","attack","critical","mana_regen","classe","condition","special","slot","damage","range","move","ability") VALUES (2,'KeyItem','Pintão','7','Item de teste',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'',NULL,NULL,NULL,NULL,NULL);
INSERT INTO "itens" ("id","item_type","name","texture","description","heal","mana","stamina","effect","defense","resistance","regen","speed","attack","critical","mana_regen","classe","condition","special","slot","damage","range","move","ability") VALUES (3,'Consumable','Poção de mana','10','Restaura 100 pontos de mana.\n \n \n "lacrou mana"',0.0,100.0,0.0,'',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
COMMIT;
