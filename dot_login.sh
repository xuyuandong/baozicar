#!/usr/bin/expect -f
set timeout 2000 
set passwd showmeng1234SVRMiMa!

spawn ssh root@118.192.26.107

expect "root@118.192.26.107's password: "

send "$passwd\n"

#expect eof
interact
