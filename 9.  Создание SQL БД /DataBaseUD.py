import sqlite3 as sl
import sqlalchemy as sa
import pandas as pd

from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column, relationship, Session
from sqlalchemy import create_engine, DateTime, String, Float, Integer, func, ForeignKey, insert, select, text
from sqlalchemy.dialects.postgresql import UUID as UUIDType
from uuid import UUID, uuid4
from typing import List
from datetime import datetime



# Путь к файлу.
dir_path: str = "data/downloads/"


# Функция по разбору файла на части(убрана)
def load(year: int, month: int, day: int, agency: str, project: str, solution: str, content: str) -> str:
    """
    Download products from the IGN [1] FTP server by a specification.

    Parameters
    ----------
    year:
        Start time of the solution: year.
    month:
        Start time of the solution: month.
    day:
        Start time of the solution: day.
    agency:
        Analysis center providing the file (COD, EMR, ESA, GFZ, GRG, IGS, JAX, JPL, MIT, NGS,
        SIO, SHA, WUH).
    project:
        Project within which the file was generated (MGX, OPS).
    solution:
        Solution type (FIN, RAP, ULT).
    content:
        Content type (ORB, SOL, ERP, ATT, CLK, OSB, GIM, TRO).

    Returns
    -------
    path:
        A local path to the downloaded file.
   
"""
Данные для теста.
"""

# Select a date.
year = 2024
month = 11
day = 1



"""
Создание Базы данных
используются классы
"""


# Родительский класс таблиц
class Base(DeclarativeBase):
    __abstract__ = True


# Проверка данных на уникальность
# Эта функция связывает словарь с сессией, которая хранит текущие "уникальные" ключи.
def _unique(session, cls, hashfunc, queryfunc, constructor, arg, kw):
    cache = session.info.get("_unique_cache", None)
    if cache is None:
        session.info['_unique_cache'] = cache = {}

    key = (cls, hashfunc(*arg, **kw))
    if key in cache:
        return cache[key]
    else:
        with session.no_autoflush:
            q = session.query(cls)
            q = queryfunc(q, *arg, **kw)
            obj = q.first()
            if not obj:
                obj = constructor(*arg, **kw)
                session.add(obj)
        cache[key] = obj
        return obj


# Проверка данных на уникальность
# Методы для классов таблиц
class UniqueMixin(object):
    @classmethod
    def unique_hash(cls, *arg, **kw):
        raise NotImplementedError()

    @classmethod
    def unique_filter(cls, query, *arg, **kw):
        raise NotImplementedError()

    @classmethod
    def as_unique(cls, session, *arg, **kw):
        return _unique(
            session,
            cls,
            cls.unique_hash,
            cls.unique_filter,
            cls,
            arg, kw
        )

    @classmethod
    async def async_as_unique(cls, async_session, *arg, **kw):
        return await async_session.run_sync(cls.as_unique, *arg, **kw)


class Satellates(UniqueMixin, Base):
    __tablename__ = 'satellate'
    __table_args__ = {'extend_existing': True}

    id: Mapped[UUID] = mapped_column(
        UUIDType(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
        nullable=False)
    prn: Mapped[str] = mapped_column(String(4), nullable=False)

    epoch: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    agency_id: Mapped[int] = mapped_column(ForeignKey('agency.id'))
    agency: Mapped['Agencies'] = relationship('Agencies', foreign_keys=[agency_id], back_populates='satellate')
    system_id: Mapped[int] = mapped_column(ForeignKey('system.id'))
    system: Mapped['Systems'] = relationship('Systems', foreign_keys=[system_id], back_populates='satellate')

    x: Mapped[float] = mapped_column(Float, nullable=False)
    y: Mapped[float] = mapped_column(Float, nullable=False)
    z: Mapped[float] = mapped_column(Float, nullable=False)


class Agencies(UniqueMixin, Base):
    __tablename__ = 'agency'
    __table_args__ = {'extend_existing': True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, autoincrement=True, unique=True)
    satellate: Mapped[list['Satellates']] = relationship('Satellates', back_populates='agency')
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)

    @classmethod
    def unique_hash(cls, name):
        return name

    @classmethod
    def unique_filter(cls, query, name):
        return query.filter(Agencies.name == name)


class Systems(Base, UniqueMixin):
    __tablename__ = 'system'
    __table_args__ = {'extend_existing': True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, autoincrement=True, unique=True)
    satellate: Mapped[list['Sattellates']] = relationship('Satellates', back_populates='system')
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)

    @classmethod
    def unique_hash(cls, name):
        return name

    @classmethod
    def unique_filter(cls, query, name):
        return query.filter(Systems.name == name)


#Create Date Base
Base.metadata.create_all(engine)

# Наполнение БД собранными данными
path_to_db = 'D:/DateBaseSatellates.db'

if path_to_db:
    engine = create_engine(f'sqlite+pysqlite:///{path_to_db}', echo=False)
    connection = sl.connect('{path_to_db}')

Session = sessionmaker(bind=engine)
session = Session()


# Читаем файл
sp3_data = sensors.gnss.read_sp3(sp3_path)

# Получаем агенство
agency = sp3_data.agency

# Итерация по эпохам
for epc_data in sp3_data.epochs:
    # Получаем дату и время
    year, month, day, hour, minute, second = epc_data.t.ymdhms
    cur_date = epc_data.t



    # Итерация по спутниками
    for (sys, prn), sat_data in epc_data.satellites.items():
        # Итерация по записям
        for rec_data in sat_data.records:
            # Если есть запись по этой дате
            if isinstance(rec_data, sat_data.PositionAndClock):
                # Получить координаты спутника
                x = rec_data.x
                y = rec_data.y
                z = rec_data.z

                                
                # запись
                _prn = prn
                _agency = agency
                _system = sys.name
                _epoch = datetime(year, month, day, hour, minute)
                _x = x
                _y = y
                _z = z

                try:
                    session.scalars(insert(Satellates).returning(Satellates),
                                    [{'prn': _prn, 'agency': _agency, 'epoch': _epoch, 'system': _system,
                                      'x': _x, 'y': _y, 'z': _z}])

                    session.flush()
                except:
                    Agencies.as_unique(session, name=_agency)
                    Systems.as_unique(session, name=_system)
                    session.flush()
                    session.scalars(insert(Satellates).returning(Satellates),
                                    [{'prn': _prn, 'epoch': _epoch, 'system': _system, 'agency': _agency, 'x': _x,
                                      'y': _y, 'z': _z,
                                      'agency_id': session.scalars(select(Agencies).filter_by(name=_agency)).first().id,
                                      'system_id': session.scalars(
                                          select(Systems).filter_by(name=_system)).first().id}])

                    session.flush()

                session.commit()

                # конец транзакции
                session.rollback()



""" Запросы в БД с выводами в ДатаФрейм """

query = """
SELECT ag.name as agency, epoch, sys.name as system, prn, x, y, z
FROM satellate as sat
JOIN agency as ag on sat.agency_id = ag.id
JOIN system as sys on sat.system_id = sys.id
WHERE epoch BETWEEN '2024-11-01 12:00:00' AND '2024-11-01 21:15:00' and sys.name = 'GPS' and prn = 14;
    """
satell = pd.read_sql(query, engine)
#satell.set_index('id', inplace=True)
satell

# и с выводом объекта result
with session:
    result = session.execute(text("SELECT * FROM agency"))
    for row in result:
        print(row)
