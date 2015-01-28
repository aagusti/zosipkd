from types import DictType
from sqlalchemy import (
    Table,
    MetaData,
    )
from data.user import UserData
from data.routes import RouteData
from data.apps import AppsData
from DbTools import (
    get_pkeys,
    execute,
    set_sequence,
    split_tablename,
    )
from ..models import (
    Base,
    BaseModel,
    CommonModel,
    DBSession,
    User,
    )


fixtures = [
    ('users', UserData),
    ('routes', RouteData),
    ('admin.apps', AppsData),
    ]

def insert():
    insert_(fixtures)
    
def insert_(fixtures): 
    engine = DBSession.bind
    metadata = MetaData(engine)
    tablenames = []
    for tablename, data in fixtures:
        if tablename == 'users':
            T = User
            table = T.__table__
        else:
            schema, tablename_ = split_tablename(tablename)
            table = Table(tablename_, metadata, autoload=True, schema=schema)
            class T(Base, BaseModel, CommonModel):
                __table__ = table
        if type(data) == DictType:
            options = data['options']        
            data = data['data']
        else:
            options = []
        if 'insert if not exists' not in options:
            q = DBSession.query(T).limit(1)
            if q.first():
                continue
        tablenames.append(tablename)                
        keys = get_pkeys(table)
        for d in data:
            filter_ = {}
            for key in keys:
                val = d[key]
                filter_[key] = val
            q = DBSession.query(T).filter_by(**filter_)
            if q.first():
                continue
            tbl = T()
            tbl.from_dict(d)
            if tablename == 'users' and 'password' in d:
                tbl.password = d['password']
            DBSession.add(tbl)
    DBSession.flush()
    update_sequence(tablenames)

# Perbaharui nilai sequence    
def update_sequence(tablenames):
    engine = DBSession.bind
    metadata = MetaData(engine)
    for item in fixtures:
        tablename = item[0]
        if tablename not in tablenames:
            continue
        schema, tablename = split_tablename(tablename)
        class T(Base):
            __table__ = Table(tablename, metadata, autoload=True, schema=schema)
        set_sequence(T)    
