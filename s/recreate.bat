echo off
call r -m utils.gm --removegit --recreate
call r -m utils.gm -d --recreate
call s\c Initial commit
call s\po
