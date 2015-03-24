use cardb;

CREATE TABLE IF NOT EXISTS t_path (
  id          INT(10) NOT NULL AUTO_INCREMENT,
  price       FLOAT(6,3)  NOT NULL,
  from_city   VARCHAR(32) NOT NULL,
  to_city     VARCHAR(32) NOT NULL,
  from_origin VARCHAR(32) NOT NULL,
  to_origin   VARCHAR(32) NOT NULL,
  from_range  FLOAT(6,3)  NOT NULL,
  to_range    FLOAT(6,3)  NOT NULL,
  from_step   FLOAT(6,3)  NOT NULL,
  to_step     FLOAT(6,3)  NOT NULL,
  PRIMARY KEY (id)
) ENGINE=InnoDB;

