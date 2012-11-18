#!/usr/bin/python
# -*- coding: utf-8 -*-

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.schema import Index
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import session as sessionlib

import datetime

with open('passwd') as fpasswd:
    db = create_engine('postgresql://subotto:%s@roma.uz.sns.it/subotto' % (fpasswd.read().strip()), echo=False)
#db = create_engine('sqlite:///subotto.sqlite', echo=True)
Session = sessionmaker(db)
Base = declarative_base(db)

class Team(Base):
    __tablename__ = 'teams'

    id = Column(Integer, primary_key=True)
    name = Column(String)

class Player(Base):
    __tablename__ = 'players'

    id = Column(Integer, primary_key=True)
    fname = Column(String)
    lname = Column(String)
    teamid = Column(Integer, ForeignKey(Team.id))

    team = relationship(Team)

class Event(Base):
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)
    type = Column(String)
    param = Column(String)
