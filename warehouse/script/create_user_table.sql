drop database if exists cardb;
create database cardb;
use cardb;

CREATE TABLE IF NOT EXISTS t_user (
  id     INT(10) NOT NULL AUTO_INCREMENT,
  phone  VARCHAR(16) NOT NULL,
  dev    VARCHAR(32) NOT NULL,
  name   VARCHAR(16) NOT NULL,
  image  VARCHAR(256) NOT NULL,
  dt     TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id)
) ENGINE=InnoDB;


CREATE TABLE IF NOT EXISTS t_order (
  id          INT(10) NOT NULL AUTO_INCREMENT,
  order_type  INT(2) NOT NULL,
  status      INT(2) NOT NULL,
  phone       VARCHAR(16) NOT NULL,
  name        VARCHAR(16) NOT NULL,
  start_time  VARCHAR(32) NOT NULL,
  from_city   VARCHAR(32) NOT NULL,
  from_place  VARCHAR(255) NOT NULL,
  to_city     VARCHAR(32) NOT NULL,
  to_place    VARCHAR(255) NOT NULL,
  num         INT(2) NOT NULL,
  msg         VARCHAR(255) NOT NULL,
  pay_id      VARCHAR(36) NOT NULL COMMENT '1.real pay_id, or 2.empty or refilled pay_id',
  price       INT(10) NOT NULL,
  fact_price  INT(10) NOT NULL,
  coupon_id    VARCHAR(10) NOT NULL,
  coupon_price INT(10) NOT NULL,
  last_modify TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  dt          TIMESTAMP NOT NULL DEFAULT 0,
  PRIMARY KEY (id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS t_payment (
  id           INT(10) NOT NULL AUTO_INCREMENT,
  pay_id       VARCHAR(36) NOT NULL,
  order_id     VARCHAR(36) NOT NULL COMMENT '1.temporary order_id, or 2.real order_id',
  trade_no     VARCHAR(36) NOT NULL COMMENT 'theoretically same with pay_id',
  price        INT(10) NOT NULL,
  status       INT(2)  NOT NULL,
  buyer        VARCHAR(32)  NOT NULL,
  seller       VARCHAR(32)  NOT NULL,
  extra_info   VARCHAR(255) NOT NULL,
  last_modify TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  dt          TIMESTAMP NOT NULL DEFAULT 0,
  PRIMARY KEY (id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS t_coupon (
  id       INT(10) NOT NULL AUTO_INCREMENT,
  ctype    INT(2) NOT NULL,
  status   INT(2) NOT NULL,
  price    INT(10) NOT NULL,
  within   INT(10) NOT NULL,
  deadline VARCHAR(32) NOT NULL,
  phone    VARCHAR(16) NOT NULL,
  code     INT(10) NOT NULL,
  last_modify TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  dt          TIMESTAMP NOT NULL DEFAULT 0,
  PRIMARY KEY (id)
) ENGINE=InnoDB;

