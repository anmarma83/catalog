from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
 
Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(250), nullable=False)
    

class Category(Base):
    __tablename__ = 'category'
   
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    
    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           
           'id':self.id,
           'name':self.name
       }
 
class CategoryItem(Base):
    __tablename__ = 'categoryitem'


    name =Column(String(80), nullable = False)
    id = Column(Integer, primary_key = True)
    description = Column(String(250))
    category_id = Column(Integer,ForeignKey('category.id'))
    category = relationship(Category)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize2(self):
       """Return object data in easily serializeable format"""
       return {
           'cat_id': self.category.id,
           'description': self.description,
           'id': self.id,
           'title': self.name
       }

    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
            'Items': self.serialize2,
           'id':self.category.id,
           'name':self.category.name
           
       }



engine = create_engine('sqlite:///catalogDB.db')
 

Base.metadata.create_all(engine)
