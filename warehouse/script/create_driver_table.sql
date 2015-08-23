use cardb;

CREATE TABLE IF NOT EXISTS t_driver (
  id      INT(10) NOT NULL AUTO_INCREMENT,
  phone   VARCHAR(16) NOT NULL,
  dev     VARCHAR(32) NOT NULL,
  name    VARCHAR(16) NOT NULL,
  image   VARCHAR(256) NOT NULL,
  license VARCHAR(16) NOT NULL,
  carno   VARCHAR(16) NOT NULL, 
  status  INT(2) NOT NULL,
  from_city VARCHAR(32) NOT NULL,
  to_city   VARCHAR(32) NOT NULL,
  priority  INT(10) NOT NULL,
  dt      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  INDEX (phone)
) ENGINE=InnoDB;

alter table t_driver add os varchar(32) not null default '-';
alter table t_driver add version varchar(32) not null default '-';


CREATE TABLE IF NOT EXISTS t_poolorder (
  id          BIGINT(20) UNSIGNED NOT NULL,
  po_id       VARCHAR(36) NOT NULL,
  po_type     INT(2) NOT NULL,
  status      INT(2) NOT NULL,
  price       FLOAT(8,3) NOT NULL,
  phone       VARCHAR(16) NOT NULL,
  from_city   VARCHAR(32) NOT NULL,
  to_city     VARCHAR(32) NOT NULL,
  orders      VARCHAR(256) NOT NULL,
  subsidy     FLOAT(8,3) NOT NULL,
  sstype      INT(2) NOT NULL,
  start_time  VARCHAR(32) NOT NULL,
  last_modify TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  dt          TIMESTAMP NOT NULL DEFAULT 0,
  PRIMARY KEY (id)
) ENGINE=InnoDB;

alter table t_poolorder add original_price FLOAT(8,3) not null default 0;
alter table t_poolorder add multiply FLOAT(8,3) not null default 1.0;

CREATE TABLE IF NOT EXISTS t_driver_data (
  phone       VARCHAR(16) NOT NULL,
  income      FLOAT(8,3) NOT NULL DEFAULT 0,
  ponum       INT(10) NOT NULL DEFAULT 0,
  mileage     INT(10) NOT NULL DEFAULT 0,
  last_modify TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  dt          TIMESTAMP NOT NULL DEFAULT 0,
  PRIMARY KEY (phone)
) ENGINE=InnoDB;


