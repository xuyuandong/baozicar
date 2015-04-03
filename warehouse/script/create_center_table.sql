use cardb;

CREATE TABLE IF NOT EXISTS t_path (
  id          INT(10) NOT NULL AUTO_INCREMENT,
  price       FLOAT(8,3)  NOT NULL,
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
  from_step   FLOAT(8,3)  NOT NULL,
  to_step     FLOAT(8,3)  NOT NULL,
  from_scale  FLOAT(8,3)  NOT NULL,
  to_scale    FLOAT(8,3)  NOT NULL,
  driver_num  INT(10)     NOT NULL,
  PRIMARY KEY (id)
) ENGINE=InnoDB;

