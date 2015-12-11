#!/bin/bash

DATE=`date`
echo "Date is $DATE"

UP=`date ; uptime`
echo "Uptime is $UP"

sqlite3 wordlist.db  "CREATE TABLE wordlist(k BLOB PRIMARY KEY, v BLOB);"
echo "Inserting ..."

while IFS='' read -r line || [[ -n "$line" ]]; do
	word="$(echo "$line" | tr -cd '[[:alnum:]]')"
	word_lower=`echo "$word" | sed 's/./\L&/g'`
	sqlite3 wordlist.db  "insert into wordlist (k,v) values ('$word_lower','not assigned');"
done < "$1"

echo "Insertion finished!"

sqlite3 wordlist.db  "SELECT v FROM wordlist WHERE k = '10th';";
sqlite3 wordlist.db  "SELECT v FROM wordlist WHERE k = 'zygote';";