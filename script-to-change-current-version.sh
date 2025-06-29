#!/usr/bin/env bash
Version_Tag=$(echo "$1" | cut -d '-' -f 1)
Host_Name=$(echo "$1" | cut -d '-' -f 3)

rm -rf /opt/telegram-notifier-web-server/html/$Host_Name/current/*
cp -r /opt/telegram-notifier-web-server/html/$Host_Name/$Version_Tag/* /opt/telegram-notifier-web-server/html/$Host_Name/current/
cd /opt/telegram-notifier-web-server/html/$Host_Name/$Version_Tag/
zip -r /opt/telegram-notifier-web-server/html/$Host_Name/$Version_Tag/$1-document.zip ./