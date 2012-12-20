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
    db = create_engine('postgresql://subotto:%s@roma.uz.sns.it/subotto_new' % (fpasswd.read().strip()), echo=True)
#db = create_engine('sqlite:///subotto.sqlite', echo=True)
Session = sessionmaker(db)
Base = declarative_base(db)

class Team(Base):
    __tablename__ = 'teams'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

NAME_MAP = {('Fabrizio', 'bianchi'): ('Fabrizio', 'Bianchi', None),
            ('Giulio', 'bresciani'): ('Giulio', 'Bresciani', None),
            ('Viglaa', ''): ('Federico', 'Vigolo', None),
            ('Vigolo', ''): ('Federico', 'Vigolo', None),
            ('Mattia', 'Carlo Sormani'): ('Mattia Carlo', 'Sormani', None),
            ('Mattia', 'Sormani'): ('Mattia Carlo', 'Sormani', None),
            ('Giacomo', 'de Palma'): ('Giacomo', 'De Palma', None),
            ('Giacomo', 'del Nin'): ('Giacomo', 'Del Nin', None),
            ('Brian', 'De Palma'): ('Giacomo', 'De Palma', None),
            ('Brian', 'de Palma'): ('Giacomo', 'De Palma', None),
            ('martina', 'bottacchiari'): ('Martina', 'Bottacchiari', None),
            ('Roberto', 'Daluisio'): ('Roberto', 'Daluiso', None),
            ('Antonio', 'Decapua'): ('Antonio', 'De Capua', None),
            ('Maria', 'Coombo'): ('Maria', 'Colombo', None),
            ('Federico', 'Fabbiano'): ('Federico', 'Fabiano', None),
            ('Davide', 'Lomardo'): ('Davide', 'Lombardo', None),
            ('Silvia', 'di Vincenzo'): ('Silvia', 'Di Vincenzo', None),
            ('Gennady', 'Ultratsev'): ('Gennady', 'Uraltsev', None),
            ('Federico', 'Lobianco'): ('Federico', 'Lo Bianco', None),
            ('Simone', 'Dimarino'): ('Simone', 'Di Marino', None),
            ('Dennis', 'Nardin'): ('Denis', 'Nardin', None),
            ('Andrea', 'Bianchi'): ('Andrea', 'Bianchi', 'Scienze'),
            ('Leslie', 'Lazzerino'): ('Leslie Lamberto', 'Lazzarino', None),
            ('Leslie', 'Lazzarino'): ('Leslie Lamberto', 'Lazzarino', None),
            ('Niccolò', 'Grilli'): ('Nicolò', 'Grilli', None),
            ('Matteo', 'Ruggero'): ('Matteo', 'Ruggiero', None),
            ('Alessandro', ''): ('Alessandro', 'Cobbe', None),
            ('Mauro', ''): ('Mauro', 'Pieroni', None),
            ('Mauro', 'Pierone'): ('Mauro', 'Pieroni', None),
            ('', ''): ('??', '??', 'Matematico'),
            ('', '*AltroMat'): ('??', '??', 'Matematico'),
            ('', '*AltroFis'): ('??', '??', 'Fisico'),
            }

class Player(Base):
    __tablename__ = 'players'
    __table_args__ = (
        UniqueConstraint('fname', 'lname', 'comment',
                         name='cst_players_fname_lname_comment'),
        )

    id = Column(Integer, primary_key=True)
    fname = Column(String, nullable=False)
    lname = Column(String, nullable=False)
    comment = Column(String)

    @classmethod
    def get_or_create(cls, session, fname, lname, comment):

        # Reduce names to a canonical (and correct) orthography
        fname = fname.strip()
        lname = lname.strip()
        comment = comment.strip() if comment is not None else None

        if (fname, lname) in NAME_MAP:
            fname, lname, comment = NAME_MAP[(fname, lname)]

        try:
            return session.query(Player).filter(Player.fname == fname). \
                filter(Player.lname == lname). \
                filter(Player.comment == comment).one()
        except NoResultFound:
            player = Player()
            player.fname = fname
            player.lname = lname
            player.comment = comment
            session.add(player)
            return player

class Match(Base):
    __tablename__ = 'matches'

    id = Column(Integer, primary_key=True)
    sched_begin = Column(DateTime, nullable=False)
    sched_end = Column(DateTime, nullable=False)
    begin = Column(DateTime)
    end = Column(DateTime)
    name = Column(String)
    team_a_id = Column(Integer, ForeignKey(Team.id, onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    team_b_id = Column(Integer, ForeignKey(Team.id, onupdate="CASCADE", ondelete="CASCADE"), nullable=False)

    team_a = relationship(Team, primaryjoin="Team.id == Match.team_a_id")
    team_b = relationship(Team, primaryjoin="Team.id == Match.team_b_id")

    def get_player_team(self, player):
        return sessionlib.object_session(self).query(PlayerMatch).filter(PlayerMatch.match == self). \
            filter(PlayerMatch.player == player).one().team

class PlayerMatch(Base):
    __tablename__ = 'player_matches'
    __table_args__ = (
        UniqueConstraint('player_id', 'match_id',
                         name='cst_player_matches_player_id_match_id'),
        )

    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey(Player.id, onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    match_id = Column(Integer, ForeignKey(Match.id, onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    team_id = Column(Integer, ForeignKey(Team.id, onupdate="CASCADE", ondelete="CASCADE"), nullable=False)

    player = relationship(Player)
    match = relationship(Match)
    team = relationship(Team)

class AdvantagePhase(Base):
    __tablename__ = 'adantage_phases'

    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey(Match.id, onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    start_sec = Column(Integer, nullable=False)
    advantage = Column(Integer, nullable=False)

    match = relationship(Match)

class Event(Base):
    __tablename__ = 'events'
    __table_args__ = (
        UniqueConstraint('timestamp', 'match_id',
                         name='cst_events_timestamp_match_id'),
        Index('ix_events_match_id_timestamp',
              'match_id', 'timestamp'),
        )

    EV_TYPE_SWAP = 'swap'
    EV_TYPE_CHANGE = 'change'
    EV_TYPE_GOAL = 'goal'
    EV_TYPE_GOAL_UNDO = 'goal_undo'
    EV_TYPE_ADVANTAGE_PHASE = 'advantage_phase'

    EV_SOURCE_MANUAL = 'manual'
    EV_SOURCE_CELL_RED_PLAIN = 'cell_red_plain'
    EV_SOURCE_CELL_BLUE_PLAIN = 'cell_blue_plain'
    EV_SOURCE_CELL_RED_SUPER = 'cell_red_super'
    EV_SOURCE_CELL_BLUE_SUPER = 'cell_blue_super'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    match_id = Column(Integer, ForeignKey(Match.id), nullable=False)
    type = Column(String, nullable=False, index=True)
    source = Column(String, nullable=False)
    team_id = Column(Integer, ForeignKey(Team.id, onupdate="CASCADE", ondelete="CASCADE"))
    player_a_id = Column(Integer, ForeignKey(Player.id, onupdate="CASCADE", ondelete="CASCADE"))
    player_b_id = Column(Integer, ForeignKey(Player.id, onupdate="CASCADE", ondelete="CASCADE"))
    red_team_id = Column(Integer, ForeignKey(Team.id, onupdate="CASCADE", ondelete="CASCADE"))
    blue_team_id = Column(Integer, ForeignKey(Team.id, onupdate="CASCADE", ondelete="CASCADE"))
    phase_id = Column(Integer, ForeignKey(AdvantagePhase.id, onupdate="CASCADE", ondelete="CASCADE"))

    match = relationship(Match)
    team = relationship(Team, primaryjoin="Team.id == Event.team_id")
    player_a = relationship(Player, primaryjoin="Player.id == Event.player_a_id")
    player_b = relationship(Player, primaryjoin="Player.id == Event.player_b_id")
    red_team = relationship(Team, primaryjoin="Team.id == Event.red_team_id")
    blue_team = relationship(Team, primaryjoin="Team.id == Event.blue_team_id")
    phase = relationship(AdvantagePhase)

    def check_type(self):
        must_none = []
        mustnt_none = []
        if self.type == Event.EV_TYPE_SWAP:
            mustnt_none = [self.red_team, self.blue_team]
            must_none = [self.team, self.player_a, self.player_b, self.phase]
        elif self.type == Event.EV_TYPE_CHANGE:
            mustnt_none = [self.team, self.player_a, self.player_b]
            must_none = [self.red_team, self.blue_team, self.phase]
        elif self.type == Event.EV_TYPE_GOAL or self.type == Event.EV_TYPE_GOAL_UNDO:
            mustnt_none = [self.team]
            must_none = [self.player_a, self.player_b, self.red_team, self.blue_team, self.phase]
        elif self.type == Event.EV_TYPE_ADVANTAGE_PHASE:
            mustnt_none = [self.phase]
            must_none = [self.team, self.player_a, self.player_b, self.red_team, self.blue_team]
        else:
            return False

        for x in must_none:
            if x is not None:
                return False
        for x in mustnt_none:
            if x is None:
                return False

        if self.type == Event.EV_TYPE_SWAP:
            if set([self.red_team, self.blue_team]) != set([self.match.team_a, self.match.team_b]):
                return False
        elif self.type == Event.EV_TYPE_CHANGE:
            if self.match.get_player_team(self.player_a) != self.team or self.match.get_player_team(self.player_b) != self.team:
                return False
            if self.team not in [self.match.team_a, self.match.team_b]:
                return False
        elif self.type == Event.EV_TYPE_GOAL or self.type == Event.EV_TYPE_GOAL_UNDO:
            if self.team not in [self.match.team_a, self.match.team_b]:
                return False
        elif self.type == Event.EV_TYPE_ADVANTAGE_PHASE:
            if self.phase.match != self.match:
                return False

        return True

if __name__ == '__main__':
    session = Session()
    Base.metadata.create_all(db)

    t1 = Team()
    t1.name = 'Matematici'
    t2 = Team()
    t2.name = 'Fisici'
    session.add(t1)
    session.add(t2)

    # m = Match()
    # m.team_a = t1
    # m.team_b = t2
    # m.sched_begin = datetime.datetime.now()
    # m.sched_end = datetime.datetime.now()
    # session.add(m)

    session.commit()
