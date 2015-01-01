from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    SmallInteger,
    Text,
    DateTime,
    Date,
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
from ..models.pemda_model import (Rekening,Unit)
from ..models.apbd_anggaran import (KegiatanSub)
        
class ARInvoiceItem(NamaModel, Base):
    __tablename__ = 'ar_invoice_item'
    __table_args__ = {'extend_existing':True, 
                      'schema' : 'apbd',}
    unit_id=Column(Integer, ForeignKey("admin.units.id"), nullable=False)
    units = relationship("Unit", backref=backref("ar_invoice_items"))
    rekening_id = Column(Integer, ForeignKey("admin.rekenings.id"), nullable=False)
    rekenings = relationship("Rekening", backref=backref("ar_invoice_items"))
    ref_kode = Column(String(32), unique=True)
    ref_nama = Column(String(64))
    tanggal = Column(DateTime(timezone=True), nullable=False)
    amount = Column(BigInteger)
    kecamatan_kd = Column(String(32))
    kecamatan_nm = Column(String(64))
    kelurahan_kd = Column(String(32))
    kelurahan_nm = Column(String(64))
    is_kota      = Column(SmallInteger)
    sumber_id    = Column(SmallInteger)#1, 2, 3, 4
    sumber_data  = Column(String(32)) #Manual, PBB, BPHTB, PAD
    tahun = Column(Integer)
    bulan = Column(Integer)
    minggu = Column(Integer)
    hari = Column(Integer)
    
class ARPaymentItem(NamaModel, Base):
    __tablename__ = 'ar_payment_item'
    __table_args__ = {'extend_existing':True, 
                      'schema' : 'apbd',}
    tahun = Column(Integer)
    amount = Column(BigInteger)
    unit_id = Column(Integer, ForeignKey("admin.units.id"), nullable=False)
    units = relationship("Unit", backref=backref("ar_payment_items"))
    kegiatan_sub_id = Column(Integer, ForeignKey("apbd.kegiatan_subs.id"), nullable=False)
    kegiatan_subs = relationship("KegiatanSub", backref=backref("ar_payment_items"))
    rekening_id = Column(Integer, ForeignKey("admin.rekenings.id"), nullable=False)
    rekenings = relationship("Rekening", backref=backref("ar_payment_items"))

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
    
class ARTargetItem(NamaModel, Base):
    __tablename__ = 'ar_target_item'
    __table_args__ = {'extend_existing':True, 
                      'schema' : 'apbd',}
    tahun = Column(Integer)
    unit_id=Column(Integer, ForeignKey("admin.units.id"), nullable=False)
    units = relationship("Unit", backref=backref("ar_target_items"))
    kegiatan_sub_id=Column(Integer, ForeignKey("apbd.kegiatan_subs.id"), nullable=False)
    kegiatan_subs = relationship("KegiatanSub", backref=backref("ar_target_items"))
    rekening_id = Column(Integer, ForeignKey("admin.rekenings.id"), nullable=False)
    rekenings = relationship("Rekening", backref=backref("ar_target_items"))
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

############################################
###  JURNAL ANGGARAN    ###
###  KegiatanItem  ###
############################################        
class JurnalAnggaran(DefaultModel, Base):
    __tablename__   ='jurnal_anggaran'
    __table_args__  = {'extend_existing':True,'schema' :'apbd'}

    kegiatan_subs   = relationship("KegiatanSub", backref=backref("jurnal_anggarans"))    
    rekenings       = relationship("Rekening",    backref=backref("jurnal_anggarans"))

    kegiatan_sub_id = Column(BigInteger, ForeignKey("apbd.kegiatan_subs.id"), nullable=False)
    rekening_id     = Column(Integer ,   ForeignKey("admin.rekenings.id"),     nullable=False)    
    amount  = Column(BigInteger, nullable=False, default=0)

    
class Jurnal(NamaModel, Base):
    __tablename__   = 'jurnals'
    __table_args__  = {'extend_existing':True, 'schema' : 'apbd',}
                    
    tanggal         = Column(Date) 
    tgl_transaksi   = Column(Date)
    tahun_id        = Column(BigInteger,    ForeignKey("apbd.tahuns.id"), nullable=False)
    unit_id         = Column(Integer,       ForeignKey("admin.units.id"),  nullable=False)                     
    units           = relationship("Unit",  backref=backref("jurnals"))
    
    #no_urut         = Column(Integer,       nullable=False)
    periode         = Column(Integer,       nullable=False)
    jv_type         = Column(SmallInteger,  nullable=False, default=0)
    source          = Column(String(10),    nullable=False)
    source_no       = Column(String(30),    nullable=False)
    tgl_source      = Column(Date)
    posted          = Column(SmallInteger,  nullable=False)
    posted_by       = Column(Integer,       nullable=False) 
    posted_date     = Column(Date) 
    notes           = Column(String(225),   nullable=False)
    is_skpd         = Column(SmallInteger,  nullable=False)
    #is_autoreverse  = Column(SmallInteger,  nullable=False)
    #rekening_id     = Column(BigInteger,  ForeignKey("admin.rekenings.id"),     nullable=False)
    #rekenings       = relationship("Rekening",    backref="jurnals")
    #amount           = Column(BigInteger,  default=0) 
 
    @classmethod
    def get_no_urut(cls, p):
        row = DBSession.query(func.max(cls.no_urut).label('no_urut'))\
                .filter(cls.tahun_id==p['tahun_id'],
                        cls.unit_id==p['unit_id']
                ).first()
        if row and row.no_urut:
           return row.no_urut+1
        else:
           return 1

class JurnalItem(NamaModel, Base):
    __tablename__   ='jurnal_items'
    __table_args__  = {'extend_existing':True,'schema' :'apbd'}

    jurnal_id       = Column(BigInteger,  ForeignKey("apbd.jurnals.id"),      nullable=False)
    jurnals          = relationship("Jurnal",      backref="jurnal_items")

    kegiatan_sub_id = Column(BigInteger,  ForeignKey("apbd.kegiatan_subs.id"), nullable=False)
    kegiatan_subs   = relationship("KegiatanSub", backref="jurnal_items")

    rekening_id     = Column(BigInteger,  ForeignKey("admin.rekenings.id"),     nullable=False)
    rekenings       = relationship("Rekening",    backref="jurnal_items")

    #rate            = Column(BigInteger,  default=1)
    #items           = Column(BigInteger,  default=1) 
    #debet           = Column(BigInteger)
    #kredit          = Column(BigInteger)
    amount           = Column(BigInteger,  default=0) 
    notes           = Column(String(225), nullable=False)

#    @classmethod
#    def get_jurnal_item_id(cls, p):
#        row = DBSession.query(func.max(cls.id).label('jurnal_item_id'))\
#                .filter(cls.jurnal_id==p['jurnal_id']
#                ).first()
#        if row and row.jurnal_item_id:
#           return row.jurnal_item_id+1
#        else:
#           return 1 

 