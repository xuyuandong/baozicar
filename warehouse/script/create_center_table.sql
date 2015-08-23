use cardb;

CREATE TABLE IF NOT EXISTS t_path (
  id          INT(10) NOT NULL AUTO_INCREMENT,
  pc_price       FLOAT(8,3)  NOT NULL,
  bc_price       FLOAT(8,3)  NOT NULL,
  from_city   VARCHAR(32) NOT NULL,
  to_city     VARCHAR(32) NOT NULL,
  from_origin VARCHAR(32) NOT NULL,
  to_origin   VARCHAR(32) NOT NULL,
  from_lat    DOUBLE(11,8) NOT NULL,
  from_lng    DOUBLE(11,8) NOT NULL,
  to_lat      DOUBLE(11,8) NOT NULL,
  to_lng      DOUBLE(11,8) NOT NULL,
  from_discount  FLOAT(8,3)  NOT NULL,
  to_discount    FLOAT(8,3)  NOT NULL,
  from_pc_step   FLOAT(8,3)  NOT NULL,
  to_pc_step     FLOAT(8,3)  NOT NULL,
  from_bc_step   FLOAT(8,3)  NOT NULL,
  to_bc_step     FLOAT(8,3)  NOT NULL,
  from_scale  FLOAT(8,3)  NOT NULL,
  to_scale    FLOAT(8,3)  NOT NULL,
  driver_num  INT(10)     NOT NULL,
  PRIMARY KEY (id)
) ENGINE=InnoDB;

alter table t_path add maxmile INT(4) not null default 0;
alter table t_path add maxnum  INT(2) not null default 3;
alter table t_path add feed    INT(4) not null default 0;
alter table t_path add subsidy INT(4) not null default 0;


CREATE TABLE IF NOT EXISTS t_feedback (
  id          INT(10) NOT NULL AUTO_INCREMENT,
  phone       VARCHAR(16) NOT NULL,
  content     VARCHAR(1024) NOT NULL,
  PRIMARY KEY (id)
) ENGINE=InnoDB;


CREATE TABLE IF NOT EXISTS t_version (
  id          INT(10) NOT NULL AUTO_INCREMENT,
  version     VARCHAR(16) NOT NULL,
  url         VARCHAR(128) NOT NULL,
  app         INT(2) NOT NULL,
  platform    INT(2) NOT NULL,
  PRIMARY KEY (id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS t_sms (
  id        INT(10) NOT NULL AUTO_INCREMENT,
  phone     VARCHAR(16) NOT NULL,
  content   VARCHAR(128) NOT NULL,
  status    VARCHAR(16) NOT NULL, 
  dt        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  INDEX (phone)
) ENGINE=InnoDB;
