import sys
from sqlalchemy import (Column, Integer, String, SmallInteger, UniqueConstraint, 
                        Date, BigInteger, ForeignKey, func)
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql.functions import concat
from osipkd.models import (DBSession,Base, DefaultModel)  
from osipkd.models.base_model import (NamaModel)  
from osipkd.models.apbd_anggaran import (KegiatanSub, KegiatanItem,Pegawai)  
from osipkd.models.pemda_model import (Unit)  

#from osipkd.tools import FixLength

class Spd(NamaModel, Base):
    __tablename__  = 'ap_spds'
    __table_args__ = {'extend_existing':True, 'schema' : 'apbd',}

    units       = relationship("Unit", backref="spds")

    tahun_id    = Column(BigInteger,   ForeignKey("apbd.tahuns.id"), nullable=False)
    triwulan_id = Column(SmallInteger, nullable=False)
    unit_id     = Column(Integer,      ForeignKey("admin.units.id"),  nullable=False) 
    tanggal     = Column(Date,         nullable=False)
    is_bl       = Column(SmallInteger, nullable=False)
    
    @classmethod
    def max_no_urut(cls, tahun):
        return DBSession.query(func.max(cls.no_urut).label('no_urut'))\
                .filter(cls.tahun_id==tahun
                ).scalar() or 0
    
    
    @classmethod
    def get_kode(cls, p):
        spd_kode = FixLength(SPD_KODE)
        
        rows = DBSession.query(func.max(cls.kode).label('kode'))
        if "tahun_id" in SPD_KODE:
            rows.filter(cls.tahun_id == p['tahun_id'])
        
        if "is_bl" in SPD_KODE:
            spd_kode['is_bl'] = p['is_bl']
            rows.filter(cls.is_bl == p['is_bl'])
        
        rows = rows.first()
        if rows and rows.kode:
            spd_kode.set_raw(rows.kode)
            spd_kode.set('no_urut', int(spd_kode.get('no_urut'))+1)

        return spd_kode.get_raw()
        #TODO: on save item calculate from other spd and kegiatan_sub
           
class SpdItem(DefaultModel, Base):
    __tablename__   = 'ap_spd_items'
    __table_args__  = {'extend_existing':True, 'schema' : 'apbd',}

    kegiatansubs    = relationship("KegiatanSub", backref="spditems")

    ap_spd_id          = Column(BigInteger, ForeignKey("apbd.ap_spds.id"),          nullable=False) 
    kegiatan_sub_id = Column(BigInteger, ForeignKey("apbd.kegiatan_subs.id"), nullable=False)
    anggaran        = Column(BigInteger, nullable=False)
    lalu            = Column(BigInteger, nullable=False)
    nominal         = Column(BigInteger, nullable=False)


class Spp(NamaModel, Base):
    __tablename__  = 'ap_spps'
    __table_args__ = {'extend_existing':True, 'schema' : 'apbd',}

    spds           = relationship("Spd", backref="spps")
    units          = relationship("Unit", backref="spps")
    
    ap_spd_id         = Column(BigInteger, ForeignKey("apbd.ap_spds.id"),   nullable=True) 
    tahun_id       = Column(BigInteger, ForeignKey("apbd.tahuns.id"), nullable=False)
    unit_id        = Column(Integer,    ForeignKey("admin.units.id"),  nullable=False) 
    no_urut        = Column(BigInteger, nullable=False)
    tanggal        = Column(Date) 
    jenis          = Column(BigInteger, nullable=False)                 
    nominal        = Column(BigInteger, nullable=False)
    ttd_uid        = Column(Integer)
    ttd_nip        = Column(String(32))
    ttd_nama       = Column(String(64))
    ttd_jab        = Column(String(64))
    ap_nama        = Column(String(64), nullable=False)
    ap_bank        = Column(String(64), nullable=False)
    ap_rekening    = Column(String(32), nullable=False)
    ap_npwp        = Column(String(32), nullable=False)
    ap_nip         = Column(String(32))
    ap_bentuk      = Column(String(64))
    ap_alamat      = Column(String(64))
    ap_pemilik     = Column(String(64))
    ap_kontrak     = Column(String(64))
    ap_waktu       = Column(String(64))
    ap_uraian      = Column(String(64))
    ap_tgl_kontrak = Column(Date)
    ap_kegiatankd  = Column(String(32))
    #PPTK
    pptk_uid       = Column(Integer)
    pptk_nama      = Column(String(64))
    pptk_nip       = Column(String(32))
    #Bendahara
    barang_uid     = Column(Integer)
    barang_nip     = Column(String(32))
    barang_nama    = Column(String(64))
    barang_jab     = Column(String(64))
    #Kasi
    kasi_uid       = Column(Integer)
    kasi_nip       = Column(String(32))
    kasi_nama      = Column(String(64))
    kasi_jab       = Column(String(64))
    verified_uid   = Column(Integer, nullable=True)

    posted         = Column(SmallInteger, default=0, nullable=False)

    @classmethod
    def max_no_urut(cls, tahun, unit_id):
        return DBSession.query(func.max(cls.no_urut).label('no_urut'))\
                .filter(cls.tahun_id==tahun,
                        cls.unit_id==unit_id
                ).scalar() or 0
    
    @classmethod
    def get_nominal(cls, p):
        return DBSession.query(func.sum(APInvoice.jml_tagihan).label('jml_tagihan')
                             ).join(SppItem,
                             ).outerjoin(cls,
                             ).filter(APInvoice.id==SppItem.ap_invoice_id, 
                                      SppItem.ap_spp_id==cls.id,
                                      cls.id==p['id']
                                      ).first()

    @classmethod
    def get_nilai(cls, ap_spp_id):
        return DBSession.query(func.sum(APInvoice.amount).label('amount')
                             ).filter(SppItem.ap_spp_id==ap_spp_id,
                                      SppItem.ap_invoice_id==APInvoice.id,                             
                                      ).first()

class SppItem(DefaultModel, Base):
    __tablename__  ='ap_spp_items'
    __table_args__ = (UniqueConstraint("ap_invoice_id", name="ap_spp_uq1"),
                        {'extend_existing':True,'schema' :'apbd'})

    spps           = relationship("Spp",       backref=backref("spps"))
    apinvoices     = relationship("APInvoice", backref=backref("apinvoices"))

    ap_spp_id      = Column(BigInteger, ForeignKey("apbd.ap_spps.id"),       nullable=False)
    ap_invoice_id  = Column(BigInteger, ForeignKey("apbd.ap_invoices.id"), nullable=False)
    

class Spm(NamaModel, Base):
    __tablename__  = 'ap_spms'
    __table_args__ = {'extend_existing':True, 'schema' : 'apbd',}
    
    spps           = relationship("Spp", backref="spms")
                   
    ap_spp_id      = Column(BigInteger,   ForeignKey("apbd.ap_spps.id"), nullable=False)
    kode           = Column(String(50),   nullable=False)
    nama           = Column(String(250),  nullable=False)
    tanggal        = Column(BigInteger,   nullable=False) 
    ttd_uid        = Column(BigInteger,   nullable=False)
    ttd_nip        = Column(String(50),   nullable=False)
    ttd_nama       = Column(String(64),   nullable=False)
    verified_uid   = Column(BigInteger,   nullable=False)
    verified_nip   = Column(String(50),   nullable=False)
    verified_nama  = Column(String(64),   nullable=False)
                   
    posted         = Column(SmallInteger, nullable=False)
    disabled       = Column(SmallInteger, nullable=False, default=1)
    @classmethod
    def max_no_urut(cls, tahun, unit_id):
        return DBSession.query(func.max(cls.no_urut).label('no_urut'))\
                .filter(cls.tahun_id==tahun,
                        cls.unit_id==unit_id
                ).scalar() or 0

class SpmPotongan(DefaultModel,Base):
    __tablename__  = 'ap_spm_potongans'
    __table_args__ = {'extend_existing':True, 'schema' : 'apbd',}
    
                   
    ap_spm_id      = Column(BigInteger,   ForeignKey("apbd.ap_spms.id"), nullable=False)
    no_urut        = Column(SmallInteger, nullable=False)
    rekening_id    = Column(Integer, ForeignKey("admin.rekenings.id"), nullable=False)
    spms           = relationship("Spm", backref=backref("spmpotongans"))
    rekenings      = relationship("Rekening", backref=backref("spmpotongans"))

    @classmethod
    def max_no_urut(cls, spm_id):
        return DBSession.query(func.max(cls.no_urut).label('no_urut'))\
                .filter(cls.tahun_id==tahun,
                        cls.unit_id==unit_id
                ).scalar() or 0
    
class Sp2d(NamaModel, Base):
    __tablename__  = 'ap_sp2ds'
    __table_args__ = {'extend_existing':True, 'schema' : 'apbd',}

    spms  = relationship("Spm", backref="sp2ds")

    ap_spm_id      = Column(BigInteger, ForeignKey("apbd.ap_spms.id"), nullable=False)
    kode           = Column(String(50), nullable=False)
    tanggal        = Column(Date) 
    bud_uid        = Column(BigInteger, nullable=False)
    bud_nip        = Column(String(50), nullable=False)
    bud_nama       = Column(String(64), nullable=False)
    verified_uid   = Column(BigInteger, nullable=False)
    verified_nip   = Column(String(50), nullable=False)
    verified_nama  = Column(String(64), nullable=False)

    posted         = Column(SmallInteger, nullable=False, default=0)
    @classmethod
    def max_no_urut(cls, tahun):
        return DBSession.query(func.max(cls.no_urut).label('no_urut'))\
                .filter(cls.tahun_id==tahun
                ).scalar() or 0

class APInvoice(NamaModel, Base):
    __tablename__  = 'ap_invoices'
    __table_args__ = {'extend_existing':True, 'schema' : 'apbd',}

    kegiatansubs   = relationship("KegiatanSub", backref="apinvoices")
    units          = relationship("Unit",        backref="apinvoices")
    tahun_id        = Column(BigInteger, ForeignKey("apbd.tahuns.id"),        nullable=False)
    unit_id         = Column(Integer,    ForeignKey("admin.units.id"),         nullable=False) 
    no_urut         = Column(Integer, nullable=False)
    tanggal         = Column(Date, nullable=False)
    
    kegiatan_sub_id = Column(BigInteger, ForeignKey("apbd.kegiatan_subs.id"), nullable=False)
    nama            = Column(String(255))
    jenis           = Column(SmallInteger, nullable=False, default=0) #1 up 2 tu 3 gu 4 LS
    ap_nomor        = Column(String(32))
    ap_nama         = Column(String(64))
    ap_tanggal      = Column(Date)
    ap_rekening     = Column(String(32))
    ap_npwp         = Column(String(16))
    amount          = Column(BigInteger, nullable=False)
                    
    disabled        = Column(SmallInteger, nullable=False, default=0)
    posted          = Column(SmallInteger, nullable=False, default=0)
    status_spp      = Column(SmallInteger, nullable=False, default=0)

    UniqueConstraint('tahun_id', 'unit_id', 'no_urut',
                name = 'invoice_ukey')

    @classmethod
    def max_no_urut(cls, tahun, unit_id):
        return DBSession.query(func.max(cls.no_urut).label('no_urut'))\
                .filter(cls.tahun_id==tahun,
                        cls.unit_id==unit_id
                ).scalar() or 0

    @classmethod
    def get_jml_tagihan(cls, p):
        return DBSession.query(func.sum(APInvoiceItem.nilai).label('nilai')
                             ).join(cls,
                             ).filter(APInvoiceItem.ap_invoice_id==cls.id,
                                      cls.id==p['id']
                                      ).first()
  
    @classmethod
    def get_nilai(cls, ap_invoice_id):
        return DBSession.query(func.sum(APInvoiceItem.amount).label('amount')
                             ).filter(APInvoiceItem.ap_invoice_id==ap_invoice_id 
                                      ).first()
                                      
class APInvoiceItem(DefaultModel, Base):
    __tablename__  = 'ap_invoice_items'
    __table_args__ = {'extend_existing':True, 'schema' : 'apbd',}
    
    kegiatanitems  =  relationship("KegiatanItem", backref="apinvoiceitems")
    apinvoices     =  relationship("APInvoice",    backref="apinvoiceitems")

    ap_invoice_id     = Column(BigInteger, ForeignKey("apbd.ap_invoices.id"),     nullable=False)
    kegiatan_item_id = Column(BigInteger, ForeignKey("apbd.kegiatan_items.id"), nullable=False)  
    no_urut          = Column(Integer) 
    nama             = Column(String(64)) 
    vol_1            = Column(BigInteger,   nullable=False, default=0)
    vol_2            = Column(BigInteger,   nullable=False, default=0)
    harga            = Column(BigInteger,   nullable=False, default=0)
    amount            = Column(BigInteger,   nullable=False, default=0)
    ppn_prsn         = Column(SmallInteger, nullable=False, default=0)
    ppn              = Column(BigInteger,   nullable=False, default=0)
    pph_prsn         = Column(SmallInteger, nullable=False, default=0)
    pph              = Column(BigInteger,   nullable=False, default=0)
    pph_id           = Column(SmallInteger) #42 #21 #22#23 #26
    notes1           = Column(String(64)) 
    notes2           = Column(String(64)) 
    notes3           = Column(String(64)) 
    
    @classmethod
    def max_no_urut(cls, ap_invoice_id):
        return DBSession.query(func.max(cls.no_urut).label('no_urut'))\
                .filter(cls.ap_invoice_id==ap_invoice_id
                ).scalar() or 0            

class Giro(NamaModel, Base):
    __tablename__  ='ap_giros'
    __table_args__ = {'extend_existing':True,'schema' :'apbd'}

    #sp2ds    = relationship("Sp2d", backref="giros")
    units    = relationship("Unit", backref="giros")

    tahun_id = Column(BigInteger, ForeignKey("apbd.tahuns.id"), nullable=False)
    unit_id  = Column(Integer,    ForeignKey("admin.units.id"),  nullable=False)
    #ap_sp2d_id  = Column(BigInteger, ForeignKey("apbd.ap_sp2ds.id"),  nullable=False)
    kode     = Column(String(50))
    nama     = Column(String(150))
    tanggal  = Column(Date,         nullable=False)
    nominal  = Column(BigInteger,   nullable=False, default=0)

    posted   = Column(SmallInteger, nullable=False, default=0)
    disabled = Column(SmallInteger, nullable=False, default=0)

    UniqueConstraint('tahun_id', 'unit_id', 'kode',
                name = 'giro_ukey')
    @classmethod
    def max_no_urut(cls, tahun, unit_id):
        return DBSession.query(func.max(cls.no_urut).label('no_urut'))\
                .filter(cls.tahun_id==tahun,
                        cls.unit_id==unit_id
                ).scalar() or 0

    @classmethod
    def get_nilai(cls, ap_giro_id):
        return DBSession.query(func.sum(Spp.nominal).label('nominal')
                             ).filter(GiroItem.ap_giro_id==ap_giro_id,
                                      GiroItem.ap_sp2d_id==Sp2d.id,
                                      Sp2d.ap_spm_id==Spm.id,
                                      Spm.ap_spp_id==Spp.id                                      
                                      ).first()
                                      
class GiroItem(DefaultModel, Base):
    __tablename__  ='ap_giro_items'
    __table_args__ = {'extend_existing':True,'schema' :'apbd'}

    sp2ds   = relationship("Sp2d", backref="giro_items")
    giros   = relationship("Giro", backref="giro_items")

    ap_giro_id = Column(BigInteger, ForeignKey("apbd.ap_giros.id"), nullable=False)
    ap_sp2d_id = Column(BigInteger, ForeignKey("apbd.ap_sp2ds.id"), nullable=False)

class ARInvoice(NamaModel, Base):
    __tablename__  ='ar_invoices'
    __table_args__ = {'extend_existing':True,'schema' :'apbd'}

    kegiatansubs   = relationship("KegiatanSub", backref="arinvoices")
    units          = relationship("Unit",        backref="arinvoices")

    tahun_id        = Column(BigInteger, ForeignKey("apbd.tahuns.id"),        nullable=False)
    unit_id         = Column(Integer,    ForeignKey("admin.units.id"),         nullable=False) 
    kegiatan_sub_id = Column(BigInteger, ForeignKey("apbd.kegiatan_subs.id"), nullable=False)
    kode            = Column(String(50))
    nama            = Column(String(255))
    nilai           = Column(BigInteger, nullable=False)
    bendahara_uid   = Column(Integer,    nullable=False)
    bendahara_nm    = Column(String(64))
    penyetor        = Column(String(64))
    alamat          = Column(String(150))
    tgl_terima      = Column(Date)    
    tgl_validasi    = Column(Date)
    posted          = Column(SmallInteger, nullable=False, default=0)
    disabled        = Column(Integer, nullable=False, default=0)

    UniqueConstraint('tahun_id', 'unit_id', 'kode',
                name = 'arinvoice_ukey')

    @classmethod
    #def get_nilai(cls, p):
    #    return DBSession.query(func.sum(ARInvoiceItem.nilai).label('nilai')
    #                         ).join(cls,
    #                         ).filter(ARInvoiceItem.arinvoice_id==cls.id, 
    #                                  cls.id==p['id']
    #                                  ).first()
    def get_nilai(cls, ar_invoice_id):
        return DBSession.query(func.sum(ARInvoiceItem.nilai).label('nilai')
                             ).filter(ARInvoiceItem.ar_invoice_id==ar_invoice_id 
                                      ).first()
                    
    @classmethod
    def max_no_urut(cls, tahun, unit_id):
        return DBSession.query(func.max(cls.no_urut).label('no_urut'))\
                .filter(cls.tahun_id==tahun,
                        cls.unit_id==unit_id
                ).scalar() or 0
                
class ARInvoiceItem(DefaultModel, Base):
    __tablename__  = 'ar_invoice_items'
    __table_args__ = {'extend_existing':True, 'schema' : 'apbd',}
    
    kegiatanitems  =  relationship("KegiatanItem", backref="arinvoiceitems")
    arinvoices     =  relationship("ARInvoice",    backref="arinvoiceitems")

    ar_invoice_id     = Column(BigInteger, ForeignKey("apbd.ar_invoices.id"),     nullable=False)
    kegiatan_item_id = Column(BigInteger, ForeignKey("apbd.kegiatan_items.id"), nullable=False)  
    no_urut          = Column(Integer) 
    nama             = Column(String(64)) 
    vol_1            = Column(BigInteger,   nullable=False, default=0)
    vol_2            = Column(BigInteger,   nullable=False, default=0)
    harga            = Column(BigInteger,   nullable=False, default=0)
    nilai            = Column(BigInteger,   nullable=False, default=0)
    notes1           = Column(String(64))  
    @classmethod
    def max_no_urut(cls, ar_invoice_id):
        return DBSession.query(func.max(cls.no_urut).label('no_urut'))\
                .filter(cls.tahun_id==tahun,
                        cls.unit_id==unit_id
                ).scalar() or 0
    
class ARInvoiceDetail(NamaModel, Base):
    __tablename__  ='ar_invoice_details'
    __table_args__ = {'extend_existing':True,'schema' :'apbd'}

    tahun_id       = Column(BigInteger, ForeignKey("apbd.tahuns.id"),    nullable=False)
    unit_id        = Column(Integer,    ForeignKey("admin.units.id"),     nullable=False) 
    rekening_id    = Column(Integer,    ForeignKey("admin.rekenings.id"), nullable=False)
    jumlah         = Column(BigInteger, nullable=False)
    tgl_ketetapan  = Column(Date)    
    units          = relationship("Unit",     backref=backref("arinvoicedetails"))
    rekenings      = relationship("Rekening", backref=backref("arinvoicedetails"))
    UniqueConstraint('tahun_id', 'unit_id', 'kode',
                name = 'ar_invoice_detail_ukey')

class Sts(NamaModel, Base):
    __tablename__  = 'ar_sts'
    __table_args__ = {'extend_existing':True, 'schema' : 'apbd',}

    units          = relationship("Unit", backref="sts")
    kegiatansubs   = relationship("KegiatanSub", backref="sts")

    tahun_id       = Column(BigInteger, ForeignKey("apbd.tahuns.id"), nullable=False)
    unit_id        = Column(Integer,    ForeignKey("admin.units.id"),  nullable=False) 
    kegiatan_sub_id = Column(BigInteger, ForeignKey("apbd.kegiatan_subs.id"), nullable=False)    

    no_urut        = Column(BigInteger, nullable=False)
    kode           = Column(String(64), nullable=False)
    nama           = Column(String(64), nullable=False)
    jenis          = Column(BigInteger, nullable=False)                 
    nominal        = Column(BigInteger, nullable=False)
    ttd_uid        = Column(Integer,    nullable=False)
    ttd_nip        = Column(String(32), nullable=False)
    ttd_nama       = Column(String(64), nullable=False)
    ttd_jab        = Column(String(64), nullable=False)
    bank_nama      = Column(String(32), nullable=False)
    bank_account   = Column(String(64), nullable=False)
    tgl_sts        = Column(Date) 
    tgl_validasi   = Column(Date)
    posted         = Column(SmallInteger, nullable=False, default=0)
    
    @classmethod
    def max_no_urut(cls, tahun, unit_id):
        return DBSession.query(func.max(cls.no_urut).label('no_urut'))\
                .filter(cls.tahun_id==tahun,
                        cls.unit_id==unit_id
                ).scalar() or 0
                
    @classmethod
    def get_nilai(cls, ar_sts_id):
        return DBSession.query(func.sum(ARInvoice.nilai).label('nominal')
                             ).filter(StsItem.ar_sts_id==ar_sts_id,
                                      StsItem.ar_invoice_id==ARInvoice.id                                     
                                      ).first()   

class StsItem(DefaultModel, Base):
    __tablename__      = 'ar_sts_items'
    __table_args__     = {'extend_existing':True,'schema' :'apbd'}

    sts                = relationship("Sts",       backref=backref("sts_items"))
    kegiatanitems      = relationship("KegiatanItem", backref="sts_items")
    ar_sts_id          = Column(BigInteger, ForeignKey("apbd.ar_sts.id"),        nullable=False)
    kegiatan_item_id   = Column(BigInteger, ForeignKey("apbd.kegiatan_items.id"), nullable=False)
    amount             = Column(BigInteger)

class AkJurnal(NamaModel, Base):
    __tablename__   = 'ak_jurnals'
    __table_args__  = {'extend_existing':True, 'schema' : 'apbd',}
                    
    tanggal         = Column(Date) 
    tgl_transaksi   = Column(Date)
    tahun_id        = Column(BigInteger,    ForeignKey("apbd.tahuns.id"), nullable=False)
    unit_id         = Column(Integer,       ForeignKey("admin.units.id"),  nullable=False)                     
    units           = relationship("Unit",  backref=backref("ak_jurnals"))
    
    #no_urut         = Column(Integer,       nullable=False)
    periode         = Column(Integer,       nullable=False)
    jv_type         = Column(SmallInteger,  nullable=False, default=0)
    source          = Column(String(10),    nullable=False)
    source_no       = Column(String(30),    nullable=False)
    tgl_source      = Column(Date)
    posted          = Column(SmallInteger,  nullable=False)
    posted_uid       = Column(Integer) 
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

class AkJurnalItem(DefaultModel, Base):
    __tablename__   ='ak_jurnal_items'
    __table_args__  = {'extend_existing':True,'schema' :'apbd'}

    ak_jurnal_id    = Column(BigInteger,  ForeignKey("apbd.ak_jurnals.id"),      nullable=False)
    ak_jurnals      = relationship("AkJurnal", backref="ak_jurnal_items")

    kegiatan_sub_id = Column(BigInteger,  ForeignKey("apbd.kegiatan_subs.id"), nullable=False)
    kegiatan_subs   = relationship("KegiatanSub", backref="ak_jurnal_items")

    rekening_id     = Column(BigInteger,  ForeignKey("admin.rekenings.id"),     nullable=False)
    rekenings       = relationship("Rekening",    backref="ak_jurnal_items")

    #rate            = Column(BigInteger,  default=1)
    #items           = Column(BigInteger,  default=1) 
    #debet           = Column(BigInteger)
    #kredit          = Column(BigInteger)
    amount          = Column(BigInteger,  default=0) 
    notes           = Column(String(225), nullable=True)
