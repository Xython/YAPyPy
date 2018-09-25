from .hinting import *
from sqlalchemy import (create_engine, Integer, String, DateTime, ForeignKey,
                        Sequence, SmallInteger, Enum, Date, Table, Column,
                        Boolean)

from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import typing


def filter_from_table(table, cond):

    return table.query.filter(cond)
