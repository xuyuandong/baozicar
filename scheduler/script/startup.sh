#!/bin/bash

cd $(dirname `ls -ls $0 | awk '{print $NF;}'`)/..
WK_DIR=`pwd`

EXE_NAME=scheduler

function _start() 
{
  cd $WK_DIR/bin
  rm -rf $WK_DIR/bin/nohup.out
  nohup ./$EXE_NAME --flagfile=../conf/$EXE_NAME.conf & echo $! >$WK_DIR/$EXE_NAME.pid &
  echo "$EXE_NAME start on pid of `cat $WK_DIR/$EXE_NAME.pid`"
}

function _stop()
{
  if [ -f $WK_DIR/$EXE_NAME.pid ]; then
    echo "pid file exist!"
    for PID in `cat ${WK_DIR}/${EXE_NAME}.pid`; do
      echo "pid: $PID"
      RUN=`ps -eo pid,cmd | grep $PID | grep $EXE_NAME`
      if [ "$RUN" != "" ]; then
        kill $PID
        echo "$PID has been killed!"
      fi
    done
    rm -rf $WK_DIR/$EXE_NAME.pid
  else
    echo "pid file not exist!"
  fi
}

function _restart() 
{
  _stop
  _start
}

function _show_useage()
{
  echo "useage: $0 {start|stop|restart}"
}

function _deploy()
{
  src=$WK_DIR
  dst="/home/deploy/scheduler"
  mkdir -p $dst
  cp -r $src/bin $dst/
  cp -r $src/script $dst/
  cp -r $src/conf $dst/
  cp -r $src/logs $dst/
}

##
# main

case $1 in 
  deploy|start|stop|restart)
  _${1}
  ;;
  *)
  _show_useage
  ;;
esac

