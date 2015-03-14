#!/usr/bin/env bash

###############################################################################
# @author: yuandong
############################################################################### 

# work dir ##########################
cd $(dirname `ls -l $0 |awk '{print $NF;}'`)/..
WK_DIR=`pwd`
source $WK_DIR/conf/default.conf

# source trap #######################
set -o pipefail
set -o errexit
#source $shell_trap
#trap 'traperror $? $LINENO $BASH_LINENO "$BASH_COMMAND" $(printf "::%s" ${FUNCNAME[@]}) "$PROCESS" '  ERR           

# write log #########################
date=`date -d -2day +"%Y%m%d"`
LOG_FILE=$WK_DIR/log/crontab.$date.log
[ "$open_log" == "true" ] && exec &>$LOG_FILE

#############################################
mysql="mysql -uroot -pbjgzz+318 -Dcardb"
mydump="mysqldump -uroot -pbjgzz+318 cardb"

src_table="t_order"
dst_table="t_order_"$date
backup_file=$WK_DIR/data/"$dst_table.sql"

from_day=`date -d -2day +"%Y-%m-%d"`
to_day=`date -d -1day +"%Y-%m-%d"`

# split daily table
echo "create table $dst_table select * from $src_table where dt >= '$from_day 00:00:00' and dt < '$to_day 00:00:00';"
$mysql -e "create table $dst_table select * from $src_table where dt >= '$from_day 00:00:00' and dt < '$to_day 00:00:00';"

# backup table
echo "$mydump $dst_table >$backup_file"
$mydump $dst_table >$backup_file

# delete old data from origin table
echo "delete from $src_table where dt >= '$from_day 00:00:00' and dt < '$to_day 00:00:00';"
$mysql -e "delete from $src_table where dt >= '$from_day 00:00:00' and dt < '$to_day 00:00:00';"

#############################################
echo "[INFO] finished all process."

