use cardb;

CREATE TABLE IF NOT EXISTS t_user (
  id     INT(10) NOT NULL AUTO_INCREMENT,
  phone  VARCHAR(16) NOT NULL,
  dev    VARCHAR(32) NOT NULL,
  name   VARCHAR(16) NOT NULL,
  image  VARCHAR(256) NOT NULL,
  dt     TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  INDEX (phone)
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
  pay_id      INT(10) NOT NULL COMMENT '-1 NOT PAY, refilled',
  price       FLOAT(8,3) NOT NULL,
  fact_price  FLOAT(8,3) NOT NULL,
  coupon_id    VARCHAR(10) NOT NULL,
  coupon_price FLOAT(8,3) NOT NULL,
  from_lat     DOUBLE(10,8) NOT NULL,
  from_lng     DOUBLE(10,8) NOT NULL,
  to_lat       DOUBLE(10,8) NOT NULL,
  to_lng       DOUBLE(10,8) NOT NULL,
  last_modify TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  dt          TIMESTAMP NOT NULL DEFAULT 0,
  PRIMARY KEY (id),
  INDEX (phone)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS t_payment (
  id           INT(10) NOT NULL AUTO_INCREMENT,
  trade_no     VARCHAR(32) NOT NULL,
  order_id     INT(10) NOT NULL,
  price        FLOAT(8,3) NOT NULL,
  status       INT(2)  NOT NULL,
  buyer        VARCHAR(32)  NOT NULL,
  seller       VARCHAR(32)  NOT NULL,
  buyer_id     VARCHAR(32)  NOT NULL,
  seller_id    VARCHAR(32)  NOT NULL,
  gmt_create   VARCHAR(32)  NOT NULL,
  gmt_payment  VARCHAR(32)  NOT NULL,
  extra_info   VARCHAR(255) NOT NULL,
  last_modify TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  dt          TIMESTAMP NOT NULL DEFAULT 0,
  PRIMARY KEY (id, trade_no),
  INDEX (order_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS t_coupon (
  id       INT(10) NOT NULL AUTO_INCREMENT,
  ctype    INT(2) NOT NULL,
  status   INT(2) NOT NULL,
  price    FLOAT(8,3) NOT NULL,
  within   INT(10) NOT NULL,
  deadline VARCHAR(32) NOT NULL,
  note     VARCHAR(255) NOT NULL,
  phone    VARCHAR(16) NOT NULL,
  code     INT(10) NOT NULL,
  last_modify TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  dt          TIMESTAMP NOT NULL DEFAULT 0,
  PRIMARY KEY (id),
  INDEX (phone, code)
) ENGINE=InnoDB;

