#!/usr/bin/env python
# 
# tournament.py -- implementation of a Swiss-system tournament
#

import psycopg2


def connect():
    """Connect to the PostgreSQL database.  Returns a database connection."""
    return psycopg2.connect("dbname=tournament")

def runSQL(qry, commit, giveTbl):
    conn = connect()
    c = conn.cursor()
    c.execute(qry + ';')
    if commit: conn.commit()
    if giveTbl: results = c.fetchall()
    if giveTbl: print(results[0])
    conn.close()    
    if giveTbl: return results

def deleteMatches():
    """Remove all the match records from the database."""

    qry = 'DELETE FROM matches;'

    runSQL(qry, True, False)

def deletePlayers():
    """Remove all the player records from the database."""

    qry = 'DELETE FROM players;'

    runSQL(qry, True, False)

def countPlayers():
    """Returns the number of players currently registered."""


    qry = 'SELECT * FROM players;' 

    conn = connect()
    c = conn.cursor()
    c.execute(qry)
    count = c.rowcount
    conn.close()

    return count

def registerPlayer(name):
    """Adds a player to the tournament database.
  
    The database assigns a unique serial id number for the player.  (This
    should be handled by your SQL database schema, not in your Python code.)
  
    Args:
      name: the player's full name (need not be unique).
    """
    name = "'" + name.replace("'", "''") + "'"
    qry = "INSERT INTO players (playername) VALUES (" + name + ")" 

    runSQL(qry, True, False)

def playerStandings():
    """Returns a list of the players and their win records, sorted by wins.

    The first entry in the list should be the player in first place, or a player
    tied for first place if there is currently a tie.

    Returns:
      A list of tuples, each of which contains (id, name, wins, matches):
        id: the player's unique id (assigned by the database)
        name: the player's full name (as registered)
        wins: the number of matches the player has won
        matches: the number of matches the player has played
    """
    conn = connect()
    c = conn.cursor()

    # counts number of matches 
    qryWins = 'SELECT playerid, playername, count(winnerid) AS wins FROM players FULL JOIN matches ON (winnerid = playerid) GROUP BY playerid, playername'
    vwWins = 'CREATE TEMP VIEW vwWins AS ' + qryWins
    c.execute(vwWins + ';')
    
    # counts number of losses
    qryLosses = 'SELECT playerid, playername, count(loserid) AS losses FROM players FULL JOIN matches ON (loserid = playerid) GROUP BY playerid, playername'
    vwLosses = 'CREATE TEMP VIEW vwLosses AS ' + qryLosses
    c.execute(vwLosses + ';')

    # collect wins and losses and calcs matches
    qryMatches = 'SELECT vwWins.playerid, vwWins.playername, wins, losses, (wins+losses) AS matches FROM vwWins FULL JOIN vwLosses ON (vwWins.playerid = vwLosses.playerid) GROUP BY vwWins.playerid, vwWins.playername, wins, losses'
    vwMatches = 'CREATE TEMP VIEW vwMatches AS ' + qryMatches
    c.execute(vwMatches + ';')

    # maps vwMatches back to full table of registered players in order to display players
    # even if they haven't played a match
    qryStandings = 'SELECT vwMatches.playerid, vwMatches.playername, wins, matches FROM vwMatches FULL JOIN players ON (vwMatches.playerid=players.playerid) GROUP BY vwMatches.playerid, vwMatches.playername, matches, wins ORDER BY wins DESC'
    c.execute(qryStandings + ';')
    conn.commit()

    standings = c.fetchall()
    conn.close() 

    return standings

def reportMatch(winner, loser):
    """Records the outcome of a single match between two players.

    Args:
      winner:  the id number of the player who won
      loser:  the id number of the player who lost
    """
    conn = connect()
    c = conn.cursor()

    # lookup the name of the winner from the players table
    qryPlayerDetail = 'SELECT playername FROM players WHERE (playerid=' + str(winner) + ')'
    c.execute(qryPlayerDetail + ';')
    row = c.fetchall()
    winnername = "'" + row[0][0].replace("'", "''") + "'"

    # lookup the name of the loser from the players table
    qryPlayerDetail = 'SELECT playername FROM players WHERE (playerid=' + str(loser) + ')'
    c.execute(qryPlayerDetail + ';')
    row = c.fetchall()
    losername = "'" + row[0][0].replace("'", "''") + "'"

    # create a string of the winner name, loser, winner id, and loser id for entry into matches table
    matchString = winnername + ', ' + losername + ', ' + str(winner) + ', ' + str(loser)

    # insert line into matches table
    qryMatchEntry = 'INSERT INTO matches (winner, loser, winnerid, loserid) VALUES (' + matchString + ');'
    c.execute(qryMatchEntry)
    conn.commit()
    conn.close()
 
def swissPairings():
    """Returns a list of pairs of players for the next round of a match.
  
    Assuming that there are an even number of players registered, each player
    appears exactly once in the pairings.  Each player is paired with another
    player with an equal or nearly-equal win record, that is, a player adjacent
    to him or her in the standings.
  
    Returns:
      A list of tuples, each of which contains (id1, name1, id2, name2)
        id1: the first player's unique id
        name1: the first player's name
        id2: the second player's unique id
        name2: the second player's name
    """

    pairings = []
    playernum = countPlayers()
    standings = playerStandings()
    
    # since the standing table is sorted by win-rank, we loop through all players in order by 2
    for row in range(0, playernum, 2):
        playerid1 = standings[row][0]
        player1 = standings[row][1]
        playerid2 = standings[row+1][0]
        player2 = standings[row+1][1]
        
        newpair = (playerid1, player1, playerid2, player2)
        pairings.append(newpair) 

    return pairings