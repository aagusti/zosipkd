import os
import unittest
import os.path
import uuid
import urlparse
import sqlalchemy

from osipkd.tools import row2dict, xls_reader

from datetime import datetime
#from sqlalchemy import not_, func, case
from sqlalchemy import *
from sqlalchemy.orm import aliased
from sqlalchemy.sql.expression import literal_column
from pyramid.view import (view_config,)
from pyramid.httpexceptions import ( HTTPFound, )
import colander
from deform import (Form, widget, ValidationFailure, )
from osipkd.models import DBSession
from osipkd.models.apbd_anggaran import Kegiatan, KegiatanSub, KegiatanItem
    
from datatables import ColumnDT, DataTables
from osipkd.views.base_view import BaseViews

from pyjasper import (JasperGenerator)
from pyjasper import (JasperGeneratorWithSubreport)
import xml.etree.ElementTree as ET
from pyramid.path import AssetResolver

from osipkd.models.base_model import *
from osipkd.models.pemda_model import *
from osipkd.models.apbd import * 
from osipkd.models.apbd_anggaran import * 
from osipkd.models.apbd_tu import *
from datetime import datetime

"""import unittest
import os.path
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPForbidden
from pyramid.httpexceptions import HTTPNotFound
from pyramid.view import view_config
from pyramid.security import remember
from pyramid.security import forget
from pyramid.security import has_permission
from sqlalchemy import *
from sqlalchemy import distinct
from sqlalchemy.sql.functions import concat
from sqlalchemy.exc import DBAPIError
from osipkd.views.views import *
from osipkd.models.model_base import *
from osipkd.models.apbd_rka_models import *
from osipkd.models.apbd_admin_models import (TahunModel, UserApbdModel,Unit,
     Urusan, RekeningModel, ProgramModel, KegiatanModel)
from osipkd.models.apbd_tu_models import *
from datetime import datetime
import os
from pyramid.renderers import render_to_response

from anggaran import AnggaranBaseViews
from pyjasper import (JasperGenerator)
from pyjasper import (JasperGeneratorWithSubreport)
import xml.etree.ElementTree as ET
from pyramid.path import AssetResolver
"""

def get_rpath(filename):
    a = AssetResolver('osipkd')
    resolver = a.resolve(''.join(['reports/',filename]))
    return resolver.abspath()
    
angka = {1:'satu',2:'dua',3:'tiga',4:'empat',5:'lima',6:'enam',7:'tujuh',\
         8:'delapan',9:'sembilan'}
b = ' puluh '
c = ' ratus '
d = ' ribu '
e = ' juta '
f = ' milyar '
g = ' triliun '
def Terbilang(x):   
    y = str(x)         
    n = len(y)        
    if n <= 3 :        
        if n == 1 :   
            if y == '0' :   
                return ''   
            else :         
                return angka[int(y)]   
        elif n == 2 :
            if y[0] == '1' :                
                if y[1] == '1' :
                    return 'sebelas'
                elif y[0] == '0':
                    x = y[1]
                    return Terbilang(x)
                elif y[1] == '0' :
                    return 'sepuluh'
                else :
                    return angka[int(y[1])] + ' belas'
            elif y[0] == '0' :
                x = y[1]
                return Terbilang(x)
            else :
                x = y[1]
                return angka[int(y[0])] + b + Terbilang(x)
        else :
            if y[0] == '1' :
                x = y[1:]
                return 'seratus ' + Terbilang(x)
            elif y[0] == '0' : 
                x = y[1:]
                return Terbilang(x)
            else :
                x = y[1:]
                return angka[int(y[0])] + c + Terbilang(x)
    elif 3< n <=6 :
        p = y[-3:]
        q = y[:-3]
        if q == '1' :
            return 'seribu' + Terbilang(p)
        elif q == '000' :
            return Terbilang(p)
        else:
            return Terbilang(q) + d + Terbilang(p)
    elif 6 < n <= 9 :
        r = y[-6:]
        s = y[:-6]
        return Terbilang(s) + e + Terbilang(r)
    elif 9 < n <= 12 :
        t = y[-9:]
        u = y[:-9]
        if t == '000000000' :
            return  Terbilang(u) + f
        else:
            return Terbilang(u) + f + Terbilang(t)
    else:
        v = y[-12:]
        w = y[:-12]
        return Terbilang(w) + g + Terbilang(v)

class ViewTUSKPDLap(BaseViews):
    def __init__(self, context, request):
        global customer
        global logo
        BaseViews.__init__(self, context, request)
        self.app = 'tuskpd'

        #if 'app' in request.params and request.params['app'] == self.app and self.logged:
        row = DBSession.query(Tahun.status_apbd).filter(Tahun.tahun==self.tahun).first()
        self.session['status_apbd'] = row and row[0] or 0

        self.status_apbd =  'status_apbd' in self.session and self.session['status_apbd'] or 0        
        #self.status_apbd_nm =  status_apbd[str(self.status_apbd)]        
        
        self.all_unit =  'all_unit' in self.session and self.session['all_unit'] or 0        
        self.unit_id  = 'unit_id' in self.session and self.session['unit_id'] or 0
        self.unit_kd  = 'unit_kd' in self.session and self.session['unit_kd'] or "X.XX.XX"
        self.unit_nm  = 'unit_nm' in self.session and self.session['unit_nm'] or "Pilih Unit"
        self.keg_id  = 'keg_id' in self.session and self.session['keg_id'] or 0
        
        self.datas['status_apbd'] = self.status_apbd 
        #self.datas['status_apbd_nm'] = self.status_apbd_nm
        self.datas['all_unit'] = self.all_unit
        self.datas['unit_kd'] = self.unit_kd
        self.datas['unit_nm'] = self.unit_nm
        self.datas['unit_id'] = self.unit_id

        self.cust_nm = 'cust_nm' in self.session and self.session['cust_nm'] or ''
        customer = self.cust_nm
        ##o = "http://"+str(urlparse.urlparse(self.request.url).netloc)
        logo = self.request.static_url('osipkd:static/img/logo.png')
        print "KKKKKKKKKKKKKKKKKKKKKKKKKKKKK", logo
        
    # PENDAPATAN
    @view_config(route_name="ar-report-skpd", renderer="templates/report-skpd/pendapatan.pt", permission="read")
    def ar_report_skpd(self):
        params = self.request.params
        return dict(datas=self.datas,)

    @view_config(route_name="ar-report-skpd-act", renderer="json", permission="read")
    def ar_report_skpd_act(self):
        req    = self.request
        params = req.params
        url_dict = req.matchdict

        tipe = 'tipe' in params and params['tipe'] and int(params['tipe']) or 0
        mulai = 'mulai' in params and params['mulai'] or 0
        selesai = 'selesai' in params and params['selesai'] or 0
        
        ### LAPORAN INVOICE
        if url_dict['act']=='1' :
            query = DBSession.query(ARInvoice.tahun_id.label('tahun'), Unit.nama.label('unit_nm'),
                  ARInvoice.kode, ARInvoice.tgl_terima, ARInvoice.tgl_validasi, ARInvoice.penyetor, ARInvoice.nama.label('uraian'), 
                  Rekening.kode.label('rek_kd'), Rekening.nama.label('rek_nm'), ARInvoiceItem.nilai.label('jumlah'
                  )).filter(ARInvoice.unit_id==Unit.id, ARInvoiceItem.kegiatan_item_id==KegiatanItem.id,
                  KegiatanItem.rekening_id==Rekening.id,
                  ARInvoiceItem.ar_invoice_id==ARInvoice.id, ARInvoice.unit_id==self.session['unit_id'],
                  ARInvoice.tahun_id==self.session['tahun'],  
                  ARInvoice.tgl_terima.between(mulai,selesai)
                  ).order_by(ARInvoice.tgl_terima)

            generator = b101r001Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
           
        # INVOICE
        elif url_dict['act']=='arinvoice' :
            pk_id = 'id' in params and params['id'] and int(params['id']) or 0
            query = DBSession.query(ARInvoice.tahun_id.label('tahun'), Unit.nama.label('unit_nm'), Unit.alamat.label('unit_alamat'),
                  ARInvoice.id.label('arinvoice_id'), ARInvoice.kode, ARInvoice.nama.label('arinvoice_nm'), 
                  ARInvoice.tgl_terima, ARInvoice.tgl_validasi, ARInvoice.bendahara_nm, ARInvoice.bendahara_nip, 
                  ARInvoice.penyetor, ARInvoice.alamat, KegiatanSub.nama.label('kegiatan_nm'),
                  func.sum(ARInvoiceItem.nilai).label('nilai')
                  ).filter(ARInvoice.unit_id==Unit.id, ARInvoice.kegiatan_sub_id==KegiatanSub.id,
                  ARInvoiceItem.ar_invoice_id==ARInvoice.id, ARInvoice.unit_id==self.session['unit_id'],
                  ARInvoice.tahun_id==self.session['tahun'], ARInvoice.id==pk_id
                  ).group_by(ARInvoice.tahun_id, Unit.nama, Unit.alamat,
                  ARInvoice.id, ARInvoice.kode, ARInvoice.nama, 
                  ARInvoice.tgl_terima, ARInvoice.tgl_validasi, ARInvoice.bendahara_nm, ARInvoice.bendahara_nip, 
                  ARInvoice.penyetor, ARInvoice.alamat, KegiatanSub.nama
                  )
            generator = b102r002Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
          
        # TBP
        elif url_dict['act']=='ap-tbp' :
            print "TTTTTTTTTTTTTTTTTTTTTTTT"
            pk_id = 'id' in params and params['id'] and int(params['id']) or 0
            query = DBSession.query(ARPaymentItem
                  ).filter(ARPaymentItem.unit_id==Unit.id, ARPaymentItem.unit_id==self.session['unit_id'],
                  ARPaymentItem.tahun==self.session['tahun'], ARPaymentItem.tanggal==mulai
                  )
            generator = b102r004Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
          
        ### AR PAYMENT
        elif url_dict['act']=='ar-sts' :
            pk_id = 'id' in params and params['id'] and int(params['id']) or 0
            query = DBSession.query(Sts
                ).join(StsItem).join(KegiatanItem).join(Rekening
                ).filter(Sts.unit_id==Unit.id, 
                Sts.unit_id==self.session['unit_id'],
                Sts.tahun_id==self.session['tahun'], Sts.id==pk_id
                )
            generator = b102r003Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
    
        ### LAPORAN STS
        if url_dict['act']=='2' :
            if tipe==0 :
               query = DBSession.query(Sts.tahun_id.label('tahun'), Unit.kode.label('unit_kd'),Unit.nama.label('unit_nm'),
                  Sts.kode, Sts.tgl_sts, Sts.tgl_validasi, Sts.jenis, Sts.nama.label('uraian'), 
                  Sts.nominal, literal_column('0').label('tipe')
                  ).filter(Sts.unit_id==Unit.id, 
                  Sts.unit_id==self.session['unit_id'],
                  Sts.tahun_id==self.session['tahun'],  
                  Sts.tgl_sts.between(mulai,selesai)
                  ).order_by(Sts.tgl_sts)
            elif tipe==1 :
               query = DBSession.query(Sts.tahun_id.label('tahun'), Unit.kode.label('unit_kd'),Unit.nama.label('unit_nm'),
                  Sts.kode, Sts.tgl_sts, Sts.tgl_validasi, Sts.jenis, Sts.nama.label('uraian'), 
                  Sts.nominal, literal_column('1').label('tipe')
                  ).filter(Sts.unit_id==Unit.id, 
                  #Sts.jenis==1,
                  Sts.jenis.in_([1,2,3]),
                  Sts.unit_id==self.session['unit_id'],
                  Sts.tahun_id==self.session['tahun'],  
                  Sts.tgl_sts.between(mulai,selesai)
                  ).order_by(Sts.tgl_sts)
            elif tipe==2 :
               query = DBSession.query(Sts.tahun_id.label('tahun'), Unit.kode.label('unit_kd'),Unit.nama.label('unit_nm'),
                  Sts.kode, Sts.tgl_sts, Sts.tgl_validasi, Sts.jenis, Sts.nama.label('uraian'), 
                  Sts.nominal, literal_column('2').label('tipe')
                  ).filter(Sts.unit_id==Unit.id, Sts.jenis==4, 
                  Sts.unit_id==self.session['unit_id'],
                  Sts.tahun_id==self.session['tahun'],  
                  Sts.tgl_sts.between(mulai,selesai)
                  ).order_by(Sts.tgl_sts)
            elif tipe==3 :
               query = DBSession.query(Sts.tahun_id.label('tahun'), Unit.kode.label('unit_kd'),Unit.nama.label('unit_nm'),
                  Sts.kode, Sts.tgl_sts, Sts.tgl_validasi, Sts.jenis, Sts.nama.label('uraian'), 
                  Sts.nominal, literal_column('3').label('tipe')
                  ).filter(Sts.unit_id==Unit.id, Sts.jenis==5, 
                  Sts.unit_id==self.session['unit_id'],
                  Sts.tahun_id==self.session['tahun'],  
                  Sts.tgl_sts.between(mulai,selesai)
                  ).order_by(Sts.tgl_sts)

            generator = b101r002Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
           
    # BELANJA
    @view_config(route_name="ap-report-skpd", renderer="templates/report-skpd/belanja.pt", permission="read")
    def ap_report_skpd(self):
        params = self.request.params
        return dict(datas=self.datas,)

    @view_config(route_name="ap-report-skpd-act", renderer="json", permission="read")
    def ap_report_skpd_act(self):
        global bulan
        global pptk_nm
        global pptk_nip
        global kpa_nm
        global kpa_nip
        global bend_nm
        global bend_nip
        global japbd
        global pa_nama
        global pa_nip
        global benda_nama
        global benda_nip
        req    = self.request
        params = req.params
        url_dict = req.matchdict

        tipe = 'tipe' in params and params['tipe'] and int(params['tipe']) or 0
        mulai = 'mulai' in params and params['mulai'] or 0
        selesai = 'selesai' in params and params['selesai'] or 0
        pptk_nm = 'nama' in params and params['nama'] or ''
        pptk_nip = 'nip' in params and params['nip'] or ''
        kpa_nm = 'kpa_nm' in params and params['kpa_nm'] or ''
        kpa_nip = 'kpa_nip' in params and params['kpa_nip'] or ''
        bend_nm = 'bend_nm' in params and params['bend_nm'] or ''
        bend_nip = 'bend_nip' in params and params['bend_nip'] or ''
        
        ### LAPORAN AP INVOICE
        if url_dict['act']=='1' :
            if tipe==0 :
                query = DBSession.query(APInvoice.tahun_id.label('tahun'), Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'),
                  APInvoice.tanggal.label('tgl_invoice'),
                  case([(APInvoice.jenis==1,"UP"),(APInvoice.jenis==2,"TU"),(APInvoice.jenis==3,"GU"),
                  (APInvoice.jenis==4,"LS")], else_="").label('jenis'),
                  APInvoice.kode.label('invoice_kd'), KegiatanSub.nama.label('kegiatan_nm'), 
                  Rekening.kode.label('rek_kd'),Rekening.nama.label('rek_nm'), 
                  func.sum(APInvoiceItem.amount).label('jumlah')
                  ).filter(APInvoice.unit_id==Unit.id, APInvoice.kegiatan_sub_id==KegiatanSub.id,
                  APInvoice.id==APInvoiceItem.ap_invoice_id, APInvoiceItem.kegiatan_item_id==KegiatanItem.id,
                  KegiatanItem.rekening_id==Rekening.id, APInvoice.unit_id==self.session['unit_id'],
                  APInvoice.tahun_id==self.session['tahun'],  
                  APInvoice.tanggal.between(mulai,selesai)
                  ).group_by(APInvoice.tahun_id, Unit.kode, Unit.nama,
                  APInvoice.tanggal,
                  case([(APInvoice.jenis==1,"UP"),(APInvoice.jenis==2,"TU"),(APInvoice.jenis==3,"GU"),
                  (APInvoice.jenis==4,"LS")], else_=""),
                  APInvoice.kode, KegiatanSub.nama, 
                  Rekening.kode,Rekening.nama
                  ).order_by(APInvoice.tanggal).all()
            else:
                query = DBSession.query(APInvoice.tahun_id.label('tahun'), Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'),
                  APInvoice.tanggal.label('tgl_invoice'),
                  case([(APInvoice.jenis==1,"UP"),(APInvoice.jenis==2,"TU"),(APInvoice.jenis==3,"GU"),
                  (APInvoice.jenis==4,"LS")], else_="").label('jenis'),
                  APInvoice.kode.label('invoice_kd'), KegiatanSub.nama.label('kegiatan_nm'), 
                  Rekening.kode.label('rek_kd'),Rekening.nama.label('rek_nm'), 
                  func.sum(APInvoiceItem.amount).label('jumlah')
                  ).filter(APInvoice.unit_id==Unit.id, APInvoice.kegiatan_sub_id==KegiatanSub.id,
                  APInvoice.id==APInvoiceItem.ap_invoice_id, APInvoiceItem.kegiatan_item_id==KegiatanItem.id,
                  KegiatanItem.rekening_id==Rekening.id, APInvoice.unit_id==self.session['unit_id'],
                  APInvoice.tahun_id==self.session['tahun'], APInvoice.jenis==tipe, 
                  APInvoice.tanggal.between(mulai,selesai)
                  ).group_by(APInvoice.tahun_id, Unit.kode, Unit.nama,
                  APInvoice.tanggal,
                  case([(APInvoice.jenis==1,"UP"),(APInvoice.jenis==2,"TU"),(APInvoice.jenis==3,"GU"),
                  (APInvoice.jenis==4,"LS")], else_=""),
                  APInvoice.kode, KegiatanSub.nama, 
                  Rekening.kode,Rekening.nama
                  ).order_by(APInvoice.tanggal).all()

            generator = b104r000Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        ### AP INVOICE
        elif url_dict['act']=='apinvoice' :
            pk_id = 'id' in params and params['id'] and int(params['id']) or 0
            query = DBSession.query(APInvoice.tahun_id.label('tahun'), Unit.kode.label('unit_kd'), 
                  Unit.id.label('unit_id'), Unit.nama.label('unit_nm'), Unit.alamat,
                  case([(APInvoice.jenis==1,"UP"),(APInvoice.jenis==2,"TU"),(APInvoice.jenis==3,"GU"),
                  (APInvoice.jenis==4,"LS"),(APInvoice.jenis==5,"SP2B")], else_="").label('jenis'),
                  APInvoice.id.label('invoice_id'), APInvoice.nama.label('invoice_nm'), 
                  APInvoice.tanggal.label('tgl_invoice'),APInvoice.kode, APInvoice.ap_nama, 
                  APInvoice.ap_rekening, APInvoice.ap_npwp, Kegiatan.kode.label('kegiatan_kd'), 
                  KegiatanSub.nama.label('kegiatan_nm'),
                  Program.kode.label('program_kd'), Program.nama.label('program_nm'),
                  APInvoice.amount.label('nilai')
                  ).filter(APInvoice.unit_id==Unit.id, APInvoice.kegiatan_sub_id==KegiatanSub.id,
                  KegiatanSub.kegiatan_id==Kegiatan.id, Kegiatan.program_id==Program.id,
                  APInvoice.unit_id==self.session['unit_id'],
                  APInvoice.tahun_id==self.session['tahun'], APInvoice.id==pk_id
                  )
            generator = b103r001Generator()  
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
            
        ### AP PAYMENT
        elif url_dict['act']=='appayment' :
            pk_id = 'id' in params and params['id'] and int(params['id']) or 0
            query = DBSession.query(APPayment.tahun_id.label('tahun'), Unit.nama.label('unit_nm'), Unit.alamat,
                  case([(APPayment.jenis==1,"UP"),(APPayment.jenis==2,"TU"),(APPayment.jenis==3,"GU"),
                  (APPayment.jenis==4,"LS")], else_="").label('jenis'),
                  APPayment.id.label('appayment_id'), APPayment.nama.label('appayment_nm'), 
                  APPayment.tanggal.label('tgl_payment'),APPayment.kode, APPayment.ap_nama, 
                  APPayment.ap_rekening, APPayment.ap_npwp, KegiatanSub.nama.label('kegiatan_nm'),
                  APPayment.amount.label('nilai')
                  ).filter(APPayment.unit_id==Unit.id, APPayment.kegiatan_sub_id==KegiatanSub.id,
                  APPayment.unit_id==self.session['unit_id'],
                  APPayment.tahun_id==self.session['tahun'], APPayment.id==pk_id
                  )
            generator = b103r004Generator()  
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
            
        ### LAPORAN SPP 1
        elif url_dict['act']=='21' :
            if tipe ==0 :
                query = DBSession.query(Spp.tahun_id.label('tahun'), Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'),
                  case([(Spp.jenis==1,"UP"),(Spp.jenis==2,"TU"),(Spp.jenis==3,"GU"),(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)=='5.1.1'),"LS-GJ"),(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)!='5.1.1'),"LS")], else_="").label('jenis'),
                  Spp.kode.label('spp_kd'), Spp.nama.label('spp_nm'), Spp.tanggal.label('tgl_spp'),
                  Spm.kode.label('spm_kd'), Spm.tanggal.label('tgl_spm'),
                  Sp2d.kode.label('sp2d_kd'), Sp2d.tanggal.label('tgl_sp2d'), 
                  #Kegiatan.kode.label('keg_kd'),
                  func.sum(APInvoiceItem.amount).label('nominal')
                  ).filter(SppItem.ap_spp_id==Spp.id, SppItem.ap_invoice_id==APInvoice.id,
                  APInvoiceItem.ap_invoice_id==APInvoice.id, APInvoiceItem.kegiatan_item_id==KegiatanItem.id,
                  KegiatanItem.rekening_id==Rekening.id, 
                  #KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                  #KegiatanSub.kegiatan_id==Kegiatan.id,
                  Spp.unit_id==Unit.id, Spp.unit_id==self.session['unit_id'],
                  Spp.tahun_id==self.session['tahun'],
                  Spp.tanggal.between(mulai,selesai)        
                  ).outerjoin(Spm,Spm.ap_spp_id==Spp.id
                  ).outerjoin(Sp2d,Sp2d.ap_spm_id==Spm.id
                  ).group_by(Spp.tahun_id, Unit.kode, Unit.nama,
                  case([(Spp.jenis==1,"UP"),(Spp.jenis==2,"TU"),(Spp.jenis==3,"GU"),(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)=='5.1.1'),"LS-GJ"),(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)!='5.1.1'),"LS")], else_=""),
                  Spp.kode, Spp.nama, Spp.tanggal,
                  Spm.kode, Spm.tanggal,
                  Sp2d.kode, Sp2d.tanggal
                  #, Kegiatan.kode
                  ).order_by(Spp.tanggal).all()
            else:
                query = DBSession.query(Spp.tahun_id.label('tahun'), Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'),
                  case([(Spp.jenis==1,"UP"),(Spp.jenis==2,"TU"),(Spp.jenis==3,"GU"),(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)=='5.1.1'),"LS-GJ"),(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)!='5.1.1'),"LS")], else_="").label('jenis'),
                  Spp.kode.label('spp_kd'), Spp.nama.label('spp_nm'), Spp.tanggal.label('tgl_spp'),
                  Spm.kode.label('spm_kd'), Spm.tanggal.label('tgl_spm'),
                  Sp2d.kode.label('sp2d_kd'), Sp2d.tanggal.label('tgl_sp2d'), 
                  #Kegiatan.kode.label('keg_kd'),
                  func.sum(APInvoiceItem.amount).label('nominal')
                  ).filter(SppItem.ap_spp_id==Spp.id, SppItem.ap_invoice_id==APInvoice.id,
                  APInvoiceItem.ap_invoice_id==APInvoice.id, APInvoiceItem.kegiatan_item_id==KegiatanItem.id,
                  KegiatanItem.rekening_id==Rekening.id, 
                  #KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                  #KegiatanSub.kegiatan_id==Kegiatan.id,
                  Spp.unit_id==Unit.id, Spp.unit_id==self.session['unit_id'],
                  Spp.tahun_id==self.session['tahun'], Spp.jenis==tipe, 
                  Spp.tanggal.between(mulai,selesai)
                  ).outerjoin(Spm,Spm.ap_spp_id==Spp.id
                  ).outerjoin(Sp2d,Sp2d.ap_spm_id==Spm.id
                  ).group_by(Spp.tahun_id, Unit.kode, Unit.nama,
                  case([(Spp.jenis==1,"UP"),(Spp.jenis==2,"TU"),(Spp.jenis==3,"GU"),(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)=='5.1.1'),"LS-GJ"),(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)!='5.1.1'),"LS")], else_=""),
                  Spp.kode, Spp.nama, Spp.tanggal,
                  Spm.kode, Spm.tanggal,
                  Sp2d.kode, Sp2d.tanggal
                  #, Kegiatan.kode
                  ).order_by(Spp.tanggal).all()
                  
            generator = b104r1001Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
            
        ### LAPORAN SPP 2
        elif url_dict['act']=='22' :
            if tipe ==0 :
                query = DBSession.query(Spp.tahun_id.label('tahun'), Unit.kode.label('unit_kd'),
                  Unit.nama.label('unit_nm'), Spp.tanggal.label('tgl_spp'), 
                  Spp.kode.label('spp_kd'), Spp.nama.label('spp_nm'), 
                  case([(Spp.jenis==1,"UP"),(Spp.jenis==2,"TU"),(Spp.jenis==3,"GU"),(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)=='5.1.1'),"LS-GJ"),(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)!='5.1.1'),"LS")], else_="").label('jenis'),
                  func.sum(case([(Spp.jenis==1,APInvoiceItem.amount)], else_=0)).label('UP'),
                  func.sum(case([(Spp.jenis==2,APInvoiceItem.amount)], else_=0)).label('TU'),
                  func.sum(case([(Spp.jenis==3,APInvoiceItem.amount)], else_=0)).label('GU'),
                  func.sum(case([(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)=='5.1.1'),APInvoiceItem.amount)], else_=0)).label('LS_GJ'),
                  func.sum(case([(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)!='5.1.1'),APInvoiceItem.amount)], else_=0)).label('LS')
                  ).filter(SppItem.ap_spp_id==Spp.id, SppItem.ap_invoice_id==APInvoice.id,
                  APInvoiceItem.ap_invoice_id==APInvoice.id, APInvoiceItem.kegiatan_item_id==KegiatanItem.id,
                  KegiatanItem.rekening_id==Rekening.id,
                  #, KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                  #KegiatanSub.kegiatan_id==Kegiatan.id,
                  Spp.unit_id==Unit.id, Spp.unit_id==self.session['unit_id'],
                  Spp.tahun_id==self.session['tahun'], 
                  Spp.tanggal.between(mulai,selesai)        
                  ).group_by(Spp.tahun_id, Unit.kode, Unit.nama, Spp.tanggal, Spp.kode, Spp.nama,
                  case([(Spp.jenis==1,"UP"),(Spp.jenis==2,"TU"),(Spp.jenis==3,"GU"),(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)=='5.1.1'),"LS-GJ"),(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)!='5.1.1'),"LS")], else_=""),
                  ).order_by(Spp.tanggal).all()
            else:
                query = DBSession.query(Spp.tahun_id.label('tahun'), Unit.kode.label('unit_kd'),
                  Unit.nama.label('unit_nm'), Spp.tanggal.label('tgl_spp'), 
                  Spp.kode.label('spp_kd'), Spp.nama.label('spp_nm'),
                  case([(Spp.jenis==1,"UP"),(Spp.jenis==2,"TU"),(Spp.jenis==3,"GU"),(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)=='5.1.1'),"LS-GJ"),(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)!='5.1.1'),"LS")], else_="").label('jenis'),
                  func.sum(case([(Spp.jenis==1,APInvoiceItem.amount)], else_=0)).label('UP'),
                  func.sum(case([(Spp.jenis==2,APInvoiceItem.amount)], else_=0)).label('TU'),
                  func.sum(case([(Spp.jenis==3,APInvoiceItem.amount)], else_=0)).label('GU'),
                  func.sum(case([(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)=='5.1.1'),APInvoiceItem.amount)], else_=0)).label('LS_GJ'),
                  func.sum(case([(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)!='5.1.1'),APInvoiceItem.amount)], else_=0)).label('LS')
                  ).filter(SppItem.ap_spp_id==Spp.id, SppItem.ap_invoice_id==APInvoice.id,
                  APInvoiceItem.ap_invoice_id==APInvoice.id, APInvoiceItem.kegiatan_item_id==KegiatanItem.id,
                  KegiatanItem.rekening_id==Rekening.id, 
                  #KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                  #KegiatanSub.kegiatan_id==Kegiatan.id,
                  Spp.unit_id==Unit.id, Spp.unit_id==self.session['unit_id'],
                  Spp.tahun_id==self.session['tahun'], Spp.jenis==tipe, 
                  Spp.tanggal.between(mulai,selesai)        
                  ).group_by(Spp.tahun_id, Unit.kode, Unit.nama, Spp.tanggal, 
                  Spp.kode, Spp.nama,
                  case([(Spp.jenis==1,"UP"),(Spp.jenis==2,"TU"),(Spp.jenis==3,"GU"),(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)=='5.1.1'),"LS-GJ"),(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)!='5.1.1'),"LS")], else_=""),
                  ).order_by(Spp.tanggal).all()
                  
            generator = b104r1002Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        ### SPP Pengantar UP/TU/GU-LSB
        elif url_dict['act']=='spp11' :
            pk_id = 'id' in params and params['id'] and int(params['id']) or 0
            query = DBSession.query(Spp.tahun_id.label('tahun'), Urusan.nama.label('urusan_nm'), 
                     Unit.id.label('unit_id'),Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'), 
                     Tahun.no_perkdh, Tahun.tgl_perkdh, 
                     Spp.id.label('spp_id'),Spp.kode.label('spp_kd'), Spp.nama.label('spp_nm'), 
                     Spp.tanggal.label('spp_tgl'), Spp.ttd_nip, Spp.ttd_nama, Spp.ttd_jab, Spp.jenis, 
                     Spp.pptk_nip, Spp.pptk_nama, Spp.ap_nama, Spp.ap_bank, Spp.ap_rekening, APInvoice.kegiatan_sub_id,
                     case([(func.substr(Rekening.kode,1,5)=='5.1.1','-GJ')], else_="").label('kode'),
                     #func.substr(Rekening.kode,1,5).label('kode'),
                     func.sum(APInvoiceItem.amount).label('nominal')
                     ).filter(Spp.unit_id==Unit.id, Tahun.id==Spp.tahun_id, Urusan.id==Unit.urusan_id,
                     SppItem.ap_spp_id==Spp.id, SppItem.ap_invoice_id==APInvoice.id, 
                     APInvoice.id==APInvoiceItem.ap_invoice_id, 
                     APInvoiceItem.kegiatan_item_id==KegiatanItem.id,
                     Rekening.id==KegiatanItem.rekening_id, 
                     Spp.unit_id==self.session['unit_id'], Spp.tahun_id==self.session['tahun'], Spp.id==pk_id
                     ).group_by(Spp.tahun_id, Urusan.nama, Unit.id,Unit.kode, Unit.nama, 
                     Tahun.no_perkdh, Tahun.tgl_perkdh, Spp.id,Spp.kode, Spp.nama, 
                     Spp.tanggal, Spp.ttd_nip, Spp.ttd_nama, Spp.ttd_jab, Spp.jenis, 
                     Spp.pptk_nip, Spp.pptk_nama, Spp.ap_nama, Spp.ap_bank, Spp.ap_rekening, APInvoice.kegiatan_sub_id, 
                     case([(func.substr(Rekening.kode,1,5)=='5.1.1','-GJ')], else_="")
                     #func.substr(Rekening.kode,1,5)
                     )                         
            generator = b103r021Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        ### SPP Pengantar LSG
        elif url_dict['act']=='spp21' :
            pk_id = 'id' in params and params['id'] and int(params['id']) or 0
            query = DBSession.query(Spp.tahun_id.label('tahun'), Urusan.nama.label('urusan_nm'), 
                     Unit.id.label('unit_id'),Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'), 
                     Tahun.no_perkdh, Tahun.tgl_perkdh, 
                     Spp.id.label('spp_id'),Spp.kode.label('spp_kd'), Spp.nama.label('spp_nm'), 
                     Spp.tanggal.label('spp_tgl'), Spp.ttd_nip, Spp.ttd_nama, Spp.ttd_jab, Spp.jenis, 
                     Spp.pptk_nip, Spp.pptk_nama, Spp.ap_nama, Spp.ap_bank, Spp.ap_rekening, 
                     case([(func.substr(Rekening.kode,1,5)=='5.1.1','-GJ')], else_="").label('kode'),
                     #func.substr(Rekening.kode,1,5).label('kode'),
                     func.sum(APInvoiceItem.amount).label('nominal')
                     ).filter(Spp.unit_id==Unit.id, Tahun.id==Spp.tahun_id, Urusan.id==Unit.urusan_id,
                     SppItem.ap_spp_id==Spp.id, SppItem.ap_invoice_id==APInvoiceItem.ap_invoice_id, 
                     APInvoiceItem.kegiatan_item_id==KegiatanItem.id,
                     Rekening.id==KegiatanItem.rekening_id, 
                     Spp.unit_id==self.session['unit_id'], Spp.tahun_id==self.session['tahun'], Spp.id==pk_id
                     ).group_by(Spp.tahun_id, Urusan.nama, Unit.id,Unit.kode, Unit.nama, 
                     Tahun.no_perkdh, Tahun.tgl_perkdh, Spp.id,Spp.kode, Spp.nama, 
                     Spp.tanggal, Spp.ttd_nip, Spp.ttd_nama, Spp.ttd_jab, Spp.jenis, 
                     Spp.pptk_nip, Spp.pptk_nama, Spp.ap_nama, Spp.ap_bank, Spp.ap_rekening, 
                     case([(func.substr(Rekening.kode,1,5)=='5.1.1','-GJ')], else_="")
                     #func.substr(Rekening.kode,1,5)
                     )                         
            generator = b103r022Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        ### SPP Pengantar LS
        elif url_dict['act']=='spp51' :
            pk_id = 'id' in params and params['id'] and int(params['id']) or 0
            query = DBSession.query(Spp.tahun_id.label('tahun'), Urusan.nama.label('urusan_nm'), 
                     Unit.id.label('unit_id'),Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'), 
                     Tahun.no_perkdh, Tahun.tgl_perkdh, 
                     Spp.id.label('spp_id'),Spp.kode.label('spp_kd'), Spp.nama.label('spp_nm'), 
                     Spp.tanggal.label('spp_tgl'), Spp.ttd_nip, Spp.ttd_nama, Spp.ttd_jab, Spp.jenis, 
                     Spp.pptk_nip, Spp.pptk_nama, Spp.ap_nama, Spp.ap_bank, Spp.ap_rekening, 
                     #func.substr(Rekening.kode,1,5).label('kode'),
                     case([(func.substr(Rekening.kode,1,5)=='5.1.1','-GJ')], else_="").label('kode'),
                     func.sum(APInvoiceItem.amount).label('nominal')
                     ).filter(Spp.unit_id==Unit.id, Tahun.id==Spp.tahun_id, Urusan.id==Unit.urusan_id,
                     SppItem.ap_spp_id==Spp.id, SppItem.ap_invoice_id==APInvoiceItem.ap_invoice_id, 
                     APInvoiceItem.kegiatan_item_id==KegiatanItem.id,
                     Rekening.id==KegiatanItem.rekening_id, 
                     Spp.unit_id==self.session['unit_id'], Spp.tahun_id==self.session['tahun'], Spp.id==pk_id
                     ).group_by(Spp.tahun_id, Urusan.nama, Unit.id,Unit.kode, Unit.nama, 
                     Tahun.no_perkdh, Tahun.tgl_perkdh, Spp.id,Spp.kode, Spp.nama, 
                     Spp.tanggal, Spp.ttd_nip, Spp.ttd_nama, Spp.ttd_jab, Spp.jenis, 
                     Spp.pptk_nip, Spp.pptk_nama, Spp.ap_nama, Spp.ap_bank, Spp.ap_rekening, 
                     case([(func.substr(Rekening.kode,1,5)=='5.1.1','-GJ')], else_=""),
                     func.substr(Rekening.kode,1,5))                         
            generator = b103r025Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        ### SPP Ringkasan UP/TU
        elif url_dict['act']=='spp12' :
            pk_id = 'id' in params and params['id'] and int(params['id']) or 0
            query = DBSession.query(Spp.tahun_id.label('tahun'), Urusan.nama.label('urusan_nm'), 
                     Unit.id.label('unit_id'),Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'), 
                     Tahun.no_perkdh, Tahun.tgl_perkdh, 
                     Spp.id.label('spp_id'),Spp.kode.label('spp_kd'), Spp.nama.label('spp_nm'), 
                     Spp.tanggal.label('spp_tgl'), Spp.ttd_nip, Spp.ttd_nama, Spp.ttd_jab, Spp.jenis, 
                     Spp.pptk_nip, Spp.pptk_nama, Spp.ap_nama, Spp.ap_bank, Spp.ap_rekening, 
                     case([(func.substr(Rekening.kode,1,5)=='5.1.1','-GJ')], else_="").label('kode'),
                     #func.substr(Rekening.kode,1,5).label('kode'),
                     func.sum(APInvoiceItem.amount).label('nominal')
                     ).filter(Spp.unit_id==Unit.id, Tahun.id==Spp.tahun_id, Urusan.id==Unit.urusan_id,
                     SppItem.ap_spp_id==Spp.id, SppItem.ap_invoice_id==APInvoiceItem.ap_invoice_id, 
                     APInvoiceItem.kegiatan_item_id==KegiatanItem.id,
                     Rekening.id==KegiatanItem.rekening_id, 
                     Spp.unit_id==self.session['unit_id'], Spp.tahun_id==self.session['tahun'], Spp.id==pk_id
                     ).group_by(Spp.tahun_id, Urusan.nama, Unit.id,Unit.kode, Unit.nama, 
                     Tahun.no_perkdh, Tahun.tgl_perkdh, Spp.id,Spp.kode, Spp.nama, 
                     Spp.tanggal, Spp.ttd_nip, Spp.ttd_nama, Spp.ttd_jab, Spp.jenis, 
                     Spp.pptk_nip, Spp.pptk_nama, Spp.ap_nama, Spp.ap_bank, Spp.ap_rekening, 
                     case([(func.substr(Rekening.kode,1,5)=='5.1.1','-GJ')], else_="")
                     #func.substr(Rekening.kode,1,5)
                     )                         
            generator = b103r031Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        ### SPP Ringkasan // LS.G
        elif url_dict['act']=='spp32' :
            pk_id = 'id' in params and params['id'] and int(params['id']) or 0
            query = DBSession.query(Spp.tahun_id.label('tahun'), Urusan.nama.label('urusan_nm'), 
                     Unit.id.label('unit_id'),Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'), 
                     Tahun.no_perkdh, Tahun.tgl_perkdh, Tahun.tanggal_2, Tahun.tanggal_4,
                     Spp.id.label('spp_id'),Spp.kode.label('spp_kd'), Spp.nama.label('spp_nm'), 
                     Spp.tanggal.label('spp_tgl'), Spp.ttd_nip, Spp.ttd_nama, Spp.ttd_jab, Spp.jenis, 
                     Spp.pptk_nip, Spp.pptk_nama, Spp.ap_nama, Spp.ap_bank, Spp.ap_rekening, APInvoice.kegiatan_sub_id,
                     #func.substr(Rekening.kode,1,5).label('kode'),
                     case([(func.substr(Rekening.kode,1,5)=='5.1.1','-GJ')], else_="").label('kode'),
                     func.sum(APInvoiceItem.amount).label('nominal'),
                     #func.sum(KegiatanItem.vol_4_1*KegiatanItem.vol_4_2*KegiatanItem.hsat_4).label('anggaran')
                     ).filter(Spp.unit_id==Unit.id, Tahun.id==Spp.tahun_id, Urusan.id==Unit.urusan_id,
                     SppItem.ap_spp_id==Spp.id, SppItem.ap_invoice_id==APInvoice.id, APInvoice.id==APInvoiceItem.ap_invoice_id, 
                     APInvoiceItem.kegiatan_item_id==KegiatanItem.id,
                     Rekening.id==KegiatanItem.rekening_id, 
                     Spp.unit_id==self.session['unit_id'], Spp.tahun_id==self.session['tahun'], Spp.id==pk_id
                     ).group_by(Spp.tahun_id, Urusan.nama, Unit.id,Unit.kode, Unit.nama, 
                     Tahun.no_perkdh, Tahun.tgl_perkdh, Tahun.tanggal_2, Tahun.tanggal_4, Spp.id,Spp.kode, Spp.nama, 
                     Spp.tanggal, Spp.ttd_nip, Spp.ttd_nama, Spp.ttd_jab, Spp.jenis, 
                     Spp.pptk_nip, Spp.pptk_nama, Spp.ap_nama, Spp.ap_bank, Spp.ap_rekening, APInvoice.kegiatan_sub_id, 
                     case([(func.substr(Rekening.kode,1,5)=='5.1.1','-GJ')], else_="")
                     #func.substr(Rekening.kode,1,5)
                     )                         
            generator = b103r033Generator()#b103r0021_2Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        ### SPP Ringkasan GU / LSB
        elif url_dict['act']=='spp42' :
            pk_id = 'id' in params and params['id'] and int(params['id']) or 0
            subq = DBSession.query(Spd.unit_id, Spd.tahun_id, Spd.tanggal, SpdItem.nominal
                    ).filter(Spd.id==SpdItem.ap_spd_id).subquery()
            query = DBSession.query(Spp.tahun_id.label('tahun'), 
                     Unit.id.label('unit_id'),Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'), 
                     Tahun.tanggal_2, Tahun.tanggal_4, 
                     Spp.id.label('spp_id'),Spp.kode.label('spp_kd'), Spp.nama.label('spp_nm'), Spp.tanggal.label('spp_tgl'), 
                     Spp.ttd_nip, Spp.ttd_nama, Spp.ttd_jab, Spp.jenis, Spp.pptk_nip, Spp.pptk_nama,
                     Spp.nominal, Spp.ap_nama, Spp.ap_bank, Spp.ap_rekening, 
                     APInvoice.ap_waktu, APInvoice.ap_uraian, APInvoice.ap_pemilik, APInvoice.ap_alamat, 
                     APInvoice.ap_bentuk, APInvoice.ap_kontrak,
                     Kegiatan.kode.label('keg_kd'), Kegiatan.nama.label('keg_nm'), KegiatanSub.no_urut,
                     Program.nama.label('prg_nm'),
                     func.sum(KegiatanItem.vol_4_1*KegiatanItem.vol_4_2*KegiatanItem.hsat_4).label('anggaran'),
                     func.sum(subq.c.nominal).label('tot_spd')
                     ).filter(Spp.unit_id==Unit.id, Tahun.id==Spp.tahun_id, 
                     SppItem.ap_spp_id==Spp.id, SppItem.ap_invoice_id==APInvoice.id, 
                     APInvoice.id==APInvoiceItem.ap_invoice_id, APInvoiceItem.kegiatan_item_id==KegiatanItem.id, 
                     KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                     Kegiatan.id==KegiatanSub.kegiatan_id, Program.id==Kegiatan.program_id, 
                     subq.c.unit_id==Unit.id, subq.c.tahun_id==Spp.tahun_id, subq.c.tanggal<=Spp.tanggal, 
                     Spp.unit_id==self.session['unit_id'], Spp.tahun_id==self.session['tahun'], Spp.id==pk_id
                     ).group_by(
                     Spp.tahun_id, Unit.id,Unit.kode, Unit.nama, 
                     Tahun.tanggal_2, Tahun.tanggal_4, 
                     Spp.id,Spp.kode, Spp.nama, Spp.tanggal, 
                     Spp.ttd_nip, Spp.ttd_nama, Spp.ttd_jab, Spp.jenis, Spp.pptk_nip, Spp.pptk_nama,
                     Spp.nominal, Spp.ap_nama, Spp.ap_bank, Spp.ap_rekening, 
                     APInvoice.ap_waktu, APInvoice.ap_uraian, APInvoice.ap_pemilik, APInvoice.ap_alamat, 
                     APInvoice.ap_bentuk, APInvoice.ap_kontrak,
                     Kegiatan.kode, Kegiatan.nama, KegiatanSub.no_urut,
                     Program.nama
                     )                     
            generator = b103r034Generator()#b103r0021_1Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        ### SPP Ringkasan // LS
        elif url_dict['act']=='spp52' :
            pk_id = 'id' in params and params['id'] and int(params['id']) or 0
            """subq1  = DBSession.query(case([(func.substr(Rekening.kode,1,5)=='5.1.1','-GJ')], else_="").label('jenis1')
                     ).filter(Rekening.id==KegiatanItem.rekening_id, KegiatanItem.id==APInvoiceItem.kegiatan_item_id,
                     APInvoiceItem.ap_invoice_id==SppItem.ap_invoice_id, SppItem.ap_spp_id==Spp.id,
                     Spp.id==Spm.ap_spp_id, Spp.unit_id==self.session['unit_id'], Spp.tahun_id==self.session['tahun'], Spp.id==pk_id
                     ).group_by(case([(func.substr(Rekening.kode,1,5)=='5.1.1','-GJ')], else_="")
                     ).subquery()
            subq = DBSession.query(Spd.unit_id, Spd.tahun_id, Spd.tanggal, SpdItem.nominal
                    ).filter(Spd.id==SpdItem.ap_spd_id).subquery()
            """
            query = DBSession.query(Spp.tahun_id.label('tahun'), 
                     Unit.id.label('unit_id'),Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'), 
                     Tahun.tanggal_2, Tahun.tanggal_4, 
                     Spp.id.label('spp_id'),Spp.kode.label('spp_kd'), Spp.nama.label('spp_nm'), Spp.tanggal.label('spp_tgl'), 
                     Spp.ttd_nip, Spp.ttd_nama, Spp.ttd_jab, Spp.jenis, Spp.pptk_nip, Spp.pptk_nama,
                     Spp.ap_nama, Spp.ap_bank, Spp.ap_rekening, 
                     APInvoice.ap_waktu, APInvoice.ap_uraian, APInvoice.ap_pemilik, APInvoice.ap_alamat, 
                     APInvoice.ap_bentuk, APInvoice.ap_kontrak, APInvoice.kegiatan_sub_id,
                     Kegiatan.kode.label('keg_kd'), Kegiatan.nama.label('keg_nm'), KegiatanSub.no_urut,
                     Program.nama.label('prg_nm'), 
                     case([(func.substr(Rekening.kode,1,5)=='5.1.1','-GJ')], else_="").label('kode'),
                     func.coalesce(func.max(Spp.nominal),0).label('nominal'),
                     ).filter(Spp.unit_id==Unit.id, Tahun.id==Spp.tahun_id, 
                     SppItem.ap_spp_id==Spp.id, SppItem.ap_invoice_id==APInvoice.id, 
                     APInvoice.id==APInvoiceItem.ap_invoice_id, APInvoiceItem.kegiatan_item_id==KegiatanItem.id, 
                     KegiatanItem.rekening_id==Rekening.id, KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                     Kegiatan.id==KegiatanSub.kegiatan_id, Program.id==Kegiatan.program_id, 
                     Spp.unit_id==self.session['unit_id'], Spp.tahun_id==self.session['tahun'], Spp.id==pk_id
                     ).group_by(Spp.tahun_id, Unit.id, Unit.kode, Unit.nama, Tahun.tanggal_2, Tahun.tanggal_4, 
                     Spp.id, Spp.kode, Spp.nama, Spp.tanggal, 
                     Spp.ttd_nip, Spp.ttd_nama, Spp.ttd_jab, Spp.jenis, Spp.pptk_nip, Spp.pptk_nama,
                     Spp.ap_nama, Spp.ap_bank, Spp.ap_rekening, 
                     APInvoice.ap_waktu, APInvoice.ap_uraian, APInvoice.ap_pemilik, APInvoice.ap_alamat, 
                     APInvoice.ap_bentuk, APInvoice.ap_kontrak, APInvoice.kegiatan_sub_id,
                     Kegiatan.kode, Kegiatan.nama, KegiatanSub.no_urut,
                     Program.nama, 
                     case([(func.substr(Rekening.kode,1,5)=='5.1.1','-GJ')], else_="")
                     )
            generator = b103r035Generator()#b103r0021_2Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        ### SPP Rincian // UP
        elif url_dict['act']=='spp13' :
            pk_id = 'id' in params and params['id'] and int(params['id']) or 0
            """subq  = DBSession.query(case([(func.substr(Rekening.kode,1,5)=='5.1.1','-GJ')], else_=" ").label('jenis1')
                     ).filter(Rekening.id==KegiatanItem.rekening_id, KegiatanItem.id==APInvoiceItem.kegiatan_item_id,
                     APInvoiceItem.ap_invoice_id==SppItem.ap_invoice_id, SppItem.ap_spp_id==Spp.id,
                     Spp.id==Spm.ap_spp_id, Spp.unit_id==self.session['unit_id'], Spp.tahun_id==self.session['tahun'], Spp.id==pk_id
                     ).group_by(case([(func.substr(Rekening.kode,1,5)=='5.1.1','-GJ')], else_=" ")
                     ).subquery()
            """         
            query = DBSession.query(Spp.tahun_id.label('tahun'), 
                  Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'), 
                  Kegiatan.kode.label('keg_kd'), Kegiatan.nama.label('keg_nm'), 
                  Program.kode.label('prg_kd'),Program.nama.label('prg_nm'),
                  Spp.kode.label('spp_kd'), Spp.nama, Spp.tanggal, Spp.jenis, Spp.unit_id.label('unit_id'),
                  Rekening.kode.label('rek_kd'), Rekening.nama.label('rek_nm'), Spp.ttd_nip, Spp.ttd_nama,
                  func.sum(APInvoiceItem.amount).label('amount'), case([(func.substr(Rekening.kode,1,5)=='5.1.1','-GJ')], else_=" ").label('jenis1')
                  ).filter(Spp.unit_id==Unit.id, Spp.id==SppItem.ap_spp_id,
                  SppItem.ap_invoice_id==APInvoiceItem.ap_invoice_id, 
                  APInvoiceItem.kegiatan_item_id==KegiatanItem.id, KegiatanItem.rekening_id==Rekening.id,
                  KegiatanItem.kegiatan_sub_id==KegiatanSub.id, KegiatanSub.kegiatan_id==Kegiatan.id, 
                  Kegiatan.program_id== Program.id,
                  Spp.unit_id==self.session['unit_id'], 
                  Spp.tahun_id==self.session['tahun'], Spp.id==pk_id
                  ).group_by(Spp.tahun_id, Unit.kode, 
                  Unit.nama, Kegiatan.kode, Kegiatan.nama, Program.nama, Program.kode, Spp.ttd_nip, Spp.ttd_nama,
                  Spp.kode, Spp.nama, Spp.tanggal, Spp.jenis, Spp.unit_id, 
                  Rekening.kode, Rekening.nama, case([(func.substr(Rekening.kode,1,5)=='5.1.1','-GJ')], else_=" ")
                  ).order_by(Rekening.kode)
                  
            generator = b103r041Generator()#b103r0022Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        ### SPP Rincian // TU
        elif url_dict['act']=='spp23' :
            pk_id = 'id' in params and params['id'] and int(params['id']) or 0
            query = DBSession.query(Spp.tahun_id.label('tahun'), 
                  Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'), 
                  Kegiatan.kode.label('keg_kd'), Kegiatan.nama.label('keg_nm'), 
                  Program.kode.label('prg_kd'),Program.nama.label('prg_nm'),
                  Spp.kode.label('spp_kd'), Spp.nama, Spp.tanggal, Spp.jenis,
                  Spp.unit_id.label('unit_id'),
                  Rekening.kode.label('rek_kd'), Rekening.nama.label('rek_nm'), Spp.ttd_nip, Spp.ttd_nama, 
                  Spp.pptk_nip, Spp.pptk_nama, case([(func.substr(Rekening.kode,1,5)=='5.1.1','-GJ')], else_=" ").label('jenis1'),
                  func.sum(APInvoiceItem.amount).label('amount')
                  ).filter(Spp.unit_id==Unit.id, Spp.id==SppItem.ap_spp_id,
                  SppItem.ap_invoice_id==APInvoiceItem.ap_invoice_id, 
                  APInvoiceItem.kegiatan_item_id==KegiatanItem.id, KegiatanItem.rekening_id==Rekening.id,
                  KegiatanItem.kegiatan_sub_id==KegiatanSub.id, KegiatanSub.kegiatan_id==Kegiatan.id, 
                  Kegiatan.program_id== Program.id,
                  Spp.unit_id==self.session['unit_id'], 
                  Spp.tahun_id==self.session['tahun'], Spp.id==pk_id
                  ).group_by(Spp.tahun_id, Unit.kode, 
                  Unit.nama, Kegiatan.kode, Kegiatan.nama, Program.nama, Program.kode, Spp.ttd_nip, Spp.ttd_nama, Spp.pptk_nip, Spp.pptk_nama,
                  Spp.kode, Spp.nama, Spp.tanggal, Spp.jenis, Spp.unit_id, 
                  Rekening.kode, Rekening.nama, case([(func.substr(Rekening.kode,1,5)=='5.1.1','-GJ')], else_=" ")
                  ).order_by(Rekening.kode)
                  
            generator = b103r042Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        ### SPP Rincian // LS.G
        elif url_dict['act']=='spp33' :
            pk_id = 'id' in params and params['id'] and int(params['id']) or 0
            query = DBSession.query(Spp.tahun_id.label('tahun'), 
                  Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'), 
                  Kegiatan.kode.label('keg_kd'), Kegiatan.nama.label('keg_nm'), 
                  Program.kode.label('prg_kd'),Program.nama.label('prg_nm'),
                  Spp.kode.label('spp_kd'), Spp.nama, Spp.tanggal, Spp.jenis, Spp.unit_id.label('unit_id'),
                  Rekening.kode.label('rek_kd'), Rekening.nama.label('rek_nm'), Spp.ttd_nip, Spp.ttd_nama, 
                  Spp.pptk_nip, Spp.pptk_nama, case([(func.substr(Rekening.kode,1,5)=='5.1.1','-GJ')], else_="").label('jenis1'),
                  func.sum(APInvoiceItem.amount).label('amount')
                  ).filter(Spp.unit_id==Unit.id, Spp.id==SppItem.ap_spp_id,
                  SppItem.ap_invoice_id==APInvoiceItem.ap_invoice_id, 
                  APInvoiceItem.kegiatan_item_id==KegiatanItem.id, KegiatanItem.rekening_id==Rekening.id,
                  KegiatanItem.kegiatan_sub_id==KegiatanSub.id, KegiatanSub.kegiatan_id==Kegiatan.id, 
                  Kegiatan.program_id== Program.id,
                  Spp.unit_id==self.session['unit_id'], 
                  Spp.tahun_id==self.session['tahun'], Spp.id==pk_id
                  ).group_by(Spp.tahun_id, Unit.kode, 
                  Unit.nama, Kegiatan.kode, Kegiatan.nama, Program.nama, Program.kode, Spp.ttd_nip, Spp.ttd_nama, Spp.pptk_nip, Spp.pptk_nama,
                  Spp.kode, Spp.nama, Spp.tanggal, Spp.jenis, Spp.unit_id, 
                  Rekening.kode, Rekening.nama, case([(func.substr(Rekening.kode,1,5)=='5.1.1','-GJ')], else_="")
                  ).order_by(Rekening.kode)
                  
            generator = b103r043Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        ### SPP Rincian // GU/LSB
        elif url_dict['act']=='spp43' :
            pk_id = 'id' in params and params['id'] and int(params['id']) or 0
            query = DBSession.query(Spp.tahun_id.label('tahun'), 
                  Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'), 
                  Kegiatan.kode.label('keg_kd'), Kegiatan.nama.label('keg_nm'), 
                  Program.kode.label('prg_kd'),Program.nama.label('prg_nm'),
                  Spp.kode.label('spp_kd'), Spp.nama, Spp.tanggal, Spp.jenis, Spp.unit_id.label('unit_id'),
                  Rekening.kode.label('rek_kd'), Rekening.nama.label('rek_nm'), Spp.ttd_nip, Spp.ttd_nama, 
                  Spp.pptk_nip, Spp.pptk_nama, case([(func.substr(Rekening.kode,1,5)=='5.1.1','-GJ')], else_="").label('jenis1'),
                  func.sum(APInvoiceItem.amount).label('amount')
                  ).filter(Spp.unit_id==Unit.id, Spp.id==SppItem.ap_spp_id,
                  SppItem.ap_invoice_id==APInvoiceItem.ap_invoice_id, 
                  APInvoiceItem.kegiatan_item_id==KegiatanItem.id, KegiatanItem.rekening_id==Rekening.id,
                  KegiatanItem.kegiatan_sub_id==KegiatanSub.id, KegiatanSub.kegiatan_id==Kegiatan.id, 
                  Kegiatan.program_id== Program.id,
                  Spp.unit_id==self.session['unit_id'], 
                  Spp.tahun_id==self.session['tahun'], Spp.id==pk_id
                  ).group_by(Spp.tahun_id, Unit.kode, 
                  Unit.nama, Kegiatan.kode, Kegiatan.nama, Program.nama, Program.kode, Spp.ttd_nip, Spp.ttd_nama, Spp.pptk_nip, Spp.pptk_nama,
                  Spp.kode, Spp.nama, Spp.tanggal, Spp.jenis, Spp.unit_id, 
                  Rekening.kode, Rekening.nama, case([(func.substr(Rekening.kode,1,5)=='5.1.1','-GJ')], else_="")
                  ).order_by(Rekening.kode)
                  
            generator = b103r044Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        ### SPP Rincian // LS.G
        elif url_dict['act']=='spp53' :
            pk_id = 'id' in params and params['id'] and int(params['id']) or 0
            query = DBSession.query(Spp.tahun_id.label('tahun'), 
                  Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'), 
                  Kegiatan.kode.label('keg_kd'), Kegiatan.nama.label('keg_nm'), 
                  Program.kode.label('prg_kd'),Program.nama.label('prg_nm'),
                  Spp.kode.label('spp_kd'), Spp.nama, Spp.tanggal, Spp.jenis, Spp.unit_id.label('unit_id'),
                  Rekening.kode.label('rek_kd'), Rekening.nama.label('rek_nm'), Spp.ttd_nip, Spp.ttd_nama, 
                  Spp.pptk_nip, Spp.pptk_nama, case([(func.substr(Rekening.kode,1,5)=='5.1.1','-GJ')], else_=" ").label('jenis1'),
                  func.sum(APInvoiceItem.amount).label('amount')
                  ).filter(Spp.unit_id==Unit.id, Spp.id==SppItem.ap_spp_id,
                  SppItem.ap_invoice_id==APInvoiceItem.ap_invoice_id, 
                  APInvoiceItem.kegiatan_item_id==KegiatanItem.id, KegiatanItem.rekening_id==Rekening.id,
                  KegiatanItem.kegiatan_sub_id==KegiatanSub.id, KegiatanSub.kegiatan_id==Kegiatan.id, 
                  Kegiatan.program_id== Program.id,
                  Spp.unit_id==self.session['unit_id'], 
                  Spp.tahun_id==self.session['tahun'], Spp.id==pk_id
                  ).group_by(Spp.tahun_id, Unit.kode, 
                  Unit.nama, Kegiatan.kode, Kegiatan.nama, Program.nama, Program.kode, Spp.ttd_nip, Spp.ttd_nama, Spp.pptk_nip, Spp.pptk_nama,
                  Spp.kode, Spp.nama, Spp.tanggal, Spp.jenis, Spp.unit_id, 
                  Rekening.kode, Rekening.nama, case([(func.substr(Rekening.kode,1,5)=='5.1.1','-GJ')], else_=" ")
                  ).order_by(Rekening.kode)
                  
            generator = b103r045Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        ### LAPORAN SPM 1
        elif url_dict['act']=='31' :
            if tipe ==0 :
                query = DBSession.query(Spp.tahun_id.label('tahun'), Unit.kode.label('unit_kd'),Unit.nama.label('unit_nm'),
                  case([(Spp.jenis==1,"UP"),(Spp.jenis==2,"TU"),(Spp.jenis==3,"GU"),(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)=="5.1.1"),"LS-GJ"),(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)!="5.1.1"),"LS")], else_="").label('jenis'),
                  Spp.kode.label('spp_kd'), Spp.nama.label('spp_nm'), Spp.tanggal.label('tgl_spp'),
                  Spm.kode.label('spm_kd'), Spm.tanggal.label('tgl_spm'),
                  Sp2d.kode.label('sp2d_kd'), Sp2d.tanggal.label('tgl_sp2d'),
                  func.sum(APInvoiceItem.amount).label('nominal')
                  ).filter(SppItem.ap_spp_id==Spp.id, SppItem.ap_invoice_id==APInvoice.id,
                  APInvoiceItem.ap_invoice_id==APInvoice.id, APInvoiceItem.kegiatan_item_id==KegiatanItem.id,
                  KegiatanItem.rekening_id==Rekening.id,
                  Spp.unit_id==Unit.id, Spp.unit_id==self.session['unit_id'],
                  Spp.tahun_id==self.session['tahun'],
                  Spm.tanggal.between(mulai,selesai)        
                  ).outerjoin(Spm,Spm.ap_spp_id==Spp.id
                  ).outerjoin(Sp2d,Sp2d.ap_spm_id==Spm.id
                  ).group_by(Spp.tahun_id, Unit.kode, Unit.nama,
                  case([(Spp.jenis==1,"UP"),(Spp.jenis==2,"TU"),(Spp.jenis==3,"GU"),(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)=="5.1.1"),"LS-GJ"),(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)!="5.1.1"),"LS")], else_=""),
                  Spp.kode, Spp.nama, Spp.tanggal,
                  Spm.kode, Spm.tanggal,
                  Sp2d.kode, Sp2d.tanggal
                  ).order_by(Spp.tanggal).all()

            else:
                query = DBSession.query(Spp.tahun_id.label('tahun'), Unit.kode.label('unit_kd'),Unit.nama.label('unit_nm'),
                  case([(Spp.jenis==1,"UP"),(Spp.jenis==2,"TU"),(Spp.jenis==3,"GU"),(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)=="5.1.1"),"LS-GJ"),(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)!="5.1.1"),"LS")], else_="").label('jenis'),
                  Spp.kode.label('spp_kd'), Spp.nama.label('spp_nm'), Spp.tanggal.label('tgl_spp'),
                  Spm.kode.label('spm_kd'), Spm.tanggal.label('tgl_spm'),
                  Sp2d.kode.label('sp2d_kd'), Sp2d.tanggal.label('tgl_sp2d'),
                  func.sum(APInvoiceItem.amount).label('nominal')
                  ).filter(SppItem.ap_spp_id==Spp.id, SppItem.ap_invoice_id==APInvoice.id,
                  APInvoiceItem.ap_invoice_id==APInvoice.id, APInvoiceItem.kegiatan_item_id==KegiatanItem.id,
                  KegiatanItem.rekening_id==Rekening.id,
                  Spp.unit_id==Unit.id, Spp.unit_id==self.session['unit_id'],
                  Spp.tahun_id==self.session['tahun'], Spp.jenis==tipe, 
                  Spm.tanggal.between(mulai,selesai)
                  ).outerjoin(Spm,Spm.ap_spp_id==Spp.id
                  ).outerjoin(Sp2d,Sp2d.ap_spm_id==Spm.id
                  ).group_by(Spp.tahun_id, Unit.kode, Unit.nama,
                  case([(Spp.jenis==1,"UP"),(Spp.jenis==2,"TU"),(Spp.jenis==3,"GU"),(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)=="5.1.1"),"LS-GJ"),(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)!="5.1.1"),"LS")], else_=""),                  Spp.kode, Spp.nama, Spp.tanggal,
                  Spm.kode, Spm.tanggal,
                  Sp2d.kode, Sp2d.tanggal,
                  ).order_by(Spp.tanggal).all()
                 
            generator = b104r2001Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        ### LAPORAN SPM 2
        elif url_dict['act']=='321' :
            if tipe ==0 :
                query = DBSession.query(Spp.tahun_id.label('tahun'), Unit.kode.label('unit_kd'),
                  Unit.nama.label('unit_nm'), Spm.tanggal.label('tgl_spp'), 
                  Spm.kode.label('spp_kd'), Spm.nama.label('spp_nm'),
                  case([(Spp.jenis==1,"UP"),(Spp.jenis==2,"TU"),(Spp.jenis==3,"GU"),(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)=="5.1.1"),"LS-GJ"),(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)!="5.1.1"),"LS")], else_="").label('jenis'),
                  func.sum(case([(Spp.jenis==1,APInvoiceItem.amount)], else_=0)).label('UP'),
                  func.sum(case([(Spp.jenis==2,APInvoiceItem.amount)], else_=0)).label('TU'),
                  func.sum(case([(Spp.jenis==3,APInvoiceItem.amount)], else_=0)).label('GU'),
                  func.sum(case([(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)=='5.1.1'),APInvoiceItem.amount)], else_=0)).label('LS_GJ'),
                  func.sum(case([(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)!='5.1.1'),APInvoiceItem.amount)], else_=0)).label('LS')
                  ).filter(SppItem.ap_spp_id==Spp.id, SppItem.ap_invoice_id==APInvoice.id,
                  APInvoiceItem.ap_invoice_id==APInvoice.id, APInvoiceItem.kegiatan_item_id==KegiatanItem.id,
                  KegiatanItem.rekening_id==Rekening.id,
                  Spp.unit_id==Unit.id, Spp.unit_id==self.session['unit_id'],
                  Spp.tahun_id==self.session['tahun'],  
                  Spm.tanggal.between(mulai,selesai)        
                  ).outerjoin(Spm,Spm.ap_spp_id==Spp.id
                  ).outerjoin(Sp2d,Sp2d.ap_spm_id==Spm.id
                  ).group_by(Spp.tahun_id, Unit.kode, Unit.nama, Spm.tanggal, 
                  Spm.kode, Spm.nama,
                  case([(Spp.jenis==1,"UP"),(Spp.jenis==2,"TU"),(Spp.jenis==3,"GU"),(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)=="5.1.1"),"LS-GJ"),(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)!="5.1.1"),"LS")], else_=""),
                  ).order_by(Spm.tanggal).all()
            else:
                query = DBSession.query(Spp.tahun_id.label('tahun'), Unit.kode.label('unit_kd'),
                  Unit.nama.label('unit_nm'), Spm.tanggal.label('tgl_spp'), 
                  Spm.kode.label('spp_kd'), Spm.nama.label('spp_nm'),
                  case([(Spp.jenis==1,"UP"),(Spp.jenis==2,"TU"),(Spp.jenis==3,"GU"),(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)=="5.1.1"),"LS-GJ"),(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)!="5.1.1"),"LS")], else_="").label('jenis'),
                  func.sum(case([(Spp.jenis==1,APInvoiceItem.amount)], else_=0)).label('UP'),
                  func.sum(case([(Spp.jenis==2,APInvoiceItem.amount)], else_=0)).label('TU'),
                  func.sum(case([(Spp.jenis==3,APInvoiceItem.amount)], else_=0)).label('GU'),
                  func.sum(case([(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)=='5.1.1'),APInvoiceItem.amount)], else_=0)).label('LS_GJ'),
                  func.sum(case([(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)!='5.1.1'),APInvoiceItem.amount)], else_=0)).label('LS')
                  ).outerjoin(Spm,Spm.ap_spp_id==Spp.id
                  ).outerjoin(Sp2d,Sp2d.ap_spm_id==Spm.id
                  ).filter(SppItem.ap_spp_id==Spp.id, SppItem.ap_invoice_id==APInvoice.id,
                  APInvoiceItem.ap_invoice_id==APInvoice.id, APInvoiceItem.kegiatan_item_id==KegiatanItem.id,
                  KegiatanItem.rekening_id==Rekening.id,
                  Spp.unit_id==Unit.id, Spp.unit_id==self.session['unit_id'],
                  Spp.tahun_id==self.session['tahun'], Spp.jenis==tipe,   
                  Spm.tanggal.between(mulai,selesai)        
                  ).group_by(Spp.tahun_id, Unit.kode, Unit.nama, Spm.tanggal, 
                  Spm.kode, Spm.nama,
                  case([(Spp.jenis==1,"UP"),(Spp.jenis==2,"TU"),(Spp.jenis==3,"GU"),(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)=="5.1.1"),"LS-GJ"),(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)!="5.1.1"),"LS")], else_=""),
                  ).order_by(Spm.tanggal).all()

            generator = b104r2002Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        ### LAPORAN SPM 3
        elif url_dict['act']=='33' :
            if tipe ==0 :
                query = DBSession.query(Spp.tahun_id.label('tahun'), Unit.kode.label('unit_kd'),
                  Unit.nama.label('unit_nm'), Spm.id.label('spm_id'), Spm.tanggal.label('tgl_spm'), 
                  Spm.kode.label('spm_kd'), Spm.nama.label('spm_nm'),
                  case([(Spp.jenis==1,"UP"),(Spp.jenis==2,"TU"),(Spp.jenis==3,"GU"),(Spp.jenis==4,"LS")], else_="").label('jenis'),
                  Spp.id.label('spp_id'), Spp.nominal
                  ).filter(Spm.ap_spp_id==Spp.id, 
                  Spp.unit_id==Unit.id, Spp.unit_id==self.session['unit_id'],
                  Spp.tahun_id==self.session['tahun'],  
                  Spm.tanggal.between(mulai,selesai)        
                  ).order_by(Spm.tanggal).all()
            else:
                query = DBSession.query(Spp.tahun_id.label('tahun'), Unit.kode.label('unit_kd'),
                  Unit.nama.label('unit_nm'), Spm.id.label('spm_id'), Spm.tanggal.label('tgl_spm'), 
                  Spm.kode.label('spm_kd'), Spm.nama.label('spm_nm'),
                  case([(Spp.jenis==1,"UP"),(Spp.jenis==2,"TU"),(Spp.jenis==3,"GU"),(Spp.jenis==4,"LS")], else_="").label('jenis'),
                  Spp.id.label('spp_id'), Spp.nominal
                  ).filter(Spm.ap_spp_id==Spp.id, 
                  Spp.unit_id==Unit.id, Spp.unit_id==self.session['unit_id'],
                  Spp.tahun_id==self.session['tahun'], Spp.jenis==tipe,   
                  Spm.tanggal.between(mulai,selesai)        
                  ).order_by(Spm.tanggal).all()

            generator = b104r2003Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        ### SPM // Pengantar
        elif url_dict['act']=='spm01' :
            pk_id = 'id' in params and params['id'] and int(params['id']) or 0
            query = DBSession.query(Spp.tahun_id.label('tahun'), Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'), Unit.alamat,
                     Spm.id.label('spm_id'),Spm.kode.label('spm_kd'), Spm.nama.label('spm_nm'), Spm.tanggal.label('spm_tgl'), Spm.ttd_nip, Spm.ttd_nama, 
                     Spp.id.label('spp_id'),Spp.jenis.label('jenis'), 
                     case([(func.substr(Rekening.kode,1,5)=='5.1.1','-GJ')], else_="").label('kode'),
                     #func.substr(Rekening.kode,1,5).label('kode'),                  
                     Kegiatan.kode.label('keg_kd'), Kegiatan.nama.label('keg_nm'), Program.kode.label('prg_kd'),
                     Rekening.kode.label('rek_kd'), Rekening.nama.label('rek_nm'), func.sum(APInvoiceItem.amount).label('amount'),
                     Jabatan.nama.label('jabatan')
                     ).filter(cast(Spm.ttd_uid, sqlalchemy.String)==Jabatan.kode, Spm.ap_spp_id==Spp.id, Spp.unit_id==Unit.id, 
                     SppItem.ap_spp_id==Spp.id, SppItem.ap_invoice_id==APInvoiceItem.ap_invoice_id, 
                     APInvoiceItem.kegiatan_item_id==KegiatanItem.id,
                     KegiatanItem.rekening_id==Rekening.id, KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                     KegiatanSub.kegiatan_id==Kegiatan.id, Kegiatan.program_id==Program.id,
                     Spp.unit_id==self.session['unit_id'], Spp.tahun_id==self.session['tahun'], Spm.id==pk_id
                     ).group_by(Spp.tahun_id, Unit.kode, Unit.nama, Unit.alamat,
                     Spm.id,Spm.kode, Spm.nama, Spm.tanggal, Spm.ttd_nip, Spm.ttd_nama, 
                     Spp.id,Spp.jenis, 
                     case([(func.substr(Rekening.kode,1,5)=='5.1.1','-GJ')], else_=""),
                     #func.substr(Rekening.kode,1,5),                  
                     Kegiatan.kode, Kegiatan.nama, Program.kode,
                     Rekening.kode, Rekening.nama, 
                     Jabatan.nama
                     ).order_by(Spm.kode, Kegiatan.kode, Rekening.kode
                     )                     
            generator = b103r003_1Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        ### SPM // Pernyataan
        elif url_dict['act']=='spm02' :
            pk_id = 'id' in params and params['id'] and int(params['id']) or 0
            query = DBSession.query(Spp.tahun_id.label('tahun'), Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'), Unit.alamat,
                     Spm.id.label('spm_id'),Spm.kode.label('spm_kd'), Spm.nama.label('spm_nm'), Spm.tanggal.label('spm_tgl'), Spm.ttd_nip, Spm.ttd_nama, 
                     Spp.id.label('spp_id'),Spp.jenis.label('jenis'), 
                     Spp.nominal.label('amount'), Jabatan.nama.label('jabatan')
                     ).filter(cast(Spm.ttd_uid, sqlalchemy.String)==Jabatan.kode, 
                     Spm.ap_spp_id==Spp.id, Spp.unit_id==Unit.id, 
                     Spp.unit_id==self.session['unit_id'], Spp.tahun_id==self.session['tahun'], Spm.id==pk_id
                     )                         
            generator = b103r003_2Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        ### SPM // Pernyataan TU
        elif url_dict['act']=='spm12' :
            pk_id = 'id' in params and params['id'] and int(params['id']) or 0
            query = DBSession.query(Spp.tahun_id.label('tahun'), Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'), Unit.alamat,
                     Spm.id.label('spm_id'),Spm.kode.label('spm_kd'), Spm.nama.label('spm_nm'), Spm.tanggal.label('spm_tgl'), Spm.ttd_nip, Spm.ttd_nama, 
                     Spp.id.label('spp_id'),Spp.jenis.label('jenis'), 
                     Spp.nominal.label('amount'), Jabatan.nama.label('jabatan')
                     ).filter(cast(Spm.ttd_uid, sqlalchemy.String)==Jabatan.kode, 
                     Spm.ap_spp_id==Spp.id, Spp.unit_id==Unit.id, 
                     Spp.unit_id==self.session['unit_id'], Spp.tahun_id==self.session['tahun'], Spm.id==pk_id
                     )                         
            """query = DBSession.query(Spp.tahun_id.label('tahun'), Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'), Unit.alamat,
                     Spm.id.label('spm_id'),Spm.kode.label('spm_kd'), Spm.nama.label('spm_nm'), Spm.tanggal.label('spm_tgl'), 
                     Spm.ttd_nip, Spm.ttd_nama, Spp.jenis.label('jenis'), Spp.nominal, Spp.nama.label('spp_nm'), Kegiatan.kode, 
                     Jabatan.nama.label('jabatan')
                     ).filter(cast(Spm.ttd_uid, sqlalchemy.String)==Jabatan.kode, 
                     Spm.ap_spp_id==Spp.id, Spp.unit_id==Unit.id, 
                     SppItem.ap_spp_id==Spp.id, SppItem.ap_invoice_id==APInvoice.id, 
                     APInvoice.kegiatan_sub_id==KegiatanSub.id,
                     Kegiatan.id==KegiatanSub.kegiatan_id,
                     Spp.unit_id==self.session['unit_id'], Spp.tahun_id==self.session['tahun'], Spm.id==pk_id
                     )                         
            """
            generator = b103r003_12Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        ### SPM // Format SPM
        elif url_dict['act']=='spm03' :
            print "KKKKKKKKKKKKKKKKKKKKKKKK"
            pk_id = 'id' in params and params['id'] and int(params['id']) or 0
            subq  = DBSession.query(case([(func.substr(Rekening.kode,1,5)=='5.1.1','-GJ')], else_="").label('jenis1')
                     ).filter(Rekening.id==KegiatanItem.rekening_id, KegiatanItem.id==APInvoiceItem.kegiatan_item_id,
                     APInvoiceItem.ap_invoice_id==SppItem.ap_invoice_id, SppItem.ap_spp_id==Spp.id,
                     Spp.id==Spm.ap_spp_id, Spp.unit_id==self.session['unit_id'], Spp.tahun_id==self.session['tahun'], Spm.id==pk_id
                     ).group_by(case([(func.substr(Rekening.kode,1,5)=='5.1.1','-GJ')], else_="")
                     ).subquery()
                     
            query = DBSession.query(Spp.tahun_id.label('tahun'), Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'), 
                     Spm.id.label('spm_id'), Spm.kode.label('spm_kd'), Spm.nama.label('spm_nm'), Spm.tanggal.label('spm_tgl'), Spm.ttd_nip, Spm.ttd_nama, 
                     Spp.id.label('spp_id'), Spp.kode.label('spp_kd'), Spp.jenis.label('jenis'), Spp.tanggal.label('spp_tgl'), Spp.ap_bank, 
                     Spp.ap_rekening, Spp.ap_npwp, Spp.ap_nama, Spp.nama.label('spp_nm'),
                     Spd.kode.label('spd_kd'), Spd.tanggal.label('spd_tgl'),
                     #Kegiatan.kode.label('keg_kd'), APInvoice.id.label('ap_invoice_id'),
                     #Program.kode.label('program_kd'),
                     Spp.nominal, Jabatan.nama.label('jabatan'), subq.c.jenis1
                     #).join(Spm).join(Unit).join(Spd).join(SppItem).join(APInvoice).join(KegiatanSub).join(Kegiatan).join(Program
                     ).filter(cast(Spm.ttd_uid, sqlalchemy.String)==Jabatan.kode, 
                     Spm.ap_spp_id==Spp.id, Spp.unit_id==Unit.id, Spd.id==Spp.ap_spd_id,
                     #SppItem.ap_spp_id==Spp.id, SppItem.ap_invoice_id==APInvoice.id, APInvoice.kegiatan_sub_id==KegiatanSub.id,
                     #Kegiatan.id==KegiatanSub.kegiatan_id, Program.id==Kegiatan.program_id,
                     Spp.unit_id==self.session['unit_id'], Spp.tahun_id==self.session['tahun'], Spm.id==pk_id
                     )                     

            generator = b103r003Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        ### SPM // Checklist
        elif url_dict['act']=='spm11' :
            pk_id = 'id' in params and params['id'] and int(params['id']) or 0
            query = DBSession.query(Spp.tahun_id.label('tahun'), Spp.unit_id ,Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'), Unit.alamat, 
                     Spm.kode.label('spm_kd'), Spm.nama.label('spm_nm'), Spm.tanggal.label('spm_tgl'), Spm.ttd_nip, Spm.ttd_nama, 
                     Spp.jenis.label('jenis'), Kegiatan.kode, KegiatanSub.nama
                     ).filter(Spm.ap_spp_id==Spp.id, Spp.unit_id==Unit.id, 
                     SppItem.ap_spp_id==Spp.id, SppItem.ap_invoice_id==APInvoice.id, APInvoice.kegiatan_sub_id==KegiatanSub.id,
                     Kegiatan.id==KegiatanSub.kegiatan_id,
                     Spp.unit_id==self.session['unit_id'], Spp.tahun_id==self.session['tahun'], Spm.id==pk_id
                     )                         

            generator = b103r003_11Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
			
        ### SPM // SPTJM LS Pihak Ketiga 1
        elif url_dict['act']=='spm04' :
            pk_id = 'id' in params and params['id'] and int(params['id']) or 0
            
            query = DBSession.query(Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'), Unit.alamat,
               Spm.kode, Spm.tanggal, Spm.ttd_nip, Spm.ttd_nama, APInvoice.amount,
               Spp.tahun_id, Spp.jenis, APInvoice.ap_bap_no, APInvoice.ap_bap_tgl, APInvoice.ap_nilai,
               APInvoice.ap_kontrak, APInvoice.ap_tgl_kontrak, APInvoice.ap_nama, APInvoice.ap_pemilik, 
               Jabatan.nama.label('jabatan')
               ).filter(cast(Spm.ttd_uid, sqlalchemy.String)==Jabatan.kode, Spm.ap_spp_id==Spp.id, 
               Spp.unit_id==Unit.id,
               SppItem.ap_spp_id==Spp.id, 
               SppItem.ap_invoice_id==APInvoice.id,
               Spm.id==pk_id
               )
               
            generator = b103r003_4Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        ### SPM // SPTJM LS Pihak Ketiga 2
        elif url_dict['act']=='spm05' :
            pk_id = 'id' in params and params['id'] and int(params['id']) or 0
            
            query = DBSession.query(Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'), Unit.alamat,
               Spm.kode, Spm.tanggal, Spm.ttd_nip, Spm.ttd_nama, APInvoice.amount,
               Spp.tahun_id, Spp.jenis, APInvoice.ap_bap_no, APInvoice.ap_bap_tgl, APInvoice.ap_nilai,
               APInvoice.ap_kontrak, APInvoice.ap_tgl_kontrak, APInvoice.ap_nama, APInvoice.ap_pemilik,
               APInvoice.ap_kwitansi_nilai, APInvoice.ap_kwitansi_no, APInvoice.ap_kwitansi_tgl, 
               Jabatan.nama.label('jabatan')
               ).filter(cast(Spm.ttd_uid, sqlalchemy.String)==Jabatan.kode, 
               Spm.ap_spp_id==Spp.id, 
               Spp.unit_id==Unit.id,
               SppItem.ap_spp_id==Spp.id, 
               SppItem.ap_invoice_id==APInvoice.id,
               Spm.id==pk_id
               )
               
            generator = b103r003_5Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        ### SPM // SPTJM LS
        elif url_dict['act']=='spm06' :
            pk_id = 'id' in params and params['id'] and int(params['id']) or 0
            
            query = DBSession.query(Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'), Unit.alamat,
               Spm.kode, Spm.tanggal, Spm.ttd_nip, Spm.ttd_nama,
               Spp.tahun_id, Spp.jenis, Jabatan.nama.label('jabatan'), Spp.id.label('spp_id')
               ).filter(cast(Spm.ttd_uid, sqlalchemy.String)==Jabatan.kode, 
               Spm.ap_spp_id==Spp.id, 
               Spp.unit_id==Unit.id,
               Spm.id==pk_id
               )
               
            generator = b103r003_6Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        ### SPM // SPTJM GU
        elif url_dict['act']=='spm07' :
            pk_id = 'id' in params and params['id'] and int(params['id']) or 0
            
            query = DBSession.query(Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'), Unit.alamat,
               Spm.kode, Spm.tanggal, Spm.ttd_nip, Spm.ttd_nama,
               Spp.tahun_id, Spp.jenis, Jabatan.nama.label('jabatan')
               ).filter(cast(Spm.ttd_uid, sqlalchemy.String)==Jabatan.kode, 
               Spm.ap_spp_id==Spp.id, 
               Spp.unit_id==Unit.id,
               Spm.id==pk_id
               )
               
            generator = b103r003_7Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        ### SPM // SPTJB UP - GU
        elif url_dict['act']=='spm08' :
            pk_id = 'id' in params and params['id'] and int(params['id']) or 0
            
            query = DBSession.query(Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'), Unit.alamat,
               Program.kode.label('program_kd'), Kegiatan.kode.label('keg_kd'), 
               Kegiatan.nama.label('keg_nm'),
               Rekening.kode.label('rek_kd'), Rekening.nama.label('rek_nm'),
               APInvoiceItem.amount, APInvoiceItem.pph, APInvoiceItem.ppn, APInvoice.ap_kwitansi_no, 
               APInvoice.ap_kwitansi_tgl, APInvoice.ap_nama, Spm.tanggal, APInvoice.no_bku, APInvoice.tgl_bku,
               Spp.tahun_id, Spp.jenis, Spm.kode, Spm.ttd_nip, Spm.ttd_nama, 
               Jabatan.nama.label('jabatan')
               ).filter(cast(Spm.ttd_uid, sqlalchemy.String)==Jabatan.kode, 
               Spm.ap_spp_id==Spp.id, 
               Spp.unit_id==Unit.id,
               SppItem.ap_spp_id==Spp.id, 
               SppItem.ap_invoice_id==APInvoice.id,
               APInvoiceItem.ap_invoice_id==APInvoice.id, 
               APInvoiceItem.kegiatan_item_id==KegiatanItem.id, 
               KegiatanItem.rekening_id==Rekening.id, 
               KegiatanItem.kegiatan_sub_id==KegiatanSub.id, 
               KegiatanSub.kegiatan_id==Kegiatan.id,
               Kegiatan.program_id==Program.id, Spm.id==pk_id
               ).order_by(Rekening.kode
               )
               
            generator = b103r003_8Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        ### SPM // SPTJB LS
        elif url_dict['act']=='spm09' :
            pk_id = 'id' in params and params['id'] and int(params['id']) or 0
            
            query = DBSession.query(Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'), Unit.alamat,
               Program.kode.label('program_kd'), Kegiatan.kode.label('keg_kd'), 
               Kegiatan.nama.label('keg_nm'),
               Rekening.kode.label('rek_kd'), Rekening.nama.label('rek_nm'),
               APInvoiceItem.amount, APInvoiceItem.pph, APInvoiceItem.ppn, APInvoice.ap_kwitansi_no, 
               APInvoice.ap_kwitansi_tgl, APInvoice.ap_nama, Spm.tanggal,
               Spp.tahun_id, Spp.jenis, Spm.kode, Spm.ttd_nip, Spm.ttd_nama,
               Jabatan.nama.label('jabatan')
               ).filter(cast(Spm.ttd_uid, sqlalchemy.String)==Jabatan.kode, 
               Spm.ap_spp_id==Spp.id, 
               Spp.unit_id==Unit.id,
               SppItem.ap_spp_id==Spp.id, 
               SppItem.ap_invoice_id==APInvoice.id,
               APInvoiceItem.ap_invoice_id==APInvoice.id, 
               APInvoiceItem.kegiatan_item_id==KegiatanItem.id, 
               KegiatanItem.rekening_id==Rekening.id, 
               KegiatanItem.kegiatan_sub_id==KegiatanSub.id, 
               KegiatanSub.kegiatan_id==Kegiatan.id,
               Kegiatan.program_id==Program.id, Spm.id==pk_id
               ).order_by(Rekening.kode
               )
               
            generator = b103r003_9Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        ### SPM // SPTJB LS PIHAK KETIGA
        elif url_dict['act']=='spm10' :
            pk_id = 'id' in params and params['id'] and int(params['id']) or 0
            query = DBSession.query(Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'), Unit.alamat,
               Program.kode.label('program_kd'), Kegiatan.kode.label('keg_kd'), 
               Kegiatan.nama.label('keg_nm'),
               Rekening.kode.label('rek_kd'), Rekening.nama.label('rek_nm'),
               APInvoiceItem.amount, APInvoiceItem.pph, APInvoiceItem.ppn, APInvoice.ap_kwitansi_no, 
               APInvoice.ap_kwitansi_tgl, APInvoice.ap_nama, Spm.tanggal,
               Spp.tahun_id, Spp.jenis, Spm.kode, Spm.ttd_nip, Spm.ttd_nama
               , Jabatan.nama.label('jabatan')
               ).filter(cast(Spm.ttd_uid, sqlalchemy.String)==Jabatan.kode, 
               Spm.ap_spp_id==Spp.id, 
               Spp.unit_id==Unit.id,
               SppItem.ap_spp_id==Spp.id, 
               SppItem.ap_invoice_id==APInvoice.id,
               APInvoiceItem.ap_invoice_id==APInvoice.id, 
               APInvoiceItem.kegiatan_item_id==KegiatanItem.id, 
               KegiatanItem.rekening_id==Rekening.id, 
               KegiatanItem.kegiatan_sub_id==KegiatanSub.id, 
               KegiatanSub.kegiatan_id==Kegiatan.id,
               Kegiatan.program_id==Program.id, Spm.id==pk_id
               ).order_by(Rekening.kode
               )
               
            generator = b103r003_10Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        ### SPJ Fungsional
        elif url_dict['act']=='4' :
            bulan = 'bulan' in params and params['bulan'] and int(params['bulan']) or 0
            japbd = 'japbd' in params and params['japbd'] and int(params['japbd']) or 0
            rek = aliased(Rekening)
            query = DBSession.query(Unit.id.label('unit_id'), Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'),
              Kegiatan.kode.label('keg_kd'), Kegiatan.nama.label('keg_nm'), 
              KegiatanSub.id.label('keg_sub_id'), Rekening.id.label('rek_id'), Rekening.kode.label('rek_kd'),
              Rekening.nama.label('rek_nm'), KegiatanSub.tahun_id.label('tahun'), 
              func.sum(KegiatanItem.vol_2_1*KegiatanItem.vol_2_2*KegiatanItem.hsat_2).label('dpa'),                      
              func.sum(KegiatanItem.vol_4_1*KegiatanItem.vol_4_2*KegiatanItem.hsat_4).label('dppa'),
              func.coalesce(func.sum(case([(and_(extract('month',APInvoice.tanggal)<bulan, APInvoice.jenis==4,func.substr(rek.kode,1,5)=='5.1.1',func.substr(rek.kode,1,8)!='5.1.1.02'),APInvoiceItem.amount)], else_=0)),0).label('LSG_lalu'),
              func.coalesce(func.sum(case([(and_(extract('month',APInvoice.tanggal)==bulan, APInvoice.jenis==4,func.substr(rek.kode,1,5)=='5.1.1',func.substr(rek.kode,1,8)!='5.1.1.02'),APInvoiceItem.amount)], else_=0)),0).label('LSG_kini'),
              func.coalesce(func.sum(case([(and_(extract('month',APInvoice.tanggal)<bulan, APInvoice.jenis==4,or_(func.substr(rek.kode,1,5)!='5.1.1',func.substr(rek.kode,1,8)=='5.1.1.02')),APInvoiceItem.amount)], else_=0)),0).label('LS_lalu'),
              func.coalesce(func.sum(case([(and_(extract('month',APInvoice.tanggal)==bulan, APInvoice.jenis==4,or_(func.substr(rek.kode,1,5)!='5.1.1',func.substr(rek.kode,1,8)=='5.1.1.02')),APInvoiceItem.amount)], else_=0)),0).label('LS_kini'),
              func.coalesce(func.sum(case([(and_(extract('month',APInvoice.tanggal)<bulan, not_(APInvoice.jenis==4)),APInvoiceItem.amount)], else_=0)),0).label('Lain_lalu'),
              func.coalesce(func.sum(case([(and_(extract('month',APInvoice.tanggal)==bulan, not_(APInvoice.jenis==4)),APInvoiceItem.amount)], else_=0)),0).label('Lain_kini')
              ).join(KegiatanSub, KegiatanItem, Rekening, Kegiatan
              ).outerjoin(APInvoiceItem, APInvoiceItem.kegiatan_item_id==KegiatanItem.id
              ).outerjoin(APInvoice, APInvoiceItem.ap_invoice_id==APInvoice.id
              ).outerjoin(rek, KegiatanItem.rekening_id==rek.id
              ).filter(Kegiatan.kode!='0.00.00.99', KegiatanSub.unit_id==self.session['unit_id'], 
              KegiatanSub.tahun_id==self.session['tahun']
              ).group_by(Unit.id, Unit.kode, Unit.nama, Kegiatan.kode, Kegiatan.nama, 
              KegiatanSub.id, Rekening.id, Rekening.kode, Rekening.nama, KegiatanSub.tahun_id,
              ).order_by(Kegiatan.kode, Rekening.kode
              )

            rows = DBSession.query(Pegawai.nama.label('pa_nama'), Pegawai.kode.label('pa_nip')
               ).filter(Pejabat.pegawai_id==Pegawai.id, Pejabat.jabatan_id==Jabatan.id, 
               Pejabat.unit_id==self.session['unit_id'], Jabatan.kode=='200')
            for row1 in rows :
              pa_nama = row1.pa_nama
              pa_nip  = row1.pa_nama
            
            rows2 = DBSession.query(Pegawai.nama.label('bend_nama'), Pegawai.kode.label('bend_nip')
               ).filter(Pejabat.pegawai_id==Pegawai.id, Pejabat.jabatan_id==Jabatan.id, 
               Pejabat.unit_id==self.session['unit_id'], Jabatan.kode=='236')
            for row2 in rows2 :
              benda_nama = row2.bend_nama
              benda_nip  = row2.bend_nama
              
            generator = b104r300Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        ### SPJ Administratif
        elif url_dict['act']=='5' :
            bulan = 'bulan' in params and params['bulan'] and int(params['bulan']) or 0
            japbd = 'japbd' in params and params['japbd'] and int(params['japbd']) or 0
            rek = aliased(Rekening)
            query = DBSession.query(Unit.id.label('unit_id'), Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'),
              Kegiatan.kode.label('keg_kd'), Kegiatan.nama.label('keg_nm'), 
              KegiatanSub.id.label('keg_sub_id'), Rekening.id.label('rek_id'), Rekening.kode.label('rek_kd'),
              Rekening.nama.label('rek_nm'), KegiatanSub.tahun_id.label('tahun'), 
              func.sum(KegiatanItem.vol_2_1*KegiatanItem.vol_2_2*KegiatanItem.hsat_2).label('dpa'),                      
              func.sum(KegiatanItem.vol_4_1*KegiatanItem.vol_4_2*KegiatanItem.hsat_4).label('dppa'),
              func.coalesce(func.sum(case([(and_(extract('month',APInvoice.tanggal)<bulan, APInvoice.jenis==4,func.substr(rek.kode,1,5)=='5.1.1',func.substr(rek.kode,1,8)!='5.1.1.02'),APInvoiceItem.amount)], else_=0)),0).label('LSG_lalu'),
              func.coalesce(func.sum(case([(and_(extract('month',APInvoice.tanggal)==bulan, APInvoice.jenis==4,func.substr(rek.kode,1,5)=='5.1.1',func.substr(rek.kode,1,8)!='5.1.1.02'),APInvoiceItem.amount)], else_=0)),0).label('LSG_kini'),
              func.coalesce(func.sum(case([(and_(extract('month',APInvoice.tanggal)<bulan, APInvoice.jenis==4,or_(func.substr(rek.kode,1,5)!='5.1.1',func.substr(rek.kode,1,8)=='5.1.1.02')),APInvoiceItem.amount)], else_=0)),0).label('LS_lalu'),
              func.coalesce(func.sum(case([(and_(extract('month',APInvoice.tanggal)==bulan, APInvoice.jenis==4,or_(func.substr(rek.kode,1,5)!='5.1.1',func.substr(rek.kode,1,8)=='5.1.1.02')),APInvoiceItem.amount)], else_=0)),0).label('LS_kini'),
              func.coalesce(func.sum(case([(and_(extract('month',APInvoice.tanggal)<bulan, not_(APInvoice.jenis==4)),APInvoiceItem.amount)], else_=0)),0).label('Lain_lalu'),
              func.coalesce(func.sum(case([(and_(extract('month',APInvoice.tanggal)==bulan, not_(APInvoice.jenis==4)),APInvoiceItem.amount)], else_=0)),0).label('Lain_kini')
              ).join(KegiatanSub, KegiatanItem, Rekening, Kegiatan
              ).outerjoin(APInvoiceItem, APInvoiceItem.kegiatan_item_id==KegiatanItem.id
              ).outerjoin(APInvoice, APInvoiceItem.ap_invoice_id==APInvoice.id
              ).outerjoin(rek, KegiatanItem.rekening_id==rek.id
              ).filter(Kegiatan.kode!='0.00.00.99', KegiatanSub.unit_id==self.session['unit_id'], 
              KegiatanSub.tahun_id==self.session['tahun']
              ).group_by(Unit.id, Unit.kode, Unit.nama, Kegiatan.kode, Kegiatan.nama, 
              KegiatanSub.id, Rekening.id, Rekening.kode, Rekening.nama, KegiatanSub.tahun_id,
              ).order_by(Kegiatan.kode, Rekening.kode
              )
              
            rows = DBSession.query(Pegawai.nama.label('pa_nama'), Pegawai.kode.label('pa_nip')
               ).filter(Pejabat.pegawai_id==Pegawai.id, Pejabat.jabatan_id==Jabatan.id, 
               Pejabat.unit_id==self.session['unit_id'], Jabatan.kode=='200')
            for row1 in rows :
              pa_nama = row1.pa_nama
              pa_nip  = row1.pa_nama
            
            rows2 = DBSession.query(Pegawai.nama.label('bend_nama'), Pegawai.kode.label('bend_nip')
               ).filter(Pejabat.pegawai_id==Pegawai.id, Pejabat.jabatan_id==Jabatan.id, 
               Pejabat.unit_id==self.session['unit_id'], Jabatan.kode=='236')
            for row2 in rows2 :
              benda_nama = row2.bend_nama
              benda_nip  = row2.bend_nama
              
            generator = b104r400Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        ###SP2D
        elif url_dict['act']=='61' :
            if tipe ==0 :
               query = DBSession.query(Spp.tahun_id.label('tahun'), Unit.id.label('unit_id'), Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'),
                  Spp.jenis, 
                  Sp2d.kode.label('sp2d_kd'), Sp2d.tanggal.label('tgl_sp2d'), Sp2d.nama.label('sp2d_nm'),
                  Sp2d.bud_nip, Sp2d.bud_nama, Spp.ap_nama, Spp.nama.label('spp_nm'), 
                  func.sum(case([(func.substr(Rekening.kode,1,5)=='5.1.1',APInvoiceItem.amount)], else_=0)).label('nominal_gj'),
                  func.sum(case([(func.substr(Rekening.kode,1,5)!='5.1.1',APInvoiceItem.amount)], else_=0)).label('nominal')
                  ).filter(Sp2d.ap_spm_id==Spm.id, Spm.ap_spp_id==Spp.id, Spp.unit_id==Unit.id,
                  SppItem.ap_spp_id==Spp.id, APInvoiceItem.ap_invoice_id==SppItem.ap_invoice_id,
                  APInvoiceItem.kegiatan_item_id==KegiatanItem.id,
                  KegiatanItem.rekening_id==Rekening.id, Spp.unit_id==self.session['unit_id'],
                  Spp.tahun_id==self.session['tahun'],
                  Sp2d.tanggal.between(mulai,selesai)        
                  ).group_by(Spp.tahun_id, Unit.id, Unit.kode, Unit.nama,
                  Spp.jenis, Sp2d.kode, Sp2d.tanggal, Sp2d.nama,
                  Sp2d.bud_nip, Sp2d.bud_nama, Spp.ap_nama, Spp.nama 
                  ).order_by(Sp2d.tanggal).all()

            else:
               query = DBSession.query(Spp.tahun_id.label('tahun'), Unit.id.label('unit_id'), Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'),
                  Spp.jenis, 
                  Sp2d.kode.label('sp2d_kd'), Sp2d.tanggal.label('tgl_sp2d'), Sp2d.nama.label('sp2d_nm'),
                  Sp2d.bud_nip, Sp2d.bud_nama, Spp.ap_nama, Spp.nama.label('spp_nm'), 
                  func.sum(case([(func.substr(Rekening.kode,1,5)=='5.1.1',APInvoiceItem.amount)], else_=0)).label('nominal_gj'),
                  func.sum(case([(func.substr(Rekening.kode,1,5)!='5.1.1',APInvoiceItem.amount)], else_=0)).label('nominal')
                  ).filter(Sp2d.ap_spm_id==Spm.id, Spm.ap_spp_id==Spp.id, Spp.unit_id==Unit.id,
                  SppItem.ap_spp_id==Spp.id, APInvoiceItem.ap_invoice_id==SppItem.ap_invoice_id,
                  APInvoiceItem.kegiatan_item_id==KegiatanItem.id,
                  KegiatanItem.rekening_id==Rekening.id, Spp.unit_id==self.session['unit_id'],
                  Spp.tahun_id==self.session['tahun'], Spp.jenis==tipe,
                  Sp2d.tanggal.between(mulai,selesai)        
                  ).group_by(Spp.tahun_id, Unit.id, Unit.kode, Unit.nama,
                  Spp.jenis, Sp2d.kode, Sp2d.tanggal, Sp2d.nama,
                  Sp2d.bud_nip, Sp2d.bud_nama, Spp.ap_nama, Spp.nama 
                  ).order_by(Sp2d.tanggal).all()

            generator = b204r0000Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
        elif url_dict['act']=='621' :
            if tipe ==0 :
                query = DBSession.query(Spp.tahun_id.label('tahun'), Unit.id.label('unit_id'), Unit.kode.label('unit_kd'), 
                  Unit.nama.label('unit_nm'), Spp.nama.label('spp_nm'), Spp.jenis, Spp.ap_nama,
                  Sp2d.kode.label('sp2d_kd'), Sp2d.tanggal.label('tgl_sp2d'), Sp2d.nama.label('sp2d_nm'),
                  Sp2d.bud_nip, Sp2d.bud_nama,  
                  func.sum(case([(Spp.jenis==1,APInvoiceItem.amount)], else_=0)).label('UP'),
                  func.sum(case([(Spp.jenis==2,APInvoiceItem.amount)], else_=0)).label('TU'),
                  func.sum(case([(Spp.jenis==3,APInvoiceItem.amount)], else_=0)).label('GU'),
                  func.sum(case([(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)=='5.1.1'),APInvoiceItem.amount)], else_=0)).label('LS_GJ'),
                  func.sum(case([(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)!='5.1.1'),APInvoiceItem.amount)], else_=0)).label('LS')
                  ).filter(Sp2d.ap_spm_id==Spm.id, Spm.ap_spp_id==Spp.id, Spp.unit_id==Unit.id,
                  SppItem.ap_spp_id==Spp.id, APInvoiceItem.ap_invoice_id==SppItem.ap_invoice_id,
                  APInvoiceItem.kegiatan_item_id==KegiatanItem.id,
                  KegiatanItem.rekening_id==Rekening.id, Spp.unit_id==self.session['unit_id'],
                  Spp.tahun_id==self.session['tahun'],  
                  Sp2d.tanggal.between(mulai,selesai)        
                  ).group_by(Spp.tahun_id, Unit.id, Unit.kode, Unit.nama, Spp.nama, Spp.jenis, Spp.ap_nama, 
                  Sp2d.tanggal, Sp2d.kode, Sp2d.nama, Sp2d.bud_nip, Sp2d.bud_nama, 
                  ).order_by(Sp2d.tanggal).all()
            else:
                query = DBSession.query(Spp.tahun_id.label('tahun'), Unit.id.label('unit_id'), Unit.kode.label('unit_kd'), 
                  Unit.nama.label('unit_nm'), Spp.nama.label('spp_nm'), Spp.jenis, Spp.ap_nama,
                  Sp2d.kode.label('sp2d_kd'), Sp2d.tanggal.label('tgl_sp2d'), Sp2d.nama.label('sp2d_nm'),
                  Sp2d.bud_nip, Sp2d.bud_nama,  
                  func.sum(case([(Spp.jenis==1,APInvoiceItem.amount)], else_=0)).label('UP'),
                  func.sum(case([(Spp.jenis==2,APInvoiceItem.amount)], else_=0)).label('TU'),
                  func.sum(case([(Spp.jenis==3,APInvoiceItem.amount)], else_=0)).label('GU'),
                  func.sum(case([(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)=='5.1.1'),APInvoiceItem.amount)], else_=0)).label('LS_GJ'),
                  func.sum(case([(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)!='5.1.1'),APInvoiceItem.amount)], else_=0)).label('LS')
                  ).filter(Sp2d.ap_spm_id==Spm.id, Spm.ap_spp_id==Spp.id, Spp.unit_id==Unit.id,
                  SppItem.ap_spp_id==Spp.id, APInvoiceItem.ap_invoice_id==SppItem.ap_invoice_id,
                  APInvoiceItem.kegiatan_item_id==KegiatanItem.id,
                  KegiatanItem.rekening_id==Rekening.id, Spp.unit_id==self.session['unit_id'],
                  Spp.tahun_id==self.session['tahun'],  Spp.jenis==tipe,  
                  Sp2d.tanggal.between(mulai,selesai)        
                  ).group_by(Spp.tahun_id, Unit.id, Unit.kode, Unit.nama, Spp.nama, Spp.jenis, Spp.ap_nama, 
                  Sp2d.tanggal, Sp2d.kode, Sp2d.nama, Sp2d.bud_nip, Sp2d.bud_nama, 
                  ).order_by(Sp2d.tanggal).all()

            generator = b204r0001Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        elif url_dict['act']=='64' :
            if tipe ==0 :
               query = DBSession.query(Spp.tahun_id.label('tahun'), Unit.id.label('unit_id'), Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'),
                  Spp.jenis, 
                  Sp2d.kode.label('sp2d_kd'), Sp2d.tanggal.label('tgl_sp2d'), Sp2d.nama.label('sp2d_nm'),
                  Sp2d.bud_nip, Sp2d.bud_nama, Spp.ap_nama, Spp.nama.label('spp_nm'), 
                  func.sum(case([(func.substr(Rekening.kode,1,5)=='5.1.1',APInvoiceItem.amount)], else_=0)).label('nominal_gj'),
                  func.sum(case([(func.substr(Rekening.kode,1,5)!='5.1.1',APInvoiceItem.amount)], else_=0)).label('nominal')
                  ).filter(Sp2d.ap_spm_id==Spm.id, Spm.ap_spp_id==Spp.id, Spp.unit_id==Unit.id,
                  SppItem.ap_spp_id==Spp.id, APInvoiceItem.ap_invoice_id==SppItem.ap_invoice_id,
                  APInvoiceItem.kegiatan_item_id==KegiatanItem.id,
                  KegiatanItem.rekening_id==Rekening.id, Spp.unit_id==self.session['unit_id'],
                  Spp.tahun_id==self.session['tahun'],
                  Sp2d.tanggal.between(mulai,selesai)        
                  ).group_by(Spp.tahun_id, Unit.id, Unit.kode, Unit.nama,
                  Spp.jenis, Sp2d.kode, Sp2d.tanggal, Sp2d.nama,
                  Sp2d.bud_nip, Sp2d.bud_nama, Spp.ap_nama, Spp.nama 
                  ).order_by(Sp2d.tanggal).all()
            else:
               query = DBSession.query(Spp.tahun_id.label('tahun'), Unit.id.label('unit_id'), Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'),
                  Spp.jenis, 
                  Sp2d.kode.label('sp2d_kd'), Sp2d.tanggal.label('tgl_sp2d'), Sp2d.nama.label('sp2d_nm'),
                  Sp2d.bud_nip, Sp2d.bud_nama, Spp.ap_nama, Spp.nama.label('spp_nm'), 
                  func.sum(case([(func.substr(Rekening.kode,1,5)=='5.1.1',APInvoiceItem.amount)], else_=0)).label('nominal_gj'),
                  func.sum(case([(func.substr(Rekening.kode,1,5)!='5.1.1',APInvoiceItem.amount)], else_=0)).label('nominal')
                  ).filter(Sp2d.ap_spm_id==Spm.id, Spm.ap_spp_id==Spp.id, Spp.unit_id==Unit.id,
                  SppItem.ap_spp_id==Spp.id, APInvoiceItem.ap_invoice_id==SppItem.ap_invoice_id,
                  APInvoiceItem.kegiatan_item_id==KegiatanItem.id,
                  KegiatanItem.rekening_id==Rekening.id, Spp.unit_id==self.session['unit_id'],
                  Spp.tahun_id==self.session['tahun'], Spp.jenis==tipe,
                  Sp2d.tanggal.between(mulai,selesai)        
                  ).group_by(Spp.tahun_id, Unit.id, Unit.kode, Unit.nama,
                  Spp.jenis, Sp2d.kode, Sp2d.tanggal, Sp2d.nama,
                  Sp2d.bud_nip, Sp2d.bud_nama, Spp.ap_nama, Spp.nama 
                  ).order_by(Sp2d.tanggal).all()

            generator = b204r0002Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        elif url_dict['act']=='65' :
            if tipe ==0 :
                query = DBSession.query(Spp.tahun_id.label('tahun'), Unit.id.label('unit_id'), Unit.kode.label('unit_kd'), 
                  Unit.nama.label('unit_nm'), Spp.nama.label('spp_nm'), Spp.jenis, Spp.ap_nama,
                  Spm.id.label('spm_id'),
                  Sp2d.kode.label('sp2d_kd'), Sp2d.tanggal.label('tgl_sp2d'), Sp2d.nama.label('sp2d_nm'),
                  Sp2d.bud_nip, Sp2d.bud_nama, func.sum(APInvoiceItem.amount).label('nominal'), 
                  ).filter(Sp2d.ap_spm_id==Spm.id, Spm.ap_spp_id==Spp.id, Spp.unit_id==Unit.id,
                  SppItem.ap_spp_id==Spp.id, APInvoiceItem.ap_invoice_id==SppItem.ap_invoice_id,
                  APInvoiceItem.kegiatan_item_id==KegiatanItem.id,
                  KegiatanItem.rekening_id==Rekening.id, Spp.unit_id==self.session['unit_id'],
                  Spp.tahun_id==self.session['tahun'], Spp.jenis==4, func.substr(Rekening.kode,1,5)=='5.1.1',
                  Sp2d.tanggal.between(mulai,selesai)        
                  ).group_by(Spp.tahun_id, Unit.id, Unit.kode, 
                  Unit.nama, Spp.nama, Spp.jenis, Spp.ap_nama,
                  Spm.id,
                  Sp2d.kode, Sp2d.tanggal, Sp2d.nama,
                  Sp2d.bud_nip, Sp2d.bud_nama
                  ).order_by(Sp2d.tanggal).all()
            else:
                query = DBSession.query(Spp.tahun_id.label('tahun'), Unit.id.label('unit_id'), Unit.kode.label('unit_kd'), 
                  Unit.nama.label('unit_nm'), Spp.nama.label('spp_nm'), Spp.jenis, Spp.ap_nama,
                  Spm.id.label('spm_id'),
                  Sp2d.kode.label('sp2d_kd'), Sp2d.tanggal.label('tgl_sp2d'), Sp2d.nama.label('sp2d_nm'),
                  Sp2d.bud_nip, Sp2d.bud_nama, func.sum(APInvoiceItem.amount).label('nominal'), 
                  ).filter(Sp2d.ap_spm_id==Spm.id, Spm.ap_spp_id==Spp.id, Spp.unit_id==Unit.id,
                  SppItem.ap_spp_id==Spp.id, APInvoiceItem.ap_invoice_id==SppItem.ap_invoice_id,
                  APInvoiceItem.kegiatan_item_id==KegiatanItem.id,
                  KegiatanItem.rekening_id==Rekening.id, Spp.unit_id==self.session['unit_id'],
                  Spp.tahun_id==self.session['tahun'], Spp.jenis==4, func.substr(Rekening.kode,1,5)=='5.1.1',
                  Sp2d.tanggal.between(mulai,selesai)        
                  ).group_by(Spp.tahun_id, Unit.id, Unit.kode, 
                  Unit.nama, Spp.nama, Spp.jenis, Spp.ap_nama,
                  Spm.id,
                  Sp2d.kode, Sp2d.tanggal, Sp2d.nama,
                  Sp2d.bud_nip, Sp2d.bud_nama
                  ).order_by(Sp2d.tanggal).all()

            generator = b204r0003Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        elif url_dict['act']=='66' :
            if tipe ==0 :
               query = DBSession.query(Spp.tahun_id.label('tahun'), Unit.id.label('unit_id'), Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'),
                  Spp.jenis, 
                  Sp2d.kode.label('sp2d_kd'), Sp2d.tanggal.label('tgl_sp2d'), Sp2d.nama.label('sp2d_nm'),
                  Sp2d.bud_nip, Sp2d.bud_nama, Spp.ap_nama, Spp.nama.label('spp_nm'), 
                  func.sum(case([(func.substr(Rekening.kode,1,5)=='5.1.1',APInvoiceItem.amount)], else_=0)).label('nominal_gj'),
                  func.sum(case([(func.substr(Rekening.kode,1,5)!='5.1.1',APInvoiceItem.amount)], else_=0)).label('nominal'),
                  func.sum(APInvoiceItem.ppn).label('ppn'),
                  func.sum(APInvoiceItem.pph).label('pph')
                  ).filter(Sp2d.ap_spm_id==Spm.id, Spm.ap_spp_id==Spp.id, Spp.unit_id==Unit.id,
                  SppItem.ap_spp_id==Spp.id, APInvoiceItem.ap_invoice_id==SppItem.ap_invoice_id,
                  APInvoiceItem.kegiatan_item_id==KegiatanItem.id,
                  KegiatanItem.rekening_id==Rekening.id, Spp.unit_id==self.session['unit_id'],
                  Spp.tahun_id==self.session['tahun'],
                  Sp2d.tanggal.between(mulai,selesai)        
                  ).group_by(Spp.tahun_id, Unit.id, Unit.kode, Unit.nama,
                  Spp.jenis, Sp2d.kode, Sp2d.tanggal, Sp2d.nama,
                  Sp2d.bud_nip, Sp2d.bud_nama, Spp.ap_nama, Spp.nama 
                  ).order_by(Sp2d.tanggal).all()
            else:
               query = DBSession.query(Spp.tahun_id.label('tahun'), Unit.id.label('unit_id'), Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'),
                  Spp.jenis, 
                  Sp2d.kode.label('sp2d_kd'), Sp2d.tanggal.label('tgl_sp2d'), Sp2d.nama.label('sp2d_nm'),
                  Sp2d.bud_nip, Sp2d.bud_nama, Spp.ap_nama, Spp.nama.label('spp_nm'), 
                  func.sum(case([(func.substr(Rekening.kode,1,5)=='5.1.1',APInvoiceItem.amount)], else_=0)).label('nominal_gj'),
                  func.sum(case([(func.substr(Rekening.kode,1,5)!='5.1.1',APInvoiceItem.amount)], else_=0)).label('nominal'),
                  func.sum(APInvoiceItem.ppn).label('ppn'),
                  func.sum(APInvoiceItem.pph).label('pph')
                  ).filter(Sp2d.ap_spm_id==Spm.id, Spm.ap_spp_id==Spp.id, Spp.unit_id==Unit.id,
                  SppItem.ap_spp_id==Spp.id, APInvoiceItem.ap_invoice_id==SppItem.ap_invoice_id,
                  APInvoiceItem.kegiatan_item_id==KegiatanItem.id,
                  KegiatanItem.rekening_id==Rekening.id, Spp.unit_id==self.session['unit_id'],
                  Spp.tahun_id==self.session['tahun'], Spp.jenis==tipe,
                  Sp2d.tanggal.between(mulai,selesai)        
                  ).group_by(Spp.tahun_id, Unit.id, Unit.kode, Unit.nama,
                  Spp.jenis, Sp2d.kode, Sp2d.tanggal, Sp2d.nama,
                  Sp2d.bud_nip, Sp2d.bud_nama, Spp.ap_nama, Spp.nama 
                  ).order_by(Sp2d.tanggal).all()

            generator = b204r0004Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        elif url_dict['act']=='sp2d' :
            pk_id = 'id' in params and params['id'] and int(params['id']) or 0
            subq1 = DBSession.query(Sp2d.id.label('sp2d_id'), Sp2d.kode.label('sp2d_kd'), Sp2d.tanggal.label('sp2d_tgl'), 
                     Spm.id.label('spm_id'), Spm.kode.label('spm_kd'), Spm.nama.label('spm_nm'), Spm.tanggal.label('spm_tgl'), Spp.id.label('spp_id'), 
                     Spp.kode.label('spp_kd'), Spp.nama.label('spp_nm'), Spp.tanggal.label('spp_tgl'), Spp.jenis.label('jenis'), 
                     Spp.ap_nama.label('ap_nama'), Spp.ap_bank.label('ap_bank'), Spp.ap_rekening.label('ap_rekening'), Spp.ap_npwp.label('ap_npwp'), 
                     Spp.tahun_id.label('tahun_id'), Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'), Kegiatan.kode.label('keg_kd'), 
                     Kegiatan.nama.label('keg_nm'), Program.kode.label('prg_kd'), Program.nama.label('prg_nm'), 
                     func.sum(APInvoiceItem.amount).label('nilai'), func.sum(APInvoiceItem.ppn).label('ppn'), 
                     func.sum(APInvoiceItem.pph).label('pph'), literal_column('0').label('potongan')
                     ).filter(Sp2d.ap_spm_id==Spm.id, Spm.ap_spp_id==Spp.id, Spp.unit_id==Unit.id,
                     SppItem.ap_spp_id==Spp.id, SppItem.ap_invoice_id==APInvoiceItem.ap_invoice_id, APInvoiceItem.kegiatan_item_id==KegiatanItem.id,
                     KegiatanItem.rekening_id==Rekening.id, KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                     KegiatanSub.kegiatan_id==Kegiatan.id, Kegiatan.program_id==Program.id,
                     Spp.unit_id==self.session['unit_id'], Spp.tahun_id==self.session['tahun'], Sp2d.id==pk_id,
                     func.left(Rekening.kode,1)=='5'
                     ).group_by(Sp2d.id, Sp2d.kode, Sp2d.tanggal, Spm.id, Spm.kode, 
                     Spm.nama, Spm.tanggal, Spp.id, Spp.kode, Spp.nama, Spp.tanggal, 
                     Spp.jenis, Spp.ap_nama, Spp.ap_bank, 
                     Spp.ap_rekening, Spp.ap_npwp, Spp.tahun_id, Unit.kode, Unit.nama, 
                     Kegiatan.kode, Kegiatan.nama, Program.kode, Program.nama 
                     )                         

            subq2 = DBSession.query(Sp2d.id.label('sp2d_id'), Sp2d.kode.label('sp2d_kd'), Sp2d.tanggal.label('sp2d_tgl'), 
                     Spm.id.label('spm_id'), Spm.kode.label('spm_kd'), Spm.nama.label('spm_nm'), Spm.tanggal.label('spm_tgl'), Spp.id.label('spp_id'), 
                     Spp.kode.label('spp_kd'), Spp.nama.label('spp_nm'), Spp.tanggal.label('spp_tgl'), Spp.jenis.label('jenis'), 
                     Spp.ap_nama.label('ap_nama'), Spp.ap_bank.label('ap_bank'), Spp.ap_rekening.label('ap_rekening'), Spp.ap_npwp.label('ap_npwp'), 
                     Spp.tahun_id.label('tahun_id'), Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'), Kegiatan.kode.label('keg_kd'), 
                     Kegiatan.nama.label('keg_nm'), Program.kode.label('prg_kd'), Program.nama.label('prg_nm'), 
                     literal_column('0').label('nilai'), literal_column('0').label('ppn'), 
                     literal_column('0').label('pph'), func.sum(APInvoiceItem.amount).label('potongan')
                     ).filter(Sp2d.ap_spm_id==Spm.id, Spm.ap_spp_id==Spp.id, Spp.unit_id==Unit.id,
                     SppItem.ap_spp_id==Spp.id, SppItem.ap_invoice_id==APInvoiceItem.ap_invoice_id, APInvoiceItem.kegiatan_item_id==KegiatanItem.id,
                     KegiatanItem.rekening_id==Rekening.id, KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                     KegiatanSub.kegiatan_id==Kegiatan.id, Kegiatan.program_id==Program.id,
                     Spp.unit_id==self.session['unit_id'], Spp.tahun_id==self.session['tahun'], Sp2d.id==pk_id,
                     func.left(Rekening.kode,1)=='7'
                     ).group_by(Sp2d.id, Sp2d.kode, Sp2d.tanggal, Spm.id, Spm.kode, 
                     Spm.nama, Spm.tanggal, Spp.id, Spp.kode, Spp.nama, Spp.tanggal, 
                     Spp.jenis, Spp.ap_nama, Spp.ap_bank, 
                     Spp.ap_rekening, Spp.ap_npwp, Spp.tahun_id, Unit.kode, Unit.nama, 
                     Kegiatan.kode, Kegiatan.nama, Program.kode, Program.nama 
                     )                         
            
            subq = subq1.union(subq2).subquery()
            
            query = DBSession.query(subq.c.sp2d_id, subq.c.sp2d_kd, subq.c.sp2d_tgl, subq.c.spm_id, subq.c.spm_kd, 
                     subq.c.spm_nm, subq.c.spm_tgl, subq.c.spp_id, subq.c.spp_kd, subq.c.spp_nm, subq.c.spp_tgl, 
                     subq.c.jenis, subq.c.ap_nama, subq.c.ap_bank, subq.c.ap_rekening, 
                     subq.c.ap_npwp, subq.c.tahun_id, subq.c.unit_kd, subq.c.unit_nm, subq.c.keg_kd, subq.c.keg_nm, subq.c.prg_kd, 
                     subq.c.prg_nm, func.sum(subq.c.nilai).label('nilai'),func.sum(subq.c.ppn).label('ppn'), 
                     func.sum(subq.c.pph).label('pph'),func.sum(subq.c.potongan).label('potongan')
                     ).group_by(subq.c.sp2d_id, subq.c.sp2d_kd, subq.c.sp2d_tgl, subq.c.spm_id, subq.c.spm_kd, 
                     subq.c.spm_nm, subq.c.spm_tgl, subq.c.spp_id, subq.c.spp_kd, subq.c.spp_nm, subq.c.spp_tgl, 
                     subq.c.jenis, subq.c.ap_nama, subq.c.ap_bank, subq.c.ap_rekening, 
                     subq.c.ap_npwp, subq.c.tahun_id, subq.c.unit_kd, subq.c.unit_nm, subq.c.keg_kd, subq.c.keg_nm, subq.c.prg_kd, 
                     subq.c.prg_nm
                     )                         

            generator = b203r001Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

    #### Realisasi
    @view_config(route_name="ap-report-real", renderer="templates/report-skpd/realisasi.pt", permission="read")
    def ar_report_real(self):
        params = self.request.params
        return dict(datas=self.datas,)

    @view_config(route_name="ap-report-real-act", renderer="json", permission="read")
    def ap_report_real_act(self):
        global bln
        global status
        global tipe
        req    = self.request
        params = req.params
        url_dict = req.matchdict

        bln = 'bulan' in params and params['bulan'] and int(params['bulan']) or 0
        status = 'status' in params and params['status'] and int(params['status']) or 0
        tipe = 'tipe' in params and params['tipe'] and int(params['tipe']) or 0
        #### Realisasi 1
        if url_dict['act']=='1' :
            subq1 = DBSession.query(Rekening.kode.label('subrek_kd'),Rekening.nama.label('subrek_nm'),
                KegiatanSub.tahun_id.label('tahun_id'),
                func.sum(KegiatanItem.vol_2_1* KegiatanItem.vol_2_2*KegiatanItem.hsat_2).label('jml1'), 
                func.sum(KegiatanItem.vol_4_1* KegiatanItem.vol_4_2*KegiatanItem.hsat_4).label('jml2'), 
                sqlalchemy.sql.literal_column("0").label('realisasi')
                ).filter(KegiatanItem.kegiatan_sub_id==KegiatanSub.id, 
                        KegiatanItem.rekening_id==Rekening.id,
                        KegiatanSub.tahun_id==self.session['tahun']
                ).group_by(Rekening.kode,Rekening.nama,KegiatanSub.tahun_id)
                
            subq2 = DBSession.query(Rekening.kode.label('subrek_kd'),Rekening.nama.label('subrek_nm'),
                Spp.tahun_id.label('tahun_id'), sqlalchemy.sql.literal_column("0").label('jml1'), sqlalchemy.sql.literal_column("0").label('jml2'),
                func.sum(APInvoiceItem.amount).label('realisasi')
                ).filter(APInvoiceItem.kegiatan_item_id==KegiatanItem.id,
                        KegiatanItem.rekening_id==Rekening.id,
                        APInvoiceItem.ap_invoice_id==SppItem.ap_invoice_id,
                        SppItem.ap_spp_id==Spp.id, 
                        Spm.ap_spp_id==Spp.id,                            
                        Sp2d.ap_spm_id==Spm.id, 
                        Spp.tahun_id==self.session['tahun'], extract('month',Sp2d.tanggal) <= bln,
                ).group_by(Rekening.kode, Rekening.nama, Spp.tahun_id)
            
            subq = subq1.union(subq2).subquery()

            query = DBSession.query(Rekening.kode.label('rek_kd'), Rekening.nama.label('rek_nm'),
                Rekening.level_id, Rekening.defsign, subq.c.tahun_id,  
                func.sum(subq.c.jml1).label('jumlah1'), func.sum(subq.c.jml2).label('jumlah2'),
                func.sum(subq.c.realisasi).label('realisasi'),
                ).filter(Rekening.kode==func.left(subq.c.subrek_kd, func.length(Rekening.kode)),
                Rekening.level_id<=tipe, func.substr(Rekening.kode,1,1)<'7'
                ).group_by(Rekening.kode, Rekening.nama,
                Rekening.level_id, Rekening.defsign, subq.c.tahun_id
                ).order_by(Rekening.kode).all()                    

            generator = b204r100Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        #### Realisasi 2
        elif url_dict['act']=='2' :
            subq1 = DBSession.query(Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'),Rekening.kode.label('subrek_kd'),Rekening.nama.label('subrek_nm'),
                KegiatanSub.tahun_id.label('tahun_id'),
                func.sum(KegiatanItem.vol_2_1* KegiatanItem.vol_2_2*KegiatanItem.hsat_2).label('jml1'), 
                func.sum(KegiatanItem.vol_4_1* KegiatanItem.vol_4_2*KegiatanItem.hsat_4).label('jml2'), 
                sqlalchemy.sql.literal_column("0").label('realisasi')
                ).filter(KegiatanItem.kegiatan_sub_id==KegiatanSub.id, KegiatanSub.unit_id==Unit.id, 
                        KegiatanItem.rekening_id==Rekening.id,
                        KegiatanSub.tahun_id==self.session['tahun'], KegiatanSub.unit_id==self.session['unit_id']
                ).group_by(Unit.kode, Unit.nama, Rekening.kode, Rekening.nama, KegiatanSub.tahun_id)
                
            subq2 = DBSession.query(Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'), Rekening.kode.label('subrek_kd'),Rekening.nama.label('subrek_nm'),
                Spp.tahun_id.label('tahun_id'), sqlalchemy.sql.literal_column("0").label('jml1'), sqlalchemy.sql.literal_column("0").label('jml2'),
                func.sum(APInvoiceItem.amount).label('realisasi')
                ).filter(APInvoiceItem.kegiatan_item_id==KegiatanItem.id,
                        KegiatanItem.rekening_id==Rekening.id,
                        APInvoiceItem.ap_invoice_id==SppItem.ap_invoice_id,
                        SppItem.ap_spp_id==Spp.id, Spp.unit_id==Unit.id, 
                        Spm.ap_spp_id==Spp.id,                            
                        Sp2d.ap_spm_id==Spm.id, 
                        Spp.tahun_id==self.session['tahun'], extract('month',Sp2d.tanggal) <= bln,
                        Spp.unit_id==self.session['unit_id']
                ).group_by(Unit.kode, Unit.nama, Rekening.kode, Rekening.nama, Spp.tahun_id)
            
            subq = subq1.union(subq2).subquery()

            query = DBSession.query(Rekening.kode.label('rek_kd'), Rekening.nama.label('rek_nm'),
                Rekening.level_id, Rekening.defsign, subq.c.tahun_id, subq.c.unit_kd, subq.c.unit_nm, 
                func.sum(subq.c.jml1).label('jumlah1'), func.sum(subq.c.jml2).label('jumlah2'),
                func.sum(subq.c.realisasi).label('realisasi'),
                ).filter(Rekening.kode==func.left(subq.c.subrek_kd, func.length(Rekening.kode)),
                Rekening.level_id<=tipe, func.substr(Rekening.kode,1,1)<'7'
                ).group_by(Rekening.kode, Rekening.nama,
                Rekening.level_id, Rekening.defsign, subq.c.tahun_id, subq.c.unit_kd, subq.c.unit_nm
                ).order_by(Rekening.kode).all()                    

            generator = b204r300Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        elif url_dict['act']=='3' :
            subq1 = DBSession.query(Rekening.kode.label('subrek_kd'),Rekening.nama.label('subrek_nm'),
                Unit.id.label('unit_id'),Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'),
                Urusan.kode.label('urusan_kd'), Urusan.nama.label('urusan_nm'), 
                KegiatanSub.tahun_id.label('tahun_id'),
                Program.kode.label('program_kd'), Program.nama.label('program_nm'), 
                Kegiatan.kode.label('kegiatan_kd'), Kegiatan.nama.label('kegiatan_nm'),
                func.sum(KegiatanItem.vol_2_1* KegiatanItem.vol_2_2*KegiatanItem.hsat_2).label('jml1'), 
                func.sum(KegiatanItem.vol_4_1* KegiatanItem.vol_4_2*KegiatanItem.hsat_4).label('jml2'), 
                sqlalchemy.sql.literal_column("0").label('realisasi')
                ).filter(KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                        KegiatanItem.rekening_id==Rekening.id, KegiatanSub.unit_id==Unit.id, 
                        Unit.urusan_id==Urusan.id, KegiatanSub.kegiatan_id==Kegiatan.id,
                        Kegiatan.program_id==Program.id,
                        KegiatanSub.tahun_id==self.session['tahun'], KegiatanSub.unit_id==self.session['unit_id']
                ).group_by(Rekening.kode,Rekening.nama,Unit.id,Unit.kode, Unit.nama,Urusan.kode, Urusan.nama, KegiatanSub.tahun_id,
                Program.kode, Program.nama, Kegiatan.kode, Kegiatan.nama,
                )
            
            subq2 = DBSession.query(Rekening.kode.label('subrek_kd'),Rekening.nama.label('subrek_nm'),
                Unit.id.label('unit_id'),Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'),
                Urusan.kode.label('urusan_kd'), Urusan.nama.label('urusan_nm'), 
                Spp.tahun_id.label('tahun_id'), 
                Program.kode.label('program_kd'), Program.nama.label('program_nm'), 
                Kegiatan.kode.label('kegiatan_kd'), Kegiatan.nama.label('kegiatan_nm'),
                sqlalchemy.sql.literal_column("0").label('jml1'), sqlalchemy.sql.literal_column("0").label('jml2'),
                func.sum(APInvoiceItem.amount).label('realisasi')
                ).filter(APInvoiceItem.kegiatan_item_id==KegiatanItem.id,
                        KegiatanItem.rekening_id==Rekening.id,
                        APInvoiceItem.ap_invoice_id==SppItem.ap_invoice_id,
                        SppItem.ap_spp_id==Spp.id,
                        Spp.unit_id==Unit.id,
                        Unit.urusan_id==Urusan.id,
                        KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                        KegiatanSub.kegiatan_id==Kegiatan.id,
                        Kegiatan.program_id==Program.id,
                        Spm.ap_spp_id==Spp.id,                            
                        Sp2d.ap_spm_id==Spm.id, 
                        Spp.tahun_id==self.session['tahun'], extract('month',Sp2d.tanggal) <= bln,
                        Spp.unit_id==self.session['unit_id']
                ).group_by(Rekening.kode, Rekening.nama, Unit.id, Unit.kode, Unit.nama,
                        Urusan.kode, Urusan.nama, Spp.tahun_id, Program.kode, Program.nama, 
                        Kegiatan.kode, Kegiatan.nama
                )

            subq = subq1.union(subq2).subquery()
            
            query = DBSession.query(Rekening.kode.label('rek_kd'), Rekening.nama.label('rek_nm'),
                Rekening.level_id, Rekening.defsign, Rekening.id.label('rekening_id'),
                subq.c.unit_id, subq.c.unit_kd, subq.c.unit_nm, subq.c.urusan_kd, subq.c.urusan_nm, 
                subq.c.tahun_id, subq.c.program_kd, subq.c.program_nm, subq.c.kegiatan_kd, subq.c.kegiatan_nm, 
                case([(subq.c.kegiatan_kd=='0.00.00.10',1),(subq.c.kegiatan_kd=='0.00.00.21',2),
                (subq.c.kegiatan_kd=='0.00.00.31',4),(subq.c.kegiatan_kd=='0.00.00.32',5)], 
                else_=3).label('jenis'),                    
                func.sum(subq.c.jml1).label('jumlah1'), func.sum(subq.c.jml2).label('jumlah2'), func.sum(subq.c.realisasi).label('realisasi')
                ).filter(Rekening.level_id<=tipe, 
                Rekening.kode==func.left(subq.c.subrek_kd, func.length(Rekening.kode)), func.substr(Rekening.kode,1,1)<'7'
                ).group_by(Rekening.kode, Rekening.nama,
                Rekening.level_id, Rekening.defsign, Rekening.id, 
                subq.c.unit_id, subq.c.unit_kd, subq.c.unit_nm, subq.c.urusan_kd, subq.c.urusan_nm, subq.c.tahun_id,
                subq.c.program_kd, subq.c.program_nm, subq.c.kegiatan_kd, subq.c.kegiatan_nm,
                case([(subq.c.kegiatan_kd=='0.00.00.10',1),(subq.c.kegiatan_kd=='0.00.00.21',2),
                (subq.c.kegiatan_kd=='0.00.00.31',4),(subq.c.kegiatan_kd=='0.00.00.32',5)], 
                else_=3))\
                .order_by(case([(subq.c.kegiatan_kd=='0.00.00.10',1),(subq.c.kegiatan_kd=='0.00.00.21',2),
                (subq.c.kegiatan_kd=='0.00.00.31',4),(subq.c.kegiatan_kd=='0.00.00.32',5)], 
                else_=3),subq.c.urusan_kd, subq.c.unit_kd, subq.c.program_kd, subq.c.kegiatan_kd, Rekening.kode).all() 
        
            generator = b204r200Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

    """
    # LAPORAN AKUNTANSI
    @view_config(route_name="ak-report-skpd", renderer="templates/report-skpd/ak-report-skpd.pt", permission="read")
    def ak_report_skpd(self):
        params = self.request.params
        return dict(datas=self.datas,)

    @view_config(route_name="ak-report-skpd-act", renderer="json", permission="read")
    def ak_report_skpd_act(self):
        global mulai, selesai, tingkat, tahun_lalu
        req    = self.request
        params = req.params
        url_dict = req.matchdict
 
        mulai   = 'mulai' in params and params['mulai'] or 0
        selesai = 'selesai' in params and params['selesai'] or 0
        kel   = 'kel' in params and params['kel'] or 0
        rekid = 'rekid' in params and params['rekid'] or 0
        sapid   = 'sapid' in params and params['sapid'] or 0
        tahun_lalu = self.session['tahun']-1
        tahun_kini = self.session['tahun']
        print "TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT", tahun_lalu
          
        if url_dict['act']=='bb' :
            if kel == '1' :
                query = DBSession.query(AkJurnal.kode.label('jurnal_kd'), AkJurnal.nama.label('jurnal_nm'), AkJurnal.tanggal, AkJurnal.tgl_transaksi, 
                   AkJurnal.tahun_id, Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'), AkJurnal.periode, AkJurnal.jv_type, AkJurnal.source, AkJurnal.source_no,
                   AkJurnalItem.amount, Sap.kode.label('rek_kd'), Sap.nama.label('rek_nm'), 
                   ).filter(AkJurnal.id==AkJurnalItem.ak_jurnal_id, AkJurnal.unit_id==Unit.id, 
                   AkJurnal.unit_id==self.session['unit_id'], 
                   AkJurnal.tahun_id==self.session['tahun'], AkJurnal.tanggal.between(mulai,selesai),
                   AkJurnalItem.sap_id==Sap.id, AkJurnal.is_skpd==0
                   ).order_by(AkJurnal.tanggal).all()
                generator = b105r011Generator()
                pdf = generator.generate(query)
                response=req.response
                response.content_type="application/pdf"
                response.content_disposition='filename=output.pdf' 
                response.write(pdf)
                return response
            elif kel == '2' :
                query = DBSession.query(AkJurnal.kode.label('jurnal_kd'), AkJurnal.nama.label('jurnal_nm'), AkJurnal.tanggal, AkJurnal.tgl_transaksi, 
                   AkJurnal.tahun_id, Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'), AkJurnal.periode, AkJurnal.jv_type, AkJurnal.source, AkJurnal.source_no,
                   AkJurnalItem.amount, Sap.kode.label('rek_kd'), Sap.nama.label('rek_nm'), 
                   ).filter(AkJurnal.id==AkJurnalItem.ak_jurnal_id, AkJurnal.unit_id==Unit.id, 
                   AkJurnal.unit_id==self.session['unit_id'], 
                   AkJurnal.tahun_id==self.session['tahun'], AkJurnal.tanggal.between(mulai,selesai),
                   AkJurnalItem.sap_id==Sap.id, AkJurnal.is_skpd==1
                   ).order_by(AkJurnal.tanggal).all()
                generator = b105r012Generator()
                pdf = generator.generate(query)
                response=req.response
                response.content_type="application/pdf"
                response.content_disposition='filename=output.pdf' 
                response.write(pdf)
                return response

        elif url_dict['act']=='lrasap' :
          if kel=='1' :
              subq1 = DBSession.query(Unit.nama.label('unit_nm'), Sap.kode.label('subrek_kd'), Sap.nama.label('rek_nm'), 
                 AkJurnalItem.amount.label('amount_kini'), AkJurnal.tahun_id.label('tahun_kini'),
                 literal_column('0').label('amount_lalu'), literal_column(str(tahun_lalu)).label('tahun_lalu'),
                 ).filter(AkJurnalItem.sap_id==Sap.id, AkJurnalItem.ak_jurnal_id==AkJurnal.id, 
                 AkJurnal.unit_id==Unit.id, AkJurnalItem.amount>0, AkJurnal.is_skpd==0,
                 AkJurnal.tahun_id==self.session['tahun'], AkJurnal.unit_id==self.session['unit_id']
                 )
              subq2 = DBSession.query(Unit.nama.label('unit_nm'),Sap.kode.label('subrek_kd'), Sap.nama.label('rek_nm'), 
                 literal_column('0').label('amount_kini'), literal_column(str(tahun_kini)).label('tahun_kini'),
                 AkJurnalItem.amount.label('amount_lalu'), AkJurnal.tahun_id.label('tahun_lalu'),
                 ).filter(AkJurnalItem.sap_id==Sap.id, AkJurnalItem.ak_jurnal_id==AkJurnal.id, 
                 AkJurnal.unit_id==Unit.id, AkJurnalItem.amount>0, AkJurnal.is_skpd==0,
                 AkJurnal.tahun_id==tahun_lalu, AkJurnal.unit_id==self.session['unit_id']
                 )
                 
              subq = subq1.union(subq2).subquery()
              
              query = DBSession.query(Sap.kode, Sap.nama, Sap.level_id, subq.c.unit_nm, subq.c.tahun_kini, subq.c.tahun_lalu,
                 func.sum(subq.c.amount_kini).label('amount_kini'), func.sum(subq.c.amount_lalu).label('amount_lalu')
                 ).filter(Sap.kode==func.left(subq.c.subrek_kd, func.length(Sap.kode)),
                 #func.substr(Sap.kode,1,1).in_(['4','5','6']) 
                 ).group_by(Sap.kode, Sap.nama, Sap.level_id, subq.c.unit_nm, subq.c.tahun_kini, subq.c.tahun_lalu,
                 ).order_by(Sap.kode)
                 
              generator = b105r021Generator()
              pdf = generator.generate(query)
              response=req.response
              response.content_type="application/pdf"
              response.content_disposition='filename=output.pdf' 
              response.write(pdf)
              return response
          elif kel=='2' :
              subq1 = DBSession.query(Unit.nama.label('unit_nm'), Sap.kode.label('subrek_kd'), Sap.nama.label('rek_nm'), 
                 AkJurnalItem.amount.label('amount_kini'), AkJurnal.tahun_id.label('tahun_kini'),
                 literal_column('0').label('amount_lalu'), literal_column(str(tahun_lalu)).label('tahun_lalu'),
                 ).filter(AkJurnalItem.sap_id==Sap.id, AkJurnalItem.ak_jurnal_id==AkJurnal.id, 
                 AkJurnal.unit_id==Unit.id, AkJurnalItem.amount>0, AkJurnal.is_skpd==1,
                 AkJurnal.tahun_id==self.session['tahun'], AkJurnal.unit_id==self.session['unit_id']
                 )
              subq2 = DBSession.query(Unit.nama.label('unit_nm'),Sap.kode.label('subrek_kd'), Sap.nama.label('rek_nm'), 
                 literal_column('0').label('amount_kini'), literal_column(str(tahun_kini)).label('tahun_kini'),
                 AkJurnalItem.amount.label('amount_lalu'), AkJurnal.tahun_id.label('tahun_lalu'),
                 ).filter(AkJurnalItem.sap_id==Sap.id, AkJurnalItem.ak_jurnal_id==AkJurnal.id, 
                 AkJurnal.unit_id==Unit.id, AkJurnalItem.amount>0, AkJurnal.is_skpd==1,
                 AkJurnal.tahun_id==tahun_lalu, AkJurnal.unit_id==self.session['unit_id']
                 )
                 
              subq = subq1.union(subq2).subquery()
              
              query = DBSession.query(Sap.kode, Sap.nama, Sap.level_id, subq.c.unit_nm, subq.c.tahun_kini, subq.c.tahun_lalu,
                 func.sum(subq.c.amount_kini).label('amount_kini'), func.sum(subq.c.amount_lalu).label('amount_lalu')
                 ).filter(Sap.kode==func.left(subq.c.subrek_kd, func.length(Sap.kode)),
                 #func.substr(Sap.kode,1,1).in_(['4','5','6']) 
                 ).group_by(Sap.kode, Sap.nama, Sap.level_id, subq.c.unit_nm, subq.c.tahun_kini, subq.c.tahun_lalu,
                 ).order_by(Sap.kode)
              
              generator = b105r022Generator()
              pdf = generator.generate(query)
              response=req.response
              response.content_type="application/pdf"
              response.content_disposition='filename=output.pdf' 
              response.write(pdf)
              return response
              
        elif url_dict['act']=='lo' :
          if kel=='1' :
              subq1 = DBSession.query(Unit.nama.label('unit_nm'), Sap.kode.label('subrek_kd'), Sap.nama.label('rek_nm'), 
                 AkJurnalItem.amount.label('amount_kini'), AkJurnal.tahun_id.label('tahun_kini'),
                 literal_column('0').label('amount_lalu'), literal_column(str(tahun_lalu)).label('tahun_lalu'),
                 ).filter(AkJurnalItem.sap_id==Sap.id, AkJurnalItem.ak_jurnal_id==AkJurnal.id, 
                 AkJurnal.unit_id==Unit.id, AkJurnalItem.amount>0, AkJurnal.is_skpd==0,
                 AkJurnal.tahun_id==self.session['tahun'], AkJurnal.unit_id==self.session['unit_id']
                 )
              subq2 = DBSession.query(Unit.nama.label('unit_nm'),Sap.kode.label('subrek_kd'), Sap.nama.label('rek_nm'), 
                 literal_column('0').label('amount_kini'), literal_column(str(tahun_kini)).label('tahun_kini'),
                 AkJurnalItem.amount.label('amount_lalu'), AkJurnal.tahun_id.label('tahun_lalu'),
                 ).filter(AkJurnalItem.sap_id==Sap.id, AkJurnalItem.ak_jurnal_id==AkJurnal.id, 
                 AkJurnal.unit_id==Unit.id, AkJurnalItem.amount>0, AkJurnal.is_skpd==0,
                 AkJurnal.tahun_id==tahun_lalu, AkJurnal.unit_id==self.session['unit_id']
                 )
                 
              subq = subq1.union(subq2).subquery()
              
              query = DBSession.query(Sap.kode, Sap.nama, Sap.level_id, subq.c.unit_nm, subq.c.tahun_kini, subq.c.tahun_lalu,
                 func.sum(subq.c.amount_kini).label('amount_kini'), func.sum(subq.c.amount_lalu).label('amount_lalu')
                 ).filter(Sap.kode==func.left(subq.c.subrek_kd, func.length(Sap.kode)),
                 #func.substr(Sap.kode,1,1).in_(['8','9']) 
                 ).group_by(Sap.kode, Sap.nama, Sap.level_id, subq.c.unit_nm, subq.c.tahun_kini, subq.c.tahun_lalu,
                 ).order_by(Sap.kode)
                 
              generator = b105r051Generator()
              pdf = generator.generate(query)
              response=req.response
              response.content_type="application/pdf"
              response.content_disposition='filename=output.pdf' 
              response.write(pdf)
              return response
          elif kel=='2' :
              subq1 = DBSession.query(Unit.nama.label('unit_nm'), Sap.kode.label('subrek_kd'), Sap.nama.label('rek_nm'), 
                 AkJurnalItem.amount.label('amount_kini'), AkJurnal.tahun_id.label('tahun_kini'),
                 literal_column('0').label('amount_lalu'), literal_column(str(tahun_lalu)).label('tahun_lalu'),
                 ).filter(AkJurnalItem.sap_id==Sap.id, AkJurnalItem.ak_jurnal_id==AkJurnal.id, 
                 AkJurnal.unit_id==Unit.id, AkJurnalItem.amount>0, AkJurnal.is_skpd==1,
                 AkJurnal.tahun_id==self.session['tahun'], AkJurnal.unit_id==self.session['unit_id']
                 )
              subq2 = DBSession.query(Unit.nama.label('unit_nm'),Sap.kode.label('subrek_kd'), Sap.nama.label('rek_nm'), 
                 literal_column('0').label('amount_kini'), literal_column(str(tahun_kini)).label('tahun_kini'),
                 AkJurnalItem.amount.label('amount_lalu'), AkJurnal.tahun_id.label('tahun_lalu'),
                 ).filter(AkJurnalItem.sap_id==Sap.id, AkJurnalItem.ak_jurnal_id==AkJurnal.id, 
                 AkJurnal.unit_id==Unit.id, AkJurnalItem.amount>0, AkJurnal.is_skpd==1,
                 AkJurnal.tahun_id==tahun_lalu, AkJurnal.unit_id==self.session['unit_id']
                 )
                 
              subq = subq1.union(subq2).subquery()
              
              query = DBSession.query(Sap.kode, Sap.nama, Sap.level_id, subq.c.unit_nm, subq.c.tahun_kini, subq.c.tahun_lalu,
                 func.sum(subq.c.amount_kini).label('amount_kini'), func.sum(subq.c.amount_lalu).label('amount_lalu')
                 ).filter(Sap.kode==func.left(subq.c.subrek_kd, func.length(Sap.kode)),
                 #func.substr(Sap.kode,1,1).in_(['8','9']) 
                 ).group_by(Sap.kode, Sap.nama, Sap.level_id, subq.c.unit_nm, subq.c.tahun_kini, subq.c.tahun_lalu,
                 ).order_by(Sap.kode)
              
              generator = b105r052Generator()
              pdf = generator.generate(query)
              response=req.response
              response.content_type="application/pdf"
              response.content_disposition='filename=output.pdf' 
              response.write(pdf)
              return response
    """
#Laporan AR Invoice
class b101r001Generator(JasperGenerator):
    def __init__(self):
        super(b101r001Generator, self).__init__()
        self.reportname = get_rpath('apbd/tuskpd/R101001.jrxml')
        self.xpath = '/apbd/arinvoice'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'arinvoice')
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "kode").text = row.kode
            ET.SubElement(xml_greeting, "tgl_terima").text = unicode(row.tgl_terima)
            ET.SubElement(xml_greeting, "tgl_validasi").text = unicode(row.tgl_validasi)
            ET.SubElement(xml_greeting, "penyetor").text = row.penyetor
            ET.SubElement(xml_greeting, "uraian").text = row.uraian
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "jumlah").text = unicode(row.jumlah)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root

#Laporan AR Sts
class b101r002Generator(JasperGenerator):
    def __init__(self):
        super(b101r002Generator, self).__init__()
        self.reportname = get_rpath('apbd/tuskpd/R101002.jrxml')
        self.xpath = '/apbd/arinvoice'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'arinvoice')
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "kode").text = row.kode
            ET.SubElement(xml_greeting, "tgl_sts").text = unicode(row.tgl_sts)
            ET.SubElement(xml_greeting, "tgl_validasi").text = unicode(row.tgl_validasi)
            ET.SubElement(xml_greeting, "jenis").text = unicode(row.jenis)
            ET.SubElement(xml_greeting, "uraian").text = row.uraian
            ET.SubElement(xml_greeting, "nominal").text = unicode(row.nominal)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "tipe").text = unicode(row.tipe)
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root

#TBP-Generator
class b102r002Generator(JasperGenerator):
    def __init__(self):
        super(b102r002Generator, self).__init__()
        self.reportname = get_rpath('apbd/tuskpd/R102002.jrxml')
        self.xpath = '/apbd/arinvoice'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'arinvoice')
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "unit_alamat").text = row.unit_alamat
            ET.SubElement(xml_greeting, "arinvoice_id").text = unicode(row.arinvoice_id)
            ET.SubElement(xml_greeting, "kode").text = row.kode
            ET.SubElement(xml_greeting, "arinvoice_nm").text = row.arinvoice_nm
            ET.SubElement(xml_greeting, "tgl_terima").text = unicode(row.tgl_terima)
            ET.SubElement(xml_greeting, "tgl_validasi").text = unicode(row.tgl_validasi)
            ET.SubElement(xml_greeting, "bendahara_nm").text = row.bendahara_nm
            ET.SubElement(xml_greeting, "bendahara_nip").text = row.bendahara_nip
            ET.SubElement(xml_greeting, "penyetor").text = row.penyetor
            ET.SubElement(xml_greeting, "alamat").text = row.alamat
            ET.SubElement(xml_greeting, "kegiatan_nm").text = row.kegiatan_nm
            ET.SubElement(xml_greeting, "nilai").text = unicode(row.nilai)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root
       
#STS-Generator
class b102r003Generator(JasperGeneratorWithSubreport):
    def __init__(self):
        self.mainreport = get_rpath('apbd/tuskpd/R102003.jrxml')
        self.subreportlist = []
        self.subreportlist.append(get_rpath('apbd/tuskpd/R102003_subreport1.jrxml'))
        self.xpath = '/apbd/sts'
        self.root = ET.Element('apbd')

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'sts')
            ET.SubElement(xml_greeting, "tahun_id").text = unicode(row.tahun_id)
            ET.SubElement(xml_greeting, "unit_id").text = unicode(row.units.id)
            ET.SubElement(xml_greeting, "unit_nm").text = row.units.nama
            ET.SubElement(xml_greeting, "unit_alamat").text = row.units.alamat
            ET.SubElement(xml_greeting, "id").text = unicode(row.id)
            ET.SubElement(xml_greeting, "kode").text = row.kode
            ET.SubElement(xml_greeting, "nama").text = row.nama
            ET.SubElement(xml_greeting, "jenis").text = unicode(row.jenis)
            ET.SubElement(xml_greeting, "tgl_sts").text = unicode(row.tgl_sts)
            ET.SubElement(xml_greeting, "tgl_validasi").text = unicode(row.tgl_validasi)
            ET.SubElement(xml_greeting, "nominal").text = unicode(row.nominal)
            ET.SubElement(xml_greeting, "bank_nama").text = row.bank_nama
            ET.SubElement(xml_greeting, "bank_account").text = row.bank_account
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
            ET.SubElement(xml_greeting, "terbilang").text = Terbilang(row.nominal)
            ET.SubElement(xml_greeting, "ttd_nama").text = row.ttd_nama
            ET.SubElement(xml_greeting, "ttd_nip").text = row.ttd_nip
            ET.SubElement(xml_greeting, "ttd_jab").text = row.ttd_jab
            
            rowttd = DBSession.query(Pejabat.uraian.label('jabatan'), Pegawai.nama.label('pa_nama'), Pegawai.kode.label('pa_nip')
               ).filter(Pejabat.pegawai_id==Pegawai.id, Pejabat.jabatan_id==Jabatan.id, 
               Pejabat.unit_id==row.units.id, Jabatan.kode=='200')
            for row3 in rowttd :
               ET.SubElement(xml_greeting, "jabatan").text = row3.jabatan
               ET.SubElement(xml_greeting, "pa_nama").text = row3.pa_nama
               ET.SubElement(xml_greeting, "pa_nip").text = row3.pa_nip
            
            rows = DBSession.query(Rekening.kode, Rekening.nama, Unit.kode.label('unit_kd'), Kegiatan.kode.label('keg_kd'),
               Program.kode.label('program_kd'),
               func.sum(StsItem.amount).label('jumlah')
               ).filter(Rekening.id==KegiatanItem.rekening_id, 
               KegiatanItem.id==StsItem.kegiatan_item_id, KegiatanSub.id==KegiatanItem.kegiatan_sub_id,
               KegiatanSub.kegiatan_id==Kegiatan.id, Program.id==Kegiatan.program_id, Unit.id==KegiatanSub.unit_id,
               StsItem.ar_sts_id==row.id
               ).group_by(Rekening.kode, Rekening.nama, Unit.kode, Kegiatan.kode, Program.kode
               ).order_by(Rekening.kode)
            for row2 in rows :
                xml_a = ET.SubElement(xml_greeting, "rekening")
                ET.SubElement(xml_a, "rek_kd").text =row2.kode
                ET.SubElement(xml_a, "rek_nm").text =row2.nama
                ET.SubElement(xml_a, "unit_kd").text =row2.unit_kd
                ET.SubElement(xml_a, "keg_kd").text =row2.keg_kd
                ET.SubElement(xml_a, "program_kd").text =row2.program_kd
                ET.SubElement(xml_a, "jumlah").text =unicode(row2.jumlah)
        return self.root

#TBP-Generator
class b102r004Generator(JasperGenerator):
    def __init__(self):
        super(b102r004Generator, self).__init__()
        self.reportname = get_rpath('apbd/tuskpd/R102004.jrxml')
        self.xpath = '/apbd/tbp'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'tbp')
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "unit_nm").text = row.units.nama
            ET.SubElement(xml_greeting, "unit_alamat").text = row.units.alamat
            ET.SubElement(xml_greeting, "kode").text = row.kode
            ET.SubElement(xml_greeting, "nama").text = row.nama
            ET.SubElement(xml_greeting, "ref_kode").text = row.ref_kode
            ET.SubElement(xml_greeting, "ref_nama").text = row.ref_nama
            ET.SubElement(xml_greeting, "tanggal").text = unicode(row.tanggal)
            ET.SubElement(xml_greeting, "amount").text = unicode(row.amount)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root

class b103r001Generator(JasperGeneratorWithSubreport):
    def __init__(self):
        self.mainreport = get_rpath('apbd/tuskpd/R103001.jrxml')
        self.subreportlist = []
        self.subreportlist.append(get_rpath('apbd/tuskpd/R103001_subreport1.jrxml'))
        self.subreportlist.append(get_rpath('apbd/tuskpd/R103001_subreport2.jrxml'))
        self.xpath = '/apbd/invoice'
        self.root = ET.Element('apbd')

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'invoice')
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "unit_id").text = unicode(row.unit_id)
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "alamat").text = row.alamat
            ET.SubElement(xml_greeting, "jenis").text = row.jenis
            ET.SubElement(xml_greeting, "invoice_id").text = unicode(row.invoice_id)
            ET.SubElement(xml_greeting, "invoice_nm").text = row.invoice_nm
            ET.SubElement(xml_greeting, "tgl_invoice").text = unicode(row.tgl_invoice)
            ET.SubElement(xml_greeting, "kode").text = row.kode
            ET.SubElement(xml_greeting, "ap_nama").text = row.ap_nama
            ET.SubElement(xml_greeting, "ap_rekening").text = row.ap_rekening
            ET.SubElement(xml_greeting, "ap_npwp").text = row.ap_npwp
            ET.SubElement(xml_greeting, "kegiatan_kd").text = row.kegiatan_kd
            ET.SubElement(xml_greeting, "kegiatan_nm").text = row.kegiatan_nm
            ET.SubElement(xml_greeting, "program_kd").text = row.program_kd
            ET.SubElement(xml_greeting, "program_nm").text = row.program_nm
            ET.SubElement(xml_greeting, "nilai").text = unicode(row.nilai)
            ET.SubElement(xml_greeting, "terbilang").text = Terbilang(row.nilai)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
            ET.SubElement(xml_greeting, "pptk_nm").text = pptk_nm
            ET.SubElement(xml_greeting, "pptk_nip").text = pptk_nip
            ET.SubElement(xml_greeting, "kpa_nm").text = kpa_nm
            ET.SubElement(xml_greeting, "kpa_nip").text = kpa_nip

            """rowttd = DBSession.query(Pejabat.uraian.label('jabatan'), Pegawai.nama.label('pa_nama'), Pegawai.kode.label('pa_nip')
               ).filter(Pejabat.pegawai_id==Pegawai.id, Pejabat.jabatan_id==Jabatan.id, 
               Pejabat.unit_id==row.unit_id, Jabatan.kode=='200')
            for row4 in rowttd :
               ET.SubElement(xml_greeting, "jabatan").text = row4.jabatan
               ET.SubElement(xml_greeting, "pa_nama").text = row4.pa_nama
               ET.SubElement(xml_greeting, "pa_nip").text = row4.pa_nip
            """
            subq1 = DBSession.query(APInvoiceItem.no_urut.label('no_urut'), 
               Rekening.kode.label('rek_kd'), APInvoiceItem.nama.label('uraian'),
               (KegiatanItem.vol_4_1*KegiatanItem.vol_4_2*KegiatanItem.hsat_4).label('anggaran'),
               literal_column('0').label('lalu'), literal_column('0').label('amount')
               ).filter(Rekening.id==KegiatanItem.rekening_id, 
               KegiatanItem.id==APInvoiceItem.kegiatan_item_id, 
               APInvoiceItem.ap_invoice_id==row.invoice_id)
               
            qrek = DBSession.query(Rekening.kode
               ).filter(Rekening.id==KegiatanItem.rekening_id, APInvoiceItem.kegiatan_item_id==KegiatanItem.id,
               APInvoiceItem.ap_invoice_id==row.invoice_id
               ).group_by(Rekening.kode).subquery()
               
            subq2 = DBSession.query(APInvoiceItem.no_urut.label('no_urut'), 
               Rekening.kode.label('rek_kd'), APInvoiceItem.nama.label('uraian'),
               literal_column('0').label('anggaran'), 
               func.sum(APInvoiceItem.amount).label('lalu'),
               literal_column('0').label('amount')
               ).filter(qrek.c.kode==Rekening.kode, Rekening.id==KegiatanItem.rekening_id, 
               KegiatanItem.id==APInvoiceItem.kegiatan_item_id, 
               APInvoiceItem.ap_invoice_id==APInvoice.id, 
               APInvoice.tahun_id==row.tahun, APInvoice.unit_id==row.unit_id,
               APInvoice.tanggal<row.tgl_invoice
               ).group_by(APInvoiceItem.no_urut, Rekening.kode, APInvoiceItem.nama)
               
            subq3 = DBSession.query(APInvoiceItem.no_urut.label('no_urut'), 
               Rekening.kode.label('rek_kd'), APInvoiceItem.nama.label('uraian'),
               literal_column('0').label('anggaran'), literal_column('0').label('lalu'), 
               APInvoiceItem.amount.label('amount')
               ).filter(Rekening.id==KegiatanItem.rekening_id, 
               KegiatanItem.id==APInvoiceItem.kegiatan_item_id, 
               APInvoiceItem.ap_invoice_id==row.invoice_id)
               
            subq = subq1.union(subq2,subq3).subquery()
            
            rows = DBSession.query(subq.c.no_urut, subq.c.rek_kd, subq.c.uraian, 
               func.coalesce(func.sum(subq.c.anggaran),0).label('anggaran'), 
               func.coalesce(func.sum(subq.c.lalu),0).label('lalu'), 
               func.coalesce(func.sum(subq.c.amount),0).label('amount'),
               ).group_by(subq.c.no_urut, subq.c.rek_kd, subq.c.uraian
               ).order_by(subq.c.no_urut)                         
               
            for row2 in rows :
                xml_a = ET.SubElement(xml_greeting, "item")
                ET.SubElement(xml_a, "no_urut").text =unicode(row2.no_urut)
                ET.SubElement(xml_a, "rek_kd").text =row2.rek_kd
                ET.SubElement(xml_a, "uraian").text =row2.uraian
                ET.SubElement(xml_a, "anggaran").text =unicode(row2.anggaran)
                ET.SubElement(xml_a, "lalu").text =unicode(row2.lalu)
                ET.SubElement(xml_a, "amount").text =unicode(row2.amount)
            
            rowppn = DBSession.query(func.coalesce(func.sum(APInvoiceItem.amount),0).label('jml'),
               func.coalesce(func.sum(APInvoiceItem.ppn),0).label('ppn'),
               func.coalesce(func.sum(APInvoiceItem.pph),0).label('pph'),
               (func.coalesce(func.sum(APInvoiceItem.amount),0)-func.coalesce(func.sum(APInvoiceItem.ppn),0)-func.coalesce(func.sum(APInvoiceItem.pph),0)).label('bayar'),
               ).filter(APInvoiceItem.ap_invoice_id==row.invoice_id)
            
            for row3 in rowppn :
                xml_b = ET.SubElement(xml_greeting, "total")
                ET.SubElement(xml_b, "jml").text =unicode(row3.jml)
                ET.SubElement(xml_b, "ppn").text =unicode(row3.ppn)
                ET.SubElement(xml_b, "pph").text =unicode(row3.pph)
                ET.SubElement(xml_b, "bayar").text =unicode(row3.bayar)
                ET.SubElement(xml_b, "terbilang").text =Terbilang(row3.bayar)
                
        return self.root

#AP Payment
class b103r004Generator(JasperGenerator):
    def __init__(self):
        super(b103r004Generator, self).__init__()
        self.reportname = get_rpath('apbd/tuskpd/R103004.jrxml')
        self.xpath = '/apbd/invoice'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'invoice')
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "alamat").text = row.alamat
            ET.SubElement(xml_greeting, "jenis").text = row.jenis
            ET.SubElement(xml_greeting, "appayment_id").text = unicode(row.appayment_id)
            ET.SubElement(xml_greeting, "appayment_nm").text = row.appayment_nm
            ET.SubElement(xml_greeting, "tgl_payment").text = unicode(row.tgl_payment)
            ET.SubElement(xml_greeting, "kode").text = row.kode
            ET.SubElement(xml_greeting, "ap_nama").text = row.ap_nama
            ET.SubElement(xml_greeting, "ap_rekening").text = row.ap_rekening
            ET.SubElement(xml_greeting, "ap_npwp").text = row.ap_npwp
            ET.SubElement(xml_greeting, "kegiatan_nm").text = row.kegiatan_nm
            ET.SubElement(xml_greeting, "nilai").text = unicode(row.nilai)
            ET.SubElement(xml_greeting, "terbilang").text = Terbilang(row.nilai)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
            ET.SubElement(xml_greeting, "bend_nm").text = bend_nm
            ET.SubElement(xml_greeting, "bend_nip").text = bend_nip
        return self.root

### SPP Pengantar UP/TU/GU-LSB
class b103r021Generator(JasperGeneratorWithSubreport):
    def __init__(self):
        self.mainreport = get_rpath('apbd/tuskpd/R103021.jrxml')
        self.subreportlist = []
        self.subreportlist.append(get_rpath('apbd/tuskpd/R103021_subreport1.jrxml'))
        self.xpath = '/apbd/spp'
        self.root = ET.Element('apbd')

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'spp')
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "no_perkdh").text = row.no_perkdh
            ET.SubElement(xml_greeting, "tgl_perkdh").text = unicode(row.tgl_perkdh)
            ET.SubElement(xml_greeting, "urusan_nm").text = row.urusan_nm
            ET.SubElement(xml_greeting, "unit_id").text = unicode(row.unit_id)
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "spp_id").text = unicode(row.spp_id)
            ET.SubElement(xml_greeting, "spp_kd").text = row.spp_kd
            ET.SubElement(xml_greeting, "spp_nm").text = row.spp_nm
            ET.SubElement(xml_greeting, "spp_tgl").text = unicode(row.spp_tgl)
            ET.SubElement(xml_greeting, "ttd_nip").text = row.ttd_nip
            ET.SubElement(xml_greeting, "ttd_nama").text = row.ttd_nama
            ET.SubElement(xml_greeting, "ttd_jab").text = row.ttd_jab
            ET.SubElement(xml_greeting, "jenis").text = unicode(row.jenis)
            ET.SubElement(xml_greeting, "nominal").text = unicode(row.nominal)
            ET.SubElement(xml_greeting, "ap_nama").text = row.ap_nama
            ET.SubElement(xml_greeting, "ap_bank").text = row.ap_bank
            ET.SubElement(xml_greeting, "ap_rekening").text = row.ap_rekening
            ET.SubElement(xml_greeting, "kegiatan_sub_id").text = unicode(row.kegiatan_sub_id)
            ET.SubElement(xml_greeting, "kode").text = row.kode
            ET.SubElement(xml_greeting, "pptk_nip").text = row.pptk_nip
            ET.SubElement(xml_greeting, "pptk_nama").text = row.pptk_nama
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
            ET.SubElement(xml_greeting, "terbilang_nominal").text = Terbilang(row.nominal)
            
            rowspd = DBSession.query(func.coalesce(func.sum(SpdItem.nominal),0).label('jml_spd')
               ).filter(Spd.id==SpdItem.ap_spd_id, Spd.unit_id==row.unit_id, Spd.tahun_id==row.tahun,
               Spd.tanggal<=row.spp_tgl, SpdItem.kegiatan_sub_id==row.kegiatan_sub_id
               )
            for row1 in rowspd :
               ET.SubElement(xml_greeting, "jml_spd").text = unicode(row1.jml_spd)

            rowsp2d = DBSession.query(func.coalesce(func.sum(APInvoiceItem.amount),0).label('jml_apinvoice_lalu')
               ).filter(APInvoice.id==APInvoiceItem.ap_invoice_id, SppItem.ap_invoice_id==APInvoice.id,
               Spp.id==SppItem.ap_spp_id,
               APInvoice.unit_id==row.unit_id, APInvoice.tahun_id==row.tahun,
               Spp.id!=row.spp_id, APInvoice.kegiatan_sub_id==row.kegiatan_sub_id
               )
            for row2 in rowsp2d :
               ET.SubElement(xml_greeting, "jml_apinvoice_lalu").text = unicode(row2.jml_apinvoice_lalu)

            ET.SubElement(xml_greeting, "terbilang_sisa").text = Terbilang(row1.jml_spd-row2.jml_apinvoice_lalu)

            rows1 = DBSession.query(Spd.id, Spd.kode.label('spd_kd'), Spd.tanggal.label('spd_tgl'),
               func.sum(SpdItem.anggaran).label('anggaran'),func.sum(SpdItem.nominal).label('nilai'),func.sum(SpdItem.lalu).label('lalu'),
               ).filter(Spd.unit_id==row.unit_id, Spd.tahun_id==row.tahun,
               Spd.tanggal<=row.spp_tgl, SpdItem.kegiatan_sub_id==row.kegiatan_sub_id
               ).group_by(Spd.id, Spd.kode, Spd.tanggal
               ).order_by(Spd.tanggal)
            for row3 in rows1 :
               xml_a = ET.SubElement(xml_greeting, "spd")
               ET.SubElement(xml_a, "spd_kd").text = row3.spd_kd
               ET.SubElement(xml_a, "spd_tgl").text = unicode(row3.spd_tgl)
               ET.SubElement(xml_a, "anggaran").text = unicode(row3.anggaran)
               ET.SubElement(xml_a, "nilai").text = unicode(row3.nilai)
               ET.SubElement(xml_a, "lalu").text = unicode(row3.lalu)
        return self.root

### SPP Pengantar LSG
class b103r022Generator(JasperGeneratorWithSubreport):
    def __init__(self):
        self.mainreport = get_rpath('apbd/tuskpd/R103022.jrxml')
        self.subreportlist = []
        self.subreportlist.append(get_rpath('apbd/tuskpd/R103022_subreport1.jrxml'))
        self.xpath = '/apbd/spp'
        self.root = ET.Element('apbd')

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'spp')
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "no_perkdh").text = row.no_perkdh
            ET.SubElement(xml_greeting, "tgl_perkdh").text = unicode(row.tgl_perkdh)
            ET.SubElement(xml_greeting, "urusan_nm").text = row.urusan_nm
            ET.SubElement(xml_greeting, "unit_id").text = unicode(row.unit_id)
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "spp_id").text = unicode(row.spp_id)
            ET.SubElement(xml_greeting, "spp_kd").text = row.spp_kd
            ET.SubElement(xml_greeting, "spp_nm").text = row.spp_nm
            ET.SubElement(xml_greeting, "spp_tgl").text = unicode(row.spp_tgl)
            ET.SubElement(xml_greeting, "ttd_nip").text = row.ttd_nip
            ET.SubElement(xml_greeting, "ttd_nama").text = row.ttd_nama
            ET.SubElement(xml_greeting, "ttd_jab").text = row.ttd_jab
            ET.SubElement(xml_greeting, "jenis").text = unicode(row.jenis)
            ET.SubElement(xml_greeting, "nominal").text = unicode(row.nominal)
            ET.SubElement(xml_greeting, "ap_nama").text = row.ap_nama
            ET.SubElement(xml_greeting, "ap_bank").text = row.ap_bank
            ET.SubElement(xml_greeting, "ap_rekening").text = row.ap_rekening
            ET.SubElement(xml_greeting, "kode").text = row.kode
            ET.SubElement(xml_greeting, "pptk_nip").text = row.pptk_nip
            ET.SubElement(xml_greeting, "pptk_nama").text = row.pptk_nama
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
            ET.SubElement(xml_greeting, "terbilang_nominal").text = Terbilang(row.nominal)
            
            """rowspd = DBSession.query(func.coalesce(func.sum(SpdItem.nominal),0).label('jml_spd')
               ).filter(Spd.id==SpdItem.ap_spd_id, Spd.unit_id==row.unit_id, Spd.tahun_id==row.tahun,
               Spd.tanggal<=row.spp_tgl
               )
            for row1 in rowspd :
               ET.SubElement(xml_greeting, "jml_spd").text = unicode(row1.jml_spd)

            rowsp2d = DBSession.query(func.coalesce(func.sum(Spp.nominal),0).label('jml_sp2d')
               ).filter(Spp.id==Spm.ap_spp_id, Spm.id==Sp2d.ap_spm_id, Spp.unit_id==row.unit_id, Spp.tahun_id==row.tahun,
               Sp2d.tanggal<=row.spp_tgl
               )
            for row2 in rowsp2d :
               ET.SubElement(xml_greeting, "jml_sp2d").text = unicode(row2.jml_sp2d)

            ET.SubElement(xml_greeting, "terbilang_sisa").text = Terbilang(row1.jml_spd-row2.jml_sp2d)

            rows1 = DBSession.query(Spd.id, Spd.kode.label('spd_kd'), Spd.tanggal.label('spd_tgl'),
               func.sum(SpdItem.anggaran).label('anggaran'),func.sum(SpdItem.nominal).label('nilai'),func.sum(SpdItem.lalu).label('lalu'),
               ).filter(Spd.unit_id==row.unit_id, Spd.tahun_id==row.tahun,
               Spd.tanggal<=row.spp_tgl
               ).group_by(Spd.id, Spd.kode, Spd.tanggal
               ).order_by(Spd.tanggal)
            for row3 in rows1 :
               xml_a = ET.SubElement(xml_greeting, "spd")
               ET.SubElement(xml_a, "spd_kd").text = row3.spd_kd
               ET.SubElement(xml_a, "spd_tgl").text = unicode(row3.spd_tgl)
               ET.SubElement(xml_a, "anggaran").text = unicode(row3.anggaran)
               ET.SubElement(xml_a, "nilai").text = unicode(row3.nilai)
               ET.SubElement(xml_a, "lalu").text = unicode(row3.lalu)
            """
            subq = DBSession.query(APInvoice.kegiatan_sub_id
               ).filter(APInvoice.unit_id==row.unit_id, APInvoice.tahun_id==row.tahun, SppItem.ap_invoice_id==APInvoice.id,
               SppItem.ap_spp_id==row.spp_id).subquery()
               
            rowspd = DBSession.query(func.coalesce(func.sum(SpdItem.nominal),0).label('jml_spd')
               ).filter(Spd.id==SpdItem.ap_spd_id, Spd.unit_id==row.unit_id, Spd.tahun_id==row.tahun,
               Spd.tanggal<=row.spp_tgl, SpdItem.kegiatan_sub_id==subq.c.kegiatan_sub_id
               )
            for row1 in rowspd :
               ET.SubElement(xml_greeting, "jml_spd").text = unicode(row1.jml_spd)

            rowsp2d = DBSession.query(func.coalesce(func.sum(APInvoiceItem.amount),0).label('jml_apinvoice_lalu')
               ).filter(APInvoice.id==APInvoiceItem.ap_invoice_id, SppItem.ap_invoice_id==APInvoice.id,
               Spp.id==SppItem.ap_spp_id,
               APInvoice.unit_id==row.unit_id, APInvoice.tahun_id==row.tahun,
               Spp.id!=row.spp_id, APInvoice.kegiatan_sub_id==subq.c.kegiatan_sub_id
               )
            for row2 in rowsp2d :
               ET.SubElement(xml_greeting, "jml_apinvoice_lalu").text = unicode(row2.jml_apinvoice_lalu)

            ET.SubElement(xml_greeting, "terbilang_sisa").text = Terbilang(row1.jml_spd-row2.jml_apinvoice_lalu)

            rows1 = DBSession.query(Spd.id, Spd.kode.label('spd_kd'), Spd.tanggal.label('spd_tgl'),
               func.sum(SpdItem.anggaran).label('anggaran'),func.sum(SpdItem.nominal).label('nilai'),func.sum(SpdItem.lalu).label('lalu'),
               ).filter(Spd.unit_id==row.unit_id, Spd.tahun_id==row.tahun,
               Spd.tanggal<=row.spp_tgl, SpdItem.kegiatan_sub_id==subq.c.kegiatan_sub_id
               ).group_by(Spd.id, Spd.kode, Spd.tanggal
               ).order_by(Spd.tanggal)
            for row3 in rows1 :
               xml_a = ET.SubElement(xml_greeting, "spd")
               ET.SubElement(xml_a, "spd_kd").text = row3.spd_kd
               ET.SubElement(xml_a, "spd_tgl").text = unicode(row3.spd_tgl)
               ET.SubElement(xml_a, "anggaran").text = unicode(row3.anggaran)
               ET.SubElement(xml_a, "nilai").text = unicode(row3.nilai)
               ET.SubElement(xml_a, "lalu").text = unicode(row3.lalu)
            
        return self.root

### SPP Pengantar LS
class b103r025Generator(JasperGeneratorWithSubreport):
    def __init__(self):
        self.mainreport = get_rpath('apbd/tuskpd/R103025.jrxml')
        self.subreportlist = []
        self.subreportlist.append(get_rpath('apbd/tuskpd/R103025_subreport1.jrxml'))
        self.xpath = '/apbd/spp'
        self.root = ET.Element('apbd')

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'spp')
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "no_perkdh").text = row.no_perkdh
            ET.SubElement(xml_greeting, "tgl_perkdh").text = unicode(row.tgl_perkdh)
            ET.SubElement(xml_greeting, "urusan_nm").text = row.urusan_nm
            ET.SubElement(xml_greeting, "unit_id").text = unicode(row.unit_id)
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "spp_id").text = unicode(row.spp_id)
            ET.SubElement(xml_greeting, "spp_kd").text = row.spp_kd
            ET.SubElement(xml_greeting, "spp_nm").text = row.spp_nm
            ET.SubElement(xml_greeting, "spp_tgl").text = unicode(row.spp_tgl)
            ET.SubElement(xml_greeting, "ttd_nip").text = row.ttd_nip
            ET.SubElement(xml_greeting, "ttd_nama").text = row.ttd_nama
            ET.SubElement(xml_greeting, "ttd_jab").text = row.ttd_jab
            ET.SubElement(xml_greeting, "jenis").text = unicode(row.jenis)
            ET.SubElement(xml_greeting, "nominal").text = unicode(row.nominal)
            ET.SubElement(xml_greeting, "ap_nama").text = row.ap_nama
            ET.SubElement(xml_greeting, "ap_bank").text = row.ap_bank
            ET.SubElement(xml_greeting, "ap_rekening").text = row.ap_rekening
            ET.SubElement(xml_greeting, "kode").text = row.kode
            ET.SubElement(xml_greeting, "pptk_nip").text = row.pptk_nip
            ET.SubElement(xml_greeting, "pptk_nama").text = row.pptk_nama
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
            ET.SubElement(xml_greeting, "terbilang_nominal").text = Terbilang(row.nominal)
            
            subq = DBSession.query(APInvoice.kegiatan_sub_id
               ).filter(APInvoice.unit_id==row.unit_id, APInvoice.tahun_id==row.tahun, SppItem.ap_invoice_id==APInvoice.id,
               SppItem.ap_spp_id==row.spp_id).subquery()
               
            rowspd = DBSession.query(func.coalesce(func.sum(SpdItem.nominal),0).label('jml_spd')
               ).filter(Spd.id==SpdItem.ap_spd_id, Spd.unit_id==row.unit_id, Spd.tahun_id==row.tahun,
               Spd.tanggal<=row.spp_tgl, SpdItem.kegiatan_sub_id==subq.c.kegiatan_sub_id
               )
            for row1 in rowspd :
               ET.SubElement(xml_greeting, "jml_spd").text = unicode(row1.jml_spd)

            rowsp2d = DBSession.query(func.coalesce(func.sum(APInvoiceItem.amount),0).label('jml_apinvoice_lalu')
               ).filter(APInvoice.id==APInvoiceItem.ap_invoice_id, SppItem.ap_invoice_id==APInvoice.id,
               Spp.id==SppItem.ap_spp_id,
               APInvoice.unit_id==row.unit_id, APInvoice.tahun_id==row.tahun,
               Spp.id!=row.spp_id, APInvoice.kegiatan_sub_id==subq.c.kegiatan_sub_id
               )
            for row2 in rowsp2d :
               ET.SubElement(xml_greeting, "jml_apinvoice_lalu").text = unicode(row2.jml_apinvoice_lalu)

            ET.SubElement(xml_greeting, "terbilang_sisa").text = Terbilang(row1.jml_spd-row2.jml_apinvoice_lalu)

            rows1 = DBSession.query(Spd.id, Spd.kode.label('spd_kd'), Spd.tanggal.label('spd_tgl'),
               func.sum(SpdItem.anggaran).label('anggaran'),func.sum(SpdItem.nominal).label('nilai'),func.sum(SpdItem.lalu).label('lalu'),
               ).filter(Spd.unit_id==row.unit_id, Spd.tahun_id==row.tahun,
               Spd.tanggal<=row.spp_tgl, SpdItem.kegiatan_sub_id==subq.c.kegiatan_sub_id
               ).group_by(Spd.id, Spd.kode, Spd.tanggal
               ).order_by(Spd.tanggal)
            for row3 in rows1 :
               xml_a = ET.SubElement(xml_greeting, "spd")
               ET.SubElement(xml_a, "spd_kd").text = row3.spd_kd
               ET.SubElement(xml_a, "spd_tgl").text = unicode(row3.spd_tgl)
               ET.SubElement(xml_a, "anggaran").text = unicode(row3.anggaran)
               ET.SubElement(xml_a, "nilai").text = unicode(row3.nilai)
               ET.SubElement(xml_a, "lalu").text = unicode(row3.lalu)
        return self.root

### SPP Ringkasan UP/TU
class b103r031Generator(JasperGenerator):
    def __init__(self):
        super(b103r031Generator, self).__init__()
        self.reportname = get_rpath('apbd/tuskpd/R103031.jrxml')
        self.xpath = '/apbd/spp'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'spp')
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "no_perkdh").text = row.no_perkdh
            ET.SubElement(xml_greeting, "tgl_perkdh").text = unicode(row.tgl_perkdh)
            ET.SubElement(xml_greeting, "urusan_nm").text = row.urusan_nm
            ET.SubElement(xml_greeting, "unit_id").text = unicode(row.unit_id)
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "spp_id").text = unicode(row.spp_id)
            ET.SubElement(xml_greeting, "spp_kd").text = row.spp_kd
            ET.SubElement(xml_greeting, "spp_nm").text = row.spp_nm
            ET.SubElement(xml_greeting, "spp_tgl").text = unicode(row.spp_tgl)
            ET.SubElement(xml_greeting, "ttd_nip").text = row.ttd_nip
            ET.SubElement(xml_greeting, "ttd_nama").text = row.ttd_nama
            ET.SubElement(xml_greeting, "ttd_jab").text = row.ttd_jab
            ET.SubElement(xml_greeting, "jenis").text = unicode(row.jenis)
            ET.SubElement(xml_greeting, "nominal").text = unicode(row.nominal)
            ET.SubElement(xml_greeting, "ap_nama").text = row.ap_nama
            ET.SubElement(xml_greeting, "ap_bank").text = row.ap_bank
            ET.SubElement(xml_greeting, "ap_rekening").text = row.ap_rekening
            ET.SubElement(xml_greeting, "kode").text = row.kode
            ET.SubElement(xml_greeting, "pptk_nip").text = row.pptk_nip
            ET.SubElement(xml_greeting, "pptk_nama").text = row.pptk_nama
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
            ET.SubElement(xml_greeting, "terbilang").text = Terbilang(row.nominal)
        return self.root

### SPP Ringkasan LS
class b103r035Generator(JasperGeneratorWithSubreport):
    def __init__(self):
        self.mainreport = get_rpath('apbd/tuskpd/R103035.jrxml')

        self.subreportlist = []
        self.subreportlist.append(get_rpath('apbd/tuskpd/R103035_subreport1.jrxml'))
        self.xpath = '/apbd/spp'
        self.root = ET.Element('apbd')

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'spp')
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "unit_id").text = unicode(row.unit_id)
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "tanggal_2").text = unicode(row.tanggal_2)
            ET.SubElement(xml_greeting, "tanggal_4").text = unicode(row.tanggal_4)
            ET.SubElement(xml_greeting, "spp_id").text = unicode(row.spp_id)
            ET.SubElement(xml_greeting, "spp_kd").text = row.spp_kd
            ET.SubElement(xml_greeting, "spp_nm").text = row.spp_nm
            ET.SubElement(xml_greeting, "spp_tgl").text = unicode(row.spp_tgl)
            ET.SubElement(xml_greeting, "ttd_nip").text = row.ttd_nip
            ET.SubElement(xml_greeting, "ttd_nama").text = row.ttd_nama
            ET.SubElement(xml_greeting, "ttd_jab").text = row.ttd_jab
            ET.SubElement(xml_greeting, "jenis").text = unicode(row.jenis)
            ET.SubElement(xml_greeting, "pptk_nip").text = row.pptk_nip
            ET.SubElement(xml_greeting, "pptk_nama").text = row.pptk_nama
            ET.SubElement(xml_greeting, "nominal").text = unicode(row.nominal)
            ET.SubElement(xml_greeting, "ap_nama").text = row.ap_nama
            ET.SubElement(xml_greeting, "ap_bank").text = row.ap_bank
            ET.SubElement(xml_greeting, "ap_rekening").text = row.ap_rekening
            ET.SubElement(xml_greeting, "ap_waktu").text = row.ap_waktu
            ET.SubElement(xml_greeting, "ap_uraian").text = row.ap_uraian
            ET.SubElement(xml_greeting, "ap_pemilik").text = row.ap_pemilik
            ET.SubElement(xml_greeting, "ap_alamat").text = row.ap_alamat
            ET.SubElement(xml_greeting, "ap_bentuk").text = row.ap_bentuk
            ET.SubElement(xml_greeting, "ap_kontrak").text = row.ap_kontrak
            ET.SubElement(xml_greeting, "kegiatan_sub_id").text = unicode(row.kegiatan_sub_id)
            ET.SubElement(xml_greeting, "keg_kd").text = row.keg_kd
            ET.SubElement(xml_greeting, "keg_nm").text = row.keg_nm
            ET.SubElement(xml_greeting, "no_urut").text = unicode(row.no_urut)
            ET.SubElement(xml_greeting, "prg_nm").text = row.prg_nm
            ET.SubElement(xml_greeting, "kode").text = row.kode
            #ET.SubElement(xml_greeting, "anggaran").text = unicode(row.anggaran)
            #ET.SubElement(xml_greeting, "tot_spd").text = unicode(row.tot_spd)
            #ET.SubElement(xml_greeting, "jenis1").text = row.jenis1
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo

            rowang = DBSession.query(func.coalesce(func.sum(KegiatanItem.vol_2_1*KegiatanItem.vol_2_2*KegiatanItem.hsat_2),0).label('jml_dpa'),
               func.coalesce(func.sum(KegiatanItem.vol_4_1*KegiatanItem.vol_4_2*KegiatanItem.hsat_4),0).label('jml_dppa')
               ).filter(KegiatanSub.id==KegiatanItem.kegiatan_sub_id, KegiatanSub.unit_id==row.unit_id, KegiatanSub.tahun_id==row.tahun,
               KegiatanSub.id==row.kegiatan_sub_id
               )
            for row0 in rowang :
               ET.SubElement(xml_greeting, "anggaran").text = unicode(row0.jml_dppa)
               
            rowspd = DBSession.query(func.coalesce(func.sum(SpdItem.nominal),0).label('jml_spd')
               ).filter(Spd.id==SpdItem.ap_spd_id, Spd.unit_id==row.unit_id, Spd.tahun_id==row.tahun,
               Spd.tanggal<=row.spp_tgl, SpdItem.kegiatan_sub_id==row.kegiatan_sub_id
               )
            for row1 in rowspd :
               ET.SubElement(xml_greeting, "jml_spd").text = unicode(row1.jml_spd)
               
            rows = DBSession.query(Spd.id, Spd.kode.label('spd_kd'), Spd.tanggal.label('spd_tgl'),
               SpdItem.nominal.label('nominal'),
               ).filter(Spd.id==SpdItem.ap_spd_id, Spd.unit_id==row.unit_id, Spd.tahun_id==row.tahun,
               Spd.tanggal<=row.spp_tgl, SpdItem.kegiatan_sub_id==row.kegiatan_sub_id
               ).order_by(Spd.tanggal)
            for row3 in rows:
                xml_a = ET.SubElement(xml_greeting, "spd")
                ET.SubElement(xml_a, "kode").text  = row3.spd_kd
                ET.SubElement(xml_a, "tanggal").text = unicode(row3.spd_tgl)
                ET.SubElement(xml_a, "nominal").text = unicode(row3.nominal)
              
        return self.root

### SPP Ringkasan LS.G
class b103r033Generator(JasperGeneratorWithSubreport):
    def __init__(self):
        self.mainreport = get_rpath('apbd/tuskpd/R103033.jrxml')
        self.subreportlist = []
        self.subreportlist.append(get_rpath('apbd/tuskpd/R103033_subreport1.jrxml'))
        self.xpath = '/apbd/spp'
        self.root = ET.Element('apbd')

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'spp')
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "urusan_nm").text = row.urusan_nm
            ET.SubElement(xml_greeting, "unit_id").text = unicode(row.unit_id)
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "no_perkdh").text = row.no_perkdh
            ET.SubElement(xml_greeting, "tgl_perkdh").text = unicode(row.tgl_perkdh)
            ET.SubElement(xml_greeting, "tanggal_2").text = unicode(row.tanggal_2)
            ET.SubElement(xml_greeting, "tanggal_4").text = unicode(row.tanggal_4)
            ET.SubElement(xml_greeting, "spp_id").text = unicode(row.spp_id)
            ET.SubElement(xml_greeting, "spp_kd").text = row.spp_kd
            ET.SubElement(xml_greeting, "spp_nm").text = row.spp_nm
            ET.SubElement(xml_greeting, "spp_tgl").text = unicode(row.spp_tgl)
            ET.SubElement(xml_greeting, "ttd_nip").text = row.ttd_nip
            ET.SubElement(xml_greeting, "ttd_nama").text = row.ttd_nama
            ET.SubElement(xml_greeting, "ttd_jab").text = row.ttd_jab
            ET.SubElement(xml_greeting, "jenis").text = unicode(row.jenis)
            ET.SubElement(xml_greeting, "pptk_nip").text = row.pptk_nip
            ET.SubElement(xml_greeting, "pptk_nama").text = row.pptk_nama
            ET.SubElement(xml_greeting, "ap_nama").text = row.ap_nama
            ET.SubElement(xml_greeting, "ap_bank").text = row.ap_bank
            ET.SubElement(xml_greeting, "ap_rekening").text = row.ap_rekening
            ET.SubElement(xml_greeting, "kegiatan_sub_id").text = unicode(row.kegiatan_sub_id)
            ET.SubElement(xml_greeting, "kode").text = row.kode
            ET.SubElement(xml_greeting, "nominal").text = unicode(row.nominal)
            #ET.SubElement(xml_greeting, "anggaran").text = unicode(row.anggaran)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
            ET.SubElement(xml_greeting, "terbilang").text = Terbilang(row.nominal)

            rowang = DBSession.query(func.coalesce(func.sum(KegiatanItem.vol_2_1*KegiatanItem.vol_2_2*KegiatanItem.hsat_2),0).label('jml_dpa'),
               func.coalesce(func.sum(KegiatanItem.vol_4_1*KegiatanItem.vol_4_2*KegiatanItem.hsat_4),0).label('jml_dppa')
               ).filter(KegiatanSub.id==KegiatanItem.kegiatan_sub_id, KegiatanSub.unit_id==row.unit_id, KegiatanSub.tahun_id==row.tahun,
               KegiatanSub.id==row.kegiatan_sub_id
               )
            for row0 in rowang :
               ET.SubElement(xml_greeting, "anggaran").text = unicode(row0.jml_dppa)
               
            rowspd = DBSession.query(func.coalesce(func.sum(SpdItem.nominal),0).label('jml_spd')
               ).filter(Spd.id==SpdItem.ap_spd_id, Spd.unit_id==row.unit_id, Spd.tahun_id==row.tahun,
               Spd.tanggal<=row.spp_tgl, SpdItem.kegiatan_sub_id==row.kegiatan_sub_id
               )
            for row1 in rowspd :
               ET.SubElement(xml_greeting, "jml_spd").text = unicode(row1.jml_spd)

            rowsp2d = DBSession.query(func.coalesce(func.sum(APInvoiceItem.amount),0).label('jml_apinvoice_lalu')
               ).filter(APInvoice.id==APInvoiceItem.ap_invoice_id, SppItem.ap_invoice_id==APInvoice.id,
               Spp.id==SppItem.ap_spp_id,
               APInvoice.unit_id==row.unit_id, APInvoice.tahun_id==row.tahun,
               Spp.id!=row.spp_id, APInvoice.kegiatan_sub_id==row.kegiatan_sub_id
               )
            for row2 in rowsp2d :
               ET.SubElement(xml_greeting, "jml_apinvoice_lalu").text = unicode(row2.jml_apinvoice_lalu)

            ET.SubElement(xml_greeting, "terbilang_sisa").text = Terbilang(row1.jml_spd-row2.jml_apinvoice_lalu)

            rows1 = DBSession.query(Spd.id, Spd.kode.label('spd_kd'), Spd.tanggal.label('spd_tgl'),
               SpdItem.anggaran.label('anggaran'),SpdItem.nominal.label('nilai'),SpdItem.lalu.label('lalu'),
               ).filter(Spd.id==SpdItem.ap_spd_id, Spd.unit_id==row.unit_id, Spd.tahun_id==row.tahun,
               Spd.tanggal<=row.spp_tgl, SpdItem.kegiatan_sub_id==row.kegiatan_sub_id
               ).order_by(Spd.tanggal)
            for row3 in rows1 :
               xml_a = ET.SubElement(xml_greeting, "spd")
               ET.SubElement(xml_a, "spd_kd").text = row3.spd_kd
               ET.SubElement(xml_a, "spd_tgl").text = unicode(row3.spd_tgl)
               ET.SubElement(xml_a, "anggaran").text = unicode(row3.anggaran)
               ET.SubElement(xml_a, "nilai").text = unicode(row3.nilai)
               ET.SubElement(xml_a, "lalu").text = unicode(row3.lalu)
        return self.root

### SPP Ringkasan GU / LSB
class b103r034Generator(JasperGeneratorWithSubreport):
    def __init__(self):
        self.mainreport = get_rpath('apbd/tuskpd/R103034.jrxml')
        self.subreportlist = []
        self.subreportlist.append(get_rpath('apbd/tuskpd/R103034_subreport1.jrxml'))
        self.xpath = '/apbd/spp'
        self.root = ET.Element('apbd')

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'spp')
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "unit_id").text = unicode(row.unit_id)
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "tanggal_2").text = unicode(row.tanggal_2)
            ET.SubElement(xml_greeting, "tanggal_4").text = unicode(row.tanggal_4)
            ET.SubElement(xml_greeting, "spp_id").text = unicode(row.spp_id)
            ET.SubElement(xml_greeting, "spp_kd").text = row.spp_kd
            ET.SubElement(xml_greeting, "spp_nm").text = row.spp_nm
            ET.SubElement(xml_greeting, "spp_tgl").text = unicode(row.spp_tgl)
            ET.SubElement(xml_greeting, "ttd_nip").text = row.ttd_nip
            ET.SubElement(xml_greeting, "ttd_nama").text = row.ttd_nama
            ET.SubElement(xml_greeting, "ttd_jab").text = row.ttd_jab
            ET.SubElement(xml_greeting, "jenis").text = unicode(row.jenis)
            ET.SubElement(xml_greeting, "pptk_nip").text = row.pptk_nip
            ET.SubElement(xml_greeting, "pptk_nama").text = row.pptk_nama
            ET.SubElement(xml_greeting, "nominal").text = unicode(row.nominal)
            ET.SubElement(xml_greeting, "ap_nama").text = row.ap_nama
            ET.SubElement(xml_greeting, "ap_bank").text = row.ap_bank
            ET.SubElement(xml_greeting, "ap_rekening").text = row.ap_rekening
            ET.SubElement(xml_greeting, "ap_waktu").text = row.ap_waktu
            ET.SubElement(xml_greeting, "ap_uraian").text = row.ap_uraian
            ET.SubElement(xml_greeting, "ap_pemilik").text = row.ap_pemilik
            ET.SubElement(xml_greeting, "ap_alamat").text = row.ap_alamat
            ET.SubElement(xml_greeting, "ap_bentuk").text = row.ap_bentuk
            ET.SubElement(xml_greeting, "ap_kontrak").text = row.ap_kontrak
            ET.SubElement(xml_greeting, "keg_kd").text = row.keg_kd
            ET.SubElement(xml_greeting, "keg_nm").text = row.keg_nm
            ET.SubElement(xml_greeting, "no_urut").text = unicode(row.no_urut)
            ET.SubElement(xml_greeting, "prg_nm").text = row.prg_nm
            ET.SubElement(xml_greeting, "anggaran").text = unicode(row.anggaran)
            ET.SubElement(xml_greeting, "tot_spd").text = unicode(row.tot_spd)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo

            rows = DBSession.query(Spd.id, Spd.kode.label('spd_kd'), Spd.tanggal.label('spd_tgl'),
               func.sum(SpdItem.nominal).label('nominal'),
               ).filter(Spd.id==SpdItem.ap_spd_id, Spd.unit_id==row.unit_id, Spd.tahun_id==row.tahun,
               Spd.tanggal<=row.spp_tgl
               ).group_by(Spd.id, Spd.kode, Spd.tanggal
               ).order_by(Spd.tanggal)
            for row3 in rows:
                xml_a = ET.SubElement(xml_greeting, "spd")
                ET.SubElement(xml_a, "kode").text  = row3.spd_kd
                ET.SubElement(xml_a, "tanggal").text = unicode(row3.spd_tgl)
                ET.SubElement(xml_a, "nominal").text = unicode(row3.nominal)
              
        return self.root

### SPP Rincian // UP
class b103r041Generator(JasperGenerator):
    def __init__(self):
        super(b103r041Generator, self).__init__()
        self.reportname = get_rpath('apbd/tuskpd/R103041.jrxml')
        self.xpath = '/apbd/spp'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'spp')
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            #ET.SubElement(xml_greeting, "urusan_kd").text = row.urusan_kd
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "keg_kd").text = row.keg_kd
            ET.SubElement(xml_greeting, "keg_nm").text = row.keg_nm
            ET.SubElement(xml_greeting, "prg_kd").text = row.prg_kd
            ET.SubElement(xml_greeting, "prg_nm").text = row.prg_nm
            ET.SubElement(xml_greeting, "spp_kd").text = row.spp_kd
            ET.SubElement(xml_greeting, "nama").text = row.nama
            ET.SubElement(xml_greeting, "tanggal").text = unicode(row.tanggal)
            ET.SubElement(xml_greeting, "jenis").text = unicode(row.jenis)
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "amount").text = unicode(row.amount)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "unit_id").text = unicode(row.unit_id)
            ET.SubElement(xml_greeting, "ttd_nip").text = row.ttd_nip
            ET.SubElement(xml_greeting, "ttd_nama").text = row.ttd_nama
            ET.SubElement(xml_greeting, "jenis1").text = row.jenis1
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root

### SPP Rincian // TU
class b103r042Generator(JasperGenerator):
    def __init__(self):
        super(b103r042Generator, self).__init__()
        self.reportname = get_rpath('apbd/tuskpd/R103042.jrxml')
        self.xpath = '/apbd/spp'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'spp')
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            #ET.SubElement(xml_greeting, "urusan_kd").text = row.urusan_kd
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "keg_kd").text = row.keg_kd
            ET.SubElement(xml_greeting, "keg_nm").text = row.keg_nm
            ET.SubElement(xml_greeting, "prg_kd").text = row.prg_kd
            ET.SubElement(xml_greeting, "prg_nm").text = row.prg_nm
            ET.SubElement(xml_greeting, "spp_kd").text = row.spp_kd
            ET.SubElement(xml_greeting, "nama").text = row.nama
            ET.SubElement(xml_greeting, "tanggal").text = unicode(row.tanggal)
            ET.SubElement(xml_greeting, "jenis").text = unicode(row.jenis)
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "amount").text = unicode(row.amount)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "unit_id").text = unicode(row.unit_id)
            ET.SubElement(xml_greeting, "ttd_nip").text = row.ttd_nip
            ET.SubElement(xml_greeting, "ttd_nama").text = row.ttd_nama
            ET.SubElement(xml_greeting, "pptk_nip").text = row.pptk_nip
            ET.SubElement(xml_greeting, "pptk_nama").text = row.pptk_nama
            ET.SubElement(xml_greeting, "jenis1").text = row.jenis1
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root

### SPP Rincian // LS
class b103r045Generator(JasperGenerator):
    def __init__(self):
        super(b103r045Generator, self).__init__()
        self.reportname = get_rpath('apbd/tuskpd/R103045.jrxml')
        self.xpath = '/apbd/spp'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'spp')
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            #ET.SubElement(xml_greeting, "urusan_kd").text = row.urusan_kd
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "keg_kd").text = row.keg_kd
            ET.SubElement(xml_greeting, "keg_nm").text = row.keg_nm
            ET.SubElement(xml_greeting, "prg_kd").text = row.prg_kd
            ET.SubElement(xml_greeting, "prg_nm").text = row.prg_nm
            ET.SubElement(xml_greeting, "spp_kd").text = row.spp_kd
            ET.SubElement(xml_greeting, "nama").text = row.nama
            ET.SubElement(xml_greeting, "tanggal").text = unicode(row.tanggal)
            ET.SubElement(xml_greeting, "jenis").text = unicode(row.jenis)
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "amount").text = unicode(row.amount)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "unit_id").text = unicode(row.unit_id)
            ET.SubElement(xml_greeting, "ttd_nip").text = row.ttd_nip
            ET.SubElement(xml_greeting, "ttd_nama").text = row.ttd_nama
            ET.SubElement(xml_greeting, "pptk_nip").text = row.pptk_nip
            ET.SubElement(xml_greeting, "pptk_nama").text = row.pptk_nama
            ET.SubElement(xml_greeting, "jenis1").text = row.jenis1
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root

### SPP Rincian // GU/LSB
class b103r043Generator(JasperGenerator):
    def __init__(self):
        super(b103r043Generator, self).__init__()
        self.reportname = get_rpath('apbd/tuskpd/R103043.jrxml')
        self.xpath = '/apbd/spp'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'spp')
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            #ET.SubElement(xml_greeting, "urusan_kd").text = row.urusan_kd
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "keg_kd").text = row.keg_kd
            ET.SubElement(xml_greeting, "keg_nm").text = row.keg_nm
            ET.SubElement(xml_greeting, "prg_kd").text = row.prg_kd
            ET.SubElement(xml_greeting, "prg_nm").text = row.prg_nm
            ET.SubElement(xml_greeting, "spp_kd").text = row.spp_kd
            ET.SubElement(xml_greeting, "nama").text = row.nama
            ET.SubElement(xml_greeting, "tanggal").text = unicode(row.tanggal)
            ET.SubElement(xml_greeting, "jenis").text = unicode(row.jenis)
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "amount").text = unicode(row.amount)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "unit_id").text = unicode(row.unit_id)
            ET.SubElement(xml_greeting, "ttd_nip").text = row.ttd_nip
            ET.SubElement(xml_greeting, "ttd_nama").text = row.ttd_nama
            ET.SubElement(xml_greeting, "pptk_nip").text = row.pptk_nip
            ET.SubElement(xml_greeting, "pptk_nama").text = row.pptk_nama
            ET.SubElement(xml_greeting, "jenis1").text = row.jenis1
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root

### SPP Rincian // LS.G
class b103r044Generator(JasperGenerator):
    def __init__(self):
        super(b103r044Generator, self).__init__()
        self.reportname = get_rpath('apbd/tuskpd/R103044.jrxml')
        self.xpath = '/apbd/spp'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'spp')
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            #ET.SubElement(xml_greeting, "urusan_kd").text = row.urusan_kd
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "keg_kd").text = row.keg_kd
            ET.SubElement(xml_greeting, "keg_nm").text = row.keg_nm
            ET.SubElement(xml_greeting, "prg_kd").text = row.prg_kd
            ET.SubElement(xml_greeting, "prg_nm").text = row.prg_nm
            ET.SubElement(xml_greeting, "spp_kd").text = row.spp_kd
            ET.SubElement(xml_greeting, "nama").text = row.nama
            ET.SubElement(xml_greeting, "tanggal").text = unicode(row.tanggal)
            ET.SubElement(xml_greeting, "jenis").text = unicode(row.jenis)
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "amount").text = unicode(row.amount)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "unit_id").text = unicode(row.unit_id)
            ET.SubElement(xml_greeting, "ttd_nip").text = row.ttd_nip
            ET.SubElement(xml_greeting, "ttd_nama").text = row.ttd_nama
            ET.SubElement(xml_greeting, "pptk_nip").text = row.pptk_nip
            ET.SubElement(xml_greeting, "pptk_nama").text = row.pptk_nama
            ET.SubElement(xml_greeting, "jenis1").text = row.jenis1
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root

class b103r0023Generator(JasperGenerator):
    def __init__(self):
        super(b103r0023Generator, self).__init__()
        self.reportname = get_rpath('apbd/tuskpd/R1030023.jrxml')
        self.xpath = '/apbd/spp'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'spp')
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "kegiatan_nm").text = row.kegiatan_nm
            ET.SubElement(xml_greeting, "no_perkdh").text = row.no_perkdh
            ET.SubElement(xml_greeting, "tgl_perkdh").text = unicode(row.tgl_perkdh)
            ET.SubElement(xml_greeting, "urusan_nm").text = row.urusan_nm
            ET.SubElement(xml_greeting, "spp_kd").text = row.spp_kd
            ET.SubElement(xml_greeting, "nama").text = row.nama
            ET.SubElement(xml_greeting, "bank_nama").text = row.bank_nama
            ET.SubElement(xml_greeting, "bank_account").text = row.bank_account
            ET.SubElement(xml_greeting, "tanggal").text = unicode(row.tanggal)
            ET.SubElement(xml_greeting, "jenis").text = row.jenis
            ET.SubElement(xml_greeting, "nominal").text = unicode(row.nominal)
            ET.SubElement(xml_greeting, "spd_kd").text = row.spd_kd
            ET.SubElement(xml_greeting, "tgl_spd").text = unicode(row.tgl_spd)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root

### SPM // Format SPM
class b103r003Generator(JasperGeneratorWithSubreport):
    def __init__(self):
        self.mainreport = get_rpath('apbd/tuskpd/R103003.jrxml')

        self.subreportlist = []
        self.subreportlist.append(get_rpath('apbd/tuskpd/R103003_subreport1.jrxml'))
        self.subreportlist.append(get_rpath('apbd/tuskpd/R103003_subreport2.jrxml'))
        #self.subreportlist.append(get_rpath('apbd/tuskpd/R103003_subreport3.jrxml'))

        self.xpath = '/apbd/spm'
        self.root = ET.Element('apbd')

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'spm')
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "spm_id").text = unicode(row.spm_id)
            ET.SubElement(xml_greeting, "spm_kd").text = row.spm_kd
            ET.SubElement(xml_greeting, "spm_nm").text = row.spm_nm
            ET.SubElement(xml_greeting, "spm_tgl").text = unicode(row.spm_tgl)
            ET.SubElement(xml_greeting, "ttd_nip").text = row.ttd_nip
            ET.SubElement(xml_greeting, "ttd_nama").text = row.ttd_nama
            ET.SubElement(xml_greeting, "spp_id").text = unicode(row.spp_id)
            ET.SubElement(xml_greeting, "spp_kd").text = row.spp_kd
            ET.SubElement(xml_greeting, "jenis").text = unicode(row.jenis)
            ET.SubElement(xml_greeting, "spp_tgl").text = unicode(row.spp_tgl)
            ET.SubElement(xml_greeting, "ap_bank").text = row.ap_bank
            ET.SubElement(xml_greeting, "ap_rekening").text = row.ap_rekening
            ET.SubElement(xml_greeting, "ap_npwp").text = row.ap_npwp
            ET.SubElement(xml_greeting, "ap_nama").text = row.ap_nama
            ET.SubElement(xml_greeting, "spp_nm").text = row.spp_nm
            ET.SubElement(xml_greeting, "spd_kd").text = row.spd_kd
            ET.SubElement(xml_greeting, "spd_tgl").text = unicode(row.spd_tgl)
            #ET.SubElement(xml_greeting, "keg_kd").text = row.keg_kd
            #ET.SubElement(xml_greeting, "prg_kd").text = row.program_kd
            ET.SubElement(xml_greeting, "nominal").text = unicode(row.nominal)
            #ET.SubElement(xml_greeting, "ap_invoice_id").text = unicode(row.ap_invoice_id)
            ET.SubElement(xml_greeting, "jabatan").text = row.jabatan
            ET.SubElement(xml_greeting, "jenis1").text = row.jenis1
            ET.SubElement(xml_greeting, "logo").text = logo
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "terbilang_nominal").text = Terbilang(row.nominal)
            
            rowppn = DBSession.query(func.coalesce(func.sum(APInvoiceItem.ppn),0).label('ppn'),
               func.coalesce(func.sum(APInvoiceItem.pph),0).label('pph')
               ).filter(APInvoiceItem.ap_invoice_id==SppItem.ap_invoice_id, SppItem.ap_spp_id==row.spp_id)
            for row5 in rowppn :
               ET.SubElement(xml_greeting, "ppn").text = unicode(row5.ppn)
               ET.SubElement(xml_greeting, "pph").text = unicode(row5.pph)
              
            rowpot = DBSession.query(func.coalesce(func.sum(SpmPotongan.nilai),0).label('nilai_pot')
               ).filter(SpmPotongan.ap_spm_id==row.spm_id)
            for row4 in rowpot :
               ET.SubElement(xml_greeting, "nilai_pot").text = unicode(row4.nilai_pot)
            ET.SubElement(xml_greeting, "terbilang").text = Terbilang(row.nominal-row4.nilai_pot)
            ET.SubElement(xml_greeting, "terbilang1").text = Terbilang(row.nominal-row4.nilai_pot-row5.ppn-row5.pph)

            rows = DBSession.query(Rekening.kode, Rekening.nama, Unit.kode.label('unit_kd'), Kegiatan.kode.label('keg_kd'),
               func.sum(APInvoiceItem.amount).label('jumlah')
               ).filter(Rekening.id==KegiatanItem.rekening_id, 
               KegiatanItem.id==APInvoiceItem.kegiatan_item_id, KegiatanSub.id==KegiatanItem.kegiatan_sub_id,
               KegiatanSub.kegiatan_id==Kegiatan.id, Program.id==Kegiatan.program_id, Unit.id==KegiatanSub.unit_id,
               SppItem.ap_invoice_id==APInvoiceItem.ap_invoice_id,
               SppItem.ap_spp_id==row.spp_id
               #, func.substr(Rekening.kode,1,1)=='5'
               ).group_by(Rekening.kode, Rekening.nama, Unit.kode, Kegiatan.kode
               ).order_by(Unit.kode, Kegiatan.kode, Rekening.kode)
            for row2 in rows :
                xml_a = ET.SubElement(xml_greeting, "rekening")
                ET.SubElement(xml_a, "rek_kd").text =row2.kode
                ET.SubElement(xml_a, "rek_nm").text =row2.nama
                ET.SubElement(xml_a, "unit_kd").text =row2.unit_kd
                ET.SubElement(xml_a, "keg_kd").text =row2.keg_kd
                ET.SubElement(xml_a, "jumlah").text =unicode(row2.jumlah)

            rows1 = DBSession.query(Rekening.kode, Rekening.nama,
               (SpmPotongan.nilai).label('jumlah')
               ).filter(Rekening.id==SpmPotongan.rekening_id,
               SpmPotongan.ap_spm_id==row.spm_id
               ).order_by(Rekening.kode)
            for row3 in rows1 :
                xml_b = ET.SubElement(xml_greeting, "potongan")
                ET.SubElement(xml_b, "rek_kd").text =row3.kode
                ET.SubElement(xml_b, "rek_nm").text =row3.nama
                ET.SubElement(xml_b, "jumlah").text =unicode(row3.jumlah)
            
        return self.root

### SPM // Pengantar
class b103r003_1Generator(JasperGeneratorWithSubreport):
    def __init__(self):
        self.mainreport = get_rpath('apbd/tuskpd/R103003_1.jrxml')
        self.subreportlist = []
        #self.subreportlist.append(get_rpath('apbd/tuskpd/R103003_1_subreport1.jrxml'))
        self.xpath = '/apbd/spm'
        self.root = ET.Element('apbd')

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'spm')
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "alamat").text = row.alamat
            ET.SubElement(xml_greeting, "spm_id").text = unicode(row.spm_id)
            ET.SubElement(xml_greeting, "spm_kd").text = row.spm_kd
            ET.SubElement(xml_greeting, "spm_nm").text = row.spm_nm
            ET.SubElement(xml_greeting, "spm_tgl").text = unicode(row.spm_tgl)
            ET.SubElement(xml_greeting, "ttd_nip").text = row.ttd_nip
            ET.SubElement(xml_greeting, "ttd_nama").text = row.ttd_nama
            ET.SubElement(xml_greeting, "spp_id").text = unicode(row.spp_id)
            ET.SubElement(xml_greeting, "jenis").text = unicode(row.jenis)
            ET.SubElement(xml_greeting, "kode").text = row.kode
            ET.SubElement(xml_greeting, "prg_kd").text = row.prg_kd
            ET.SubElement(xml_greeting, "keg_kd").text = row.keg_kd
            ET.SubElement(xml_greeting, "keg_nm").text = row.keg_nm
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "amount").text = unicode(row.amount)
            ET.SubElement(xml_greeting, "jabatan").text = row.jabatan
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root

### SPM // Pernyataan
class b103r003_2Generator(JasperGeneratorWithSubreport):
    def __init__(self):
        self.mainreport = get_rpath('apbd/tuskpd/R103003_2.jrxml')
        self.subreportlist = []
        #self.subreportlist.append(get_rpath('apbd/tuskpd/R103003_subreport1.jrxml'))
        self.xpath = '/apbd/spm'
        self.root = ET.Element('apbd')

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'spm')
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "alamat").text = row.alamat
            ET.SubElement(xml_greeting, "spm_id").text = unicode(row.spm_id)
            ET.SubElement(xml_greeting, "spm_kd").text = row.spm_kd
            ET.SubElement(xml_greeting, "spm_nm").text = row.spm_nm
            ET.SubElement(xml_greeting, "spm_tgl").text = unicode(row.spm_tgl)
            ET.SubElement(xml_greeting, "ttd_nip").text = row.ttd_nip
            ET.SubElement(xml_greeting, "ttd_nama").text = row.ttd_nama
            ET.SubElement(xml_greeting, "spp_id").text = unicode(row.spp_id)
            ET.SubElement(xml_greeting, "jenis").text = unicode(row.jenis)
            ET.SubElement(xml_greeting, "amount").text = unicode(row.amount)
            ET.SubElement(xml_greeting, "terbilang").text = Terbilang(row.amount)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "jabatan").text = row.jabatan
            ET.SubElement(xml_greeting, "logo").text = logo

            rows = DBSession.query(case([(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)=='5.1.1'),"-GJ")], else_=" ").label('kode')
               ).filter(Spp.id==SppItem.ap_spp_id, SppItem.ap_invoice_id==APInvoiceItem.ap_invoice_id, APInvoiceItem.kegiatan_item_id==KegiatanItem.id,
               KegiatanItem.rekening_id==Rekening.id, Spp.id==row.spp_id
               ).group_by(case([(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)=='5.1.1'),"-GJ")], else_=" "))

            for row1 in rows:
                ET.SubElement(xml_greeting, "kode").text  = row1.kode
        return self.root

### SPM // Pernyataan
class b103r003_12Generator(JasperGeneratorWithSubreport):
    def __init__(self):
        self.mainreport = get_rpath('apbd/tuskpd/R103003_12.jrxml')
        self.subreportlist = []
        #self.subreportlist.append(get_rpath('apbd/tuskpd/R103003_subreport1.jrxml'))
        self.xpath = '/apbd/spm'
        self.root = ET.Element('apbd')

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'spm')
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "alamat").text = row.alamat
            ET.SubElement(xml_greeting, "spm_id").text = unicode(row.spm_id)
            ET.SubElement(xml_greeting, "spm_kd").text = row.spm_kd
            ET.SubElement(xml_greeting, "spm_nm").text = row.spm_nm
            ET.SubElement(xml_greeting, "spm_tgl").text = unicode(row.spm_tgl)
            ET.SubElement(xml_greeting, "ttd_nip").text = row.ttd_nip
            ET.SubElement(xml_greeting, "ttd_nama").text = row.ttd_nama
            ET.SubElement(xml_greeting, "spp_id").text = unicode(row.spp_id)
            ET.SubElement(xml_greeting, "jenis").text = unicode(row.jenis)
            ET.SubElement(xml_greeting, "amount").text = unicode(row.amount)
            ET.SubElement(xml_greeting, "terbilang").text = Terbilang(row.amount)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "jabatan").text = row.jabatan
            ET.SubElement(xml_greeting, "logo").text = logo
            
            rows = DBSession.query(case([(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)=='5.1.1'),"-GJ")], else_=" ").label('kode')
               ).filter(Spp.id==SppItem.ap_spp_id, SppItem.ap_invoice_id==APInvoiceItem.ap_invoice_id, APInvoiceItem.kegiatan_item_id==KegiatanItem.id,
               KegiatanItem.rekening_id==Rekening.id, Spp.id==row.spp_id
               ).group_by(case([(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)=='5.1.1'),"-GJ")], else_=" "))

            for row1 in rows:
                ET.SubElement(xml_greeting, "kode").text  = row1.kode
        return self.root

### SPM // SPTJM LS Pihak Ketiga 1
class b103r003_4Generator(JasperGeneratorWithSubreport):
    def __init__(self):
        self.mainreport = get_rpath('apbd/tuskpd/R103003_4.jrxml')
        self.subreportlist = []
        self.xpath = '/apbd/spm'
        self.root = ET.Element('apbd')

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'spm')
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "alamat").text = row.alamat
            ET.SubElement(xml_greeting, "kode").text = row.kode
            ET.SubElement(xml_greeting, "tanggal").text = unicode(row.tanggal)
            ET.SubElement(xml_greeting, "ttd_nip").text = row.ttd_nip
            ET.SubElement(xml_greeting, "ttd_nama").text = row.ttd_nama
            ET.SubElement(xml_greeting, "amount").text = unicode(row.amount)
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun_id)
            ET.SubElement(xml_greeting, "jenis").text = unicode(row.jenis)
            ET.SubElement(xml_greeting, "ap_bap_no").text = row.ap_bap_no
            ET.SubElement(xml_greeting, "ap_bap_tgl").text = unicode(row.ap_bap_tgl)
            ET.SubElement(xml_greeting, "nilai").text = unicode(row.ap_nilai)
            ET.SubElement(xml_greeting, "ap_kontrak").text = row.ap_kontrak
            ET.SubElement(xml_greeting, "ap_tgl_kontrak").text = unicode(row.ap_tgl_kontrak)
            ET.SubElement(xml_greeting, "ap_nama").text = row.ap_nama
            ET.SubElement(xml_greeting, "ap_pemilik").text = row.ap_pemilik
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "jabatan").text = row.jabatan
            ET.SubElement(xml_greeting, "logo").text = logo
            ET.SubElement(xml_greeting, "terbilang_nilai").text = Terbilang(row.ap_nilai)
        return self.root

### SPM // SPTJM LS Pihak Ketiga 1
class b103r003_5Generator(JasperGeneratorWithSubreport):
    def __init__(self):
        self.mainreport = get_rpath('apbd/tuskpd/R103003_5.jrxml')
        self.subreportlist = []
        self.xpath = '/apbd/spm'
        self.root = ET.Element('apbd')

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'spm')
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "alamat").text = row.alamat
            ET.SubElement(xml_greeting, "kode").text = row.kode
            ET.SubElement(xml_greeting, "tanggal").text = unicode(row.tanggal)
            ET.SubElement(xml_greeting, "ttd_nip").text = row.ttd_nip
            ET.SubElement(xml_greeting, "ttd_nama").text = row.ttd_nama
            ET.SubElement(xml_greeting, "amount").text = unicode(row.amount)
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun_id)
            ET.SubElement(xml_greeting, "jenis").text = unicode(row.jenis)
            ET.SubElement(xml_greeting, "ap_bap_no").text = row.ap_bap_no
            ET.SubElement(xml_greeting, "ap_bap_tgl").text = unicode(row.ap_bap_tgl)
            ET.SubElement(xml_greeting, "nilai").text = unicode(row.ap_nilai)
            ET.SubElement(xml_greeting, "ap_kontrak").text = row.ap_kontrak
            ET.SubElement(xml_greeting, "ap_tgl_kontrak").text = unicode(row.ap_tgl_kontrak)
            ET.SubElement(xml_greeting, "ap_nama").text = row.ap_nama
            ET.SubElement(xml_greeting, "ap_pemilik").text = row.ap_pemilik
            ET.SubElement(xml_greeting, "ap_kwitansi_nilai").text = unicode(row.ap_kwitansi_nilai)
            ET.SubElement(xml_greeting, "ap_kwitansi_no").text = row.ap_kwitansi_no
            ET.SubElement(xml_greeting, "ap_kwitansi_tgl").text = unicode(row.ap_kwitansi_tgl)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "jabatan").text = row.jabatan
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root

### SPM // SPTJM LS
class b103r003_6Generator(JasperGeneratorWithSubreport):
    def __init__(self):
        self.mainreport = get_rpath('apbd/tuskpd/R103003_6.jrxml')
        self.subreportlist = []
        self.xpath = '/apbd/spm'
        self.root = ET.Element('apbd')

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'spm')
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "alamat").text = row.alamat
            ET.SubElement(xml_greeting, "kode").text = row.kode
            ET.SubElement(xml_greeting, "tanggal").text = unicode(row.tanggal)
            ET.SubElement(xml_greeting, "ttd_nip").text = row.ttd_nip
            ET.SubElement(xml_greeting, "ttd_nama").text = row.ttd_nama
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun_id)
            ET.SubElement(xml_greeting, "jenis").text = unicode(row.jenis)
            ET.SubElement(xml_greeting, "jabatan").text = row.jabatan
            ET.SubElement(xml_greeting, "spp_id").text = unicode(row.spp_id)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
            rows = DBSession.query(case([(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)=='5.1.1'),"-GJ")], else_=" ").label('kode1')
               ).filter(Spp.id==SppItem.ap_spp_id, SppItem.ap_invoice_id==APInvoiceItem.ap_invoice_id, APInvoiceItem.kegiatan_item_id==KegiatanItem.id,
               KegiatanItem.rekening_id==Rekening.id, Spp.id==row.spp_id
               ).group_by(case([(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)=='5.1.1'),"-GJ")], else_=" "))

            for row1 in rows:
                ET.SubElement(xml_greeting, "kode1").text  = row1.kode1
        return self.root

### SPM // SPTJM GU
class b103r003_7Generator(JasperGeneratorWithSubreport):
    def __init__(self):
        self.mainreport = get_rpath('apbd/tuskpd/R103003_7.jrxml')
        self.subreportlist = []
        self.xpath = '/apbd/spm'
        self.root = ET.Element('apbd')

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'spm')
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "alamat").text = row.alamat
            ET.SubElement(xml_greeting, "kode").text = row.kode
            ET.SubElement(xml_greeting, "tanggal").text = unicode(row.tanggal)
            ET.SubElement(xml_greeting, "ttd_nip").text = row.ttd_nip
            ET.SubElement(xml_greeting, "ttd_nama").text = row.ttd_nama
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun_id)
            ET.SubElement(xml_greeting, "jenis").text = unicode(row.jenis)
            ET.SubElement(xml_greeting, "jabatan").text = row.jabatan
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root

### SPM // SPTJB GU
class b103r003_8Generator(JasperGeneratorWithSubreport):
    def __init__(self):
        self.mainreport = get_rpath('apbd/tuskpd/R103003_8.jrxml')
        self.subreportlist = []
        #self.subreportlist.append(get_rpath('apbd/tuskpd/R103003_subreport1.jrxml'))
        self.xpath = '/apbd/spm'
        self.root = ET.Element('apbd')

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'spm')
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "alamat").text = row.alamat
            ET.SubElement(xml_greeting, "prg_kd").text = row.program_kd
            ET.SubElement(xml_greeting, "keg_kd").text = row.keg_kd
            ET.SubElement(xml_greeting, "keg_nm").text = row.keg_nm
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "amount").text = unicode(row.amount)
            ET.SubElement(xml_greeting, "pph").text = unicode(row.pph)
            ET.SubElement(xml_greeting, "ppn").text = unicode(row.ppn)
            ET.SubElement(xml_greeting, "ap_kwitansi_no").text = row.ap_kwitansi_no
            ET.SubElement(xml_greeting, "ap_kwitansi_tgl").text = unicode(row.ap_kwitansi_tgl)
            ET.SubElement(xml_greeting, "ap_nama").text = row.ap_nama
            ET.SubElement(xml_greeting, "tanggal").text = unicode(row.tanggal)
            ET.SubElement(xml_greeting, "no_bku").text = row.no_bku
            ET.SubElement(xml_greeting, "tgl_bku").text = unicode(row.tgl_bku)
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun_id)
            ET.SubElement(xml_greeting, "jenis").text = unicode(row.jenis)
            ET.SubElement(xml_greeting, "kode").text = row.kode
            ET.SubElement(xml_greeting, "ttd_nip").text = row.ttd_nip
            ET.SubElement(xml_greeting, "ttd_nama").text = row.ttd_nama
            ET.SubElement(xml_greeting, "jabatan").text = row.jabatan
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root

### SPM // SPTJB LS
class b103r003_9Generator(JasperGeneratorWithSubreport):
    def __init__(self):
        self.mainreport = get_rpath('apbd/tuskpd/R103003_9.jrxml')
        self.subreportlist = []
        #self.subreportlist.append(get_rpath('apbd/tuskpd/R103003_5_subreport1.jrxml'))
        self.xpath = '/apbd/spm'
        self.root = ET.Element('apbd')

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'spm')
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "alamat").text = row.alamat
            ET.SubElement(xml_greeting, "prg_kd").text = row.program_kd
            ET.SubElement(xml_greeting, "keg_kd").text = row.keg_kd
            ET.SubElement(xml_greeting, "keg_nm").text = row.keg_nm
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "amount").text = unicode(row.amount)
            ET.SubElement(xml_greeting, "pph").text = unicode(row.pph)
            ET.SubElement(xml_greeting, "ppn").text = unicode(row.ppn)
            ET.SubElement(xml_greeting, "ap_kwitansi_no").text = row.ap_kwitansi_no
            ET.SubElement(xml_greeting, "ap_kwitansi_tgl").text = unicode(row.ap_kwitansi_tgl)
            ET.SubElement(xml_greeting, "ap_nama").text = row.ap_nama
            ET.SubElement(xml_greeting, "tanggal").text = unicode(row.tanggal)
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun_id)
            ET.SubElement(xml_greeting, "jenis").text = unicode(row.jenis)
            ET.SubElement(xml_greeting, "kode").text = row.kode
            ET.SubElement(xml_greeting, "ttd_nip").text = row.ttd_nip
            ET.SubElement(xml_greeting, "ttd_nama").text = row.ttd_nama
            ET.SubElement(xml_greeting, "jabatan").text = row.jabatan
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root

### SPM // SPTJB LS Pihak Ketiga
class b103r003_10Generator(JasperGeneratorWithSubreport):
    def __init__(self):
        self.mainreport = get_rpath('apbd/tuskpd/R103003_10.jrxml')
        self.subreportlist = []
        #self.subreportlist.append(get_rpath('apbd/tuskpd/R103003_subreport1.jrxml'))
        self.xpath = '/apbd/spm'
        self.root = ET.Element('apbd')

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'spm')
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "alamat").text = row.alamat
            ET.SubElement(xml_greeting, "prg_kd").text = row.program_kd
            ET.SubElement(xml_greeting, "keg_kd").text = row.keg_kd
            ET.SubElement(xml_greeting, "keg_nm").text = row.keg_nm
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "amount").text = unicode(row.amount)
            ET.SubElement(xml_greeting, "pph").text = unicode(row.pph)
            ET.SubElement(xml_greeting, "ppn").text = unicode(row.ppn)
            ET.SubElement(xml_greeting, "ap_kwitansi_no").text = row.ap_kwitansi_no
            ET.SubElement(xml_greeting, "ap_kwitansi_tgl").text = unicode(row.ap_kwitansi_tgl)
            ET.SubElement(xml_greeting, "ap_nama").text = row.ap_nama
            ET.SubElement(xml_greeting, "tanggal").text = unicode(row.tanggal)
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun_id)
            ET.SubElement(xml_greeting, "jenis").text = unicode(row.jenis)
            ET.SubElement(xml_greeting, "kode").text = row.kode
            ET.SubElement(xml_greeting, "ttd_nip").text = row.ttd_nip
            ET.SubElement(xml_greeting, "ttd_nama").text = row.ttd_nama
            ET.SubElement(xml_greeting, "jabatan").text = row.jabatan
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root

### SPM // Checklist
class b103r003_11Generator(JasperGeneratorWithSubreport):
    def __init__(self):
        self.mainreport = get_rpath('apbd/tuskpd/R103003_11.jrxml')
        self.subreportlist = []
        #self.subreportlist.append(get_rpath('apbd/tuskpd/R103003_subreport1.jrxml'))
        self.xpath = '/apbd/spm'
        self.root = ET.Element('apbd')

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'spm')
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "unit_id").text = unicode(row.unit_id)
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "alamat").text = row.alamat
            ET.SubElement(xml_greeting, "spm_kd").text = row.spm_kd
            ET.SubElement(xml_greeting, "spm_nm").text = row.spm_nm
            ET.SubElement(xml_greeting, "spm_tgl").text = unicode(row.spm_tgl)
            ET.SubElement(xml_greeting, "ttd_nip").text = row.ttd_nip
            ET.SubElement(xml_greeting, "ttd_nama").text = row.ttd_nama
            ET.SubElement(xml_greeting, "jenis").text = unicode(row.jenis)
            ET.SubElement(xml_greeting, "kode").text = row.kode
            ET.SubElement(xml_greeting, "kegiatan").text = row.nama
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
            rowttd = DBSession.query(Pejabat.uraian.label('jabatan'), Pegawai.nama.label('pa_nama'), Pegawai.kode.label('pa_nip')
               ).filter(Pejabat.pegawai_id==Pegawai.id, Pejabat.jabatan_id==Jabatan.id, 
               Pejabat.unit_id==row.unit_id, Jabatan.kode=='220')
            for row3 in rowttd :
               ET.SubElement(xml_greeting, "jabatan").text = row3.jabatan
               ET.SubElement(xml_greeting, "pa_nama").text = row3.pa_nama
               ET.SubElement(xml_greeting, "pa_nip").text = row3.pa_nip
        return self.root

class b104r000Generator(JasperGenerator):
    def __init__(self):
        super(b104r000Generator, self).__init__()
        self.reportname = get_rpath('apbd/tuskpd/R104000.jrxml')
        self.xpath = '/apbd/invoice'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'invoice')
            ET.SubElement(xml_greeting, "tahun_id").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "tgl_invoice").text = unicode(row.tgl_invoice)
            ET.SubElement(xml_greeting, "jenis").text = row.jenis
            ET.SubElement(xml_greeting, "invoice_kd").text = row.invoice_kd
            ET.SubElement(xml_greeting, "kegiatan_nm").text = row.kegiatan_nm
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "jumlah").text = unicode(row.jumlah)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root

class b104r1001Generator(JasperGenerator):
    def __init__(self):
        super(b104r1001Generator, self).__init__()
        self.reportname = get_rpath('apbd/tuskpd/R1041001.jrxml')
        self.xpath = '/apbd/spp'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'spp')
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "jenis").text = row.jenis
            ET.SubElement(xml_greeting, "spp_kd").text = row.spp_kd
            ET.SubElement(xml_greeting, "spp_nm").text = row.spp_nm
            ET.SubElement(xml_greeting, "tgl_spp").text = unicode(row.tgl_spp)
            ET.SubElement(xml_greeting, "spm_kd").text = row.spm_kd
            ET.SubElement(xml_greeting, "tgl_spm").text = unicode(row.tgl_spm)
            ET.SubElement(xml_greeting, "sp2d_kd").text = row.sp2d_kd
            ET.SubElement(xml_greeting, "tgl_sp2d").text = unicode(row.tgl_sp2d)
            ET.SubElement(xml_greeting, "nominal").text = unicode(row.nominal)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root

class b104r1002Generator(JasperGenerator):
    def __init__(self):
        super(b104r1002Generator, self).__init__()
        self.reportname = get_rpath('apbd/tuskpd/R1041002.jrxml')
        self.xpath = '/apbd/spp'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'spp')
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "tgl_spp").text = unicode(row.tgl_spp)
            ET.SubElement(xml_greeting, "spp_kd").text = row.spp_kd
            ET.SubElement(xml_greeting, "spp_nm").text = row.spp_nm
            ET.SubElement(xml_greeting, "UP").text = unicode(row.UP)
            ET.SubElement(xml_greeting, "GU").text = unicode(row.GU)
            ET.SubElement(xml_greeting, "TU").text = unicode(row.TU)
            ET.SubElement(xml_greeting, "LS_GJ").text = unicode(row.LS_GJ)
            ET.SubElement(xml_greeting, "LS").text = unicode(row.LS)
            ET.SubElement(xml_greeting, "jenis").text = row.jenis
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root

class b104r1003Generator(JasperGenerator):
    def __init__(self):
        super(b104r1003Generator, self).__init__()
        self.reportname = get_rpath('apbd/tuskpd/R1041003.jrxml')
        self.xpath = '/apbd/spp'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'spp')
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "tgl_spp").text = unicode(row.tgl_spp)
            ET.SubElement(xml_greeting, "spp_kd").text = row.spp_kd
            ET.SubElement(xml_greeting, "spp_nm").text = row.spp_nm
            ET.SubElement(xml_greeting, "UP").text = unicode(row.UP)
            ET.SubElement(xml_greeting, "GU").text = unicode(row.GU)
            ET.SubElement(xml_greeting, "TU").text = unicode(row.TU)
            ET.SubElement(xml_greeting, "LS").text = unicode(row.LS)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root

class b104r1004Generator(JasperGenerator):
    def __init__(self):
        super(b104r1004Generator, self).__init__()
        self.reportname = get_rpath('apbd/tuskpd/R1041004.jrxml')
        self.xpath = '/apbd/spp'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'spp')
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "tgl_spm").text = unicode(row.tgl_spm)
            ET.SubElement(xml_greeting, "spm_kd").text = row.spm_kd
            ET.SubElement(xml_greeting, "spm_nm").text = row.spm_nm
            ET.SubElement(xml_greeting, "BRUTO").text = unicode(row.BRUTO)
            ET.SubElement(xml_greeting, "POTONGAN").text = unicode(row.POTONGAN)
            ET.SubElement(xml_greeting, "NETTO").text = unicode(row.NETTO)
            ET.SubElement(xml_greeting, "INFORMASI").text = unicode(row.INFORMASI)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root 

class b104r2001Generator(JasperGenerator):
    def __init__(self):
        super(b104r2001Generator, self).__init__()
        self.reportname = get_rpath('apbd/tuskpd/R1042001.jrxml')
        self.xpath = '/apbd/spp'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'spp')
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "jenis").text = row.jenis
            ET.SubElement(xml_greeting, "spp_kd").text = row.spp_kd
            ET.SubElement(xml_greeting, "spp_nm").text = row.spp_nm
            ET.SubElement(xml_greeting, "tgl_spp").text = unicode(row.tgl_spp)
            ET.SubElement(xml_greeting, "spm_kd").text = row.spm_kd
            ET.SubElement(xml_greeting, "tgl_spm").text = unicode(row.tgl_spm)
            ET.SubElement(xml_greeting, "sp2d_kd").text = row.sp2d_kd
            ET.SubElement(xml_greeting, "tgl_sp2d").text = unicode(row.tgl_sp2d)
            ET.SubElement(xml_greeting, "nominal").text = unicode(row.nominal)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root

class b104r2002Generator(JasperGenerator):
    def __init__(self):
        super(b104r2002Generator, self).__init__()
        self.reportname = get_rpath('apbd/tuskpd/R1042002.jrxml')
        self.xpath = '/apbd/spp'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'spp')
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "jenis").text = row.jenis
            ET.SubElement(xml_greeting, "tgl_spp").text = unicode(row.tgl_spp)
            ET.SubElement(xml_greeting, "spp_kd").text = row.spp_kd
            ET.SubElement(xml_greeting, "spp_nm").text = row.spp_nm
            ET.SubElement(xml_greeting, "UP").text = unicode(row.UP)
            ET.SubElement(xml_greeting, "GU").text = unicode(row.GU)
            ET.SubElement(xml_greeting, "TU").text = unicode(row.TU)
            ET.SubElement(xml_greeting, "LS_GJ").text = unicode(row.LS_GJ)
            ET.SubElement(xml_greeting, "LS").text = unicode(row.LS)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root

class b104r2003Generator(JasperGenerator):
    def __init__(self):
        super(b104r2003Generator, self).__init__()
        self.reportname = get_rpath('apbd/tuskpd/R1042003.jrxml')
        self.xpath = '/apbd/spp'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'spp')
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "spm_id").text = unicode(row.spm_id)
            ET.SubElement(xml_greeting, "tgl_spm").text = unicode(row.tgl_spm)
            ET.SubElement(xml_greeting, "spm_kd").text = row.spm_kd
            ET.SubElement(xml_greeting, "spm_nm").text = row.spm_nm
            ET.SubElement(xml_greeting, "jenis").text = row.jenis
            ET.SubElement(xml_greeting, "spp_id").text = unicode(row.spp_id)
            ET.SubElement(xml_greeting, "nominal").text = unicode(row.nominal)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
            
            rowpot = DBSession.query(func.coalesce(func.sum(SpmPotongan.nilai),0).label('nilai_pot')
               ).filter(SpmPotongan.ap_spm_id==row.spm_id)
            for row2 in rowpot :
               ET.SubElement(xml_greeting, "nilai_pot").text = unicode(row2.nilai_pot)

            rowppn = DBSession.query(func.coalesce(func.sum(APInvoiceItem.ppn),0).label('ppn'),
               func.coalesce(func.sum(APInvoiceItem.pph),0).label('pph')
               ).filter(APInvoiceItem.ap_invoice_id==SppItem.ap_invoice_id, SppItem.ap_spp_id==row.spp_id)
            for row3 in rowppn :
               ET.SubElement(xml_greeting, "ppn").text = unicode(row3.ppn)
               ET.SubElement(xml_greeting, "pph").text = unicode(row3.pph)

        return self.root

class b104r2004Generator(JasperGenerator):
    def __init__(self):
        super(b104r2004Generator, self).__init__()
        self.reportname = get_rpath('apbd/tuskpd/R1042004.jrxml')
        self.xpath = '/apbd/spp'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'spp')
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "tgl_spm").text = unicode(row.tgl_spm)
            ET.SubElement(xml_greeting, "spm_kd").text = row.spm_kd
            ET.SubElement(xml_greeting, "spm_nm").text = row.spm_nm
            ET.SubElement(xml_greeting, "BRUTO").text = unicode(row.BRUTO)
            ET.SubElement(xml_greeting, "POTONGAN").text = unicode(row.POTONGAN)
            ET.SubElement(xml_greeting, "NETTO").text = unicode(row.NETTO)
            ET.SubElement(xml_greeting, "INFORMASI").text = unicode(row.INFORMASI)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root 

class b103r003_10Generator(JasperGeneratorWithSubreport):
    def __init__(self):
        self.mainreport = get_rpath('apbd/tuskpd/R103003_10.jrxml')
        self.subreportlist = []
        #self.subreportlist.append(get_rpath('apbd/tuskpd/R103003_subreport1.jrxml'))
        self.xpath = '/apbd/spm'
        self.root = ET.Element('apbd')

class b104r300Generator(JasperGeneratorWithSubreport):
    def __init__(self):
        self.mainreport = get_rpath('apbd/tuskpd/R104300.jrxml')
        self.subreportlist = []
        self.subreportlist.append(get_rpath('apbd/tuskpd/R104300_subreport1.jrxml'))
        self.xpath = '/apbd/spj'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'spj')
            ET.SubElement(xml_greeting, "unit_id").text = unicode(row.unit_id)
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "keg_kd").text = row.keg_kd
            ET.SubElement(xml_greeting, "keg_nm").text = row.keg_nm
            ET.SubElement(xml_greeting, "keg_sub_id").text = unicode(row.keg_sub_id)
            ET.SubElement(xml_greeting, "rek_id").text = unicode(row.rek_id)
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "dpa").text = unicode(row.dpa)
            ET.SubElement(xml_greeting, "dppa").text = unicode(row.dppa)
            ET.SubElement(xml_greeting, "LSG_lalu").text = unicode(row.LSG_lalu)
            ET.SubElement(xml_greeting, "LSG_kini").text = unicode(row.LSG_kini)
            ET.SubElement(xml_greeting, "LS_lalu").text = unicode(row.LS_lalu)
            ET.SubElement(xml_greeting, "LS_kini").text = unicode(row.LS_kini)
            ET.SubElement(xml_greeting, "Lain_lalu").text = unicode(row.Lain_lalu)
            ET.SubElement(xml_greeting, "Lain_kini").text = unicode(row.Lain_kini)
            ET.SubElement(xml_greeting, "bulan").text = unicode(bulan)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
            ET.SubElement(xml_greeting, "japbd").text = unicode(japbd)
            
            """rows = DBSession.query(Pegawai.nama.label('pa_nama'), Pegawai.kode.label('pa_nip')
               ).filter(Pejabat.pegawai_id==Pegawai.id, Pejabat.jabatan_id==Jabatan.id, 
               Pejabat.unit_id==row.unit_id, Jabatan.kode=='200')
            for row2 in rows :
               ET.SubElement(xml_greeting, "pa_nama").text = row2.pa_nama
               ET.SubElement(xml_greeting, "pa_nip").text = row2.pa_nip
            """
            ET.SubElement(xml_greeting, "pa_nama").text = pa_nama
            ET.SubElement(xml_greeting, "pa_nip").text = pa_nip
            
            """rows2 = DBSession.query(Pegawai.nama.label('bend_nama'), Pegawai.kode.label('bend_nip')
               ).filter(Pejabat.pegawai_id==Pegawai.id, Pejabat.jabatan_id==Jabatan.id, 
               Pejabat.unit_id==row.unit_id, Jabatan.kode=='236')
            for row3 in rows2 :
               ET.SubElement(xml_greeting, "bend_nama").text = row3.bend_nama
               ET.SubElement(xml_greeting, "bend_nip").text = row3.bend_nip
            """
            ET.SubElement(xml_greeting, "bend_nama").text = benda_nama
            ET.SubElement(xml_greeting, "bend_nip").text = benda_nip
            
            subq = DBSession.query(APInvoice.id, Sp2d.id.label('sp2d_id'), 
                func.coalesce(func.sum(case([(and_(extract('month',APInvoice.tanggal)<bulan, Rekening.kode=='7.1.1.02.01'),SpmPotongan.nilai)], else_=0)),0).label('ppn_lalu'),
                func.coalesce(func.sum(case([(and_(extract('month',APInvoice.tanggal)==bulan, Rekening.kode=='7.1.1.02.01'),SpmPotongan.nilai)], else_=0)),0).label('ppn_kini'),
                func.coalesce(func.sum(case([(and_(extract('month',APInvoice.tanggal)<bulan, Rekening.kode=='7.1.1.02.02'),SpmPotongan.nilai)], else_=0)),0).label('pph21_lalu'),
                func.coalesce(func.sum(case([(and_(extract('month',APInvoice.tanggal)==bulan, Rekening.kode=='7.1.1.02.02'),SpmPotongan.nilai)], else_=0)),0).label('pph21_kini'),
                func.coalesce(func.sum(case([(and_(extract('month',APInvoice.tanggal)<bulan, Rekening.kode=='7.1.1.02.03'),SpmPotongan.nilai)], else_=0)),0).label('pph22_lalu'),
                func.coalesce(func.sum(case([(and_(extract('month',APInvoice.tanggal)==bulan, Rekening.kode=='7.1.1.02.03'),SpmPotongan.nilai)], else_=0)),0).label('pph22_kini'),
                func.coalesce(func.sum(case([(and_(extract('month',APInvoice.tanggal)<bulan, Rekening.kode=='7.1.1.02.04'),SpmPotongan.nilai)], else_=0)),0).label('pph23_lalu'),
                func.coalesce(func.sum(case([(and_(extract('month',APInvoice.tanggal)==bulan, Rekening.kode=='7.1.1.02.04'),SpmPotongan.nilai)], else_=0)),0).label('pph23_kini'),
                func.coalesce(func.sum(case([(and_(extract('month',APInvoice.tanggal)<bulan, func.substr(Rekening.kode,1,3)=='7.1', 
                not_(Rekening.kode.in_(['7.1.1.02.01','7.1.1.02.02','7.1.1.02.03','7.1.1.02.04']))),SpmPotongan.nilai)], else_=0)),0).label('lain_lalu'),
                func.coalesce(func.sum(case([(and_(extract('month',APInvoice.tanggal)==bulan, func.substr(Rekening.kode,1,3)=='7.1', 
                not_(Rekening.kode.in_(['7.1.1.02.01','7.1.1.02.02','7.1.1.02.03','7.1.1.02.04']))),SpmPotongan.nilai)], else_=0)),0).label('lain_kini'),
               ).join(SppItem, Spp, Spm, SpmPotongan, Rekening
               ).outerjoin(Sp2d, Sp2d.ap_spm_id==Spm.id
               ).filter(
                #SpmPotongan.rekening_id==Rekening.id, SpmPotongan.ap_spm_id==Spm.id, Spm.ap_spp_id==Spp.id,
                #SppItem.ap_spp_id==Spp.id, SppItem.ap_invoice_id==APInvoice.id,
                APInvoice.unit_id==row.unit_id, APInvoice.tahun_id==row.tahun
               ).group_by(APInvoice.id, Sp2d.id
               ).subquery()

            subq2 = DBSession.query(APInvoice.tahun_id, APInvoice.id, APInvoice.tanggal, Unit.id.label('unit_id'), 
               case([(and_(APInvoice.jenis==4, func.substr(Rekening.kode,1,5)=='5.1.1', func.substr(Rekening.kode,1,8)!='5.1.1.02'),'LSG'), 
               (and_(APInvoice.jenis==4, or_(func.substr(Rekening.kode,1,5)!='5.1.1',func.substr(Rekening.kode,1,8)=='5.1.1.02')),'LS')], else_='LAIN').label('jenis'),
               func.coalesce(func.sum(APInvoiceItem.amount),0).label('amount'), 
               case([(subq.c.sp2d_id>0,subq.c.sp2d_id)], else_=0).label('sp2d_id'), subq.c.ppn_lalu, subq.c.ppn_kini, subq.c.pph21_lalu, subq.c.pph21_kini, subq.c.pph22_lalu, subq.c.pph22_kini, 
               subq.c.pph23_lalu, subq.c.pph23_kini, subq.c.lain_lalu, subq.c.lain_kini
               ).join(Unit,APInvoiceItem, KegiatanItem, Rekening
               ).outerjoin(subq, APInvoice.id==subq.c.id
               ).filter(Unit.id==row.unit_id, APInvoice.tahun_id==row.tahun
               ).group_by(APInvoice.tahun_id, APInvoice.id, APInvoice.tanggal, Unit.id, 
               case([(and_(APInvoice.jenis==4, func.substr(Rekening.kode,1,5)=='5.1.1', func.substr(Rekening.kode,1,8)!='5.1.1.02'),'LSG'), 
               (and_(APInvoice.jenis==4, or_(func.substr(Rekening.kode,1,5)!='5.1.1',func.substr(Rekening.kode,1,8)=='5.1.1.02')),'LS')], else_='LAIN'),
               case([(subq.c.sp2d_id>0,subq.c.sp2d_id)], else_=0), subq.c.ppn_lalu, subq.c.ppn_kini, subq.c.pph21_lalu, subq.c.pph21_kini, subq.c.pph22_lalu, subq.c.pph22_kini, 
               subq.c.pph23_lalu, subq.c.pph23_kini, subq.c.lain_lalu, subq.c.lain_kini
               ).subquery()
               
            rowitem = DBSession.query(subq2.c.tahun_id, subq2.c.unit_id, 
               #Amount
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LSG', subq2.c.sp2d_id<>0),subq2.c.amount)], else_=0)),0).label('lsg_amount_lalu'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LSG'),subq2.c.amount)], else_=0)),0).label('lsg_amount_lalu1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LSG', subq2.c.sp2d_id<>0),subq2.c.amount)], else_=0)),0).label('lsg_amount_kini'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LSG'),subq2.c.amount)], else_=0)),0).label('lsg_amount_kini1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LS', subq2.c.sp2d_id<>0),subq2.c.amount)], else_=0)),0).label('ls_amount_lalu'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LS'),subq2.c.amount)], else_=0)),0).label('ls_amount_lalu1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LS', subq2.c.sp2d_id<>0),subq2.c.amount)], else_=0)),0).label('ls_amount_kini'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LS'),subq2.c.amount)], else_=0)),0).label('ls_amount_kini1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LAIN', subq2.c.sp2d_id<>0),subq2.c.amount)], else_=0)),0).label('lain_amount_lalu'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LAIN'),subq2.c.amount)], else_=0)),0).label('lain_amount_lalu1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LAIN', subq2.c.sp2d_id<>0),subq2.c.amount)], else_=0)),0).label('lain_amount_kini'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LAIN'),subq2.c.amount)], else_=0)),0).label('lain_amount_kini1'),
               #PPn
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LSG', subq2.c.sp2d_id<>0),subq2.c.ppn_lalu)], else_=0)),0).label('lsg_ppn_lalu'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LSG', subq2.c.sp2d_id<>0),subq2.c.ppn_kini)], else_=0)),0).label('lsg_ppn_kini'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LS', subq2.c.sp2d_id<>0),subq2.c.ppn_lalu)], else_=0)),0).label('ls_ppn_lalu'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LS', subq2.c.sp2d_id<>0),subq2.c.ppn_kini)], else_=0)),0).label('ls_ppn_kini'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LAIN', subq2.c.sp2d_id<>0),subq2.c.ppn_lalu)], else_=0)),0).label('lain_ppn_lalu'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LAIN', subq2.c.sp2d_id<>0),subq2.c.ppn_kini)], else_=0)),0).label('lain_ppn_kini'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LSG'),subq2.c.ppn_lalu)], else_=0)),0).label('lsg_ppn_lalu1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LSG'),subq2.c.ppn_kini)], else_=0)),0).label('lsg_ppn_kini1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LS'),subq2.c.ppn_lalu)], else_=0)),0).label('ls_ppn_lalu1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LS'),subq2.c.ppn_kini)], else_=0)),0).label('ls_ppn_kini1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LAIN'),subq2.c.ppn_lalu)], else_=0)),0).label('lain_ppn_lalu1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LAIN'),subq2.c.ppn_kini)], else_=0)),0).label('lain_ppn_kini1'),
               #PPh21
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LSG', subq2.c.sp2d_id<>0),subq2.c.pph21_lalu)], else_=0)),0).label('lsg_pph21_lalu'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LSG', subq2.c.sp2d_id<>0),subq2.c.pph21_kini)], else_=0)),0).label('lsg_pph21_kini'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LS', subq2.c.sp2d_id<>0),subq2.c.pph21_lalu)], else_=0)),0).label('ls_pph21_lalu'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LS', subq2.c.sp2d_id<>0),subq2.c.pph21_kini)], else_=0)),0).label('ls_pph21_kini'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LAIN', subq2.c.sp2d_id<>0),subq2.c.pph21_lalu)], else_=0)),0).label('lain_pph21_lalu'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LAIN', subq2.c.sp2d_id<>0),subq2.c.pph21_kini)], else_=0)),0).label('lain_pph21_kini'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LSG'),subq2.c.pph21_lalu)], else_=0)),0).label('lsg_pph21_lalu1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LSG'),subq2.c.pph21_kini)], else_=0)),0).label('lsg_pph21_kini1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LS'),subq2.c.pph21_lalu)], else_=0)),0).label('ls_pph21_lalu1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LS'),subq2.c.pph21_kini)], else_=0)),0).label('ls_pph21_kini1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LAIN'),subq2.c.pph21_lalu)], else_=0)),0).label('lain_pph21_lalu1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LAIN'),subq2.c.pph21_kini)], else_=0)),0).label('lain_pph21_kini1'),
               #PPh22
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LSG', subq2.c.sp2d_id<>0),subq2.c.pph22_lalu)], else_=0)),0).label('lsg_pph22_lalu'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LSG', subq2.c.sp2d_id<>0),subq2.c.pph22_kini)], else_=0)),0).label('lsg_pph22_kini'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LS', subq2.c.sp2d_id<>0),subq2.c.pph22_lalu)], else_=0)),0).label('ls_pph22_lalu'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LS', subq2.c.sp2d_id<>0),subq2.c.pph22_kini)], else_=0)),0).label('ls_pph22_kini'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LAIN', subq2.c.sp2d_id<>0),subq2.c.pph22_lalu)], else_=0)),0).label('lain_pph22_lalu'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LAIN', subq2.c.sp2d_id<>0),subq2.c.pph22_kini)], else_=0)),0).label('lain_pph22_kini'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LSG'),subq2.c.pph22_lalu)], else_=0)),0).label('lsg_pph22_lalu1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LSG'),subq2.c.pph22_kini)], else_=0)),0).label('lsg_pph22_kini1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LS'),subq2.c.pph22_lalu)], else_=0)),0).label('ls_pph22_lalu1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LS'),subq2.c.pph22_kini)], else_=0)),0).label('ls_pph22_kini1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LAIN'),subq2.c.pph22_lalu)], else_=0)),0).label('lain_pph22_lalu1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LAIN'),subq2.c.pph22_kini)], else_=0)),0).label('lain_pph22_kini1'),
               #PPh23
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LSG', subq2.c.sp2d_id<>0),subq2.c.pph23_lalu)], else_=0)),0).label('lsg_pph23_lalu'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LSG', subq2.c.sp2d_id<>0),subq2.c.pph23_kini)], else_=0)),0).label('lsg_pph23_kini'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LS', subq2.c.sp2d_id<>0),subq2.c.pph23_lalu)], else_=0)),0).label('ls_pph23_lalu'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LS', subq2.c.sp2d_id<>0),subq2.c.pph23_kini)], else_=0)),0).label('ls_pph23_kini'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LAIN', subq2.c.sp2d_id<>0),subq2.c.pph23_lalu)], else_=0)),0).label('lain_pph23_lalu'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LAIN', subq2.c.sp2d_id<>0),subq2.c.pph23_kini)], else_=0)),0).label('lain_pph23_kini'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LSG'),subq2.c.pph23_lalu)], else_=0)),0).label('lsg_pph23_lalu1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LSG'),subq2.c.pph23_kini)], else_=0)),0).label('lsg_pph23_kini1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LS'),subq2.c.pph23_lalu)], else_=0)),0).label('ls_pph23_lalu1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LS'),subq2.c.pph23_kini)], else_=0)),0).label('ls_pph23_kini1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LAIN'),subq2.c.pph23_lalu)], else_=0)),0).label('lain_pph23_lalu1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LAIN'),subq2.c.pph23_kini)], else_=0)),0).label('lain_pph23_kini1'),
               #Lainnya
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LSG', subq2.c.sp2d_id<>0),subq2.c.lain_lalu)], else_=0)),0).label('lsg_lain_lalu'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LSG', subq2.c.sp2d_id<>0),subq2.c.lain_kini)], else_=0)),0).label('lsg_lain_kini'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LS', subq2.c.sp2d_id<>0),subq2.c.lain_lalu)], else_=0)),0).label('ls_lain_lalu'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LS', subq2.c.sp2d_id<>0),subq2.c.lain_kini)], else_=0)),0).label('ls_lain_kini'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LAIN', subq2.c.sp2d_id<>0),subq2.c.lain_lalu)], else_=0)),0).label('lain_lain_lalu'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LAIN', subq2.c.sp2d_id<>0),subq2.c.lain_kini)], else_=0)),0).label('lain_lain_kini'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LSG'),subq2.c.lain_lalu)], else_=0)),0).label('lsg_lain_lalu1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LSG'),subq2.c.lain_kini)], else_=0)),0).label('lsg_lain_kini1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LS'),subq2.c.lain_lalu)], else_=0)),0).label('ls_lain_lalu1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LS'),subq2.c.lain_kini)], else_=0)),0).label('ls_lain_kini1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LAIN'),subq2.c.lain_lalu)], else_=0)),0).label('lain_lain_lalu1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LAIN'),subq2.c.lain_kini)], else_=0)),0).label('lain_lain_kini1'),
               #).filter(subq2.c.tahun_id==row.unit_id, subq2.c.unit_id==row.tahun
               ).group_by(subq2.c.tahun_id, subq2.c.unit_id
               )
               
            for row4 in rowitem :
                xml_a = ET.SubElement(xml_greeting, "item")
                ET.SubElement(xml_a, "unit_id").text =unicode(row4.unit_id)
                ET.SubElement(xml_a, "tahun_id").text =unicode(row4.tahun_id)
                ET.SubElement(xml_a, "lsg_amount_lalu").text =unicode(row4.lsg_amount_lalu)
                ET.SubElement(xml_a, "lsg_amount_kini").text =unicode(row4.lsg_amount_kini)
                ET.SubElement(xml_a, "ls_amount_lalu").text =unicode(row4.ls_amount_lalu)
                ET.SubElement(xml_a, "ls_amount_kini").text =unicode(row4.ls_amount_kini)
                ET.SubElement(xml_a, "lain_amount_lalu").text =unicode(row4.lain_amount_lalu)
                ET.SubElement(xml_a, "lain_amount_kini").text =unicode(row4.lain_amount_kini)
                ET.SubElement(xml_a, "lsg_ppn_lalu").text =unicode(row4.lsg_ppn_lalu)
                ET.SubElement(xml_a, "lsg_ppn_kini").text =unicode(row4.lsg_ppn_kini)
                ET.SubElement(xml_a, "ls_ppn_lalu").text =unicode(row4.ls_ppn_lalu)
                ET.SubElement(xml_a, "ls_ppn_kini").text =unicode(row4.ls_ppn_kini)
                ET.SubElement(xml_a, "lain_ppn_lalu").text =unicode(row4.lain_ppn_lalu)
                ET.SubElement(xml_a, "lain_ppn_kini").text =unicode(row4.lain_ppn_kini)
                ET.SubElement(xml_a, "lsg_pph21_lalu").text =unicode(row4.lsg_pph21_lalu)
                ET.SubElement(xml_a, "lsg_pph21_kini").text =unicode(row4.lsg_pph21_kini)
                ET.SubElement(xml_a, "ls_pph21_lalu").text =unicode(row4.ls_pph21_lalu)
                ET.SubElement(xml_a, "ls_pph21_kini").text =unicode(row4.ls_pph21_kini)
                ET.SubElement(xml_a, "lain_pph21_lalu").text =unicode(row4.lain_pph21_lalu)
                ET.SubElement(xml_a, "lain_pph21_kini").text =unicode(row4.lain_pph21_kini)
                ET.SubElement(xml_a, "lsg_pph22_lalu").text =unicode(row4.lsg_pph22_lalu)
                ET.SubElement(xml_a, "lsg_pph22_kini").text =unicode(row4.lsg_pph22_kini)
                ET.SubElement(xml_a, "ls_pph22_lalu").text =unicode(row4.ls_pph22_lalu)
                ET.SubElement(xml_a, "ls_pph22_kini").text =unicode(row4.ls_pph22_kini)
                ET.SubElement(xml_a, "lain_pph22_lalu").text =unicode(row4.lain_pph22_lalu)
                ET.SubElement(xml_a, "lain_pph22_kini").text =unicode(row4.lain_pph22_kini)
                ET.SubElement(xml_a, "lsg_pph23_lalu").text =unicode(row4.lsg_pph23_lalu)
                ET.SubElement(xml_a, "lsg_pph23_kini").text =unicode(row4.lsg_pph23_kini)
                ET.SubElement(xml_a, "ls_pph23_lalu").text =unicode(row4.ls_pph23_lalu)
                ET.SubElement(xml_a, "ls_pph23_kini").text =unicode(row4.ls_pph23_kini)
                ET.SubElement(xml_a, "lain_pph23_lalu").text =unicode(row4.lain_pph23_lalu)
                ET.SubElement(xml_a, "lain_pph23_kini").text =unicode(row4.lain_pph23_kini)
                ET.SubElement(xml_a, "lsg_lain_lalu").text =unicode(row4.lsg_lain_lalu)
                ET.SubElement(xml_a, "lsg_lain_kini").text =unicode(row4.lsg_lain_kini)
                ET.SubElement(xml_a, "ls_lain_lalu").text =unicode(row4.ls_lain_lalu)
                ET.SubElement(xml_a, "ls_lain_kini").text =unicode(row4.ls_lain_kini)
                ET.SubElement(xml_a, "lain_lain_lalu").text =unicode(row4.lain_lain_lalu)
                ET.SubElement(xml_a, "lain_lain_kini").text =unicode(row4.lain_lain_kini)

                ET.SubElement(xml_a, "lsg_tot_lalu").text =unicode(row4.lsg_amount_lalu + row4.lsg_ppn_lalu + row4.lsg_pph21_lalu + row4.lsg_pph22_lalu + row4.lsg_pph23_lalu + row4.lsg_lain_lalu)
                ET.SubElement(xml_a, "lsg_tot_kini").text =unicode(row4.lsg_amount_kini + row4.lsg_ppn_kini + row4.lsg_pph21_kini + row4.lsg_pph22_kini + row4.lsg_pph23_kini + row4.lsg_lain_kini)
                ET.SubElement(xml_a, "ls_tot_lalu").text =unicode(row4.ls_amount_lalu + row4.ls_ppn_lalu + row4.ls_pph21_lalu + row4.ls_pph22_lalu + row4.ls_pph23_lalu + row4.ls_lain_lalu)
                ET.SubElement(xml_a, "ls_tot_kini").text =unicode(row4.ls_amount_kini + row4.ls_ppn_kini + row4.ls_pph21_kini + row4.ls_pph22_kini + row4.ls_pph23_kini + row4.ls_lain_kini)
                ET.SubElement(xml_a, "lain_tot_lalu").text =unicode(row4.lain_amount_lalu + row4.lain_ppn_lalu + row4.lain_pph21_lalu + row4.lain_pph22_lalu + row4.lain_pph23_lalu + row4.lain_lain_lalu)
                ET.SubElement(xml_a, "lain_tot_kini").text =unicode(row4.lain_amount_kini + row4.lain_ppn_kini + row4.lain_pph21_kini + row4.lain_pph22_kini + row4.lain_pph23_kini + row4.lain_lain_kini)
                
                ET.SubElement(xml_a, "lsg_amount_lalu1").text =unicode(row4.lsg_amount_lalu1)
                ET.SubElement(xml_a, "lsg_amount_kini1").text =unicode(row4.lsg_amount_kini1)
                ET.SubElement(xml_a, "ls_amount_lalu1").text =unicode(row4.ls_amount_lalu1)
                ET.SubElement(xml_a, "ls_amount_kini1").text =unicode(row4.ls_amount_kini1)
                ET.SubElement(xml_a, "lain_amount_lalu1").text =unicode(row4.lain_amount_lalu1)
                ET.SubElement(xml_a, "lain_amount_kini1").text =unicode(row4.lain_amount_kini1)
                ET.SubElement(xml_a, "lsg_ppn_lalu1").text =unicode(row4.lsg_ppn_lalu1)
                ET.SubElement(xml_a, "lsg_ppn_kini1").text =unicode(row4.lsg_ppn_kini1)
                ET.SubElement(xml_a, "ls_ppn_lalu1").text =unicode(row4.ls_ppn_lalu1)
                ET.SubElement(xml_a, "ls_ppn_kini1").text =unicode(row4.ls_ppn_kini1)
                ET.SubElement(xml_a, "lain_ppn_lalu1").text =unicode(row4.lain_ppn_lalu1)
                ET.SubElement(xml_a, "lain_ppn_kini1").text =unicode(row4.lain_ppn_kini1)
                ET.SubElement(xml_a, "lsg_pph21_lalu1").text =unicode(row4.lsg_pph21_lalu1)
                ET.SubElement(xml_a, "lsg_pph21_kini1").text =unicode(row4.lsg_pph21_kini1)
                ET.SubElement(xml_a, "ls_pph21_lalu1").text =unicode(row4.ls_pph21_lalu1)
                ET.SubElement(xml_a, "ls_pph21_kini1").text =unicode(row4.ls_pph21_kini1)
                ET.SubElement(xml_a, "lain_pph21_lalu1").text =unicode(row4.lain_pph21_lalu1)
                ET.SubElement(xml_a, "lain_pph21_kini1").text =unicode(row4.lain_pph21_kini1)
                ET.SubElement(xml_a, "lsg_pph22_lalu1").text =unicode(row4.lsg_pph22_lalu1)
                ET.SubElement(xml_a, "lsg_pph22_kini1").text =unicode(row4.lsg_pph22_kini1)
                ET.SubElement(xml_a, "ls_pph22_lalu1").text =unicode(row4.ls_pph22_lalu1)
                ET.SubElement(xml_a, "ls_pph22_kini1").text =unicode(row4.ls_pph22_kini1)
                ET.SubElement(xml_a, "lain_pph22_lalu1").text =unicode(row4.lain_pph22_lalu1)
                ET.SubElement(xml_a, "lain_pph22_kini1").text =unicode(row4.lain_pph22_kini1)
                ET.SubElement(xml_a, "lsg_pph23_lalu1").text =unicode(row4.lsg_pph23_lalu1)
                ET.SubElement(xml_a, "lsg_pph23_kini1").text =unicode(row4.lsg_pph23_kini1)
                ET.SubElement(xml_a, "ls_pph23_lalu1").text =unicode(row4.ls_pph23_lalu1)
                ET.SubElement(xml_a, "ls_pph23_kini1").text =unicode(row4.ls_pph23_kini1)
                ET.SubElement(xml_a, "lain_pph23_lalu1").text =unicode(row4.lain_pph23_lalu1)
                ET.SubElement(xml_a, "lain_pph23_kini1").text =unicode(row4.lain_pph23_kini1)
                ET.SubElement(xml_a, "lsg_lain_lalu1").text =unicode(row4.lsg_lain_lalu1)
                ET.SubElement(xml_a, "lsg_lain_kini1").text =unicode(row4.lsg_lain_kini1)
                ET.SubElement(xml_a, "ls_lain_lalu1").text =unicode(row4.ls_lain_lalu1)
                ET.SubElement(xml_a, "ls_lain_kini1").text =unicode(row4.ls_lain_kini1)
                ET.SubElement(xml_a, "lain_lain_lalu1").text =unicode(row4.lain_lain_lalu1)
                ET.SubElement(xml_a, "lain_lain_kini1").text =unicode(row4.lain_lain_kini1)

                ET.SubElement(xml_a, "lsg_tot_lalu1").text =unicode(row4.lsg_amount_lalu1 + row4.lsg_ppn_lalu1 + row4.lsg_pph21_lalu1 + row4.lsg_pph22_lalu1 + row4.lsg_pph23_lalu1 + row4.lsg_lain_lalu1)
                ET.SubElement(xml_a, "lsg_tot_kini1").text =unicode(row4.lsg_amount_kini1 + row4.lsg_ppn_kini1 + row4.lsg_pph21_kini1 + row4.lsg_pph22_kini1 + row4.lsg_pph23_kini1 + row4.lsg_lain_kini1)
                ET.SubElement(xml_a, "ls_tot_lalu1").text =unicode(row4.ls_amount_lalu1 + row4.ls_ppn_lalu1 + row4.ls_pph21_lalu1 + row4.ls_pph22_lalu1 + row4.ls_pph23_lalu1 + row4.ls_lain_lalu1)
                ET.SubElement(xml_a, "ls_tot_kini1").text =unicode(row4.ls_amount_kini1 + row4.ls_ppn_kini1 + row4.ls_pph21_kini1 + row4.ls_pph22_kini1 + row4.ls_pph23_kini1 + row4.ls_lain_kini1)
                ET.SubElement(xml_a, "lain_tot_lalu1").text =unicode(row4.lain_amount_lalu1 + row4.lain_ppn_lalu1 + row4.lain_pph21_lalu1 + row4.lain_pph22_lalu1 + row4.lain_pph23_lalu1 + row4.lain_lain_lalu1)
                ET.SubElement(xml_a, "lain_tot_kini1").text =unicode(row4.lain_amount_kini1 + row4.lain_ppn_kini1 + row4.lain_pph21_kini1 + row4.lain_pph22_kini1 + row4.lain_pph23_kini1 + row4.lain_lain_kini1)
                
        return self.root 

class b104r400Generator(JasperGeneratorWithSubreport):
    def __init__(self):
        self.mainreport = get_rpath('apbd/tuskpd/R104400.jrxml')
        self.subreportlist = []
        self.subreportlist.append(get_rpath('apbd/tuskpd/R104400_subreport1.jrxml'))
        self.xpath = '/apbd/spj'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'spj')
            ET.SubElement(xml_greeting, "unit_id").text = unicode(row.unit_id)
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "keg_kd").text = row.keg_kd
            ET.SubElement(xml_greeting, "keg_nm").text = row.keg_nm
            ET.SubElement(xml_greeting, "keg_sub_id").text = unicode(row.keg_sub_id)
            ET.SubElement(xml_greeting, "rek_id").text = unicode(row.rek_id)
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "dpa").text = unicode(row.dpa)
            ET.SubElement(xml_greeting, "dppa").text = unicode(row.dppa)
            ET.SubElement(xml_greeting, "LSG_lalu").text = unicode(row.LSG_lalu)
            ET.SubElement(xml_greeting, "LSG_kini").text = unicode(row.LSG_kini)
            ET.SubElement(xml_greeting, "LS_lalu").text = unicode(row.LS_lalu)
            ET.SubElement(xml_greeting, "LS_kini").text = unicode(row.LS_kini)
            ET.SubElement(xml_greeting, "Lain_lalu").text = unicode(row.Lain_lalu)
            ET.SubElement(xml_greeting, "Lain_kini").text = unicode(row.Lain_kini)
            ET.SubElement(xml_greeting, "bulan").text = unicode(bulan)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
            ET.SubElement(xml_greeting, "japbd").text = unicode(japbd)
            
            """rows = DBSession.query(Pegawai.nama.label('pa_nama'), Pegawai.kode.label('pa_nip')
               ).filter(Pejabat.pegawai_id==Pegawai.id, Pejabat.jabatan_id==Jabatan.id, 
               Pejabat.unit_id==row.unit_id, Jabatan.kode=='200')
            for row2 in rows :
               ET.SubElement(xml_greeting, "pa_nama").text = row2.pa_nama
               ET.SubElement(xml_greeting, "pa_nip").text = row2.pa_nip
            """
            ET.SubElement(xml_greeting, "pa_nama").text = pa_nama
            ET.SubElement(xml_greeting, "pa_nip").text = pa_nip
            
            """rows2 = DBSession.query(Pegawai.nama.label('bend_nama'), Pegawai.kode.label('bend_nip')
               ).filter(Pejabat.pegawai_id==Pegawai.id, Pejabat.jabatan_id==Jabatan.id, 
               Pejabat.unit_id==row.unit_id, Jabatan.kode=='236')
            for row3 in rows2 :
               ET.SubElement(xml_greeting, "bend_nama").text = row3.bend_nama
               ET.SubElement(xml_greeting, "bend_nip").text = row3.bend_nip
            """
            ET.SubElement(xml_greeting, "bend_nama").text = benda_nama
            ET.SubElement(xml_greeting, "bend_nip").text = benda_nip
            
            subq = DBSession.query(APInvoice.id, Sp2d.id.label('sp2d_id'), 
                func.coalesce(func.sum(case([(and_(extract('month',APInvoice.tanggal)<bulan, Rekening.kode=='7.1.1.02.01'),SpmPotongan.nilai)], else_=0)),0).label('ppn_lalu'),
                func.coalesce(func.sum(case([(and_(extract('month',APInvoice.tanggal)==bulan, Rekening.kode=='7.1.1.02.01'),SpmPotongan.nilai)], else_=0)),0).label('ppn_kini'),
                func.coalesce(func.sum(case([(and_(extract('month',APInvoice.tanggal)<bulan, Rekening.kode=='7.1.1.02.02'),SpmPotongan.nilai)], else_=0)),0).label('pph21_lalu'),
                func.coalesce(func.sum(case([(and_(extract('month',APInvoice.tanggal)==bulan, Rekening.kode=='7.1.1.02.02'),SpmPotongan.nilai)], else_=0)),0).label('pph21_kini'),
                func.coalesce(func.sum(case([(and_(extract('month',APInvoice.tanggal)<bulan, Rekening.kode=='7.1.1.02.03'),SpmPotongan.nilai)], else_=0)),0).label('pph22_lalu'),
                func.coalesce(func.sum(case([(and_(extract('month',APInvoice.tanggal)==bulan, Rekening.kode=='7.1.1.02.03'),SpmPotongan.nilai)], else_=0)),0).label('pph22_kini'),
                func.coalesce(func.sum(case([(and_(extract('month',APInvoice.tanggal)<bulan, Rekening.kode=='7.1.1.02.04'),SpmPotongan.nilai)], else_=0)),0).label('pph23_lalu'),
                func.coalesce(func.sum(case([(and_(extract('month',APInvoice.tanggal)==bulan, Rekening.kode=='7.1.1.02.04'),SpmPotongan.nilai)], else_=0)),0).label('pph23_kini'),
                func.coalesce(func.sum(case([(and_(extract('month',APInvoice.tanggal)<bulan, func.substr(Rekening.kode,1,3)=='7.1', 
                not_(Rekening.kode.in_(['7.1.1.02.01','7.1.1.02.02','7.1.1.02.03','7.1.1.02.04']))),SpmPotongan.nilai)], else_=0)),0).label('lain_lalu'),
                func.coalesce(func.sum(case([(and_(extract('month',APInvoice.tanggal)==bulan, func.substr(Rekening.kode,1,3)=='7.1', 
                not_(Rekening.kode.in_(['7.1.1.02.01','7.1.1.02.02','7.1.1.02.03','7.1.1.02.04']))),SpmPotongan.nilai)], else_=0)),0).label('lain_kini'),
               ).join(SppItem, Spp, Spm, SpmPotongan, Rekening
               ).outerjoin(Sp2d, Sp2d.ap_spm_id==Spm.id
               ).filter(
                #SpmPotongan.rekening_id==Rekening.id, SpmPotongan.ap_spm_id==Spm.id, Spm.ap_spp_id==Spp.id,
                #SppItem.ap_spp_id==Spp.id, SppItem.ap_invoice_id==APInvoice.id,
                APInvoice.unit_id==row.unit_id, APInvoice.tahun_id==row.tahun
               ).group_by(APInvoice.id, Sp2d.id
               ).subquery()

            subq2 = DBSession.query(APInvoice.tahun_id, APInvoice.id, APInvoice.tanggal, Unit.id.label('unit_id'), 
               case([(and_(APInvoice.jenis==4, func.substr(Rekening.kode,1,5)=='5.1.1', func.substr(Rekening.kode,1,8)!='5.1.1.02'),'LSG'), 
               (and_(APInvoice.jenis==4, or_(func.substr(Rekening.kode,1,5)!='5.1.1',func.substr(Rekening.kode,1,8)=='5.1.1.02')),'LS')], else_='LAIN').label('jenis'),
               func.coalesce(func.sum(APInvoiceItem.amount),0).label('amount'), 
               case([(subq.c.sp2d_id>0,subq.c.sp2d_id)], else_=0).label('sp2d_id'), subq.c.ppn_lalu, subq.c.ppn_kini, subq.c.pph21_lalu, subq.c.pph21_kini, subq.c.pph22_lalu, subq.c.pph22_kini, 
               subq.c.pph23_lalu, subq.c.pph23_kini, subq.c.lain_lalu, subq.c.lain_kini
               ).join(Unit,APInvoiceItem, KegiatanItem, Rekening
               ).outerjoin(subq, APInvoice.id==subq.c.id
               ).filter(Unit.id==row.unit_id, APInvoice.tahun_id==row.tahun
               ).group_by(APInvoice.tahun_id, APInvoice.id, APInvoice.tanggal, Unit.id, 
               case([(and_(APInvoice.jenis==4, func.substr(Rekening.kode,1,5)=='5.1.1', func.substr(Rekening.kode,1,8)!='5.1.1.02'),'LSG'), 
               (and_(APInvoice.jenis==4, or_(func.substr(Rekening.kode,1,5)!='5.1.1',func.substr(Rekening.kode,1,8)=='5.1.1.02')),'LS')], else_='LAIN'),
               case([(subq.c.sp2d_id>0,subq.c.sp2d_id)], else_=0), subq.c.ppn_lalu, subq.c.ppn_kini, subq.c.pph21_lalu, subq.c.pph21_kini, subq.c.pph22_lalu, subq.c.pph22_kini, 
               subq.c.pph23_lalu, subq.c.pph23_kini, subq.c.lain_lalu, subq.c.lain_kini
               ).subquery()
               
            rowitem = DBSession.query(subq2.c.tahun_id, subq2.c.unit_id, 
               #Amount
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LSG', subq2.c.sp2d_id<>0),subq2.c.amount)], else_=0)),0).label('lsg_amount_lalu'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LSG'),subq2.c.amount)], else_=0)),0).label('lsg_amount_lalu1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LSG', subq2.c.sp2d_id<>0),subq2.c.amount)], else_=0)),0).label('lsg_amount_kini'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LSG'),subq2.c.amount)], else_=0)),0).label('lsg_amount_kini1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LS', subq2.c.sp2d_id<>0),subq2.c.amount)], else_=0)),0).label('ls_amount_lalu'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LS'),subq2.c.amount)], else_=0)),0).label('ls_amount_lalu1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LS', subq2.c.sp2d_id<>0),subq2.c.amount)], else_=0)),0).label('ls_amount_kini'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LS'),subq2.c.amount)], else_=0)),0).label('ls_amount_kini1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LAIN', subq2.c.sp2d_id<>0),subq2.c.amount)], else_=0)),0).label('lain_amount_lalu'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LAIN'),subq2.c.amount)], else_=0)),0).label('lain_amount_lalu1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LAIN', subq2.c.sp2d_id<>0),subq2.c.amount)], else_=0)),0).label('lain_amount_kini'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LAIN'),subq2.c.amount)], else_=0)),0).label('lain_amount_kini1'),
               #PPn
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LSG', subq2.c.sp2d_id<>0),subq2.c.ppn_lalu)], else_=0)),0).label('lsg_ppn_lalu'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LSG', subq2.c.sp2d_id<>0),subq2.c.ppn_kini)], else_=0)),0).label('lsg_ppn_kini'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LS', subq2.c.sp2d_id<>0),subq2.c.ppn_lalu)], else_=0)),0).label('ls_ppn_lalu'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LS', subq2.c.sp2d_id<>0),subq2.c.ppn_kini)], else_=0)),0).label('ls_ppn_kini'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LAIN', subq2.c.sp2d_id<>0),subq2.c.ppn_lalu)], else_=0)),0).label('lain_ppn_lalu'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LAIN', subq2.c.sp2d_id<>0),subq2.c.ppn_kini)], else_=0)),0).label('lain_ppn_kini'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LSG'),subq2.c.ppn_lalu)], else_=0)),0).label('lsg_ppn_lalu1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LSG'),subq2.c.ppn_kini)], else_=0)),0).label('lsg_ppn_kini1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LS'),subq2.c.ppn_lalu)], else_=0)),0).label('ls_ppn_lalu1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LS'),subq2.c.ppn_kini)], else_=0)),0).label('ls_ppn_kini1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LAIN'),subq2.c.ppn_lalu)], else_=0)),0).label('lain_ppn_lalu1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LAIN'),subq2.c.ppn_kini)], else_=0)),0).label('lain_ppn_kini1'),
               #PPh21
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LSG', subq2.c.sp2d_id<>0),subq2.c.pph21_lalu)], else_=0)),0).label('lsg_pph21_lalu'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LSG', subq2.c.sp2d_id<>0),subq2.c.pph21_kini)], else_=0)),0).label('lsg_pph21_kini'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LS', subq2.c.sp2d_id<>0),subq2.c.pph21_lalu)], else_=0)),0).label('ls_pph21_lalu'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LS', subq2.c.sp2d_id<>0),subq2.c.pph21_kini)], else_=0)),0).label('ls_pph21_kini'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LAIN', subq2.c.sp2d_id<>0),subq2.c.pph21_lalu)], else_=0)),0).label('lain_pph21_lalu'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LAIN', subq2.c.sp2d_id<>0),subq2.c.pph21_kini)], else_=0)),0).label('lain_pph21_kini'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LSG'),subq2.c.pph21_lalu)], else_=0)),0).label('lsg_pph21_lalu1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LSG'),subq2.c.pph21_kini)], else_=0)),0).label('lsg_pph21_kini1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LS'),subq2.c.pph21_lalu)], else_=0)),0).label('ls_pph21_lalu1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LS'),subq2.c.pph21_kini)], else_=0)),0).label('ls_pph21_kini1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LAIN'),subq2.c.pph21_lalu)], else_=0)),0).label('lain_pph21_lalu1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LAIN'),subq2.c.pph21_kini)], else_=0)),0).label('lain_pph21_kini1'),
               #PPh22
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LSG', subq2.c.sp2d_id<>0),subq2.c.pph22_lalu)], else_=0)),0).label('lsg_pph22_lalu'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LSG', subq2.c.sp2d_id<>0),subq2.c.pph22_kini)], else_=0)),0).label('lsg_pph22_kini'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LS', subq2.c.sp2d_id<>0),subq2.c.pph22_lalu)], else_=0)),0).label('ls_pph22_lalu'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LS', subq2.c.sp2d_id<>0),subq2.c.pph22_kini)], else_=0)),0).label('ls_pph22_kini'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LAIN', subq2.c.sp2d_id<>0),subq2.c.pph22_lalu)], else_=0)),0).label('lain_pph22_lalu'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LAIN', subq2.c.sp2d_id<>0),subq2.c.pph22_kini)], else_=0)),0).label('lain_pph22_kini'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LSG'),subq2.c.pph22_lalu)], else_=0)),0).label('lsg_pph22_lalu1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LSG'),subq2.c.pph22_kini)], else_=0)),0).label('lsg_pph22_kini1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LS'),subq2.c.pph22_lalu)], else_=0)),0).label('ls_pph22_lalu1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LS'),subq2.c.pph22_kini)], else_=0)),0).label('ls_pph22_kini1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LAIN'),subq2.c.pph22_lalu)], else_=0)),0).label('lain_pph22_lalu1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LAIN'),subq2.c.pph22_kini)], else_=0)),0).label('lain_pph22_kini1'),
               #PPh23
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LSG', subq2.c.sp2d_id<>0),subq2.c.pph23_lalu)], else_=0)),0).label('lsg_pph23_lalu'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LSG', subq2.c.sp2d_id<>0),subq2.c.pph23_kini)], else_=0)),0).label('lsg_pph23_kini'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LS', subq2.c.sp2d_id<>0),subq2.c.pph23_lalu)], else_=0)),0).label('ls_pph23_lalu'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LS', subq2.c.sp2d_id<>0),subq2.c.pph23_kini)], else_=0)),0).label('ls_pph23_kini'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LAIN', subq2.c.sp2d_id<>0),subq2.c.pph23_lalu)], else_=0)),0).label('lain_pph23_lalu'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LAIN', subq2.c.sp2d_id<>0),subq2.c.pph23_kini)], else_=0)),0).label('lain_pph23_kini'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LSG'),subq2.c.pph23_lalu)], else_=0)),0).label('lsg_pph23_lalu1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LSG'),subq2.c.pph23_kini)], else_=0)),0).label('lsg_pph23_kini1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LS'),subq2.c.pph23_lalu)], else_=0)),0).label('ls_pph23_lalu1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LS'),subq2.c.pph23_kini)], else_=0)),0).label('ls_pph23_kini1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LAIN'),subq2.c.pph23_lalu)], else_=0)),0).label('lain_pph23_lalu1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LAIN'),subq2.c.pph23_kini)], else_=0)),0).label('lain_pph23_kini1'),
               #Lainnya
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LSG', subq2.c.sp2d_id<>0),subq2.c.lain_lalu)], else_=0)),0).label('lsg_lain_lalu'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LSG', subq2.c.sp2d_id<>0),subq2.c.lain_kini)], else_=0)),0).label('lsg_lain_kini'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LS', subq2.c.sp2d_id<>0),subq2.c.lain_lalu)], else_=0)),0).label('ls_lain_lalu'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LS', subq2.c.sp2d_id<>0),subq2.c.lain_kini)], else_=0)),0).label('ls_lain_kini'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LAIN', subq2.c.sp2d_id<>0),subq2.c.lain_lalu)], else_=0)),0).label('lain_lain_lalu'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LAIN', subq2.c.sp2d_id<>0),subq2.c.lain_kini)], else_=0)),0).label('lain_lain_kini'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LSG'),subq2.c.lain_lalu)], else_=0)),0).label('lsg_lain_lalu1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LSG'),subq2.c.lain_kini)], else_=0)),0).label('lsg_lain_kini1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LS'),subq2.c.lain_lalu)], else_=0)),0).label('ls_lain_lalu1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LS'),subq2.c.lain_kini)], else_=0)),0).label('ls_lain_kini1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)<bulan, subq2.c.jenis=='LAIN'),subq2.c.lain_lalu)], else_=0)),0).label('lain_lain_lalu1'),
               func.coalesce(func.sum(case([(and_(extract('month',subq2.c.tanggal)==bulan, subq2.c.jenis=='LAIN'),subq2.c.lain_kini)], else_=0)),0).label('lain_lain_kini1'),
               #).filter(subq2.c.tahun_id==row.unit_id, subq2.c.unit_id==row.tahun
               ).group_by(subq2.c.tahun_id, subq2.c.unit_id
               )
               
            for row4 in rowitem :
                xml_a = ET.SubElement(xml_greeting, "item")
                ET.SubElement(xml_a, "unit_id").text =unicode(row4.unit_id)
                ET.SubElement(xml_a, "tahun_id").text =unicode(row4.tahun_id)
                ET.SubElement(xml_a, "lsg_amount_lalu").text =unicode(row4.lsg_amount_lalu)
                ET.SubElement(xml_a, "lsg_amount_kini").text =unicode(row4.lsg_amount_kini)
                ET.SubElement(xml_a, "ls_amount_lalu").text =unicode(row4.ls_amount_lalu)
                ET.SubElement(xml_a, "ls_amount_kini").text =unicode(row4.ls_amount_kini)
                ET.SubElement(xml_a, "lain_amount_lalu").text =unicode(row4.lain_amount_lalu)
                ET.SubElement(xml_a, "lain_amount_kini").text =unicode(row4.lain_amount_kini)
                ET.SubElement(xml_a, "lsg_ppn_lalu").text =unicode(row4.lsg_ppn_lalu)
                ET.SubElement(xml_a, "lsg_ppn_kini").text =unicode(row4.lsg_ppn_kini)
                ET.SubElement(xml_a, "ls_ppn_lalu").text =unicode(row4.ls_ppn_lalu)
                ET.SubElement(xml_a, "ls_ppn_kini").text =unicode(row4.ls_ppn_kini)
                ET.SubElement(xml_a, "lain_ppn_lalu").text =unicode(row4.lain_ppn_lalu)
                ET.SubElement(xml_a, "lain_ppn_kini").text =unicode(row4.lain_ppn_kini)
                ET.SubElement(xml_a, "lsg_pph21_lalu").text =unicode(row4.lsg_pph21_lalu)
                ET.SubElement(xml_a, "lsg_pph21_kini").text =unicode(row4.lsg_pph21_kini)
                ET.SubElement(xml_a, "ls_pph21_lalu").text =unicode(row4.ls_pph21_lalu)
                ET.SubElement(xml_a, "ls_pph21_kini").text =unicode(row4.ls_pph21_kini)
                ET.SubElement(xml_a, "lain_pph21_lalu").text =unicode(row4.lain_pph21_lalu)
                ET.SubElement(xml_a, "lain_pph21_kini").text =unicode(row4.lain_pph21_kini)
                ET.SubElement(xml_a, "lsg_pph22_lalu").text =unicode(row4.lsg_pph22_lalu)
                ET.SubElement(xml_a, "lsg_pph22_kini").text =unicode(row4.lsg_pph22_kini)
                ET.SubElement(xml_a, "ls_pph22_lalu").text =unicode(row4.ls_pph22_lalu)
                ET.SubElement(xml_a, "ls_pph22_kini").text =unicode(row4.ls_pph22_kini)
                ET.SubElement(xml_a, "lain_pph22_lalu").text =unicode(row4.lain_pph22_lalu)
                ET.SubElement(xml_a, "lain_pph22_kini").text =unicode(row4.lain_pph22_kini)
                ET.SubElement(xml_a, "lsg_pph23_lalu").text =unicode(row4.lsg_pph23_lalu)
                ET.SubElement(xml_a, "lsg_pph23_kini").text =unicode(row4.lsg_pph23_kini)
                ET.SubElement(xml_a, "ls_pph23_lalu").text =unicode(row4.ls_pph23_lalu)
                ET.SubElement(xml_a, "ls_pph23_kini").text =unicode(row4.ls_pph23_kini)
                ET.SubElement(xml_a, "lain_pph23_lalu").text =unicode(row4.lain_pph23_lalu)
                ET.SubElement(xml_a, "lain_pph23_kini").text =unicode(row4.lain_pph23_kini)
                ET.SubElement(xml_a, "lsg_lain_lalu").text =unicode(row4.lsg_lain_lalu)
                ET.SubElement(xml_a, "lsg_lain_kini").text =unicode(row4.lsg_lain_kini)
                ET.SubElement(xml_a, "ls_lain_lalu").text =unicode(row4.ls_lain_lalu)
                ET.SubElement(xml_a, "ls_lain_kini").text =unicode(row4.ls_lain_kini)
                ET.SubElement(xml_a, "lain_lain_lalu").text =unicode(row4.lain_lain_lalu)
                ET.SubElement(xml_a, "lain_lain_kini").text =unicode(row4.lain_lain_kini)

                ET.SubElement(xml_a, "lsg_tot_lalu").text =unicode(row4.lsg_amount_lalu + row4.lsg_ppn_lalu + row4.lsg_pph21_lalu + row4.lsg_pph22_lalu + row4.lsg_pph23_lalu + row4.lsg_lain_lalu)
                ET.SubElement(xml_a, "lsg_tot_kini").text =unicode(row4.lsg_amount_kini + row4.lsg_ppn_kini + row4.lsg_pph21_kini + row4.lsg_pph22_kini + row4.lsg_pph23_kini + row4.lsg_lain_kini)
                ET.SubElement(xml_a, "ls_tot_lalu").text =unicode(row4.ls_amount_lalu + row4.ls_ppn_lalu + row4.ls_pph21_lalu + row4.ls_pph22_lalu + row4.ls_pph23_lalu + row4.ls_lain_lalu)
                ET.SubElement(xml_a, "ls_tot_kini").text =unicode(row4.ls_amount_kini + row4.ls_ppn_kini + row4.ls_pph21_kini + row4.ls_pph22_kini + row4.ls_pph23_kini + row4.ls_lain_kini)
                ET.SubElement(xml_a, "lain_tot_lalu").text =unicode(row4.lain_amount_lalu + row4.lain_ppn_lalu + row4.lain_pph21_lalu + row4.lain_pph22_lalu + row4.lain_pph23_lalu + row4.lain_lain_lalu)
                ET.SubElement(xml_a, "lain_tot_kini").text =unicode(row4.lain_amount_kini + row4.lain_ppn_kini + row4.lain_pph21_kini + row4.lain_pph22_kini + row4.lain_pph23_kini + row4.lain_lain_kini)
                
                ET.SubElement(xml_a, "lsg_amount_lalu1").text =unicode(row4.lsg_amount_lalu1)
                ET.SubElement(xml_a, "lsg_amount_kini1").text =unicode(row4.lsg_amount_kini1)
                ET.SubElement(xml_a, "ls_amount_lalu1").text =unicode(row4.ls_amount_lalu1)
                ET.SubElement(xml_a, "ls_amount_kini1").text =unicode(row4.ls_amount_kini1)
                ET.SubElement(xml_a, "lain_amount_lalu1").text =unicode(row4.lain_amount_lalu1)
                ET.SubElement(xml_a, "lain_amount_kini1").text =unicode(row4.lain_amount_kini1)
                ET.SubElement(xml_a, "lsg_ppn_lalu1").text =unicode(row4.lsg_ppn_lalu1)
                ET.SubElement(xml_a, "lsg_ppn_kini1").text =unicode(row4.lsg_ppn_kini1)
                ET.SubElement(xml_a, "ls_ppn_lalu1").text =unicode(row4.ls_ppn_lalu1)
                ET.SubElement(xml_a, "ls_ppn_kini1").text =unicode(row4.ls_ppn_kini1)
                ET.SubElement(xml_a, "lain_ppn_lalu1").text =unicode(row4.lain_ppn_lalu1)
                ET.SubElement(xml_a, "lain_ppn_kini1").text =unicode(row4.lain_ppn_kini1)
                ET.SubElement(xml_a, "lsg_pph21_lalu1").text =unicode(row4.lsg_pph21_lalu1)
                ET.SubElement(xml_a, "lsg_pph21_kini1").text =unicode(row4.lsg_pph21_kini1)
                ET.SubElement(xml_a, "ls_pph21_lalu1").text =unicode(row4.ls_pph21_lalu1)
                ET.SubElement(xml_a, "ls_pph21_kini1").text =unicode(row4.ls_pph21_kini1)
                ET.SubElement(xml_a, "lain_pph21_lalu1").text =unicode(row4.lain_pph21_lalu1)
                ET.SubElement(xml_a, "lain_pph21_kini1").text =unicode(row4.lain_pph21_kini1)
                ET.SubElement(xml_a, "lsg_pph22_lalu1").text =unicode(row4.lsg_pph22_lalu1)
                ET.SubElement(xml_a, "lsg_pph22_kini1").text =unicode(row4.lsg_pph22_kini1)
                ET.SubElement(xml_a, "ls_pph22_lalu1").text =unicode(row4.ls_pph22_lalu1)
                ET.SubElement(xml_a, "ls_pph22_kini1").text =unicode(row4.ls_pph22_kini1)
                ET.SubElement(xml_a, "lain_pph22_lalu1").text =unicode(row4.lain_pph22_lalu1)
                ET.SubElement(xml_a, "lain_pph22_kini1").text =unicode(row4.lain_pph22_kini1)
                ET.SubElement(xml_a, "lsg_pph23_lalu1").text =unicode(row4.lsg_pph23_lalu1)
                ET.SubElement(xml_a, "lsg_pph23_kini1").text =unicode(row4.lsg_pph23_kini1)
                ET.SubElement(xml_a, "ls_pph23_lalu1").text =unicode(row4.ls_pph23_lalu1)
                ET.SubElement(xml_a, "ls_pph23_kini1").text =unicode(row4.ls_pph23_kini1)
                ET.SubElement(xml_a, "lain_pph23_lalu1").text =unicode(row4.lain_pph23_lalu1)
                ET.SubElement(xml_a, "lain_pph23_kini1").text =unicode(row4.lain_pph23_kini1)
                ET.SubElement(xml_a, "lsg_lain_lalu1").text =unicode(row4.lsg_lain_lalu1)
                ET.SubElement(xml_a, "lsg_lain_kini1").text =unicode(row4.lsg_lain_kini1)
                ET.SubElement(xml_a, "ls_lain_lalu1").text =unicode(row4.ls_lain_lalu1)
                ET.SubElement(xml_a, "ls_lain_kini1").text =unicode(row4.ls_lain_kini1)
                ET.SubElement(xml_a, "lain_lain_lalu1").text =unicode(row4.lain_lain_lalu1)
                ET.SubElement(xml_a, "lain_lain_kini1").text =unicode(row4.lain_lain_kini1)

                ET.SubElement(xml_a, "lsg_tot_lalu1").text =unicode(row4.lsg_amount_lalu1 + row4.lsg_ppn_lalu1 + row4.lsg_pph21_lalu1 + row4.lsg_pph22_lalu1 + row4.lsg_pph23_lalu1 + row4.lsg_lain_lalu1)
                ET.SubElement(xml_a, "lsg_tot_kini1").text =unicode(row4.lsg_amount_kini1 + row4.lsg_ppn_kini1 + row4.lsg_pph21_kini1 + row4.lsg_pph22_kini1 + row4.lsg_pph23_kini1 + row4.lsg_lain_kini1)
                ET.SubElement(xml_a, "ls_tot_lalu1").text =unicode(row4.ls_amount_lalu1 + row4.ls_ppn_lalu1 + row4.ls_pph21_lalu1 + row4.ls_pph22_lalu1 + row4.ls_pph23_lalu1 + row4.ls_lain_lalu1)
                ET.SubElement(xml_a, "ls_tot_kini1").text =unicode(row4.ls_amount_kini1 + row4.ls_ppn_kini1 + row4.ls_pph21_kini1 + row4.ls_pph22_kini1 + row4.ls_pph23_kini1 + row4.ls_lain_kini1)
                ET.SubElement(xml_a, "lain_tot_lalu1").text =unicode(row4.lain_amount_lalu1 + row4.lain_ppn_lalu1 + row4.lain_pph21_lalu1 + row4.lain_pph22_lalu1 + row4.lain_pph23_lalu1 + row4.lain_lain_lalu1)
                ET.SubElement(xml_a, "lain_tot_kini1").text =unicode(row4.lain_amount_kini1 + row4.lain_ppn_kini1 + row4.lain_pph21_kini1 + row4.lain_pph22_kini1 + row4.lain_pph23_kini1 + row4.lain_lain_kini1)
                
        return self.root 
"""
class b105r011Generator(JasperGenerator):
    def __init__(self):
        super(b105r011Generator, self).__init__()
        self.reportname = get_rpath('apbd/tuskpd/R105101.jrxml')
        self.xpath = '/apbd/akuntansi'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'akuntansi')
            ET.SubElement(xml_greeting, "jurnal_kd").text = row.jurnal_kd
            ET.SubElement(xml_greeting, "jurnal_nm").text = row.jurnal_nm
            ET.SubElement(xml_greeting, "tanggal").text = unicode(row.tanggal)
            ET.SubElement(xml_greeting, "tgl_transaksi").text = unicode(row.tgl_transaksi)
            ET.SubElement(xml_greeting, "tahun_id").text = unicode(row.tahun_id)
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "periode").text = unicode(row.periode)
            ET.SubElement(xml_greeting, "jv_type").text = unicode(row.jv_type)
            ET.SubElement(xml_greeting, "source").text = row.source
            ET.SubElement(xml_greeting, "source_no").text = row.source_no
            ET.SubElement(xml_greeting, "amount").text = unicode(row.amount)
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "mulai").text = mulai
            ET.SubElement(xml_greeting, "selesai").text = selesai
            ET.SubElement(xml_greeting, "customer").text = customer
        return self.root

class b105r012Generator(JasperGenerator):
    def __init__(self):
        super(b105r012Generator, self).__init__()
        self.reportname = get_rpath('apbd/tuskpd/R105102.jrxml')
        self.xpath = '/apbd/akuntansi'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'akuntansi')
            ET.SubElement(xml_greeting, "jurnal_kd").text = row.jurnal_kd
            ET.SubElement(xml_greeting, "jurnal_nm").text = row.jurnal_nm
            ET.SubElement(xml_greeting, "tanggal").text = unicode(row.tanggal)
            ET.SubElement(xml_greeting, "tgl_transaksi").text = unicode(row.tgl_transaksi)
            ET.SubElement(xml_greeting, "tahun_id").text = unicode(row.tahun_id)
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "periode").text = unicode(row.periode)
            ET.SubElement(xml_greeting, "jv_type").text = unicode(row.jv_type)
            ET.SubElement(xml_greeting, "source").text = row.source
            ET.SubElement(xml_greeting, "source_no").text = row.source_no
            ET.SubElement(xml_greeting, "amount").text = unicode(row.amount)
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "mulai").text = mulai
            ET.SubElement(xml_greeting, "selesai").text = selesai
            ET.SubElement(xml_greeting, "customer").text = customer
        return self.root

class b105r021Generator(JasperGenerator):
    def __init__(self):
        super(b105r021Generator, self).__init__()
        self.reportname = get_rpath('apbd/tuskpd/R105201.jrxml')
        self.xpath = '/apbd/akuntansi'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'akuntansi')
            ET.SubElement(xml_greeting, "kode").text = row.kode
            ET.SubElement(xml_greeting, "nama").text = row.nama
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "level_id").text = unicode(row.level_id)
            ET.SubElement(xml_greeting, "tahun_kini").text = unicode(row.tahun_kini)
            ET.SubElement(xml_greeting, "tahun_lalu").text = unicode(row.tahun_lalu)
            ET.SubElement(xml_greeting, "amount_kini").text = unicode(row.amount_kini)
            ET.SubElement(xml_greeting, "amount_lalu").text = unicode(row.amount_lalu)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root

class b105r022Generator(JasperGenerator):
    def __init__(self):
        super(b105r022Generator, self).__init__()
        self.reportname = get_rpath('apbd/tuskpd/R105202.jrxml')
        self.xpath = '/apbd/akuntansi'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'akuntansi')
            ET.SubElement(xml_greeting, "kode").text = row.kode
            ET.SubElement(xml_greeting, "nama").text = row.nama
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "level_id").text = unicode(row.level_id)
            ET.SubElement(xml_greeting, "tahun_kini").text = unicode(row.tahun_kini)
            ET.SubElement(xml_greeting, "tahun_lalu").text = unicode(row.tahun_lalu)
            ET.SubElement(xml_greeting, "amount_kini").text = unicode(row.amount_kini)
            ET.SubElement(xml_greeting, "amount_lalu").text = unicode(row.amount_lalu)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root

class b105r051Generator(JasperGenerator):
    def __init__(self):
        super(b105r051Generator, self).__init__()
        self.reportname = get_rpath('apbd/tuskpd/R105501.jrxml')
        self.xpath = '/apbd/akuntansi'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'akuntansi')
            ET.SubElement(xml_greeting, "kode").text = row.kode
            ET.SubElement(xml_greeting, "nama").text = row.nama
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "level_id").text = unicode(row.level_id)
            ET.SubElement(xml_greeting, "tahun_kini").text = unicode(row.tahun_kini)
            ET.SubElement(xml_greeting, "tahun_lalu").text = unicode(row.tahun_lalu)
            ET.SubElement(xml_greeting, "amount_kini").text = unicode(row.amount_kini)
            ET.SubElement(xml_greeting, "amount_lalu").text = unicode(row.amount_lalu)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root

class b105r052Generator(JasperGenerator):
    def __init__(self):
        super(b105r052Generator, self).__init__()
        self.reportname = get_rpath('apbd/tuskpd/R105502.jrxml')
        self.xpath = '/apbd/akuntansi'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'akuntansi')
            ET.SubElement(xml_greeting, "kode").text = row.kode
            ET.SubElement(xml_greeting, "nama").text = row.nama
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "level_id").text = unicode(row.level_id)
            ET.SubElement(xml_greeting, "tahun_kini").text = unicode(row.tahun_kini)
            ET.SubElement(xml_greeting, "tahun_lalu").text = unicode(row.tahun_lalu)
            ET.SubElement(xml_greeting, "amount_kini").text = unicode(row.amount_kini)
            ET.SubElement(xml_greeting, "amount_lalu").text = unicode(row.amount_lalu)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root
"""
#Realisasi
class b204r100Generator(JasperGenerator):
    def __init__(self):
        super(b204r100Generator, self).__init__()
        self.reportname = get_rpath('apbd/tuppkd/R204100.jrxml')
        self.xpath = '/apbd/realisasi'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'realisasi')
            ET.SubElement(xml_greeting, "bulan").text = unicode(bln)
            ET.SubElement(xml_greeting, "status").text = unicode(status)
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "level_id").text = unicode(row.level_id)
            ET.SubElement(xml_greeting, "defsign").text = unicode(row.defsign)
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun_id)
            ET.SubElement(xml_greeting, "jumlah1").text = unicode(row.jumlah1)
            ET.SubElement(xml_greeting, "jumlah2").text = unicode(row.jumlah2)
            ET.SubElement(xml_greeting, "realisasi").text = unicode(row.realisasi)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root

#Realisasi SKPD Kegiatan
class b204r200Generator(JasperGenerator):
    def __init__(self):
        super(b204r200Generator, self).__init__()
        self.reportname = get_rpath('apbd/tuppkd/R204200.jrxml')
        self.xpath = '/apbd/realisasi'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'realisasi')
            ET.SubElement(xml_greeting, "tahun_id").text = unicode(row.tahun_id)
            ET.SubElement(xml_greeting, "bulan").text = unicode(bln)
            ET.SubElement(xml_greeting, "status").text = unicode(status)
            ET.SubElement(xml_greeting, "tipe").text = unicode(tipe)
            ET.SubElement(xml_greeting, "urusan_kd").text = row.urusan_kd
            ET.SubElement(xml_greeting, "urusan_nm").text = row.urusan_nm
            ET.SubElement(xml_greeting, "unit_id").text = unicode(row.unit_id)
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "program_kd").text = row.program_kd
            ET.SubElement(xml_greeting, "program_nm").text = row.program_nm
            ET.SubElement(xml_greeting, "kegiatan_kd").text = row.kegiatan_kd
            ET.SubElement(xml_greeting, "kegiatan_nm").text = row.kegiatan_nm
            ET.SubElement(xml_greeting, "jenis").text = unicode(row.jenis)
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "level_id").text = unicode(row.level_id)
            ET.SubElement(xml_greeting, "defsign").text = unicode(row.defsign)
            ET.SubElement(xml_greeting, "rekening_id").text = unicode(row.rekening_id)
            ET.SubElement(xml_greeting, "jumlah1").text = unicode(row.jumlah1)
            ET.SubElement(xml_greeting, "jumlah2").text = unicode(row.jumlah2)
            ET.SubElement(xml_greeting, "realisasi").text = unicode(row.realisasi)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root

#Realisasi SKPD
class b204r300Generator(JasperGenerator):
    def __init__(self):
        super(b204r300Generator, self).__init__()
        self.reportname = get_rpath('apbd/tuppkd/R204300.jrxml')
        self.xpath = '/apbd/realisasi'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'realisasi')
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "bulan").text = unicode(bln)
            ET.SubElement(xml_greeting, "status").text = unicode(status)
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "level_id").text = unicode(row.level_id)
            ET.SubElement(xml_greeting, "defsign").text = unicode(row.defsign)
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun_id)
            ET.SubElement(xml_greeting, "jumlah1").text = unicode(row.jumlah1)
            ET.SubElement(xml_greeting, "jumlah2").text = unicode(row.jumlah2)
            ET.SubElement(xml_greeting, "realisasi").text = unicode(row.realisasi)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root

# Register SP2D
class b204r0000Generator(JasperGenerator):
    def __init__(self):
        super(b204r0000Generator, self).__init__()
        self.reportname = get_rpath('apbd/tuppkd/R2040000.jrxml')
        self.xpath = '/apbd/spp'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'spp')
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "unit_id").text = unicode(row.unit_id)
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "jenis").text = unicode(row.jenis)
            ET.SubElement(xml_greeting, "sp2d_kd").text = row.sp2d_kd
            ET.SubElement(xml_greeting, "tgl_sp2d").text = unicode(row.tgl_sp2d)
            ET.SubElement(xml_greeting, "sp2d_nm").text = row.sp2d_nm
            ET.SubElement(xml_greeting, "bud_nip").text = row.bud_nip
            ET.SubElement(xml_greeting, "bud_nama").text = row.bud_nama
            ET.SubElement(xml_greeting, "ap_nama").text = row.ap_nama
            ET.SubElement(xml_greeting, "spp_nm").text = row.spp_nm
            ET.SubElement(xml_greeting, "nominal_gj").text = unicode(row.nominal_gj)
            ET.SubElement(xml_greeting, "nominal").text = unicode(row.nominal)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
            rows = DBSession.query(Pegawai.nama.label('pa_nama'), Pegawai.kode.label('pa_nip')
               ).filter(Pejabat.pegawai_id==Pegawai.id, Pejabat.jabatan_id==Jabatan.id, 
               Pejabat.unit_id==row.unit_id, Jabatan.id==7)
            for row2 in rows :
               ET.SubElement(xml_greeting, "pa_nama").text = row2.pa_nama
               ET.SubElement(xml_greeting, "pa_nip").text = row2.pa_nip
        return self.root

class b204r0001Generator(JasperGenerator):
    def __init__(self):
        super(b204r0001Generator, self).__init__()
        self.reportname = get_rpath('apbd/tuppkd/R2040001.jrxml')
        self.xpath = '/apbd/spp'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'spp')
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "unit_id").text = unicode(row.unit_id)
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "spp_nm").text = row.spp_nm
            ET.SubElement(xml_greeting, "jenis").text = unicode(row.jenis)
            ET.SubElement(xml_greeting, "ap_nama").text = row.ap_nama
            ET.SubElement(xml_greeting, "sp2d_kd").text = row.sp2d_kd
            ET.SubElement(xml_greeting, "tgl_sp2d").text = unicode(row.tgl_sp2d)
            ET.SubElement(xml_greeting, "sp2d_nm").text = row.sp2d_nm
            ET.SubElement(xml_greeting, "bud_nip").text = row.bud_nip
            ET.SubElement(xml_greeting, "bud_nama").text = row.bud_nama
            ET.SubElement(xml_greeting, "UP").text = unicode(row.UP)
            ET.SubElement(xml_greeting, "GU").text = unicode(row.GU)
            ET.SubElement(xml_greeting, "TU").text = unicode(row.TU)
            ET.SubElement(xml_greeting, "LS_GJ").text = unicode(row.LS_GJ)
            ET.SubElement(xml_greeting, "LS").text = unicode(row.LS)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
            rows = DBSession.query(Pegawai.nama.label('pa_nama'), Pegawai.kode.label('pa_nip')
               ).filter(Pejabat.pegawai_id==Pegawai.id, Pejabat.jabatan_id==Jabatan.id, 
               Pejabat.unit_id==row.unit_id, Jabatan.id==7)
            for row2 in rows :
               ET.SubElement(xml_greeting, "pa_nama").text = row2.pa_nama
               ET.SubElement(xml_greeting, "pa_nip").text = row2.pa_nip
        return self.root

# Register SP2D SKPD
class b204r0002Generator(JasperGenerator):
    def __init__(self):
        super(b204r0002Generator, self).__init__()
        self.reportname = get_rpath('apbd/tuppkd/R2040002.jrxml')
        self.xpath = '/apbd/spp'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'spp')
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "unit_id").text = unicode(row.unit_id)
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "jenis").text = unicode(row.jenis)
            ET.SubElement(xml_greeting, "sp2d_kd").text = row.sp2d_kd
            ET.SubElement(xml_greeting, "tgl_sp2d").text = unicode(row.tgl_sp2d)
            ET.SubElement(xml_greeting, "sp2d_nm").text = row.sp2d_nm
            ET.SubElement(xml_greeting, "bud_nip").text = row.bud_nip
            ET.SubElement(xml_greeting, "bud_nama").text = row.bud_nama
            ET.SubElement(xml_greeting, "ap_nama").text = row.ap_nama
            ET.SubElement(xml_greeting, "spp_nm").text = row.spp_nm
            ET.SubElement(xml_greeting, "nominal_gj").text = unicode(row.nominal_gj)
            ET.SubElement(xml_greeting, "nominal").text = unicode(row.nominal)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
            rows = DBSession.query(Pegawai.nama.label('pa_nama'), Pegawai.kode.label('pa_nip')
               ).filter(Pejabat.pegawai_id==Pegawai.id, Pejabat.jabatan_id==Jabatan.id, 
               Pejabat.unit_id==row.unit_id, Jabatan.id==7)
            for row2 in rows :
               ET.SubElement(xml_greeting, "pa_nama").text = row2.pa_nama
               ET.SubElement(xml_greeting, "pa_nip").text = row2.pa_nip
        return self.root

# Register SP2D SKPD
class b204r0003Generator(JasperGenerator):
    def __init__(self):
        super(b204r0003Generator, self).__init__()
        self.reportname = get_rpath('apbd/tuppkd/R2040003.jrxml')
        self.xpath = '/apbd/spp'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'spp')
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "unit_id").text = unicode(row.unit_id)
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "spp_nm").text = row.spp_nm
            ET.SubElement(xml_greeting, "jenis").text = unicode(row.jenis)
            ET.SubElement(xml_greeting, "ap_nama").text = row.ap_nama
            ET.SubElement(xml_greeting, "spm_id").text = unicode(row.spm_id)
            ET.SubElement(xml_greeting, "sp2d_kd").text = row.sp2d_kd
            ET.SubElement(xml_greeting, "tgl_sp2d").text = unicode(row.tgl_sp2d)
            ET.SubElement(xml_greeting, "sp2d_nm").text = row.sp2d_nm
            ET.SubElement(xml_greeting, "bud_nip").text = row.bud_nip
            ET.SubElement(xml_greeting, "bud_nama").text = row.bud_nama
            ET.SubElement(xml_greeting, "nominal").text = unicode(row.nominal)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
            rows = DBSession.query(Pegawai.nama.label('pa_nama'), Pegawai.kode.label('pa_nip')
               ).filter(Pejabat.pegawai_id==Pegawai.id, Pejabat.jabatan_id==Jabatan.id, 
               Pejabat.unit_id==row.unit_id, Jabatan.id==7)
            for row2 in rows :
               ET.SubElement(xml_greeting, "pa_nama").text = row2.pa_nama
               ET.SubElement(xml_greeting, "pa_nip").text = row2.pa_nip
            
            rows1 = DBSession.query(func.coalesce(func.sum(SpmPotongan.nilai),0).label('iwp')
               ).filter(SpmPotongan.ap_spm_id==row.spm_id, Rekening.id==SpmPotongan.rekening_id,
               Rekening.kode=="7.1.1.01.01")
            for row3 in rows1 :
               ET.SubElement(xml_greeting, "iwp").text = unicode(row3.iwp)

            rows2 = DBSession.query(func.coalesce(func.sum(SpmPotongan.nilai),0).label('pph')
               ).filter(SpmPotongan.ap_spm_id==row.spm_id, Rekening.id==SpmPotongan.rekening_id,
               Rekening.kode=="7.1.1.01.03")
            for row4 in rows2 :
               ET.SubElement(xml_greeting, "pph").text = unicode(row4.pph)

            rows3 = DBSession.query(func.coalesce(func.sum(SpmPotongan.nilai),0).label('taperum')
               ).filter(SpmPotongan.ap_spm_id==row.spm_id, Rekening.id==SpmPotongan.rekening_id,
               Rekening.kode=="7.1.1.01.05")
            for row5 in rows3 :
               ET.SubElement(xml_greeting, "taperum").text = unicode(row5.taperum)
               
            rows4 = DBSession.query(func.coalesce(func.sum(SpmPotongan.nilai),0).label('askes')
               ).filter(SpmPotongan.ap_spm_id==row.spm_id, Rekening.id==SpmPotongan.rekening_id,
               Rekening.kode=="7.1.1.01.02")
            for row6 in rows4 :
               ET.SubElement(xml_greeting, "askes").text = unicode(row6.askes)
               
        return self.root

# Register PPN PPH
class b204r0004Generator(JasperGenerator):
    def __init__(self):
        super(b204r0004Generator, self).__init__()
        self.reportname = get_rpath('apbd/tuppkd/R2040004.jrxml')
        self.xpath = '/apbd/spp'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'spp')
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "unit_id").text = unicode(row.unit_id)
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "jenis").text = unicode(row.jenis)
            ET.SubElement(xml_greeting, "sp2d_kd").text = row.sp2d_kd
            ET.SubElement(xml_greeting, "tgl_sp2d").text = unicode(row.tgl_sp2d)
            ET.SubElement(xml_greeting, "sp2d_nm").text = row.sp2d_nm
            ET.SubElement(xml_greeting, "bud_nip").text = row.bud_nip
            ET.SubElement(xml_greeting, "bud_nama").text = row.bud_nama
            ET.SubElement(xml_greeting, "ap_nama").text = row.ap_nama
            ET.SubElement(xml_greeting, "spp_nm").text = row.spp_nm
            ET.SubElement(xml_greeting, "nominal_gj").text = unicode(row.nominal_gj)
            ET.SubElement(xml_greeting, "nominal").text = unicode(row.nominal)
            ET.SubElement(xml_greeting, "ppn").text = unicode(row.ppn)
            ET.SubElement(xml_greeting, "pph").text = unicode(row.pph)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
            rows = DBSession.query(Pegawai.nama.label('pa_nama'), Pegawai.kode.label('pa_nip')
               ).filter(Pejabat.pegawai_id==Pegawai.id, Pejabat.jabatan_id==Jabatan.id, 
               Pejabat.unit_id==row.unit_id, Jabatan.id==7)
            for row2 in rows :
               ET.SubElement(xml_greeting, "pa_nama").text = row2.pa_nama
               ET.SubElement(xml_greeting, "pa_nip").text = row2.pa_nip
        return self.root
