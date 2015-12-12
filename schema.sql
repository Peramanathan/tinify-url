drop table if exists wordlist;
create table wordlist (
  k text primary key,
  v text,
  up integer 
);