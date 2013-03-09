#!/usr/bin/env python

import threading

import MySQLdb
import MySQLdb.cursors

def synchronized(method):
	def f(*args,**kwargs):
		self = args[0]
		if not hasattr( self, "__lock__" ):
			self.__lock__ = threading.Lock()
		if not hasattr( self, "__lock_owner__" ):
			self.__lock_owner__ = threading.current_thread()
		if self.__lock_owner__ == threading.current_thread() and self.__lock__.locked():
			return method( *args, **kwargs )
		else:
			with self.__lock__:
				self.__lock_owner__ = threading.current_thread()
				return method(*args,**kwargs)
	return f

class MyDB( object ):

	def __init__( self, host='localhost', user='vuln-user', passw='vuln-pass', db='my_movies', cursorclass=MySQLdb.cursors.DictCursor):
		self.create_singleton( lambda : MySQLdb.connect(host=host, user=user, passwd=passw, db=db, cursorclass=cursorclass, charset="utf8", use_unicode=True) )
	
	@classmethod
	@synchronized
	def create_singleton( clazz, instance_creator ):
		if not hasattr( clazz, "conn" ):
			clazz.conn = instance_creator()
	
	@classmethod
	def get_movies( clazz ):
		cur = clazz.conn.cursor()
		cur.execute( "SELECT `index`, `title`, `description`, `actors`, `price`, `image_path` FROM `movie`" )
		return cur.fetchall()
	
	@classmethod
	def get_movie_by_id( clazz, movie_id ):
		cur = clazz.conn.cursor()
		cur.execute( "SELECT `index`, `title`, `description`, `actors`, `price`, `image_path` FROM `movie` WHERE `index` = %d" % movie_id )
		return cur.fetchone()
	
	@classmethod
	def get_reviews_by_id( clazz, movie_id ):
		cur = clazz.conn.cursor()
		cur.execute( "SELECT `username`, `timestamp`, `text` FROM `reviews` WHERE `movie_id` = %d ORDER BY `timestamp` ASC" % movie_id )
		return cur.fetchall()

	@classmethod
	@synchronized
	def create_user( clazz, username, password ):
		try:
			clazz.conn.execute( "INSERT INTO `users` (`username`,`password`) VALUES ('%s','%s')" % (username,password) )
			clazz.conn.commit()
			return True
		except MySQLdb.Error:
			clazz.conn.rollback()
			return False
	
	@classmethod
	def validate_credentials( clazz, username, password ):
		cur = clazz.conn.cursor()
		cur.execute( "SELECT `user_id` FROM `users` WHERE `username` = '%s' AND `password` = '%s'" % (username, password) )
		return cur.rowcount > 0
