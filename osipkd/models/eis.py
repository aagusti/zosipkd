from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    SmallInteger,
    Text,
    DateTime,
    String,
    UniqueConstraint
    )
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    )
from zope.sqlalchemy import ZopeTransactionExtension
import transaction
from ..tools import as_timezone
from ..models import (DBSession, DefaultModel,Base,)
from ..models.base_model import (NamaModel)

class Eis(DefaultModel, Base):
    __tablename__ = 'wells'
    __table_args__ = {'extend_existing':True, 
                      'schema' : 'eis',}
    
    tahun = Column(Integer)
    kode  = Column(String(24))
    uraian = Column(String(128))
    amt_tahun = Column(BigInteger)
    amt_bulan = Column(BigInteger)
    amt_minggu = Column(BigInteger)
    amt_hari   = Column(BigInteger)
    order_id   = Column(Integer)
    is_aktif   = Column(SmallInteger)
    disabled    = Column(SmallInteger, default=0)
    @classmethod
    def sum_data(cls, kode, tahun):
        q = DBSession.query(cls).filter_by(
                kode==kode,
                tahun=tahun).first()
        if q:
            sum_minggu = q.amt_minggu+q.amt_hari
            sum_bulan  = q.amt_bulan + sum_minggu
            sum_tahun  = q.amt_tahun + sum_bulan
            return  dict(sum_hari = sum_hari, sum_minggu = sum_minggu, 
                         sum_bulan = sum_bulan, sum_tahun = sum_tahun)
            
        return {}
        
    @classmethod
    def sum_order_id(cls, tahun):
        q = DBSession.query(cls).filter_by(
                tahun=tahun)
        if q:
            return  q
        return 

trigger_text = """
    CREATE function func_ar_payment_detail_aiu
    
    CREATE TRIGGER trg_insert_update AFTER INSERT,UPDATE ON ar_payment_item
    FOR EACH ROW BEGIN
      IF NEW.rank = 0 THEN
         SET NEW.rank = (SELECT IFNULL(MAX(a.rank),0) + 1
                          FROM authors AS a
                           WHERE a.id = NEW.pub_id);
      END IF;
    END
    """
    
class LastUpdate(DefaultModel, Base):
    __tablename__ = 'last_update'
    __table_args__ = {'extend_existing':True, 
                      'schema' : 'eis',}
    
    wells = Column(DateTime(timezone=True), nullable=True)


class ARPaymentDetail(NamaModel, Base):
    __tablename__ = 'ar_payment_detail'
    __table_args__ = {'extend_existing':True, 
                      'schema' : 'eis',}
    tahun = Column(Integer)
    amount = Column(BigInteger)
    ref_kode = Column(String(32))
    ref_nama = Column(String(64))
    tanggal = Column(DateTime(timezone=True), nullable=True)
    kecamatan_kd = Column(String(32))
    kecamatan_nm = Column(String(64))
    kelurahan_kd = Column(String(32))
    kelurahan_nm = Column(String(64))
    is_kota      = Column(SmallInteger)
    sumber_data  = Column(String(32)) #Manual, PBB, BPHTB, PAD
    sumber_id    = Column(SmallInteger)#1, 2, 3, 4
    
class ARInvoiceDetail(NamaModel, Base):
    __tablename__ = 'ar_invoice_detail'
    __table_args__ = {'extend_existing':True, 
                      'schema' : 'eis',}
    tahun = Column(Integer)
    amount = Column(BigInteger)
    ref_kode = Column(String(32))
    ref_nama = Column(String(64))
    tanggal = Column(DateTime(timezone=True), nullable=True)
    kecamatan_kd = Column(String(32))
    kecamatan_nm = Column(String(64))
    kelurahan_kd = Column(String(32))
    kelurahan_nm = Column(String(64))
    is_kota      = Column(SmallInteger)
    sumber_data  = Column(String(32)) #Manual, PBB, BPHTB, PAD
    sumber_id    = Column(SmallInteger)#1, 2, 3, 4
    
    
    
