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
    tanggal = datetime.strptime('2014-09-21','%Y-%m-%d') #datetime.now()
    tahun   = tanggal.year
    rows = cls.query().filter_by(tanggal=datetime.date(tanggal)).all()
    rekening = Rekening.get_by_kode(bphtb['rekening_kd'])
    for row in rows:
      odata = ARPayment.get_by_ref_kode(row.tahun,row.transno)
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
          odata.ref_kode        = row.transno
          odata.ref_nama        = row.wpnama
          odata.tanggal         = row.tanggal
          odata.sumber_data     = 'BPHTB'
          odata.sumber_id       = 2
          odata.posted          = 0
          osipkd_Session.add(odata)
          osipkd_Session.flush()

          #odata.updated         =
          #odata.update_uid      =
    osipkd_Session.commit()
      
if __name__ == '__main__':
  BphtbBank.import_data()