import os
import unittest
import os.path
import uuid
import urlparse

from osipkd.tools import row2dict, xls_reader

from datetime import datetime
#from sqlalchemy import not_, func, case
from sqlalchemy import *
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
        return Terbilang(u) + f + Terbilang(t)
    else:
        v = y[-12:]
        w = y[:-12]
        return Terbilang(w) + g + Terbilang(v)

class ViewAKPPKDLap(BaseViews):
    def __init__(self, context, request):
        global customer
        global logo
        BaseViews.__init__(self, context, request)
        self.app = 'akppkd'

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
        
    # LAPORAN AKUNTANSI SKPD
    @view_config(route_name="ak-report-skpd", renderer="templates/ak-report/ak-report-skpd.pt", permission="read")
    def ak_report_skpd(self):
        params = self.request.params
        return dict(datas=self.datas,)

    @view_config(route_name="ak-report-skpd-act", renderer="json", permission="read")
    def ak_report_skpd_act(self):
        global mulai, selesai, tingkat, tahun_lalu, bulan
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
        bulan   = 'bulan' in params and params['bulan'] or 0
        print "TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT", tahun_lalu
          
        if url_dict['act']=='bb' :
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
              subq1 = DBSession.query(Unit.nama.label('unit_nm'), Sap.kode.label('subrek_kd'), Sap.nama.label('rek_nm'), 
                 AkJurnalItem.amount.label('amount_kini'), AkJurnal.tahun_id.label('tahun_kini'),
                 literal_column('0').label('amount_lalu'), literal_column(str(tahun_lalu)).label('tahun_lalu'),
                 ).filter(AkJurnalItem.sap_id==Sap.id, AkJurnalItem.ak_jurnal_id==AkJurnal.id, 
                 AkJurnal.unit_id==Unit.id, AkJurnal.is_skpd==1,
                 #AkJurnalItem.amount>0, 
                 AkJurnal.tahun_id==self.session['tahun'], AkJurnal.unit_id==self.session['unit_id']
                 )
              subq2 = DBSession.query(Unit.nama.label('unit_nm'),Sap.kode.label('subrek_kd'), Sap.nama.label('rek_nm'), 
                 literal_column('0').label('amount_kini'), literal_column(str(tahun_kini)).label('tahun_kini'),
                 AkJurnalItem.amount.label('amount_lalu'), AkJurnal.tahun_id.label('tahun_lalu'),
                 ).filter(AkJurnalItem.sap_id==Sap.id, AkJurnalItem.ak_jurnal_id==AkJurnal.id, 
                 AkJurnal.unit_id==Unit.id, AkJurnal.is_skpd==1,
                 #AkJurnalItem.amount>0, 
                 AkJurnal.tahun_id==tahun_lalu, AkJurnal.unit_id==self.session['unit_id']
                 )
                 
              subq = subq1.union(subq2).subquery()
              
              query = DBSession.query(Sap.kode, Sap.nama, Sap.level_id, subq.c.unit_nm, subq.c.tahun_kini, subq.c.tahun_lalu,
                 func.sum(subq.c.amount_kini).label('amount_kini'), func.sum(subq.c.amount_lalu).label('amount_lalu')
                 ).filter(Sap.kode==func.left(subq.c.subrek_kd, func.length(Sap.kode)),
                 func.substr(Sap.kode,1,1).in_(['4','5','6']) 
                 ).group_by(Sap.kode, Sap.nama, Sap.level_id, subq.c.unit_nm, subq.c.tahun_kini, subq.c.tahun_lalu,
                 ).order_by(Sap.kode)
              
              generator = b105r022Generator()
              pdf = generator.generate(query)
              response=req.response
              response.content_type="application/pdf"
              response.content_disposition='filename=output.pdf' 
              response.write(pdf)
              return response
              
        elif url_dict['act']=='psal' :
            q1 = DBSession.query(Unit.nama.label('unit_nm'), literal_column('1').label('urut'),
               literal_column("'Saldo Anggaran Lebih Awal'").label('nama'),
               AkJurnal.tahun_id.label('tahun_kini'), literal_column(str(tahun_lalu)).label('tahun_lalu'),
               literal_column('0').label('amount_kini'), literal_column('0').label('amount_lalu')
               ).filter(AkJurnal.unit_id==Unit.id, AkJurnal.is_skpd==1,
               AkJurnal.tahun_id==self.session['tahun'], AkJurnal.unit_id==self.session['unit_id']
               ).group_by(Unit.nama, AkJurnal.tahun_id
               )
            q2 = DBSession.query(Unit.nama.label('unit_nm'), literal_column('2').label('urut'),
               literal_column("'Penggunaan SAL sebagai Penerimaan Tahun Berjalan'").label('nama'),
               AkJurnal.tahun_id.label('tahun_kini'), literal_column(str(tahun_lalu)).label('tahun_lalu'),
               literal_column('0').label('amount_kini'), literal_column('0').label('amount_lalu')
               ).filter(AkJurnal.unit_id==Unit.id, AkJurnal.is_skpd==1,
               AkJurnal.tahun_id==self.session['tahun'], AkJurnal.unit_id==self.session['unit_id']
               ).group_by(Unit.nama, AkJurnal.tahun_id
               )
            q3 = DBSession.query(Unit.nama.label('unit_nm'), literal_column('3').label('urut'),
               literal_column("'Koreksi Kesalahan Pembukuan Tahun Sebelumnya'").label('nama'),
               AkJurnal.tahun_id.label('tahun_kini'), literal_column(str(tahun_lalu)).label('tahun_lalu'),
               literal_column('0').label('amount_kini'), literal_column('0').label('amount_lalu')
               ).filter(AkJurnal.unit_id==Unit.id, AkJurnal.is_skpd==1,
               AkJurnal.tahun_id==self.session['tahun'], AkJurnal.unit_id==self.session['unit_id']
               ).group_by(Unit.nama, AkJurnal.tahun_id
               )
            q4 = DBSession.query(Unit.nama.label('unit_nm'), literal_column('4').label('urut'),
               literal_column("'Lain-lain'").label('nama'),
               AkJurnal.tahun_id.label('tahun_kini'), literal_column(str(tahun_lalu)).label('tahun_lalu'),
               literal_column('0').label('amount_kini'), literal_column('0').label('amount_lalu')
               ).filter(AkJurnal.unit_id==Unit.id, AkJurnal.is_skpd==1,
               AkJurnal.tahun_id==self.session['tahun'], AkJurnal.unit_id==self.session['unit_id']
               ).group_by(Unit.nama, AkJurnal.tahun_id
               )
               
            subq = q1.union(q2,q3,q4).subquery()
            
            query = DBSession.query(subq.c.unit_nm.label('unit_nm'), subq.c.urut.label('urut'), 
               subq.c.nama.label('nama'), subq.c.tahun_kini.label('tahun_kini'), subq.c.tahun_lalu.label('tahun_lalu'),
               subq.c.amount_kini.label('amount_kini'), subq.c.amount_lalu.label('amount_lalu')
               ).order_by(subq.c.urut)
               
            generator = b105r032Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
            
        elif url_dict['act']=='lo' :
              subq1 = DBSession.query(Unit.nama.label('unit_nm'), Sap.kode.label('subrek_kd'), Sap.nama.label('rek_nm'), 
                 AkJurnalItem.amount.label('amount_kini'), AkJurnal.tahun_id.label('tahun_kini'),
                 literal_column('0').label('amount_lalu'), literal_column(str(tahun_lalu)).label('tahun_lalu'),
                 ).filter(AkJurnalItem.sap_id==Sap.id, AkJurnalItem.ak_jurnal_id==AkJurnal.id, 
                 AkJurnal.unit_id==Unit.id, AkJurnal.is_skpd==1,
                 #AkJurnalItem.amount>0, 
                 AkJurnal.tahun_id==self.session['tahun'], AkJurnal.unit_id==self.session['unit_id']
                 )
              subq2 = DBSession.query(Unit.nama.label('unit_nm'),Sap.kode.label('subrek_kd'), Sap.nama.label('rek_nm'), 
                 literal_column('0').label('amount_kini'), literal_column(str(tahun_kini)).label('tahun_kini'),
                 AkJurnalItem.amount.label('amount_lalu'), AkJurnal.tahun_id.label('tahun_lalu'),
                 ).filter(AkJurnalItem.sap_id==Sap.id, AkJurnalItem.ak_jurnal_id==AkJurnal.id, 
                 AkJurnal.unit_id==Unit.id, AkJurnal.is_skpd==1,
                 #AkJurnalItem.amount>0, 
                 AkJurnal.tahun_id==tahun_lalu, AkJurnal.unit_id==self.session['unit_id']
                 )
                 
              subq = subq1.union(subq2).subquery()
              
              query = DBSession.query(Sap.kode, Sap.nama, Sap.level_id, subq.c.unit_nm, subq.c.tahun_kini, subq.c.tahun_lalu,
                 func.sum(subq.c.amount_kini).label('amount_kini'), func.sum(subq.c.amount_lalu).label('amount_lalu')
                 ).filter(Sap.kode==func.left(subq.c.subrek_kd, func.length(Sap.kode)),
                 func.substr(Sap.kode,1,1).in_(['8','9']) 
                 ).group_by(Sap.kode, Sap.nama, Sap.level_id, subq.c.unit_nm, subq.c.tahun_kini, subq.c.tahun_lalu,
                 ).order_by(Sap.kode)
              
              generator = b105r052Generator()
              pdf = generator.generate(query)
              response=req.response
              response.content_type="application/pdf"
              response.content_disposition='filename=output.pdf' 
              response.write(pdf)
              return response

        elif url_dict['act']=='neraca' :
              subq1 = DBSession.query(Unit.nama.label('unit_nm'), Sap.kode.label('subrek_kd'), Sap.nama.label('rek_nm'), 
                 AkJurnalItem.amount.label('amount_kini'), AkJurnal.tahun_id.label('tahun_kini'),
                 literal_column('0').label('amount_lalu'), literal_column(str(tahun_lalu)).label('tahun_lalu'),
                 ).filter(AkJurnalItem.sap_id==Sap.id, AkJurnalItem.ak_jurnal_id==AkJurnal.id, 
                 AkJurnal.unit_id==Unit.id, AkJurnal.is_skpd==1,
                 #AkJurnalItem.amount>0, 
                 AkJurnal.tahun_id==self.session['tahun'], AkJurnal.unit_id==self.session['unit_id']
                 )
              subq2 = DBSession.query(Unit.nama.label('unit_nm'),Sap.kode.label('subrek_kd'), Sap.nama.label('rek_nm'), 
                 literal_column('0').label('amount_kini'), literal_column(str(tahun_kini)).label('tahun_kini'),
                 AkJurnalItem.amount.label('amount_lalu'), AkJurnal.tahun_id.label('tahun_lalu'),
                 ).filter(AkJurnalItem.sap_id==Sap.id, AkJurnalItem.ak_jurnal_id==AkJurnal.id, 
                 AkJurnal.unit_id==Unit.id, AkJurnal.is_skpd==1,
                 #AkJurnalItem.amount>0, 
                 AkJurnal.tahun_id==tahun_lalu, AkJurnal.unit_id==self.session['unit_id']
                 )
                 
              subq = subq1.union(subq2).subquery()
              
              query = DBSession.query(Sap.kode, Sap.nama, Sap.level_id, subq.c.unit_nm, subq.c.tahun_kini, subq.c.tahun_lalu,
                 func.sum(subq.c.amount_kini).label('amount_kini'), func.sum(subq.c.amount_lalu).label('amount_lalu')
                 ).filter(Sap.kode==func.left(subq.c.subrek_kd, func.length(Sap.kode)),
                 func.substr(Sap.kode,1,1).in_(['1','2','3']), Sap.level_id<4 
                 ).group_by(Sap.kode, Sap.nama, Sap.level_id, subq.c.unit_nm, subq.c.tahun_kini, subq.c.tahun_lalu,
                 ).order_by(Sap.kode)
              
              generator = b105r042Generator()
              pdf = generator.generate(query)
              response=req.response
              response.content_type="application/pdf"
              response.content_disposition='filename=output.pdf' 
              response.write(pdf)
              return response

        elif url_dict['act']=='le' :
            q1 = DBSession.query(Unit.nama.label('unit_nm'), literal_column('1').label('urut'),
               literal_column("'Ekuitas Awal Tahun'").label('nama'),
               AkJurnal.tahun_id.label('tahun'), 
               literal_column('0').label('amount')
               ).filter(AkJurnal.unit_id==Unit.id, AkJurnal.is_skpd==1,
               AkJurnal.tahun_id==self.session['tahun'], AkJurnal.unit_id==self.session['unit_id']
               ).group_by(Unit.nama, AkJurnal.tahun_id
               )
            q2 = DBSession.query(Unit.nama.label('unit_nm'), literal_column('2').label('urut'),
               literal_column("'Surplus Operasional'").label('nama'),
               AkJurnal.tahun_id.label('tahun'), 
               literal_column('0').label('amount')
               ).filter(AkJurnal.unit_id==Unit.id, AkJurnal.is_skpd==1,
               AkJurnal.tahun_id==self.session['tahun'], AkJurnal.unit_id==self.session['unit_id']
               ).group_by(Unit.nama, AkJurnal.tahun_id
               )
            q3 = DBSession.query(Unit.nama.label('unit_nm'), literal_column('3').label('urut'),
               literal_column("'Ekuitas Akhir Tahun'").label('nama'),
               AkJurnal.tahun_id.label('tahun'), 
               literal_column('0').label('amount')
               ).filter(AkJurnal.unit_id==Unit.id, AkJurnal.is_skpd==1,
               AkJurnal.tahun_id==self.session['tahun'], AkJurnal.unit_id==self.session['unit_id']
               ).group_by(Unit.nama, AkJurnal.tahun_id
               )
               
            subq = q1.union(q2,q3).subquery()
            
            query = DBSession.query(subq.c.unit_nm.label('unit_nm'), subq.c.urut.label('urut'), 
               subq.c.nama.label('nama'), subq.c.tahun.label('tahun'),
               subq.c.amount.label('amount')
               ).order_by(subq.c.urut)
               
            generator = b105r062Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
            
        elif url_dict['act']=='ro' :
              subq1 = DBSession.query(Unit.nama.label('unit_nm'), Sap.kode.label('subrek_kd'), Sap.nama.label('rek_nm'), 
                 AkJurnalItem.amount.label('amount_kini'), AkJurnal.tahun_id.label('tahun_kini'),
                 literal_column('0').label('amount_lalu'), literal_column(str(tahun_lalu)).label('tahun_lalu'),
                 ).filter(AkJurnalItem.sap_id==Sap.id, AkJurnalItem.ak_jurnal_id==AkJurnal.id, 
                 AkJurnal.unit_id==Unit.id, AkJurnal.is_skpd==1,
                 #AkJurnalItem.amount>0, 
                 AkJurnal.tahun_id==self.session['tahun'], AkJurnal.unit_id==self.session['unit_id']
                 )
              subq2 = DBSession.query(Unit.nama.label('unit_nm'),Sap.kode.label('subrek_kd'), Sap.nama.label('rek_nm'), 
                 literal_column('0').label('amount_kini'), literal_column(str(tahun_kini)).label('tahun_kini'),
                 AkJurnalItem.amount.label('amount_lalu'), AkJurnal.tahun_id.label('tahun_lalu'),
                 ).filter(AkJurnalItem.sap_id==Sap.id, AkJurnalItem.ak_jurnal_id==AkJurnal.id, 
                 AkJurnal.unit_id==Unit.id, AkJurnal.is_skpd==1,
                 #AkJurnalItem.amount>0, 
                 AkJurnal.tahun_id==tahun_lalu, AkJurnal.unit_id==self.session['unit_id']
                 )
                 
              subq = subq1.union(subq2).subquery()
              
              query = DBSession.query(Sap.kode, Sap.nama, Sap.level_id, subq.c.unit_nm, subq.c.tahun_kini, subq.c.tahun_lalu,
                 func.sum(subq.c.amount_kini).label('amount_kini'), func.sum(subq.c.amount_lalu).label('amount_lalu')
                 ).filter(Sap.kode==func.left(subq.c.subrek_kd, func.length(Sap.kode)),
                 func.substr(Sap.kode,1,1).in_(['1','2','3'])
                 ).group_by(Sap.kode, Sap.nama, Sap.level_id, subq.c.unit_nm, subq.c.tahun_kini, subq.c.tahun_lalu,
                 ).order_by(Sap.kode)
              
              generator = b105r042Generator()
              pdf = generator.generate(query)
              response=req.response
              response.content_type="application/pdf"
              response.content_disposition='filename=output.pdf' 
              response.write(pdf)
              return response
              
        ### Jurnal pendapatan SKPD
        elif url_dict['act']=='jurnal1' :
              query = DBSession.query(Unit.nama.label('unit_nm'), AkJurnal.tanggal, AkJurnal.source,
                 AkJurnal.source_no, AkJurnal.tahun_id, AkJurnal.periode, AkJurnalItem.amount,
                 Sap.kode.label('rek_kd'), Sap.nama.label('rek_nm')
                 ).filter(AkJurnal.unit_id==Unit.id, AkJurnal.id==AkJurnalItem.ak_jurnal_id, 
                 AkJurnalItem.sap_id==Sap.id, 
                 AkJurnal.is_skpd==1, AkJurnal.jv_type==1,
                 AkJurnal.tahun_id==self.session['tahun'], AkJurnal.unit_id==self.session['unit_id'], 
                 AkJurnal.periode==bulan
                 ).order_by(AkJurnal.tanggal, AkJurnalItem.id)
              
              generator = b105r101Generator()
              pdf = generator.generate(query)
              response=req.response
              response.content_type="application/pdf"
              response.content_disposition='filename=output.pdf' 
              response.write(pdf)
              return response

        ### Jurnal penerimaan SKPD
        elif url_dict['act']=='jurnal2' :
              query = DBSession.query(Unit.nama.label('unit_nm'), AkJurnal.tanggal, AkJurnal.source,
                 AkJurnal.source_no, AkJurnal.tahun_id, AkJurnal.periode, AkJurnalItem.amount,
                 AkJurnal.kode, AkJurnal.nama
                 ).filter(AkJurnal.unit_id==Unit.id, AkJurnal.id==AkJurnalItem.ak_jurnal_id, 
                 AkJurnal.is_skpd==1, AkJurnal.jv_type==1, AkJurnalItem.amount>0,
                 AkJurnal.tahun_id==self.session['tahun'], AkJurnal.unit_id==self.session['unit_id'], 
                 AkJurnal.periode==bulan
                 ).order_by(AkJurnal.tanggal, AkJurnalItem.id)
              
              generator = b105r102Generator()
              pdf = generator.generate(query)
              response=req.response
              response.content_type="application/pdf"
              response.content_disposition='filename=output.pdf' 
              response.write(pdf)
              return response
              
        ### Jurnal BELANJA SKPD UP/TU/GU
        elif url_dict['act']=='jurnal3' :
              query = DBSession.query(Unit.nama.label('unit_nm'), AkJurnal.tanggal, AkJurnal.source,
                 AkJurnal.source_no, AkJurnal.tahun_id, AkJurnal.periode, AkJurnalItem.amount,
                 Sap.kode.label('rek_kd'), Sap.nama.label('rek_nm')
                 ).filter(AkJurnal.unit_id==Unit.id, AkJurnal.id==AkJurnalItem.ak_jurnal_id, 
                 AkJurnalItem.sap_id==Sap.id, AkJurnal.source.in_(('SP2D-GU','Tagihan-GU','SP2D-TU','Tagihan-TU','SP2D-UP','Tagihan-UP')),
                 AkJurnal.is_skpd==1, AkJurnal.jv_type==2,
                 AkJurnal.tahun_id==self.session['tahun'], AkJurnal.unit_id==self.session['unit_id'], 
                 AkJurnal.periode==bulan
                 ).order_by(AkJurnal.tanggal, AkJurnalItem.id)
              
              generator = b105r103Generator()
              pdf = generator.generate(query)
              response=req.response
              response.content_type="application/pdf"
              response.content_disposition='filename=output.pdf' 
              response.write(pdf)
              return response
              
        ### Jurnal BELANJA LS
        elif url_dict['act']=='jurnal4' :
              query = DBSession.query(Unit.nama.label('unit_nm'), AkJurnal.tanggal, AkJurnal.source,
                 AkJurnal.source_no, AkJurnal.tahun_id, AkJurnal.periode, AkJurnalItem.amount,
                 Sap.kode.label('rek_kd'), Sap.nama.label('rek_nm')
                 ).filter(AkJurnal.unit_id==Unit.id, AkJurnal.id==AkJurnalItem.ak_jurnal_id, 
                 AkJurnalItem.sap_id==Sap.id, AkJurnal.source.in_(('SP2D-LS','Tagihan-LS')),
                 AkJurnal.is_skpd==1, AkJurnal.jv_type==2,
                 AkJurnal.tahun_id==self.session['tahun'], AkJurnal.unit_id==self.session['unit_id'], 
                 AkJurnal.periode==bulan
                 ).order_by(AkJurnal.tanggal, AkJurnalItem.id)
              
              generator = b105r104Generator()
              pdf = generator.generate(query)
              response=req.response
              response.content_type="application/pdf"
              response.content_disposition='filename=output.pdf' 
              response.write(pdf)
              return response
              
        ### Jurnal UMUM
        elif url_dict['act']=='jurnal5' :
              query = DBSession.query(Unit.nama.label('unit_nm'), AkJurnal.tanggal, AkJurnal.source,
                 AkJurnal.source_no, AkJurnal.tahun_id, AkJurnal.periode, 
                 case([(AkJurnalItem.amount>0,AkJurnalItem.amount)], else_=0).label('debet'),
                 case([(AkJurnalItem.amount<0,AkJurnalItem.amount)], else_=0).label('kredit'),
                 AkJurnalItem.amount,
                 Sap.kode.label('rek_kd'), Sap.nama.label('rek_nm')
                 ).filter(AkJurnal.unit_id==Unit.id, AkJurnal.id==AkJurnalItem.ak_jurnal_id, 
                 AkJurnalItem.sap_id==Sap.id, 
                 AkJurnal.is_skpd==1, AkJurnal.jv_type==3,
                 AkJurnal.tahun_id==self.session['tahun'], AkJurnal.unit_id==self.session['unit_id'], 
                 AkJurnal.periode==bulan
                 ).order_by(AkJurnal.tanggal, AkJurnalItem.id)
              
              generator = b105r105Generator()
              pdf = generator.generate(query)
              response=req.response
              response.content_type="application/pdf"
              response.content_disposition='filename=output.pdf' 
              response.write(pdf)
              return response
              
        ### Jurnal Gabungan
        elif url_dict['act']=='jurnal6' :
              query = DBSession.query(Unit.nama.label('unit_nm'), AkJurnal.tanggal, AkJurnal.source,
                 AkJurnal.source_no, AkJurnal.tahun_id, AkJurnal.periode, 
                 case([(AkJurnalItem.amount>0,AkJurnalItem.amount)], else_=0).label('debet'),
                 case([(AkJurnalItem.amount<0,AkJurnalItem.amount)], else_=0).label('kredit'),
                 AkJurnalItem.amount,
                 Sap.kode.label('rek_kd'), Sap.nama.label('rek_nm')
                 ).filter(AkJurnal.unit_id==Unit.id, AkJurnal.id==AkJurnalItem.ak_jurnal_id, 
                 AkJurnalItem.sap_id==Sap.id, 
                 AkJurnal.is_skpd==1, 
                 AkJurnal.tahun_id==self.session['tahun'], AkJurnal.unit_id==self.session['unit_id'], 
                 AkJurnal.periode==bulan
                 ).order_by(AkJurnal.tanggal, AkJurnalItem.id)
              
              generator = b105r106Generator()
              pdf = generator.generate(query)
              response=req.response
              response.content_type="application/pdf"
              response.content_disposition='filename=output.pdf' 
              response.write(pdf)
              return response
              
    # LAPORAN AKUNTANSI PPKD
    @view_config(route_name="ak-report-ppkd", renderer="templates/ak-report/ak-report-ppkd.pt", permission="read")
    def ak_report_ppkd(self):
        params = self.request.params
        return dict(datas=self.datas,)

    @view_config(route_name="ak-report-ppkd-act", renderer="json", permission="read")
    def ak_report_ppkd_act(self):
        global mulai, selesai, tingkat, tahun_lalu, bulan
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
        bulan   = 'bulan' in params and params['bulan'] or 0
        print "TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT", tahun_lalu
          
        if url_dict['act']=='bb' :
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

        elif url_dict['act']=='lrasap' :
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
               func.substr(Sap.kode,1,1).in_(['4','5','6']) 
               ).group_by(Sap.kode, Sap.nama, Sap.level_id, subq.c.unit_nm, subq.c.tahun_kini, subq.c.tahun_lalu,
               ).order_by(Sap.kode)
               
            generator = b105r021Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
              
        elif url_dict['act']=='psal' :
            q1 = DBSession.query(Unit.nama.label('unit_nm'), literal_column('1').label('urut'),
               literal_column("'Saldo Anggaran Lebih Awal'").label('nama'),
               AkJurnal.tahun_id.label('tahun_kini'), literal_column(str(tahun_lalu)).label('tahun_lalu'),
               literal_column('0').label('amount_kini'), literal_column('0').label('amount_lalu')
               ).filter(AkJurnal.unit_id==Unit.id, AkJurnal.is_skpd==0,
               AkJurnal.tahun_id==self.session['tahun'], AkJurnal.unit_id==self.session['unit_id']
               ).group_by(Unit.nama, AkJurnal.tahun_id
               )
            q2 = DBSession.query(Unit.nama.label('unit_nm'), literal_column('2').label('urut'),
               literal_column("'Penggunaan SAL sebagai Penerimaan Tahun Berjalan'").label('nama'),
               AkJurnal.tahun_id.label('tahun_kini'), literal_column(str(tahun_lalu)).label('tahun_lalu'),
               literal_column('0').label('amount_kini'), literal_column('0').label('amount_lalu')
               ).filter(AkJurnal.unit_id==Unit.id, AkJurnal.is_skpd==0,
               AkJurnal.tahun_id==self.session['tahun'], AkJurnal.unit_id==self.session['unit_id']
               ).group_by(Unit.nama, AkJurnal.tahun_id
               )
            q3 = DBSession.query(Unit.nama.label('unit_nm'), literal_column('3').label('urut'),
               literal_column("'Koreksi Kesalahan Pembukuan Tahun Sebelumnya'").label('nama'),
               AkJurnal.tahun_id.label('tahun_kini'), literal_column(str(tahun_lalu)).label('tahun_lalu'),
               literal_column('0').label('amount_kini'), literal_column('0').label('amount_lalu')
               ).filter(AkJurnal.unit_id==Unit.id, AkJurnal.is_skpd==0,
               AkJurnal.tahun_id==self.session['tahun'], AkJurnal.unit_id==self.session['unit_id']
               ).group_by(Unit.nama, AkJurnal.tahun_id
               )
            q4 = DBSession.query(Unit.nama.label('unit_nm'), literal_column('4').label('urut'),
               literal_column("'Lain-lain'").label('nama'),
               AkJurnal.tahun_id.label('tahun_kini'), literal_column(str(tahun_lalu)).label('tahun_lalu'),
               literal_column('0').label('amount_kini'), literal_column('0').label('amount_lalu')
               ).filter(AkJurnal.unit_id==Unit.id, AkJurnal.is_skpd==0,
               AkJurnal.tahun_id==self.session['tahun'], AkJurnal.unit_id==self.session['unit_id']
               ).group_by(Unit.nama, AkJurnal.tahun_id
               )
               
            subq = q1.union(q2,q3,q4).subquery()
            
            query = DBSession.query(subq.c.unit_nm.label('unit_nm'), subq.c.urut.label('urut'), 
               subq.c.nama.label('nama'), subq.c.tahun_kini.label('tahun_kini'), subq.c.tahun_lalu.label('tahun_lalu'),
               subq.c.amount_kini.label('amount_kini'), subq.c.amount_lalu.label('amount_lalu')
               ).order_by(subq.c.urut)
               
            generator = b105r031Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
            
        elif url_dict['act']=='neraca' :
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
               func.substr(Sap.kode,1,1).in_(['1','2','3']), Sap.level_id<4
               ).group_by(Sap.kode, Sap.nama, Sap.level_id, subq.c.unit_nm, subq.c.tahun_kini, subq.c.tahun_lalu,
               ).order_by(Sap.kode)
               
            generator = b105r041Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        elif url_dict['act']=='lo' :
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
               func.substr(Sap.kode,1,1).in_(['8','9']) 
               ).group_by(Sap.kode, Sap.nama, Sap.level_id, subq.c.unit_nm, subq.c.tahun_kini, subq.c.tahun_lalu,
               ).order_by(Sap.kode)
               
            generator = b105r051Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        elif url_dict['act']=='le' :
            q1 = DBSession.query(Unit.nama.label('unit_nm'), literal_column('1').label('urut'),
               literal_column("'Ekuitas Awal Tahun'").label('nama'),
               AkJurnal.tahun_id.label('tahun'), 
               literal_column('0').label('amount')
               ).filter(AkJurnal.unit_id==Unit.id, AkJurnal.is_skpd==0,
               AkJurnal.tahun_id==self.session['tahun'], AkJurnal.unit_id==self.session['unit_id']
               ).group_by(Unit.nama, AkJurnal.tahun_id
               )
            q2 = DBSession.query(Unit.nama.label('unit_nm'), literal_column('2').label('urut'),
               literal_column("'Surplus Operasional'").label('nama'),
               AkJurnal.tahun_id.label('tahun'), 
               literal_column('0').label('amount')
               ).filter(AkJurnal.unit_id==Unit.id, AkJurnal.is_skpd==0,
               AkJurnal.tahun_id==self.session['tahun'], AkJurnal.unit_id==self.session['unit_id']
               ).group_by(Unit.nama, AkJurnal.tahun_id
               )
            q3 = DBSession.query(Unit.nama.label('unit_nm'), literal_column('3').label('urut'),
               literal_column("'Ekuitas Akhir Tahun'").label('nama'),
               AkJurnal.tahun_id.label('tahun'), 
               literal_column('0').label('amount')
               ).filter(AkJurnal.unit_id==Unit.id, AkJurnal.is_skpd==0,
               AkJurnal.tahun_id==self.session['tahun'], AkJurnal.unit_id==self.session['unit_id']
               ).group_by(Unit.nama, AkJurnal.tahun_id
               )
               
            subq = q1.union(q2,q3).subquery()
            
            query = DBSession.query(subq.c.unit_nm.label('unit_nm'), subq.c.urut.label('urut'), 
               subq.c.nama.label('nama'), subq.c.tahun.label('tahun'),
               subq.c.amount.label('amount')
               ).order_by(subq.c.urut)
               
            generator = b105r061Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
            
        elif url_dict['act']=='ro' :
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
               func.substr(Sap.kode,1,1).in_(['1','2','3']) 
               ).group_by(Sap.kode, Sap.nama, Sap.level_id, subq.c.unit_nm, subq.c.tahun_kini, subq.c.tahun_lalu,
               ).order_by(Sap.kode)
               
            generator = b105r041Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
            
        ### Jurnal penerimaan PPKD
        elif url_dict['act']=='jurnal1' :
              query = DBSession.query(Unit.nama.label('unit_nm'), AkJurnal.tanggal, AkJurnal.source,
                 AkJurnal.source_no, AkJurnal.tahun_id, AkJurnal.periode, AkJurnalItem.amount,
                 AkJurnal.kode, AkJurnal.nama
                 ).filter(AkJurnal.unit_id==Unit.id, AkJurnal.id==AkJurnalItem.ak_jurnal_id, 
                 AkJurnal.is_skpd==0, AkJurnal.jv_type==1, AkJurnalItem.amount>0,
                 AkJurnal.tahun_id==self.session['tahun'], AkJurnal.unit_id==self.session['unit_id'], 
                 AkJurnal.periode==bulan
                 ).order_by(AkJurnal.tanggal, AkJurnalItem.id)
              
              generator = b105r201Generator()
              pdf = generator.generate(query)
              response=req.response
              response.content_type="application/pdf"
              response.content_disposition='filename=output.pdf' 
              response.write(pdf)
              return response

        ### Jurnal Pengeluaran PPKD
        elif url_dict['act']=='jurnal2' :
              query = DBSession.query(Unit.nama.label('unit_nm'), AkJurnal.tanggal, AkJurnal.source,
                 AkJurnal.source_no, AkJurnal.tahun_id, AkJurnal.periode, AkJurnalItem.amount,
                 AkJurnal.kode, AkJurnal.nama
                 ).filter(AkJurnal.unit_id==Unit.id, AkJurnal.id==AkJurnalItem.ak_jurnal_id, 
                 AkJurnal.is_skpd==0, AkJurnal.jv_type==2, AkJurnalItem.amount>0,
                 AkJurnal.tahun_id==self.session['tahun'], AkJurnal.unit_id==self.session['unit_id'], 
                 AkJurnal.periode==bulan
                 ).order_by(AkJurnal.tanggal, AkJurnalItem.id)
              
              generator = b105r202Generator()
              pdf = generator.generate(query)
              response=req.response
              response.content_type="application/pdf"
              response.content_disposition='filename=output.pdf' 
              response.write(pdf)
              return response
              
        ### Jurnal Kas PPKD
        elif url_dict['act']=='jurnal3' :
              query = DBSession.query(Unit.nama.label('unit_nm'), AkJurnal.tanggal, AkJurnal.source,
                 AkJurnal.source_no, AkJurnal.tahun_id, AkJurnal.periode, 
                 case([(AkJurnalItem.amount>0,AkJurnalItem.amount)], else_=0).label('debet'),
                 case([(AkJurnalItem.amount<0,AkJurnalItem.amount)], else_=0).label('kredit'),
                 AkJurnalItem.amount,
                 Sap.kode.label('rek_kd'), Sap.nama.label('rek_nm')
                 ).filter(AkJurnal.unit_id==Unit.id, AkJurnal.id==AkJurnalItem.ak_jurnal_id, 
                 AkJurnalItem.sap_id==Sap.id, 
                 AkJurnal.is_skpd==0, 
                 AkJurnal.tahun_id==self.session['tahun'], AkJurnal.unit_id==self.session['unit_id'], 
                 AkJurnal.periode==bulan
                 ).order_by(AkJurnal.tanggal, AkJurnalItem.id)
              
              generator = b105r203Generator()
              pdf = generator.generate(query)
              response=req.response
              response.content_type="application/pdf"
              response.content_disposition='filename=output.pdf' 
              response.write(pdf)
              return response
              
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

class b105r031Generator(JasperGenerator):
    def __init__(self):
        super(b105r031Generator, self).__init__()
        self.reportname = get_rpath('apbd/tuskpd/R105301.jrxml')
        self.xpath = '/apbd/akuntansi'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'akuntansi')
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "urut").text = unicode(row.urut)
            ET.SubElement(xml_greeting, "nama").text = row.nama
            ET.SubElement(xml_greeting, "tahun_kini").text = unicode(row.tahun_kini)
            ET.SubElement(xml_greeting, "tahun_lalu").text = unicode(row.tahun_lalu)
            ET.SubElement(xml_greeting, "amount_kini").text = unicode(row.amount_kini)
            ET.SubElement(xml_greeting, "amount_lalu").text = unicode(row.amount_lalu)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root
        
class b105r041Generator(JasperGenerator):
    def __init__(self):
        super(b105r041Generator, self).__init__()
        self.reportname = get_rpath('apbd/tuskpd/R105401.jrxml')
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

class b105r061Generator(JasperGenerator):
    def __init__(self):
        super(b105r061Generator, self).__init__()
        self.reportname = get_rpath('apbd/tuskpd/R105601.jrxml')
        self.xpath = '/apbd/akuntansi'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'akuntansi')
            ET.SubElement(xml_greeting, "urut").text = unicode(row.urut)
            ET.SubElement(xml_greeting, "nama").text = row.nama
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "amount").text = unicode(row.amount)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root

class b105r032Generator(JasperGenerator):
    def __init__(self):
        super(b105r032Generator, self).__init__()
        self.reportname = get_rpath('apbd/tuskpd/R105302.jrxml')
        self.xpath = '/apbd/akuntansi'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'akuntansi')
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "urut").text = unicode(row.urut)
            ET.SubElement(xml_greeting, "nama").text = row.nama
            ET.SubElement(xml_greeting, "tahun_kini").text = unicode(row.tahun_kini)
            ET.SubElement(xml_greeting, "tahun_lalu").text = unicode(row.tahun_lalu)
            ET.SubElement(xml_greeting, "amount_kini").text = unicode(row.amount_kini)
            ET.SubElement(xml_greeting, "amount_lalu").text = unicode(row.amount_lalu)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root
        
class b105r042Generator(JasperGenerator):
    def __init__(self):
        super(b105r042Generator, self).__init__()
        self.reportname = get_rpath('apbd/tuskpd/R105402.jrxml')
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

class b105r062Generator(JasperGenerator):
    def __init__(self):
        super(b105r062Generator, self).__init__()
        self.reportname = get_rpath('apbd/tuskpd/R105602.jrxml')
        self.xpath = '/apbd/akuntansi'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'akuntansi')
            ET.SubElement(xml_greeting, "urut").text = unicode(row.urut)
            ET.SubElement(xml_greeting, "nama").text = row.nama
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "amount").text = unicode(row.amount)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root
        
class b105r101Generator(JasperGenerator):
    def __init__(self):
        super(b105r101Generator, self).__init__()
        self.reportname = get_rpath('apbd/akskpd/J001001.jrxml')
        self.xpath = '/apbd/akuntansi'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'akuntansi')
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "tanggal").text = unicode(row.tanggal)
            ET.SubElement(xml_greeting, "source").text = row.source
            ET.SubElement(xml_greeting, "source_no").text = row.source_no
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "jumlah").text = unicode(row.amount)
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun_id)
            ET.SubElement(xml_greeting, "bulan").text = unicode(row.periode)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root

class b105r102Generator(JasperGenerator):
    def __init__(self):
        super(b105r102Generator, self).__init__()
        self.reportname = get_rpath('apbd/akskpd/J001002.jrxml')
        self.xpath = '/apbd/akuntansi'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'akuntansi')
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "tanggal").text = unicode(row.tanggal)
            ET.SubElement(xml_greeting, "source").text = row.source
            ET.SubElement(xml_greeting, "source_no").text = row.source_no
            ET.SubElement(xml_greeting, "kode").text = row.kode
            ET.SubElement(xml_greeting, "nama").text = row.nama
            ET.SubElement(xml_greeting, "jumlah").text = unicode(row.amount)
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun_id)
            ET.SubElement(xml_greeting, "bulan").text = unicode(row.periode)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root

class b105r103Generator(JasperGenerator):
    def __init__(self):
        super(b105r103Generator, self).__init__()
        self.reportname = get_rpath('apbd/akskpd/J001003.jrxml')
        self.xpath = '/apbd/akuntansi'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'akuntansi')
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "tanggal").text = unicode(row.tanggal)
            ET.SubElement(xml_greeting, "source").text = row.source
            ET.SubElement(xml_greeting, "source_no").text = row.source_no
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "jumlah").text = unicode(row.amount)
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun_id)
            ET.SubElement(xml_greeting, "bulan").text = unicode(row.periode)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root

class b105r104Generator(JasperGenerator):
    def __init__(self):
        super(b105r104Generator, self).__init__()
        self.reportname = get_rpath('apbd/akskpd/J001004.jrxml')
        self.xpath = '/apbd/akuntansi'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'akuntansi')
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "tanggal").text = unicode(row.tanggal)
            ET.SubElement(xml_greeting, "source").text = row.source
            ET.SubElement(xml_greeting, "source_no").text = row.source_no
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "jumlah").text = unicode(row.amount)
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun_id)
            ET.SubElement(xml_greeting, "bulan").text = unicode(row.periode)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root

class b105r105Generator(JasperGenerator):
    def __init__(self):
        super(b105r105Generator, self).__init__()
        self.reportname = get_rpath('apbd/akskpd/J001005.jrxml')
        self.xpath = '/apbd/akuntansi'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'akuntansi')
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "tanggal").text = unicode(row.tanggal)
            ET.SubElement(xml_greeting, "source").text = row.source
            ET.SubElement(xml_greeting, "source_no").text = row.source_no
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "debet").text = unicode(row.debet)
            ET.SubElement(xml_greeting, "kredit").text = unicode(row.kredit)
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun_id)
            ET.SubElement(xml_greeting, "bulan").text = unicode(row.periode)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root

class b105r106Generator(JasperGenerator):
    def __init__(self):
        super(b105r106Generator, self).__init__()
        self.reportname = get_rpath('apbd/akskpd/J001006.jrxml')
        self.xpath = '/apbd/akuntansi'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'akuntansi')
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "tanggal").text = unicode(row.tanggal)
            ET.SubElement(xml_greeting, "source").text = row.source
            ET.SubElement(xml_greeting, "source_no").text = row.source_no
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "debet").text = unicode(row.debet)
            ET.SubElement(xml_greeting, "kredit").text = unicode(row.kredit)
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun_id)
            ET.SubElement(xml_greeting, "bulan").text = unicode(row.periode)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root

class b105r201Generator(JasperGenerator):
    def __init__(self):
        super(b105r201Generator, self).__init__()
        self.reportname = get_rpath('apbd/akskpd/J002001.jrxml')
        self.xpath = '/apbd/akuntansi'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'akuntansi')
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "tanggal").text = unicode(row.tanggal)
            ET.SubElement(xml_greeting, "source").text = row.source
            ET.SubElement(xml_greeting, "source_no").text = row.source_no
            ET.SubElement(xml_greeting, "kode").text = row.kode
            ET.SubElement(xml_greeting, "nama").text = row.nama
            ET.SubElement(xml_greeting, "jumlah").text = unicode(row.amount)
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun_id)
            ET.SubElement(xml_greeting, "bulan").text = unicode(row.periode)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root

class b105r202Generator(JasperGenerator):
    def __init__(self):
        super(b105r202Generator, self).__init__()
        self.reportname = get_rpath('apbd/akskpd/J002002.jrxml')
        self.xpath = '/apbd/akuntansi'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'akuntansi')
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "tanggal").text = unicode(row.tanggal)
            ET.SubElement(xml_greeting, "source").text = row.source
            ET.SubElement(xml_greeting, "source_no").text = row.source_no
            ET.SubElement(xml_greeting, "kode").text = row.kode
            ET.SubElement(xml_greeting, "nama").text = row.nama
            ET.SubElement(xml_greeting, "jumlah").text = unicode(row.amount)
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun_id)
            ET.SubElement(xml_greeting, "bulan").text = unicode(row.periode)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root

class b105r203Generator(JasperGenerator):
    def __init__(self):
        super(b105r203Generator, self).__init__()
        self.reportname = get_rpath('apbd/akskpd/J002003.jrxml')
        self.xpath = '/apbd/akuntansi'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'akuntansi')
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "tanggal").text = unicode(row.tanggal)
            ET.SubElement(xml_greeting, "source").text = row.source
            ET.SubElement(xml_greeting, "source_no").text = row.source_no
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "debet").text = unicode(row.debet)
            ET.SubElement(xml_greeting, "kredit").text = unicode(row.kredit)
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun_id)
            ET.SubElement(xml_greeting, "bulan").text = unicode(row.periode)
            ET.SubElement(xml_greeting, "customer").text = customer
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root


