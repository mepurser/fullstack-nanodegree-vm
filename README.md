How to run Swiss Pairings Tournament Assignment
-----------------------------------------------

1. Open Git Shell.
2. Change to directory where vagrant lives:
	C:\**\**> cd **/*/vagrant
3. Start up vagrant VM:
	C:\**\**\vagrant> vagrant up
4. Start ssh:
	C:\**\**\vagrant> vagrant ssh
5. Navigate to vagrant directory:
	vagrant@vagrant-ubuntu-trusty-32$ cd /vagrant
6. Use [ls] to see directory contents. Navigate to tournament folder:
	vagrant@vagrant-ubuntu-trusty-32/vagrant$ cd tournament
7. Initialize tournament database connection using psql:
	vagrant@vagrant-ubuntu-trusty-32/vagrant/tournament$ psql
8. Run tournament.sql:
	vagrant=> \i tournament.sql
9. Exit psql:
	vagrant=> \q
10. Run tournament_test.py using Python:
	vagrant@vagrant-ubuntu-trusty-32/vagrant/tournament$ python tournament_test.py
11. If the file runs correctly, the following should be printed:
	*******************
	1. Old matches can be deleted.
	2. Player records can be deleted.
	3. After deleting, countPlayers() returns zero.
	4. After registering a player, countPlayers() returns 1.
	5. Players can be registered and deleted.
	6. Newly registered players appear in the standings with no matches.
	7. After a match, players have updated standings.
	8. After one match, players with one win are paired.
	Success!  All tests pass!
	*******************