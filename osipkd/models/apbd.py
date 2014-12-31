from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    SmallInteger,
    Text,
    DateTime,
    String,
    UniqueConstraint,
    ForeignKey
    )
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    relationship, backref
    )
from zope.sqlalchemy import ZopeTransactionExtension
import transaction
from ..tools import as_timezone
from ..models import (DBSession, DefaultModel,Base,)
from ..models.base_model import (NamaModel)
from ..models.pemda_model import (Rekening)
        
class ARInvoiceItem(NamaModel, Base):
    __tablename__ = 'ar_invoice_item'
    __table_args__ = {'extend_existing':True, 
                      'schema' : 'apbd',}
    tahun = Column(Integer)
    amount = Column(BigInteger)
    rekening_id = Column(Integer, ForeignKey("admin.rekenings.id"), nullable=False)
    rekening = relationship("Rekening", backref=backref("ar_invoice_items"))
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
    bulan = Column(Integer)
    minggu = Column(Integer)
    hari = Column(Integer)
    
class ARPaymentItem(NamaModel, Base):
    __tablename__ = 'ar_payment_item'
    __table_args__ = {'extend_existing':True, 
                      'schema' : 'apbd',}
    tahun = Column(Integer)
    amount = Column(BigInteger)
    rekening_id = Column(Integer, ForeignKey("admin.rekenings.id"), nullable=False)
    rekening = relationship("Rekening", backref=backref("ar_payment_items"))
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
    bulan = Column(Integer)
    minggu = Column(Integer)
    hari = Column(Integer)
    
class ARTargetDetail(NamaModel, Base):
    __tablename__ = 'ar_target_detail'
    __table_args__ = {'extend_existing':True, 
                      'schema' : 'eis',}
    tahun = Column(Integer)
    amount_01 = Column(BigInteger)
    amount_02 = Column(BigInteger)
    amount_03 = Column(BigInteger)
    amount_04 = Column(BigInteger)
    amount_05 = Column(BigInteger)
    amount_06 = Column(BigInteger)
    amount_07 = Column(BigInteger)
    amount_08 = Column(BigInteger)
    amount_09 = Column(BigInteger)
    amount_10 = Column(BigInteger)
    amount_11 = Column(BigInteger)
    amount_12 = Column(BigInteger)
    