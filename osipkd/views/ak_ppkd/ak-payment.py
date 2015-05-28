import os
import uuid
from osipkd.tools import row2dict, xls_reader
from datetime import datetime
from sqlalchemy import not_, func
from pyramid.view import (view_config,)
from pyramid.httpexceptions import ( HTTPFound, )
import colander
from deform import (Form, widget, ValidationFailure, )
from osipkd.models import DBSession
from osipkd.models.apbd_anggaran import Kegiatan, KegiatanSub, KegiatanItem
from osipkd.models.pemda_model import Unit, Rekening, RekeningSap, Sap
from osipkd.models.apbd_tu import APPayment, APPaymentItem, APInvoice, APInvoiceItem, SppItem, Spp, AkJurnal, AkJurnalItem
    
from datatables import ColumnDT, DataTables
from osipkd.views.base_view import BaseViews

SESS_ADD_FAILED = 'Tambah ak-payment gagal'
SESS_EDIT_FAILED = 'Edit ak-payment gagal'

def deferred_ap_type(node, kw):
    values = kw.get('ap_type', [])
    return widget.SelectWidget(values=values)
    
AP_TYPE = (
    ('1', 'UP'),
    ('2', 'TU'),
    ('3', 'GU'),
    ('4', 'LS'),
    ('5', 'SP2B'),
    )

def deferred_kontrak_type(node, kw):
    values = kw.get('kontrak_type', [])
    return widget.SelectWidget(values=values)
    
KONTRAK_TYPE = (
    ('1', 'PT / NV'),
    ('2', 'CV'),
    ('3', 'FIRMA'),
    ('4', 'Lain-lain'),
    )
    
class view_ak_payment(BaseViews):

    @view_config(route_name="ak-payment", renderer="templates/ak-payment/list.pt",
                 permission='read')
    def view_list(self):
        ses = self.request.session
        req = self.request
        params = req.params
        url_dict = req.matchdict
        return dict(project='EIS', 
        )
        
    ##########                    
    # Action #
    ##########    
    @view_config(route_name='ak-payment-act', renderer='json',
                 permission='read')
    def view_act(self):
        ses = self.request.session
        req = self.request
        params = req.params
        url_dict = req.matchdict
        if url_dict['act']=='grid':
            pk_id = 'id' in params and params['id'] and int(params['id']) or 0
            if url_dict['act']=='grid':
                # defining columns
                columns = []
                columns.append(ColumnDT('id'))
                columns.append(ColumnDT('kode'))
                columns.append(ColumnDT('jenis'))
                columns.append(ColumnDT('tanggal', filter=self._DTstrftime))
                columns.append(ColumnDT('kegiatan_sub_nm'))
                columns.append(ColumnDT('nama'))
                columns.append(ColumnDT('invoice_kd'))
                columns.append(ColumnDT('amount'))
                columns.append(ColumnDT('posted'))

                query = DBSession.query(APPayment.id,
                          APPayment.kode,
                          APPayment.jenis,                          
                          APPayment.tanggal,
                          KegiatanSub.nama.label('kegiatan_sub_nm'),
                          APPayment.nama,
                          APInvoice.kode.label('invoice_kd'),
                          APPayment.amount,
                          APPayment.posted,
                        ).outerjoin(APPaymentItem
                        ).filter(APPayment.tahun_id==ses['tahun'],
                                 APPayment.unit_id==ses['unit_id'],
                                 APPayment.kegiatan_sub_id==KegiatanSub.id,
                                 APPayment.invoice_id==APInvoice.id,
                        ).order_by(APPayment.no_urut.desc()
                        ).group_by(APPayment.id,
                                   APPayment.tanggal,
                                   KegiatanSub.nama,
                                   APInvoice.kode,
                        )
                rowTable = DataTables(req, APPayment, query, columns)
                return rowTable.output_result()
        
def route_list(request):
    return HTTPFound(location=request.route_url('ak-payment'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
def query_id(request):
    return DBSession.query(APPayment).filter(APPayment.id==request.matchdict['id'])
    
def id_not_found(request):    
    msg = 'User ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

###########
# Posting #
###########     
def save_request2(request, row=None):
    row = APPayment()
    request.session.flash('Pembayaran Tagihan sudah diposting dan dibuat Jurnalnya.')
    return row
    
@view_config(route_name='ak-payment-posting', renderer='templates/ak-payment/posting.pt',
             permission='posting')
def view_edit_posting(request):
    row    = query_id(request).first()
    id_inv = row.id
    gi     = row.jenis
    g      = '%s' % gi
    keg    = row.kegiatan_sub_id
    nam    = row.nama
    kod    = row.kode
    tgl    = row.tanggal
    
    if not row:
        return id_not_found(request)
    if not row.amount:
        request.session.flash('Data tidak dapat diposting, karena bernilai 0.', 'error')
        return route_list(request)
    if row.posted:
        request.session.flash('Data sudah diposting jurnal', 'error')
        return route_list(request)
        
    form = Form(colander.Schema(), buttons=('jurnal','cancel'))
    
    if request.POST:
        if 'jurnal' in request.POST: 
            #Update posted pada Payment
            row.posted=1
            save_request2(request, row)
            
            gi = row.jenis
            g  = '%s' % gi
            #Tambah ke Jurnal -Utang terhadap Kas di ben.Pengeluaran-
            nama    = nam
            kode    = kod
            tanggal = tgl
            tipe    = APPayment.get_tipe(id_inv)
            periode = APPayment.get_periode(id_inv)
            
            row = AkJurnal()
            row.created    = datetime.now()
            row.create_uid = request.user.id
            row.updated    = datetime.now()
            row.update_uid = request.user.id
            row.tahun_id   = request.session['tahun']
            row.unit_id    = request.session['unit_id']
            row.nama       = "Diterima Payment %s" % tipe + " %s" % nama
            row.notes      = nama
            row.periode    = request.session['bulan']
            row.posted     = 0
            row.disabled   = 0
            row.is_skpd    = 1
            row.jv_type    = 1
            row.source     = "Payment-%s" % tipe
            row.source_no  = kode
            row.tgl_source = tanggal
            row.tanggal    = datetime.now()
            row.tgl_transaksi = datetime.now()
            row.no_urut = AkJurnal.max_no_urut(row.tahun_id,row.unit_id)+1;
            
            if not row.kode:
                tahun    = request.session['tahun']
                unit_kd  = request.session['unit_kd']
                is_skpd  = row.is_skpd
                tipe     = AkJurnal.get_tipe(row.jv_type)
                no_urut  = row.no_urut
                no       = "0000%d" % no_urut
                nomor    = no[-5:]     
                row.kode = "%d" % tahun + "-%s" % is_skpd + "-%s" % unit_kd + "-%s" % tipe + "-%s" % nomor
            
            DBSession.add(row)
            DBSession.flush()
            
            jui   = row.id
            rows = DBSession.query(KegiatanItem.kegiatan_sub_id.label('kegiatan_sub_id1'),
                                       func.sum(APInvoiceItem.amount).label('nilai2'),
                                       RekeningSap.kr_lo_sap_id.label('sap2'),
                                       Rekening.id.label('rek'),
                                ).filter(APPayment.id==id_inv,
                                       APPayment.invoice_id==APInvoiceItem.ap_invoice_id,
                                       APInvoiceItem.kegiatan_item_id==KegiatanItem.id,
                                       KegiatanItem.rekening_id==RekeningSap.rekening_id,
                                       RekeningSap.rekening_id==Rekening.id,
                                       RekeningSap.kr_lo_sap_id==Sap.id
                                ).group_by(KegiatanItem.kegiatan_sub_id,
                                       RekeningSap.kr_lo_sap_id,
                                       Rekening.id,
                                ).all()
            #Utang
            for row in rows:                    
                ji1 = AkJurnalItem()
                ji1.ak_jurnal_id = "%d" % jui
                ji1.kegiatan_sub_id = row.kegiatan_sub_id1
                ji1.rekening_id  = row.rek
                ji1.sap_id       = row.sap2
                ji1.amount       = row.nilai2
                ji1.notes        = ""
                DBSession.add(ji1)
                DBSession.flush()
            
            #Kas di Bendahara Pengeluaran
            ji2 = AkJurnalItem()
            ji2.ak_jurnal_id = "%d" % jui
            ji2.kegiatan_sub_id = 0
            ji2.rekening_id  = 0
            ji2.notes        = ""
            
            s=DBSession.query(Sap.id).filter(Sap.kode=='1.1.1.03.01').first()
            ji2.sap_id       = s
            
            n = DBSession.query(func.sum(APInvoiceItem.amount).label('nilai3'),
                        ).filter(APPayment.id==id_inv,
                                 APPayment.invoice_id==APInvoiceItem.ap_invoice_id
                        ).first()
                        
            ni = n.nilai3
            ji2.amount       = ni * -1
            DBSession.add(ji2)
            DBSession.flush()
                    
        return route_list(request)
    return dict(row=row, form=form.render())    
    
#############
# UnPosting #
#############   
def save_request3(request, row=None):
    row = APPayment()
    request.session.flash('Pembayaran Tagihan sudah di Unposting jurnal.')
    return row
    
@view_config(route_name='ak-payment-unposting', renderer='templates/ak-payment/unposting.pt',
             permission='unposting') 
def view_edit_unposting(request):
    row = query_id(request).first()
    
    if not row:
        return id_not_found(request)
    if not row.posted:
        request.session.flash('Data tidak dapat di Unposting jurnal, karena belum diposting jurnal.', 'error')
        return route_list(request)
    if row.disabled:
        request.session.flash('Data jurnal Pembayaran Tagihan sudah diposting jurnal.', 'error')
        return route_list(request)
        
    form = Form(colander.Schema(), buttons=('un-jurnal','cancel'))
    
    if request.POST:
        if 'un-jurnal' in request.POST: 
        
            #Update status posted pada Payment
            row.posted=0
            save_request3(request, row)
            
            ji = row.jenis
            j  = '%s' % ji
            if j=='3':
                s='GU'
                x='Payment-%s' % s
                
            r = DBSession.query(AkJurnal.id).filter(AkJurnal.source_no==row.kode,AkJurnal.source==x).first()
            #Menghapus Item Jurnal
            DBSession.query(AkJurnalItem).filter(AkJurnalItem.ak_jurnal_id==r).delete()
            DBSession.flush()
                
            #Menghapus UTANG yang sudah menjadi jurnal
            DBSession.query(AkJurnal).filter(AkJurnal.source_no==row.kode,AkJurnal.source==x).delete()
            DBSession.flush()
            
        return route_list(request)
    return dict(row=row, form=form.render())
    
      