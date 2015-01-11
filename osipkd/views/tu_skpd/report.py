import os
import unittest
import os.path
import uuid

from osipkd.tools import row2dict, xls_reader

from datetime import datetime
#from sqlalchemy import not_, func, case
from sqlalchemy import *
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
    
class ViewTUSKPDLap(BaseViews):
    def __init__(self, context, request):
        global customer
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
           print XXXXXXXX
           
        # INVOICE
        elif url_dict['act']=='invoice' :
          pk_id = 'id' in params and params['id'] and int(params['id']) or 0
          query = DBSession.query(ARInvoice.tahun_id.label('tahun'), Unit.nama.label('unit_nm'),
                  ARInvoice.id.label('arinvoice_id'), ARInvoice.kode, ARInvoice.nama.label('arinvoice_nm'), 
                  ARInvoice.tgl_terima, ARInvoice.tgl_validasi, ARInvoice.bendahara_nm, 
                  ARInvoice.penyetor, ARInvoice.alamat, KegiatanSub.nama.label('kegiatan_nm'),
                  func.sum(ARInvoiceItem.nilai).label('nilai')
                  ).filter(ARInvoice.unit_id==Unit.id, ARInvoice.kegiatan_sub_id==KegiatanSub.id,
                  ARInvoiceItem.arinvoice_id==ARInvoice.id, ARInvoice.unit_id==self.unit_id,
                  ARInvoice.tahun_id==self.tahun, ARInvoice.id==pk_id
                  ).group_by(ARInvoice.tahun_id, Unit.nama,
                  ARInvoice.id, ARInvoice.kode, ARInvoice.nama, 
                  ARInvoice.tgl_terima, ARInvoice.tgl_validasi, ARInvoice.bendahara_nm, 
                  ARInvoice.penyetor, ARInvoice.alamat, KegiatanSub.nama
                  )
          generator = b102r002Generator()
          pdf = generator.generate(query)
          response=req.response
          response.content_type="application/pdf"
          response.content_disposition='filename=output.pdf' 
          response.write(pdf)
          return response
          
        ### AR PAYMENT
        elif url_dict['act']=='arpayment' :
          pk_id = 'id' in params and params['id'] and int(params['id']) or 0
          query = DBSession.query(Sts
                ).filter(Sts.unit_id==Unit.id, 
                Sts.unit_id==self.unit_id,
                Sts.tahun_id==self.tahun, Sts.id==pk_id
                )
          generator = b102r003Generator()
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
        req    = self.request
        params = req.params
        url_dict = req.matchdict

        tipe = 'tipe' in params and params['tipe'] and int(params['tipe']) or 0
        mulai = 'mulai' in params and params['mulai'] or 0
        selesai = 'selesai' in params and params['selesai'] or 0
        
        ### LAPORAN AP INVOICE
        if url_dict['act']=='1' :
          if tipe==0 :
            query = DBSession.query(APInvoice.tahun_id.label('tahun'), Unit.nama.label('unit_nm'),
                  APInvoice.ap_tanggal.label('tgl_invoice'),
                  case([(APInvoice.jenis==1,"UP"),(APInvoice.jenis==2,"TU"),(APInvoice.jenis==3,"GU"),
                  (APInvoice.jenis==4,"LS")], else_="").label('jenis'),
                  APInvoice.kode.label('invoice_kd'), KegiatanSub.nama.label('kegiatan_nm'), 
                  Rekening.kode.label('rek_kd'),Rekening.nama.label('rek_nm'), 
                  func.sum(APInvoiceItem.amount).label('jumlah')
                  ).filter(APInvoice.unit_id==Unit.id, APInvoice.kegiatan_sub_id==KegiatanSub.id,
                  APInvoice.id==APInvoiceItem.ap_invoice_id, APInvoiceItem.kegiatan_item_id==KegiatanItem.id,
                  KegiatanItem.rekening_id==Rekening.id, APInvoice.unit_id==self.unit_id,
                  APInvoice.tahun_id==self.session['tahun'],  
                  APInvoice.ap_tanggal.between(mulai,selesai)
                  ).group_by(APInvoice.tahun_id, Unit.nama,
                  APInvoice.ap_tanggal,
                  case([(APInvoice.jenis==1,"UP"),(APInvoice.jenis==2,"TU"),(APInvoice.jenis==3,"GU"),
                  (APInvoice.jenis==4,"LS")], else_=""),
                  APInvoice.kode, KegiatanSub.nama, 
                  Rekening.kode,Rekening.nama
                  ).order_by(APInvoice.ap_tanggal).all()
          else:
                query = DBSession.query(APInvoice.tahun_id.label('tahun'), Unit.nama.label('unit_nm'),
                  APInvoice.ap_tanggal.label('tgl_invoice'),
                  case([(APInvoice.jenis==1,"UP"),(APInvoice.jenis==2,"TU"),(APInvoice.jenis==3,"GU"),
                  (APInvoice.jenis==4,"LS")], else_="").label('jenis'),
                  APInvoice.kode.label('invoice_kd'), KegiatanSub.nama.label('kegiatan_nm'), 
                  Rekening.kode.label('rek_kd'),Rekening.nama.label('rek_nm'), 
                  func.sum(APInvoiceItem.amount).label('jumlah')
                  ).filter(APInvoice.unit_id==Unit.id, APInvoice.kegiatan_sub_id==KegiatanSub.id,
                  APInvoice.id==APInvoiceItem.ap_invoice_id, APInvoiceItem.kegiatan_item_id==KegiatanItem.id,
                  KegiatanItem.rekening_id==Rekening.id, APInvoice.unit_id==self.unit_id,
                  APInvoice.tahun_id==self.session['tahun'], APInvoice.jenis==tipe, 
                  APInvoice.ap_tanggal.between(mulai,selesai)
                  ).group_by(APInvoice.tahun_id, Unit.nama,
                  APInvoice.ap_tanggal,
                  case([(APInvoice.jenis==1,"UP"),(APInvoice.jenis==2,"TU"),(APInvoice.jenis==3,"GU"),
                  (APInvoice.jenis==4,"LS")], else_=""),
                  APInvoice.kode, KegiatanSub.nama, 
                  Rekening.kode,Rekening.nama
                  ).order_by(APInvoice.ap_tanggal).all()

          generator = b104r000Generator()
          pdf = generator.generate(query)
          response=req.response
          response.content_type="application/pdf"
          response.content_disposition='filename=output.pdf' 
          response.write(pdf)
          return response

        ### AP INVOICE
        elif url_dict['act']=='apinvoice' :
            print "AP INVOICE"
            
        ### LAPORAN SPP 1
        elif url_dict['act']=='21' :
            if tipe ==0 :
               query = DBSession.query(Spp.tahun_id.label('tahun'), Unit.nama.label('unit_nm'),
                  case([(Spp.jenis==1,"UP"),(Spp.jenis==2,"TU"),(Spp.jenis==3,"GU"),(Spp.jenis==4,"LS")], else_="").label('jenis'),
                  Spp.kode.label('spp_kd'), Spp.nama.label('spp_nm'), Spp.tanggal.label('tgl_spp'),
                  Spm.kode.label('spm_kd'), Spm.tanggal.label('tgl_spm'),
                  Sp2d.kode.label('sp2d_kd'), Sp2d.tanggal.label('tgl_sp2d'),
                  func.sum(APInvoiceItem.amount).label('nominal')
                  ).filter(SppItem.ap_spp_id==Spp.id, SppItem.ap_invoice_id==APInvoice.id,
                  APInvoiceItem.ap_invoice_id==APInvoice.id, APInvoiceItem.kegiatan_item_id==KegiatanItem.id,
                  KegiatanItem.rekening_id==Rekening.id,
                  Spp.unit_id==Unit.id, Spp.unit_id==self.session['unit_id'],
                  Spp.tahun_id==self.session['tahun'],
                  Spp.tanggal.between(mulai,selesai)        
                  ).outerjoin(Spm,Spm.ap_spp_id==Spp.id
                  ).outerjoin(Sp2d,Sp2d.ap_spm_id==Spm.id
                  ).group_by(Spp.tahun_id, Unit.nama,
                  case([(Spp.jenis==1,"UP"),(Spp.jenis==2,"TU"),(Spp.jenis==3,"GU"),(Spp.jenis==4,"LS")], else_=""),
                  Spp.kode, Spp.nama, Spp.tanggal,
                  Spm.kode, Spm.tanggal,
                  Sp2d.kode, Sp2d.tanggal,
                  ).order_by(Spp.tanggal).all()
            else:
                query = DBSession.query(Spp.tahun_id.label('tahun'), Unit.nama.label('unit_nm'),
                  case([(Spp.jenis==1,"UP"),(Spp.jenis==2,"TU"),(Spp.jenis==3,"GU"),(Spp.jenis==4,"LS")], else_="").label('jenis'),
                  Spp.kode.label('spp_kd'), Spp.nama.label('spp_nm'), Spp.tanggal.label('tgl_spp'),
                  Spm.kode.label('spm_kd'), Spm.tanggal.label('tgl_spm'),
                  Sp2d.kode.label('sp2d_kd'), Sp2d.tanggal.label('tgl_sp2d'),
                  func.sum(APInvoiceItem.amount).label('nominal')
                  ).filter(SppItem.ap_spp_id==Spp.id, SppItem.ap_invoice_id==APInvoice.id,
                  APInvoiceItem.ap_invoice_id==APInvoice.id, APInvoiceItem.kegiatan_item_id==KegiatanItem.id,
                  KegiatanItem.rekening_id==Rekening.id,
                  Spp.unit_id==Unit.id, Spp.unit_id==self.unit_id,
                  Spp.tahun_id==self.session['tahun'], Spp.jenis==tipe, 
                  Spp.tanggal.between(mulai,selesai)
                  ).outerjoin(Spm,Spm.ap_spp_id==Spp.id
                  ).outerjoin(Sp2d,Sp2d.ap_spm_id==Spm.id
                  ).group_by(Spp.tahun_id, Unit.nama,
                  case([(Spp.jenis==1,"UP"),(Spp.jenis==2,"TU"),(Spp.jenis==3,"GU"),(Spp.jenis==4,"LS")], else_=""),
                  Spp.kode, Spp.nama, Spp.tanggal,
                  Spm.kode, Spm.tanggal,
                  Sp2d.kode, Sp2d.tanggal,
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
                query = DBSession.query(Spp.tahun_id.label('tahun'), 
                  Unit.nama.label('unit_nm'), Spp.tanggal.label('tgl_spp'), 
                  Spp.kode.label('spp_kd'), Spp.nama.label('spp_nm'),
                  func.sum(case([(Spp.jenis==1,APInvoiceItem.amount)], else_=0)).label('UP'),
                  func.sum(case([(Spp.jenis==2,APInvoiceItem.amount)], else_=0)).label('GU'),
                  func.sum(case([(Spp.jenis==3,APInvoiceItem.amount)], else_=0)).label('TU'),
                  func.sum(case([(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)=='5.2.1'),APInvoiceItem.amount)], else_=0)).label('LS_GJ'),
                  func.sum(case([(and_(Spp.jenis==4,not_(func.substr(Rekening.kode,1,5)=='5.2.1')),APInvoiceItem.amount)], else_=0)).label('LS')
                  ).filter(SppItem.ap_spp_id==Spp.id, SppItem.ap_invoice_id==APInvoice.id,
                  APInvoiceItem.ap_invoice_id==APInvoice.id, APInvoiceItem.kegiatan_item_id==KegiatanItem.id,
                  KegiatanItem.rekening_id==Rekening.id,
                  Spp.unit_id==Unit.id, Spp.unit_id==self.unit_id,
                  Spp.tahun_id==self.session['tahun'], 
                  Spp.tanggal.between(mulai,selesai)        
                  ).group_by(Spp.tahun_id, Unit.nama, Spp.tanggal, 
                  Spp.kode, Spp.nama
                  ).order_by(Spp.tanggal).all()
            else:
                query = DBSession.query(Spp.tahun_id.label('tahun'), 
                  Unit.nama.label('unit_nm'), Spp.tanggal.label('tgl_spp'), 
                  Spp.kode.label('spp_kd'), Spp.nama.label('spp_nm'),
                  func.sum(case([(Spp.jenis==1,APInvoiceItem.amount)], else_=0)).label('UP'),
                  func.sum(case([(Spp.jenis==2,APInvoiceItem.amount)], else_=0)).label('GU'),
                  func.sum(case([(Spp.jenis==3,APInvoiceItem.amount)], else_=0)).label('TU'),
                  func.sum(case([(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)=='5.2.1'),APInvoiceItem.amount)], else_=0)).label('LS_GJ'),
                  func.sum(case([(and_(Spp.jenis==4,not_(func.substr(Rekening.kode,1,5)=='5.2.1')),APInvoiceItem.amount)], else_=0)).label('LS')
                  ).filter(SppItem.ap_spp_id==Spp.id, SppItem.ap_invoice_id==APInvoice.id,
                  APInvoiceItem.ap_invoice_id==APInvoice.id, APInvoiceItem.kegiatan_item_id==KegiatanItem.id,
                  KegiatanItem.rekening_id==Rekening.id,
                  Spp.unit_id==Unit.id, Spp.unit_id==self.unit_id,
                  Spp.tahun_id==self.session['tahun'], Spp.jenis==tipe, 
                  Spp.tanggal.between(mulai,selesai)        
                  ).group_by(Spp.tahun_id, Unit.nama, Spp.tanggal, 
                  Spp.kode, Spp.nama
                  ).order_by(Spp.tanggal).all()
                  
            generator = b104r1002Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        ### SPP
        elif url_dict['act']=='spp' :
            pk_id = 'id' in params and params['id'] and int(params['id']) or 0
            query = DBSession.query(Spp.tahun_id.label('tahun'), Unit.kode.label('unit_kd'), 
                  Unit.nama.label('unit_nm'), KegiatanSub.nama.label('kegiatan_nm'),
                  Tahun.no_perkdh, Tahun.tgl_perkdh, Urusan.nama.label('urusan_nm'),
                  Spp.kode.label('spp_kd'), Spp.nama, Spp.bank_nama, Spp.bank_account,
                  Spp.tanggal, case([(Spp.jenis==1,"UP"),(Spp.jenis==2,"TU"),(Spp.jenis==3,"GU"),
                  (Spp.jenis==4,"LS")], else_="").label('jenis'), Spp.nominal,
                  Spd.kode.label('spd_kd'), Spd.tanggal.label('tgl_spd')
                  ).join(Unit,Tahun,SppItem,APInvoice,KegiatanSub
                  ).outerjoin(Spd,Spd.id==Spp.spd_id
                  ).outerjoin(Urusan,Unit.urusan_id==Urusan.id
                  ).filter(Spp.unit_id==Unit.id, Spp.id==SppItem.ap_spp_id, 
                  SppItem.ap_invoice_id==APInvoice.id, KegiatanSub.id==APInvoice.kegiatan_sub_id,
                  Spp.tahun_id==Tahun.id, Spp.unit_id==self.unit_id, 
                  Spp.tahun_id==self.tahun, Spp.id==pk_id
                  )
            generator = b103r002Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        ### LAPORAN SPM 1
        elif url_dict['act']=='31' :
            if tipe ==0 :
               query = DBSession.query(Spp.tahun_id.label('tahun'), Unit.nama.label('unit_nm'),
                  case([(Spp.jenis==1,"UP"),(Spp.jenis==2,"TU"),(Spp.jenis==3,"GU"),(Spp.jenis==4,"LS")], else_="").label('jenis'),
                  Spp.kode.label('spp_kd'), Spp.nama.label('spp_nm'), Spp.tanggal.label('tgl_spp'),
                  Spm.kode.label('spm_kd'), Spm.tanggal.label('tgl_spm'),
                  Sp2d.kode.label('sp2d_kd'), Sp2d.tanggal.label('tgl_sp2d'),
                  func.sum(APInvoiceItem.amount).label('nominal')
                  ).filter(SppItem.ap_spp_id==Spp.id, SppItem.ap_invoice_id==APInvoice.id,
                  APInvoiceItem.ap_invoice_id==APInvoice.id, APInvoiceItem.kegiatan_item_id==KegiatanItem.id,
                  KegiatanItem.rekening_id==Rekening.id,
                  Spp.unit_id==Unit.id, Spp.unit_id==self.unit_id,
                  Spp.tahun_id==self.session['tahun'],
                  Spm.tanggal.between(mulai,selesai)        
                  ).outerjoin(Spm,Spm.ap_spp_id==Spp.id
                  ).outerjoin(Sp2d,Sp2d.ap_spm_id==Spm.id
                  ).group_by(Spp.tahun_id, Unit.nama,
                  case([(Spp.jenis==1,"UP"),(Spp.jenis==2,"TU"),(Spp.jenis==3,"GU"),(Spp.jenis==4,"LS")], else_=""),
                  Spp.kode, Spp.nama, Spp.tanggal,
                  Spm.kode, Spm.tanggal,
                  Sp2d.kode, Sp2d.tanggal
                  ).order_by(Spp.tanggal).all()

            else:
                query = DBSession.query(Spp.tahun_id.label('tahun'), Unit.nama.label('unit_nm'),
                  case([(Spp.jenis==1,"UP"),(Spp.jenis==2,"TU"),(Spp.jenis==3,"GU"),(Spp.jenis==4,"LS")], else_="").label('jenis'),
                  Spp.kode.label('spp_kd'), Spp.nama.label('spp_nm'), Spp.tanggal.label('tgl_spp'),
                  Spm.kode.label('spm_kd'), Spm.tanggal.label('tgl_spm'),
                  Sp2d.kode.label('sp2d_kd'), Sp2d.tanggal.label('tgl_sp2d'),
                  func.sum(APInvoiceItem.amount).label('nominal')
                  ).filter(SppItem.ap_spp_id==Spp.id, SppItem.ap_invoice_id==APInvoice.id,
                  APInvoiceItem.ap_invoice_id==APInvoice.id, APInvoiceItem.kegiatan_item_id==KegiatanItem.id,
                  KegiatanItem.rekening_id==Rekening.id,
                  Spp.unit_id==Unit.id, Spp.unit_id==self.unit_id,
                  Spp.tahun_id==self.session['tahun'], Spp.jenis==tipe, 
                  Spm.tanggal.between(mulai,selesai)
                  ).outerjoin(Spm,Spm.ap_spp_id==Spp.id
                  ).outerjoin(Sp2d,Sp2d.ap_spm_id==Spm.id
                  ).group_by(Spp.tahun_id, Unit.nama,
                  case([(Spp.jenis==1,"UP"),(Spp.jenis==2,"TU"),(Spp.jenis==3,"GU"),(Spp.jenis==4,"LS")], else_=""),
                  Spp.kode, Spp.nama, Spp.tanggal,
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
        elif url_dict['act']=='32' :
            if tipe ==0 :
                query = DBSession.query(Spp.tahun_id.label('tahun'), 
                  Unit.nama.label('unit_nm'), Spm.tanggal.label('tgl_spp'), 
                  Spm.kode.label('spp_kd'), Spm.nama.label('spp_nm'),
                  func.sum(case([(Spp.jenis==1,APInvoiceItem.amount)], else_=0)).label('UP'),
                  func.sum(case([(Spp.jenis==2,APInvoiceItem.amount)], else_=0)).label('GU'),
                  func.sum(case([(Spp.jenis==3,APInvoiceItem.amount)], else_=0)).label('TU'),
                  func.sum(case([(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)=='5.2.1'),APInvoiceItem.amount)], else_=0)).label('LS_GJ'),
                  func.sum(case([(and_(Spp.jenis==4,not_(func.substr(Rekening.kode,1,5)=='5.2.1')),APInvoiceItem.amount)], else_=0)).label('LS')
                  ).filter(SppItem.ap_spp_id==Spp.id, SppItem.ap_invoice_id==APInvoice.id,
                  APInvoiceItem.ap_invoice_id==APInvoice.id, APInvoiceItem.kegiatan_item_id==KegiatanItem.id,
                  KegiatanItem.rekening_id==Rekening.id,
                  Spp.unit_id==Unit.id, Spp.unit_id==self.unit_id,
                  Spp.tahun_id==self.session['tahun'],  
                  Spm.tanggal.between(mulai,selesai)        
                  ).outerjoin(Spm,Spm.ap_spp_id==Spp.id
                  ).outerjoin(Sp2d,Sp2d.ap_spm_id==Spm.id
                  ).group_by(Spp.tahun_id, Unit.nama, Spm.tanggal, 
                  Spm.kode, Spm.nama
                  ).order_by(Spm.tanggal).all()
            else:
                query = DBSession.query(Spp.tahun_id.label('tahun'), 
                  Unit.nama.label('unit_nm'), Spm.tanggal.label('tgl_spp'), 
                  Spm.kode.label('spp_kd'), Spm.nama.label('spp_nm'),
                  func.sum(case([(Spp.jenis==1,APInvoiceItem.amount)], else_=0)).label('UP'),
                  func.sum(case([(Spp.jenis==2,APInvoiceItem.amount)], else_=0)).label('GU'),
                  func.sum(case([(Spp.jenis==3,APInvoiceItem.amount)], else_=0)).label('TU'),
                  func.sum(case([(and_(Spp.jenis==4,func.substr(Rekening.kode,1,5)=='5.2.1'),APInvoiceItem.amount)], else_=0)).label('LS_GJ'),
                  func.sum(case([(and_(Spp.jenis==4,not_(func.substr(Rekening.kode,1,5)=='5.2.1')),APInvoiceItem.amount)], else_=0)).label('LS')
                  ).outerjoin(Spm,Spm.ap_spp_id==Spp.id
                  ).outerjoin(Sp2d,Sp2d.ap_spm_id==Spm.id
                  ).filter(SppItem.ap_spp_id==Spp.id, SppItem.ap_invoice_id==APInvoice.id,
                  APInvoiceItem.ap_invoice_id==APInvoice.id, APInvoiceItem.kegiatan_item_id==KegiatanItem.id,
                  KegiatanItem.rekening_id==Rekening.id,
                  Spp.unit_id==Unit.id, Spp.unit_id==self.unit_id,
                  Spp.tahun_id==self.session['tahun'], Spp.jenis==tipe,   
                  Spm.tanggal.between(mulai,selesai)        
                  ).group_by(Spp.tahun_id, Unit.nama, Spm.tanggal, 
                  Spm.kode, Spm.nama
                  ).order_by(Spm.tanggal).all()

            generator = b104r2002Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        ### SPM
        elif url_dict['act']=='spm' :
            pk_id = 'id' in params and params['id'] and int(params['id']) or 0
            subq1 = DBSession.query(Spm.id.label('spm_id'), Spm.kode.label('spm_kd'), Spm.nama.label('spm_nm'), Spm.tanggal.label('spm_tgl'), Spp.id.label('spp_id'), 
                     Spp.kode.label('spp_kd'), Spp.nama.label('spp_nm'), Spp.tanggal.label('spp_tgl'), Spp.jenis.label('jenis'), 
                     Spp.bank_nama.label('bank_nama'), Spp.bank_account.label('bank_account'), Spp.ap_nama.label('ap_nama'), Spp.ap_bank.label('ap_bank'), Spp.ap_rekening.label('ap_rekening'), Spp.ap_npwp.label('ap_npwp'), 
                     Spp.tahun_id.label('tahun_id'), Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'), Kegiatan.kode.label('keg_kd'), 
                     Kegiatan.nama.label('keg_nm'), Program.kode.label('prg_kd'), Program.nama.label('prg_nm'), Spp.spd_id.label('spd_id'),
                     func.sum(APInvoiceItem.amount).label('nilai'), func.sum(APInvoiceItem.ppn).label('ppn'), 
                     func.sum(APInvoiceItem.pph).label('pph'), literal_column('0').label('potongan')
                     ).filter(Spm.ap_spp_id==Spp.id, Spp.unit_id==Unit.id,
                     SppItem.ap_spp_id==Spp.id, SppItem.ap_invoice_id==APInvoiceItem.ap_invoice_id, APInvoiceItem.kegiatan_item_id==KegiatanItem.id,
                     KegiatanItem.rekening_id==Rekening.id, KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                     KegiatanSub.kegiatan_id==Kegiatan.id, Kegiatan.program_id==Program.id,
                     Spp.unit_id==self.unit_id, Spp.tahun_id==self.tahun, Spm.id==pk_id,
                     func.left(Rekening.kode,1)=='5'
                     ).group_by(Spm.id, Spm.kode, 
                     Spm.nama, Spm.tanggal, Spp.id, Spp.kode, Spp.nama, Spp.tanggal, 
                     Spp.jenis, Spp.bank_nama, Spp.bank_account, Spp.ap_nama, Spp.ap_bank, 
                     Spp.ap_rekening, Spp.ap_npwp, Spp.tahun_id, Unit.kode, Unit.nama, 
                     Kegiatan.kode, Kegiatan.nama, Program.kode, Program.nama, Spp.spd_id
                     )                         

            subq2 = DBSession.query(Spm.id.label('spm_id'), Spm.kode.label('spm_kd'), Spm.nama.label('spm_nm'), Spm.tanggal.label('spm_tgl'), Spp.id.label('spp_id'), 
                     Spp.kode.label('spp_kd'), Spp.nama.label('spp_nm'), Spp.tanggal.label('spp_tgl'), Spp.jenis.label('jenis'), 
                     Spp.bank_nama.label('bank_nama'), Spp.bank_account.label('bank_account'), Spp.ap_nama.label('ap_nama'), Spp.ap_bank.label('ap_bank'), Spp.ap_rekening.label('ap_rekening'), Spp.ap_npwp.label('ap_npwp'), 
                     Spp.tahun_id.label('tahun_id'), Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'), Kegiatan.kode.label('keg_kd'), 
                     Kegiatan.nama.label('keg_nm'), Program.kode.label('prg_kd'), Program.nama.label('prg_nm'), Spp.spd_id.label('spd_id'),
                     literal_column('0').label('nilai'), literal_column('0').label('ppn'), 
                     literal_column('0').label('pph'), func.sum(APInvoiceItem.amount).label('potongan')
                     ).filter(Spm.ap_spp_id==Spp.id, Spp.unit_id==Unit.id,
                     SppItem.ap_spp_id==Spp.id, SppItem.ap_invoice_id==APInvoiceItem.ap_invoice_id, APInvoiceItem.kegiatan_item_id==KegiatanItem.id,
                     KegiatanItem.rekening_id==Rekening.id, KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                     KegiatanSub.kegiatan_id==Kegiatan.id, Kegiatan.program_id==Program.id,
                     Spp.unit_id==self.unit_id, Spp.tahun_id==self.tahun, Spm.id==pk_id,
                     func.left(Rekening.kode,1)=='7'
                     ).group_by(Spm.id, Spm.kode, 
                     Spm.nama, Spm.tanggal, Spp.id, Spp.kode, Spp.nama, Spp.tanggal, 
                     Spp.jenis, Spp.bank_nama, Spp.bank_account, Spp.ap_nama, Spp.ap_bank, 
                     Spp.ap_rekening, Spp.ap_npwp, Spp.tahun_id, Unit.kode, Unit.nama, 
                     Kegiatan.kode, Kegiatan.nama, Program.kode, Program.nama, Spp.spd_id 
                     )                         
            
            subq = subq1.union(subq2).subquery()
            
            query = DBSession.query(subq.c.spm_id, subq.c.spm_kd, 
                     subq.c.spm_nm, subq.c.spm_tgl, subq.c.spp_id, subq.c.spp_kd, subq.c.spp_nm, subq.c.spp_tgl, 
                     subq.c.jenis, subq.c.bank_nama, subq.c.bank_account, subq.c.ap_nama, subq.c.ap_bank, subq.c.ap_rekening, 
                     subq.c.ap_npwp, subq.c.tahun_id, subq.c.unit_kd, subq.c.unit_nm, subq.c.keg_kd, subq.c.keg_nm, subq.c.prg_kd, 
                     subq.c.prg_nm, subq.c.spd_id, func.sum(subq.c.nilai).label('nilai'),func.sum(subq.c.ppn).label('ppn'), 
                     func.sum(subq.c.pph).label('pph'),func.sum(subq.c.potongan).label('potongan')
                     ).group_by(subq.c.spm_id, subq.c.spm_kd, 
                     subq.c.spm_nm, subq.c.spm_tgl, subq.c.spp_id, subq.c.spp_kd, subq.c.spp_nm, subq.c.spp_tgl, 
                     subq.c.jenis, subq.c.bank_nama, subq.c.bank_account, subq.c.ap_nama, subq.c.ap_bank, subq.c.ap_rekening, 
                     subq.c.ap_npwp, subq.c.tahun_id, subq.c.unit_kd, subq.c.unit_nm, subq.c.keg_kd, subq.c.keg_nm, subq.c.prg_kd, 
                     subq.c.prg_nm, subq.c.spd_id
                     )                         

            generator = b103r003Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        ### SPJ Fungsional
        elif url_dict['act']=='4' :
            bulan = 'bulan' in params and params['bulan'] and int(params['bulan']) or 0
            subq = DBSession.query(Urusan.kode.label('urusan_kd'), Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'),
                      Program.kode.label('program_kd'), Kegiatan.kode.label('keg_kd'),
                      Kegiatan.nama.label('keg_nm'), Rekening.kode.label('rek_kd'),
                      Rekening.nama.label('rek_nm'), Spp.tahun_id.label('tahun'), Sp2d.tanggal.label('tanggal'),
                      Spp.jenis.label('jenis'), (KegiatanItem.vol_4_1*KegiatanItem.vol_4_2*KegiatanItem.hsat_4).label('anggaran'),
                      APInvoiceItem.amount.label('nilai')
                      ).filter(Sp2d.ap_spm_id==Spm.id, Spm.ap_spp_id==Spp.id,
                      Spp.unit_id==Unit.id, Spp.id==SppItem.ap_spp_id,
                      SppItem.ap_invoice_id==APInvoiceItem.ap_invoice_id,
                      APInvoiceItem.kegiatan_item_id==KegiatanItem.id,
                      KegiatanItem.rekening_id==Rekening.id,
                      KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                      Unit.urusan_id==Urusan.id, KegiatanSub.kegiatan_id==Kegiatan.id,
                      Kegiatan.program_id==Program.id,
                      Spp.unit_id==self.unit_id, Spp.tahun_id==self.session['tahun']
                      ).subquery()
                
            query = DBSession.query(subq.c.urusan_kd, subq.c.unit_kd, subq.c.unit_nm, subq.c.program_kd, subq.c.keg_kd,
                      subq.c.keg_nm, subq.c.rek_kd, subq.c.rek_nm, subq.c.tahun, func.sum(subq.c.anggaran).label('anggaran'),
                      func.sum(case([(and_(extract('month',subq.c.tanggal)<bulan, subq.c.jenis==4,func.substr(subq.c.rek_kd,1,5)=='5.2.1'),subq.c.nilai)], else_=0)).label('LSG_lalu'),
                      func.sum(case([(and_(extract('month',subq.c.tanggal)==bulan, subq.c.jenis==4,func.substr(subq.c.rek_kd,1,5)=='5.2.1'),subq.c.nilai)], else_=0)).label('LSG_kini'),
                      func.sum(case([(and_(extract('month',subq.c.tanggal)<bulan, subq.c.jenis==4,not_(func.substr(subq.c.rek_kd,1,5)=='5.2.1')),subq.c.nilai)], else_=0)).label('LS_lalu'),
                      func.sum(case([(and_(extract('month',subq.c.tanggal)==bulan, subq.c.jenis==4,not_(func.substr(subq.c.rek_kd,1,5)=='5.2.1')),subq.c.nilai)], else_=0)).label('LS_kini'),
                      func.sum(case([(and_(extract('month',subq.c.tanggal)<bulan, not_(subq.c.jenis==4)),subq.c.nilai)], else_=0)).label('Lain_lalu'),
                      func.sum(case([(and_(extract('month',subq.c.tanggal)==bulan, not_(subq.c.jenis==4)),subq.c.nilai)], else_=0)).label('Lain_kini'),
                      ).group_by(subq.c.urusan_kd, subq.c.unit_kd, subq.c.unit_nm, subq.c.program_kd, subq.c.keg_kd,
                      subq.c.keg_nm, subq.c.rek_kd, subq.c.rek_nm, subq.c.tahun 
                      ).order_by(subq.c.keg_kd
                      )

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
            subq = DBSession.query(Urusan.kode.label('urusan_kd'), Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'),
                      Program.kode.label('program_kd'), Kegiatan.kode.label('keg_kd'),
                      Kegiatan.nama.label('keg_nm'), Rekening.kode.label('rek_kd'),
                      Rekening.nama.label('rek_nm'), Spp.tahun_id.label('tahun'), Sp2d.tanggal.label('tanggal'),
                      Spp.jenis.label('jenis'), (KegiatanItem.vol_4_1*KegiatanItem.vol_4_2*KegiatanItem.hsat_4).label('anggaran'),
                      APInvoiceItem.amount.label('nilai')
                      ).filter(Sp2d.ap_spm_id==Spm.id, Spm.ap_spp_id==Spp.id,
                      Spp.unit_id==Unit.id, Spp.id==SppItem.ap_spp_id,
                      SppItem.ap_invoice_id==APInvoiceItem.ap_invoice_id,
                      APInvoiceItem.kegiatan_item_id==KegiatanItem.id,
                      KegiatanItem.rekening_id==Rekening.id,
                      KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                      Unit.urusan_id==Urusan.id, KegiatanSub.kegiatan_id==Kegiatan.id,
                      Kegiatan.program_id==Program.id,
                      Spp.unit_id==self.unit_id, Spp.tahun_id==self.session['tahun']
                      ).subquery()
                
            query = DBSession.query(subq.c.urusan_kd, subq.c.unit_kd, subq.c.unit_nm, subq.c.program_kd, subq.c.keg_kd,
                      subq.c.keg_nm, subq.c.rek_kd, subq.c.rek_nm, subq.c.tahun, func.sum(subq.c.anggaran).label('anggaran'),
                      func.sum(case([(and_(extract('month',subq.c.tanggal)<bulan, subq.c.jenis==4,func.substr(subq.c.rek_kd,1,5)=='5.2.1'),subq.c.nilai)], else_=0)).label('LSG_lalu'),
                      func.sum(case([(and_(extract('month',subq.c.tanggal)==bulan, subq.c.jenis==4,func.substr(subq.c.rek_kd,1,5)=='5.2.1'),subq.c.nilai)], else_=0)).label('LSG_kini'),
                      func.sum(case([(and_(extract('month',subq.c.tanggal)<bulan, subq.c.jenis==4,not_(func.substr(subq.c.rek_kd,1,5)=='5.2.1')),subq.c.nilai)], else_=0)).label('LS_lalu'),
                      func.sum(case([(and_(extract('month',subq.c.tanggal)==bulan, subq.c.jenis==4,not_(func.substr(subq.c.rek_kd,1,5)=='5.2.1')),subq.c.nilai)], else_=0)).label('LS_kini'),
                      func.sum(case([(and_(extract('month',subq.c.tanggal)<bulan, not_(subq.c.jenis==4)),subq.c.nilai)], else_=0)).label('Lain_lalu'),
                      func.sum(case([(and_(extract('month',subq.c.tanggal)==bulan, not_(subq.c.jenis==4)),subq.c.nilai)], else_=0)).label('Lain_kini'),
                      ).group_by(subq.c.urusan_kd, subq.c.unit_kd, subq.c.unit_nm, subq.c.program_kd, subq.c.keg_kd,
                      subq.c.keg_nm, subq.c.rek_kd, subq.c.rek_nm, subq.c.tahun 
                      ).order_by(subq.c.keg_kd
                      )

            generator = b104r400Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

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
            ET.SubElement(xml_greeting, "arinvoice_id").text = unicode(row.arinvoice_id)
            ET.SubElement(xml_greeting, "kode").text = row.kode
            ET.SubElement(xml_greeting, "arinvoice_nm").text = row.arinvoice_nm
            ET.SubElement(xml_greeting, "tgl_terima").text = unicode(row.tgl_terima)
            ET.SubElement(xml_greeting, "tgl_validasi").text = unicode(row.tgl_validasi)
            ET.SubElement(xml_greeting, "bendahara_nm").text = row.bendahara_nm
            ET.SubElement(xml_greeting, "penyetor").text = row.penyetor
            ET.SubElement(xml_greeting, "alamat").text = row.alamat
            ET.SubElement(xml_greeting, "kegiatan_nm").text = row.kegiatan_nm
            ET.SubElement(xml_greeting, "nilai").text = unicode(row.nilai)
            ET.SubElement(xml_greeting, "customer").text = customer
        return self.root
       
#STS-Generator
class b102r003Generator(JasperGenerator):
    def __init__(self):
        super(b102r003Generator, self).__init__()
        self.reportname = get_rpath('apbd/tuskpd/R102003.jrxml')
        self.xpath = '/apbd/sts'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'sts')
            ET.SubElement(xml_greeting, "tahun_id").text = unicode(row.tahun_id)
            ET.SubElement(xml_greeting, "unit_nm").text = row.units.nama
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
        return self.root

class b103r001Generator(JasperGenerator):
    def __init__(self):
        super(b103r001Generator, self).__init__()
        self.reportname = get_rpath('apbd/tuskpd/R103001.jrxml')
        self.xpath = '/apbd/invoice'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'invoice')
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "jenis").text = row.jenis
            ET.SubElement(xml_greeting, "invoice_id").text = unicode(row.invoice_id)
            ET.SubElement(xml_greeting, "invoice_nm").text = row.invoice_nm
            ET.SubElement(xml_greeting, "tgl_invoice").text = unicode(row.tgl_invoice)
            ET.SubElement(xml_greeting, "ap_nomor").text = row.ap_nomor
            ET.SubElement(xml_greeting, "ap_nama").text = row.ap_nama
            ET.SubElement(xml_greeting, "ap_rekening").text = row.ap_rekening
            ET.SubElement(xml_greeting, "ap_npwp").text = row.ap_npwp
            ET.SubElement(xml_greeting, "kegiatan_nm").text = row.kegiatan_nm
            ET.SubElement(xml_greeting, "nilai").text = unicode(row.nilai)
            ET.SubElement(xml_greeting, "customer").text = customer
        return self.root

class b103r002Generator(JasperGenerator):
    def __init__(self):
        super(b103r002Generator, self).__init__()
        self.reportname = get_rpath('apbd/tuskpd/R103002.jrxml')
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
        return self.root

class b103r0021Generator(JasperGenerator):
    def __init__(self):
        super(b103r0021Generator, self).__init__()
        self.reportname = get_rpath('apbd/tuskpd/R1030021.jrxml')
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
        return self.root

class b103r0022Generator(JasperGenerator):
    def __init__(self):
        super(b103r0022Generator, self).__init__()
        self.reportname = get_rpath('apbd/tuskpd/R1030022.jrxml')
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
        return self.root

class b103r003Generator(JasperGeneratorWithSubreport):
    def __init__(self):
        self.mainreport = get_rpath('apbd/tuskpd/R103003.jrxml')

        self.subreportlist = []
        self.subreportlist.append(get_rpath('apbd/tuskpd/R103003_subreport1.jrxml'))
        self.subreportlist.append(get_rpath('apbd/tuskpd/R103003_subreport2.jrxml'))
        self.subreportlist.append(get_rpath('apbd/tuskpd/R103003_subreport3.jrxml'))

        self.xpath = '/apbd/spm'
        
        self.root = ET.Element('apbd')

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'spm')
            ET.SubElement(xml_greeting, "spm_id").text = unicode(row.spm_id)
            ET.SubElement(xml_greeting, "spm_kd").text = row.spm_kd
            ET.SubElement(xml_greeting, "spm_nm").text = row.spm_nm
            ET.SubElement(xml_greeting, "spm_tgl").text = unicode(row.spm_tgl)
            ET.SubElement(xml_greeting, "spp_id").text = unicode(row.spp_id)
            ET.SubElement(xml_greeting, "spp_kd").text = row.spp_kd
            ET.SubElement(xml_greeting, "spp_nm").text = row.spp_nm
            ET.SubElement(xml_greeting, "spp_tgl").text = unicode(row.spp_tgl)
            ET.SubElement(xml_greeting, "jenis").text = unicode(row.jenis)
            ET.SubElement(xml_greeting, "bank_nama").text = row.bank_nama
            ET.SubElement(xml_greeting, "bank_account").text = row.bank_account
            ET.SubElement(xml_greeting, "ap_nama").text = row.ap_nama
            ET.SubElement(xml_greeting, "ap_bank").text = row.ap_bank
            ET.SubElement(xml_greeting, "ap_rekening").text = row.ap_rekening
            ET.SubElement(xml_greeting, "ap_npwp").text = row.ap_npwp
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun_id)
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "keg_kd").text = row.keg_kd
            ET.SubElement(xml_greeting, "keg_nm").text = row.keg_nm
            ET.SubElement(xml_greeting, "prg_kd").text = row.prg_kd
            ET.SubElement(xml_greeting, "prg_nm").text = row.prg_nm
            ET.SubElement(xml_greeting, "spd_id").text = unicode(row.spd_id)
            ET.SubElement(xml_greeting, "nilai").text = unicode(row.nilai)
            ET.SubElement(xml_greeting, "ppn").text = unicode(row.ppn)
            ET.SubElement(xml_greeting, "pph").text = unicode(row.pph)
            ET.SubElement(xml_greeting, "potongan").text = unicode(row.potongan)
            ET.SubElement(xml_greeting, "customer").text = customer

            rows = DBSession.query(Rekening.kode, Rekening.nama,
               func.sum(APInvoiceItem.amount).label('jumlah')
               ).filter(Rekening.id==KegiatanItem.rekening_id, 
               KegiatanItem.id==APInvoiceItem.kegiatan_item_id,
               SppItem.ap_invoice_id==APInvoiceItem.ap_invoice_id,
               SppItem.ap_spp_id==row.spp_id, func.substr(Rekening.kode,1,1)=='5'
               ).group_by(Rekening.kode, Rekening.nama
               ).order_by(Rekening.kode)
            for row2 in rows :
                xml_a = ET.SubElement(xml_greeting, "rekening")
                ET.SubElement(xml_a, "rek_kd").text =row2.kode
                ET.SubElement(xml_a, "rek_nm").text =row2.nama
                ET.SubElement(xml_a, "jumlah").text =unicode(row2.jumlah)

            rows1 = DBSession.query(Rekening.kode, Rekening.nama,
               (KegiatanItem.vol_4_1* KegiatanItem.vol_4_2*KegiatanItem.hsat_4).label('jumlah')
               ).filter(Rekening.id==KegiatanItem.rekening_id, 
               KegiatanItem.id==APInvoiceItem.kegiatan_item_id,
               SppItem.ap_invoice_id==APInvoiceItem.ap_invoice_id,
               SppItem.ap_spp_id==row.spp_id, func.substr(Rekening.kode,1,1)=='7'
               ).order_by(Rekening.kode)
            for row3 in rows1 :
                xml_b = ET.SubElement(xml_greeting, "potongan")
                ET.SubElement(xml_b, "rek_kd").text =row3.kode
                ET.SubElement(xml_b, "rek_nm").text =row3.nama
                ET.SubElement(xml_b, "jumlah").text =unicode(row3.jumlah)

            rows2 = DBSession.query(Spd.kode.label('spd_no'), Spd.tanggal.label('spd_tgl'),
               func.sum(SpdItem.nominal).label('spd_jml')
               ).filter(Spd.id==SpdItem.spd_id, 
               Spd.id==row.spd_id
               ).group_by(Spd.kode,Spd.tanggal)
            for row4 in rows2 :
                xml_c = ET.SubElement(xml_greeting, "spd")
                ET.SubElement(xml_c, "spd_no").text =row4.spd_no
                ET.SubElement(xml_c, "spd_tgl").text =unicode(row4.spd_tgl)
                ET.SubElement(xml_c, "spd_jml").text =unicode(row4.spd_jml)

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
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "tgl_invoice").text = unicode(row.tgl_invoice)
            ET.SubElement(xml_greeting, "jenis").text = row.jenis
            ET.SubElement(xml_greeting, "invoice_kd").text = row.invoice_kd
            ET.SubElement(xml_greeting, "kegiatan_nm").text = row.kegiatan_nm
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "jumlah").text = unicode(row.jumlah)
            ET.SubElement(xml_greeting, "customer").text = customer
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
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "tgl_spp").text = unicode(row.tgl_spp)
            ET.SubElement(xml_greeting, "spp_kd").text = row.spp_kd
            ET.SubElement(xml_greeting, "spp_nm").text = row.spp_nm
            ET.SubElement(xml_greeting, "UP").text = unicode(row.UP)
            ET.SubElement(xml_greeting, "GU").text = unicode(row.GU)
            ET.SubElement(xml_greeting, "TU").text = unicode(row.TU)
            ET.SubElement(xml_greeting, "LS_GJ").text = unicode(row.LS_GJ)
            ET.SubElement(xml_greeting, "LS").text = unicode(row.LS)
            ET.SubElement(xml_greeting, "customer").text = customer
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
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "tgl_spp").text = unicode(row.tgl_spp)
            ET.SubElement(xml_greeting, "spp_kd").text = row.spp_kd
            ET.SubElement(xml_greeting, "spp_nm").text = row.spp_nm
            ET.SubElement(xml_greeting, "UP").text = unicode(row.UP)
            ET.SubElement(xml_greeting, "GU").text = unicode(row.GU)
            ET.SubElement(xml_greeting, "TU").text = unicode(row.TU)
            ET.SubElement(xml_greeting, "LS_GJ").text = unicode(row.LS_GJ)
            ET.SubElement(xml_greeting, "LS").text = unicode(row.LS)
            ET.SubElement(xml_greeting, "customer").text = customer
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
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "tgl_spp").text = unicode(row.tgl_spp)
            ET.SubElement(xml_greeting, "spp_kd").text = row.spp_kd
            ET.SubElement(xml_greeting, "spp_nm").text = row.spp_nm
            ET.SubElement(xml_greeting, "UP").text = unicode(row.UP)
            ET.SubElement(xml_greeting, "GU").text = unicode(row.GU)
            ET.SubElement(xml_greeting, "TU").text = unicode(row.TU)
            ET.SubElement(xml_greeting, "LS").text = unicode(row.LS)
            ET.SubElement(xml_greeting, "customer").text = customer
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
        return self.root 

class b104r300Generator(JasperGenerator):
    def __init__(self):
        super(b104r300Generator, self).__init__()
        self.reportname = get_rpath('apbd/tuskpd/R104300.jrxml')
        self.xpath = '/apbd/spj'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'spj')
            ET.SubElement(xml_greeting, "urusan_kd").text = row.urusan_kd
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "program_kd").text = row.program_kd
            ET.SubElement(xml_greeting, "keg_kd").text = row.keg_kd
            ET.SubElement(xml_greeting, "keg_nm").text = row.keg_nm
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "anggaran").text = unicode(row.anggaran)
            ET.SubElement(xml_greeting, "LSG_lalu").text = unicode(row.LSG_lalu)
            ET.SubElement(xml_greeting, "LSG_kini").text = unicode(row.LSG_kini)
            ET.SubElement(xml_greeting, "LS_lalu").text = unicode(row.LS_lalu)
            ET.SubElement(xml_greeting, "LS_kini").text = unicode(row.LS_kini)
            ET.SubElement(xml_greeting, "Lain_lalu").text = unicode(row.Lain_lalu)
            ET.SubElement(xml_greeting, "Lain_kini").text = unicode(row.Lain_kini)
            ET.SubElement(xml_greeting, "bulan").text = unicode(bulan)
            ET.SubElement(xml_greeting, "customer").text = customer
        return self.root 

class b104r400Generator(JasperGenerator):
    def __init__(self):
        super(b104r400Generator, self).__init__()
        self.reportname = get_rpath('apbd/tuskpd/R104400.jrxml')
        self.xpath = '/apbd/spj'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'spj')
            ET.SubElement(xml_greeting, "urusan_kd").text = row.urusan_kd
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "program_kd").text = row.program_kd
            ET.SubElement(xml_greeting, "keg_kd").text = row.keg_kd
            ET.SubElement(xml_greeting, "keg_nm").text = row.keg_nm
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "anggaran").text = unicode(row.anggaran)
            ET.SubElement(xml_greeting, "LSG_lalu").text = unicode(row.LSG_lalu)
            ET.SubElement(xml_greeting, "LSG_kini").text = unicode(row.LSG_kini)
            ET.SubElement(xml_greeting, "LS_lalu").text = unicode(row.LS_lalu)
            ET.SubElement(xml_greeting, "LS_kini").text = unicode(row.LS_kini)
            ET.SubElement(xml_greeting, "Lain_lalu").text = unicode(row.Lain_lalu)
            ET.SubElement(xml_greeting, "Lain_kini").text = unicode(row.Lain_kini)
            ET.SubElement(xml_greeting, "bulan").text = unicode(bulan)
            ET.SubElement(xml_greeting, "customer").text = customer
        return self.root 

