#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import argparse
import getpass
import sys, commands
import MySQLdb as mdb

class Options_parser():

	"""
	Class for command line options
	"""

        def __init__(self):
	        self.parser = argparse.ArgumentParser(description='Script to manage user db')
		# DB Credentials #################################################
        	self.parser.add_argument('-A', '--admindb',
                	        help='db admin',
                        	required='True')
	        self.parser.add_argument('-P', '--passdb',
        	                help='db password',
                	        required='True')
	        self.parser.add_argument('-D', '--database',
        	                help='db name')
	        self.parser.add_argument('-H', '--hostname',
        	                help='db host')
		##################################################################
	        self.parser.add_argument('-u', '--username',
        	                help='username : prenom.nom')
	        self.parser.add_argument('-c', '--creategroup',
        	                help='groupname')
	        self.parser.add_argument('-g1', '--group1',
        	                help='first group id')
	        self.parser.add_argument('-g2', '--group2',
        	                help='second group id')
	        #option sans recuperation d'argument
        	self.parser.add_argument('-p', '--password', action='store_true',
                	        help='password')
	        self.parser.add_argument('-d', '--disable', action='store_true',
        	                help='disable account')
                self.parser.parse_args(namespace=self)

class DB():

	"""
	This class contains the database connection credentials and all sql requests
	"""

	#DB connection test
    	def __init__(self, admindb, passdb, hostname, dbname ):
		
        	if not dbname:
                	dbname = 'auth'
        	if not hostname:
                	hostname = 'localhost'
		try:
        		self.db = mdb.connect(hostname, admindb, passdb, dbname)
	        	self.cur = self.db.cursor()
		except mdb.Error:
			sys.exit("Invalid connect parameters")
		
	#Debug Method
	def version(self):
	    	query = "SELECT VERSION()"
		self.cur.execute(query)
        	self.result = self.cur.fetchone()
    		print "MySQL version: %s" % \
        	self.result

	# Create group if it does not exists
	def creategroup(self, groupname):
                sql="SELECT gid FROM groups WHERE name=%s"
                self.cur.execute(sql,(groupname))
                groupexists = self.cur.fetchall()
                if not groupexists:
                        sql="SELECT MAX( gid ) FROM groups"
                        self.cur.execute(sql)
                        gid = self.cur.fetchone()[0]+1
                        sql="INSERT INTO groups(password, name, gid) VALUES('x',%s,%s)"
                        self.cur.execute(sql,(groupname,gid))
                        print 'This group have been created :',groupname
                        print 'Corresponding GID is :',gid
                else:
                        print 'This group allready exists :',groupname

	# Disable user if present in DB
	def disable_db_user(self, username, system_date):
                sql="SELECT UID FROM users WHERE username=%s"
                self.cur.execute(sql,(username))
                userexists = self.cur.fetchall()
                if userexists:
			sql="UPDATE users SET expire='1', modification=%s WHERE username=%s"
                        self.cur.execute(sql,(system_date, username))
                        print 'Disabling account : ',username
                else:
                        print 'This account does not exist : ',username

	#Check if user exists in DB
	def user_exists(self, username):
		sql="SELECT UID FROM users WHERE username=%s"
                self.cur.execute(sql,(username))
                userexists = self.cur.fetchall()
		if userexists:
			result = 'True'
		else:
			result = 'False'
		return result

	#Check if gid1 exists in DB
	def g1_exists(self, gid1):
                sql="SELECT gid FROM groups WHERE gid=%s"
                self.cur.execute(sql,(gid1))
                g1exists = self.cur.fetchall()
                if g1exists:
                        result = 'True'
                else:
                        result = 'False'
                return result
	
	#Return existing gid1 value
	def g1_old(self, username):
                sql="SELECT GID FROM users WHERE username=%s"
                self.cur.execute(sql,(username))
                gid1 = self.cur.fetchone()[0]
		return gid1

	#Return existing password value
	def passwd_old(self, username):
                sql="SELECT password FROM users WHERE username=%s"
                self.cur.execute(sql,(username))
                hashedPassword = self.cur.fetchone()[0]
		return hashedPassword

	def update_db_user(self, username, hashed_password, gid1, dateOutput):
                sql="UPDATE users SET password=%s, gid=%s, shell='/bin/bash', expire='99999', modification=%s WHERE username=%s"
                self.cur.execute(sql,(hashed_password,gid1,dateOutput,username))
                sql="SELECT UID FROM users WHERE username=%s"
                self.cur.execute(sql,(username))
                uid = self.cur.fetchone()[0]
		return uid,gid1
	
	def create_db_user(self, username, home_dir, hashed_password, gid1, system_date):	
                if not gid1:
                	gid1='5000'
		#Defining new UID
                sql="SELECT MAX( uid ) FROM users"
                self.cur.execute(sql)
                uid = self.cur.fetchone()[0]+1
		#Insert Request
                sql="INSERT INTO users(username, password, uid, gid, gecos, homedir, shell, lstchg, min, warn, max, inact, expire, flag, source, creation, modification) "\
                "VALUES(%s,%s,%s,%s,'',%s,'/bin/bash','1','0','0','99999','0','99999','0','LOCAL',%s,%s)"
                self.cur.execute(sql,(username,hashed_password,uid,gid1,home_dir,system_date,system_date))
		return uid,gid1

	def g2_delete(self,username):
                sql="DELETE FROM grouplist WHERE username=%s"
                self.cur.execute(sql,(username))

	#Check if gid2 exists in DB
	def g2_exists(self, gid2):
                sql="SELECT gid FROM groups WHERE gid=%s"
                self.cur.execute(sql,(gid2))
                g2exists = self.cur.fetchall()
                if g2exists:
                        result = 'True'
                else:
                        result = 'False'
                return result

	#Add user to secondary group
	def g2_add_user(self, gid2, username):
             	#Check if user alredy belongs to the group
                sql="SELECT id FROM grouplist WHERE gid=%s AND username=%s"
                self.cur.execute(sql,(gid2,username))
                alreadyexists = self.cur.fetchall()
                if not alreadyexists:
			#Defining ID
                       	sql="SELECT MAX( id ) FROM grouplist"
                        self.cur.execute(sql)
                        dbid = self.cur.fetchone()[0]+1
			#Insert Request
                        sql="INSERT INTO grouplist(id, gid, username) VALUES(%s,%s,%s)"
                        self.cur.execute(sql,(dbid, gid2, username))
			result = 'True'
		else:
			result = 'False'
		return result
			
	
	def close(self):
		self.cur.close()
		self.db.close()
			
##################################################################

optionClass = Options_parser()
db = DB(optionClass.admindb, optionClass.passdb, optionClass.hostname, optionClass.database)

def defining_password():
        passwd ='1'
        passwdcheck ='2'

        #verification du mot de passe
        while passwd != passwdcheck:
                print 'Set a password for the account:'
                passwd = getpass.getpass()
                print 'Check your password:'
                passwdcheck = getpass.getpass()
        #hachage du mot de passe
        hashStatus, hashOutput = commands.getstatusoutput('mkpasswd -m md5 %s'+ passwd)
        return (hashOutput)

def home_dir(username):
	home = '/home/'+username
	return home

def date():
	dateStatus, dateOutput = commands.getstatusoutput('date +"%F %X"')
	return dateOutput

def username_check(username):
        if not username:
                print 'You need to specify a username'
                sys.exit(1)
        #Regex username
        if not re.match("^[a-z.]+$", username):
                print 'Invalid username : '+username
                sys.exit(1)

def gid_check(gid):
        if not re.match("^-?[0-9]+$", gid):
		print 'GID must be an integer, this value is invalid : ',gid
                sys.exit(1)
	

def main():

	#Defining variables
	system_date = date()
	username = optionClass.username
	g2_update = ''

	#Create new group
	if optionClass.creategroup:
		groupname=optionClass.creategroup
		#Error if SQL injection
		username_check(groupname)
		db.creategroup(groupname)
		db.close()
                sys.exit(0)

#########################################################################################
	#Error if SQL injection and if username empty
	username_check(username)
	home_directory = home_dir(username)

	#Disable user
	if optionClass.disable:
		db.disable_db_user(username, system_date)
		db.close()
		sys.exit(0)

	#Check if user exists in DB
	userExists = db.user_exists(username)

	#Ask for password in case of user creation or update
        if optionClass.password or userExists is 'False':
                hashed_password = defining_password()
	else:
		hashed_password = db.passwd_old(username)

	## Check if gid1 exists or empty
        if not optionClass.group1:
        	gid1 = ''
	else:
            	gid1 = optionClass.group1
		#Check if gid1 is integer
		gid_check(gid1)
                g1Exists = db.g1_exists(gid1)
                if g1Exists is 'False':
                	print "This group does not exists : "+gid1
                        gid1 = ''

	#Update user if user exists
	if userExists is 'True':
		if not gid1:
			gid1 = db.g1_old(username)
		uid,gid1 = db.update_db_user(username, hashed_password, gid1, system_date)

	#Else create user
	else:
		if not gid1:
			gid1 = '5000'
		uid,gid1 = db.create_db_user(username, home_directory, hashed_password, gid1, system_date)	

	#Tips to delete all user secondary groups
	if optionClass.group2 == 'delete':
		db.g2_delete(username)
                print 'All secondary groups deleted for user : '+username

	else:
		#Check if gid2 exists
		if optionClass.group2:
        	        gid2 = optionClass.group2
			#Check if gid2 is integer
			gid_check(gid2)
                	g2Exists = db.g2_exists(gid2)
	                if g2Exists is 'False':
        	                print "This group does not exists : "+gid2
			else:
				g2_update = db.g2_add_user(gid2, username)
	db.close()

	#Output
	if userExists is 'True':
		print 'This user has been updated : '+username
	else:
		print 'This user has been created : '+username
	print '--------------------------------------------------------------------'	
        print 'Username : '+username
        print 'UID : ',uid
        if optionClass.group1 : print 'Primary GID updated to: ',gid1
	else : print 'Primary GID : ',gid1
	if g2_update is 'True' : print 'User %s added to Secondary GID %s' % (username,gid2)
        print 'Homedir : '+home_directory
        print 'Modification date : '+system_date
        print '--------------------------------------------------------------------'


main()
