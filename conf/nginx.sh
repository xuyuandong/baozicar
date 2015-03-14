#!/bin/bash

pid="/home/deploy/run/nginx.pid"
nginx="/usr/local/nginx/sbin/nginx"

function start() {
  $nginx -t
  $nginx -s reload 
}

