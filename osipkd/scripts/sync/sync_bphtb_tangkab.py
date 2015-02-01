#!/usr/bin/python

from base import *

from sync_osipkd import ARInvoice, ARPayment, Rekening, Unit

class BphtbBank(bphtb_Base, base):
  __tablename__ ='bphtb_bank'
  __table_args__ = {'extend_existing':True,
         'schema' :'bphtb','autoload':True}
  
  @classmethod
  def query(cls):
      return bphtb_Session.query(cls)
  
  @classmethod
  def get_by_kode(cls,kode):
      return cls.query().filter_by(kode=kode).first()
  
  @classmethod
  def import_data(cls):
    tanggal = datetime.now()
    tahun   = tanggal.year
    rows = cls.query().filter_by(tanggal=datetime.date(tanggal)).all()
    rekening = Rekening.get_by_kode(bphtb['rekening_kd'])
    i = 0
    for row in rows:
      odata = ARPayment.get_by_ref_kode(row.tahun,''.join([row.transno,'/',str(row.seq)]))
      if not odata:
          odata = ARPayment()
          odata.unit_id         = Unit.get_by_kode(bphtb['unit_kd'])
          odata.kode            = rekening.kode
          odata.disabled        = 0
          odata.created         = tanggal
          odata.create_uid      = 1
          odata.nama            = 'Setoran BPHTB WP'
          odata.tahun           = row.tahun
          odata.amount          = row.bayar
          odata.unit_id         = Unit.get_by_kode(bphtb['unit_kd']).id
          odata.rekening_id     = Rekening.get_by_kode(bphtb['rekening_kd']).id
          odata.ref_kode        = '%s/%s' % (row.transno,row.seq)
          odata.ref_nama        = row.wpnama
          odata.tanggal         = row.tanggal
          odata.sumber_data     = 'BPHTB'
          odata.sumber_id       = 3
          odata.posted          = 0
          osipkd_Session.add(odata)
          osipkd_Session.flush()

          #odata.updated         =
          #odata.update_uid      =
      i += 1
      if i/100 == i/100.0:
        print 'Commit ', i
        osipkd_Session.commit()
          
    osipkd_Session.commit()
    
if __name__ == '__main__':
  BphtbBank.import_data()
