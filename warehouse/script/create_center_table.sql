use cardb;

CREATE TABLE IF NOT EXISTS t_path (
  id     INT(10) NOT NULL AUTO_INCREMENT,
  from_city  VARCHAR(32) NOT NULL,
  to_city    VARCHAR(32) NOT NULL,
  price      INT(10) NOT NULL,
  from_step  INT(10) NOT NULL,
  to_step    INT(10) NOT NULL,
  PRIMARY KEY (id)
) ENGINE=InnoDB;

