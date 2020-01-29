from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
 
from database_setup import Category, Base, CategoryItem,User
 
engine = create_engine('sqlite:///catalogDB.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine
 
DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


category = Category(name='Soccer')
session.add(category)
session.commit()

category = Category(name='Basketball')
session.add(category)
session.commit()

category = Category(name='Baseball')
session.add(category)
session.commit()

category = Category(name='Frisbee')
session.add(category)
session.commit()

category = Category(name='Snowboarding')
session.add(category)
session.commit()

category = Category(name='Rock Climbing')
session.add(category)
session.commit()

category = Category(name='Football')
session.add(category)
session.commit()

category = Category(name='Skating')
session.add(category)
session.commit()

category = Category(name='Hockey')
session.add(category)
session.commit()
print "added Categories!"

