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
from osipkd.models.apbd_anggaran import Kegiatan, KegiatanSub, KegiatanItem, Pegawai, Pejabat, Jabatan
from osipkd.models.pemda_model import Unit, Rekening, RekeningSap, Sap
from osipkd.models.apbd_tu import ARInvoice, ARInvoiceItem, AkJurnal, AkJurnalItem
    
from datatables import ColumnDT, DataTables
from osipkd.views.base_view import BaseViews

SESS_ADD_FAILED  = 'Tambah ak-arinvoice gagal'
SESS_EDIT_FAILED = 'Edit ak-arinvoice gagal'

def deferred_jenis_id(node, kw):
    values = kw.get('jenis_id', [])
    return widget.SelectWidget(values=values)
    
JENIS_ID = (
    (1, 'Tagihan'),
    (2, 'Piutang'),
    (3, 'Ketetapan'))

class view_ak_arinvoice(BaseViews):

    @view_config(route_name="ak-arinvoice", renderer="templates/ak-arinvoice/list.pt",
                 permission='read')
    def view_list(self):
        ses = self.request.session
        req = self.request
        params   = req.params
        url_dict = req.matchdict
        return dict(project='EIS',
        )
        
    ##########                    
    # Action #
    ##########    
    @view_config(route_name='ak-arinvoice-act', renderer='json',
                 permission='read')
    def view_act(self):
        ses = self.request.session
        req = self.request
        params   = req.params
        url_dict = req.matchdict

        if url_dict['act']=='grid':
            pk_id = 'id' in params and params['id'] and int(params['id']) or 0
            if url_dict['act']=='grid':
                # defining columns
                columns = []
                columns.append(ColumnDT('id'))
                columns.append(ColumnDT('kode'))
                columns.append(ColumnDT('tgl_terima', filter=self._DTstrftime))
                #columns.append(ColumnDT('tgl_validasi', filter=self._DTstrftime))
                columns.append(ColumnDT('nama'))
                columns.append(ColumnDT('nilai'))
                columns.append(ColumnDT('posted'))
                columns.append(ColumnDT('posted1'))

                query = DBSession.query(ARInvoice.id,
                          ARInvoice.kode,
                          ARInvoice.tgl_terima,
                          #ARInvoice.tgl_validasi,
                          ARInvoice.nama,
                          ARInvoice.nilai,
                          ARInvoice.posted,
                          ARInvoice.posted1,
                        ).filter(ARInvoice.tahun_id==ses['tahun'],
                                 ARInvoice.unit_id==ses['unit_id'],
                        ).order_by(ARInvoice.id.asc()
                        )
                rowTable = DataTables(req, ARInvoice, query, columns)
                return rowTable.output_result()
                
def route_list(request):
    return HTTPFound(location=request.route_url('ak-arinvoice'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
def query_id(request):
    return DBSession.query(ARInvoice).filter(ARInvoice.id==request.matchdict['id'])
    
def id_not_found(request):    
    msg = 'User ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)
    
###########
# Posting #
###########     
def save_request2(request, row=None):
    row = ARInvoice()
    request.session.flash('Tagihan sudah diposting dan dibuat Jurnalnya.')
    return row
    
@view_config(route_name='ak-arinvoice-posting', renderer='templates/ak-arinvoice/posting.pt',
             permission='posting')
def view_edit_posting(request):
    row    = query_id(request).first()
    id_inv = row.id
    
    if not row:
        return id_not_found(request)
    if not row.nilai:
        request.session.flash('Data tidak dapat di jurnal, karena bernilai 0.', 'error')
        return route_list(request)
    if row.posted:
        request.session.flash('Data sudah dibuat jurnal', 'error')
        return route_list(request)
        
    form = Form(colander.Schema(), buttons=('jurnal','cancel'))
    
    if request.POST:
        if 'jurnal' in request.POST: 
            #Update posted pada ARInvoice
            row.posted=1
            save_request2(request, row)
            
            #Tambah ke Jurnal SKPD
            nama    = row.nama
            kode    = row.kode
            tanggal = row.tgl_terima
            #tipe    = ARInvoice.get_tipe(row.id)
            periode = ARInvoice.get_periode(row.id)
            
            row = AkJurnal()
            row.created    = datetime.now()
            row.create_uid = request.user.id
            row.updated    = datetime.now()
            row.update_uid = request.user.id
            row.tahun_id   = request.session['tahun']
            row.unit_id    = request.session['unit_id']
            row.nama       = "Diterima PIUTANG %s" % nama
            row.notes      = nama
            row.periode    = request.session['bulan']
            row.posted     = 0
            row.disabled   = 0
            row.is_skpd    = 1
            row.jv_type    = 1
            row.source     = "PIUTANG"
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
                #no_urut  = AkJurnal.get_norut(row.tahun_id,row.unit_id)+1
                no_urut  = row.no_urut
                no       = "0000%d" % no_urut
                nomor    = no[-5:]     
                row.kode = "%d" % tahun + "-%s" % is_skpd + "-%s" % unit_kd + "-%s" % tipe + "-%s" % nomor
            
            DBSession.add(row)
            DBSession.flush()
            
            #Tambah ke Item Jurnal SKPD
            jui   = row.id
            rows = DBSession.query(KegiatanItem.kegiatan_sub_id.label('kegiatan_sub_id1'),
                                   func.sum(ARInvoiceItem.nilai).label('nilai1'),
                                   RekeningSap.db_lo_sap_id.label('sap1'),
                                   RekeningSap.kr_lo_sap_id.label('sap2'),
                                   Rekening.id.label('rek'),
                            ).join(KegiatanSub, ARInvoiceItem 
                            ).filter(ARInvoice.id==id_inv,
                                     ARInvoice.kegiatan_sub_id==KegiatanSub.id,
                                     ARInvoiceItem.ar_invoice_id==ARInvoice.id,
                                     ARInvoiceItem.kegiatan_item_id==KegiatanItem.id,
                                     KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                                     KegiatanItem.rekening_id==RekeningSap.rekening_id,
                                     RekeningSap.rekening_id==Rekening.id,
                                     RekeningSap.kr_lo_sap_id==Sap.id
                            ).group_by(KegiatanItem.kegiatan_sub_id,
                                       RekeningSap.db_lo_sap_id,
                                       RekeningSap.kr_lo_sap_id,
                                       Rekening.id,
                            ).all()
            
            for row in rows:
                ji = AkJurnalItem()
                
                ji.ak_jurnal_id = "%d" % jui
                ji.kegiatan_sub_id = row.kegiatan_sub_id1
                ji.rekening_id  = row.rek
                ji.sap_id       = row.sap1
                ji.notes        = ""
                ji.amount       = row.nilai1
                
                DBSession.add(ji)
                DBSession.flush()
            
            n=0
            for row in rows:
                ji2 = AkJurnalItem()
                
                ji2.ak_jurnal_id = "%d" % jui
                ji2.kegiatan_sub_id = row.kegiatan_sub_id1
                ji2.rekening_id  = row.rek
                ji2.sap_id       = row.sap2
                n = row.nilai1
                ji2.amount       = n * -1
                ji2.notes        = ""
                n = n + 1
                
                DBSession.add(ji2)
                DBSession.flush()
            
        return route_list(request)
    return dict(row=row, form=form.render())    
    
#############
# UnPosting #
#############   
def save_request3(request, row=None):
    row = ARInvoice()
    request.session.flash('PIUTANG sudah di Un-Jurnal.')
    return row
    
@view_config(route_name='ak-arinvoice-unposting', renderer='templates/ak-arinvoice/unposting.pt',
             permission='unposting') 
def view_edit_unposting(request):
    row = query_id(request).first()
    
    if not row:
        return id_not_found(request)
    if not row.posted:
        request.session.flash('Data tidak dapat di Un-Jurnal, karena belum dibuat jurnal.', 'error')
        return route_list(request)
    if row.disabled:
        request.session.flash('Data jurnal PIUTANG sudah diposting.', 'error')
        return route_list(request)
        
    form = Form(colander.Schema(), buttons=('un-jurnal','cancel'))
    
    if request.POST:
        if 'un-jurnal' in request.POST: 
        
            #Update status posted pada PIUTANG
            row.posted=0
            save_request3(request, row)
            
            r = DBSession.query(AkJurnal.id).filter(AkJurnal.source_no==row.kode,AkJurnal.source=='PIUTANG').first()
            #Menghapus Item Jurnal
            DBSession.query(AkJurnalItem).filter(AkJurnalItem.ak_jurnal_id==r).delete()
            DBSession.flush()
                
            #Menghapus PIUTANG yang sudah menjadi jurnal
            DBSession.query(AkJurnal).filter(AkJurnal.source_no==row.kode,AkJurnal.source=='PIUTANG').delete()
            DBSession.flush()
            
        return route_list(request)
    return dict(row=row, form=form.render())
    
#################
# Posting Rekap #
#################     
def save_request4(request, rowd=None):
    rowd = ARInvoice()
    #request.session.flash('Piutang sudah diposting rekap dan dibuat Jurnalnya.')
    return rowd
    
@view_config(route_name='ak-arinvoice-posting1', renderer='templates/ak-arinvoice/posting1.pt',
             permission='posting')
def view_edit_posting1(request):
    req    = request
    params = req.params
    
    t = 'tanggal' in params and params['tanggal'] or 0
    a = datetime.strftime(datetime.now(),'%Y-%m-%d')
    b = " 00:00:00+07"
    tanggal = t
    #tanggal = datetime.datetime.fromtimestamp(1386181800).strftime('%Y-%m-%d %H:%M:%S')
        
    rekaps = DBSession.query(ARInvoice.id.label('ar_id1'),
                            ).filter(ARInvoice.tgl_terima==tanggal,
                                     ARInvoice.posted1==0,
                                     ARInvoice.nilai!=0,
                                     ARInvoice.disabled==0,
                            ).group_by(ARInvoice.id.label('ar_id1'),
                            ).all()
    if not rekaps:
        request.session.flash('Data posting rekap tidak ada.', 'error')
        return route_list(request)
        
    form = Form(colander.Schema(), buttons=('jurnal','cancel'))
    
    if request.POST:
        if 'jurnal' in request.POST: 
            rekaps = DBSession.query(ARInvoice.id.label('ar_id1'),
                            ).filter(ARInvoice.tgl_terima==tanggal,
                                     ARInvoice.posted1==0,
                                     ARInvoice.nilai!=0,
                                     ARInvoice.disabled==0,
                            ).group_by(ARInvoice.id.label('ar_id1'),
                            ).all()
            for row in rekaps:
                a = row.ar_id1
                #Update posted1 pada ARInvoice
                rowd = DBSession.query(ARInvoice).filter(ARInvoice.id==a).first()
                rowd.posted1=1
                save_request4(request,rowd)
            
            request.session.flash('Piutang sudah diposting rekap dan dibuat Jurnalnya.')
            
            #Tambah ke Jurnal
            tanggal = t
            kode    = "Piutang-%s" % tanggal
            
            row = AkJurnal()
            row.created    = datetime.now()
            row.create_uid = request.user.id
            row.updated    = datetime.now()
            row.update_uid = request.user.id
            row.tahun_id   = request.session['tahun']
            row.unit_id    = request.session['unit_id']
            row.nama       = "Diterima Rekap Piutang pada tanggal %s" % tanggal
            row.notes      = "Rekap Piutang pada tanggal %s" % tanggal
            row.periode    = request.session['bulan']
            row.posted     = 0
            row.disabled   = 0
            row.is_skpd    = 1
            row.jv_type    = 1
            row.source     = "Rekap-inv"
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
            
            #Tambah ke Item Jurnal SKPD
            jui   = row.id
            rows = DBSession.query(KegiatanItem.kegiatan_sub_id.label('kegiatan_sub_id1'),
                                 func.sum(ARInvoiceItem.nilai).label('nilai1'),
                                 RekeningSap.db_lo_sap_id.label('sap1'),
                                 RekeningSap.kr_lo_sap_id.label('sap2'),
                                 Rekening.id.label('rek'),
                        ).join(KegiatanSub, ARInvoiceItem 
                        ).filter(ARInvoice.tgl_terima==tanggal,
                                 ARInvoice.posted1==1,
                                 ARInvoice.nilai!=0,
                                 ARInvoice.disabled==0,
                                 ARInvoice.kegiatan_sub_id==KegiatanSub.id,
                                 ARInvoiceItem.ar_invoice_id==ARInvoice.id,
                                 ARInvoiceItem.kegiatan_item_id==KegiatanItem.id,
                                 KegiatanItem.rekening_id==RekeningSap.rekening_id,
                                 RekeningSap.rekening_id==Rekening.id,
                                 RekeningSap.kr_lo_sap_id==Sap.id
                        ).group_by(KegiatanItem.kegiatan_sub_id,
                                 RekeningSap.db_lo_sap_id,
                                 RekeningSap.kr_lo_sap_id,
                                 Rekening.id,
                        ).all()
            
            for row in rows:
                ji = AkJurnalItem()
                
                ji.ak_jurnal_id = "%d" % jui
                ji.kegiatan_sub_id = row.kegiatan_sub_id1
                ji.rekening_id  = row.rek
                ji.sap_id       = row.sap1
                ji.notes        = ""
                ji.amount       = row.nilai1
                
                DBSession.add(ji)
                DBSession.flush()
            
            n=0
            for row in rows:
                ji2 = AkJurnalItem()
                
                ji2.ak_jurnal_id = "%d" % jui
                ji2.kegiatan_sub_id = row.kegiatan_sub_id1
                ji2.rekening_id  = row.rek
                ji2.sap_id       = row.sap2
                n = row.nilai1
                ji2.amount       = n * -1
                ji2.notes        = ""
                n = n + 1
                
                DBSession.add(ji2)
                DBSession.flush()
            
        return route_list(request)
    return dict(form=form.render())    

###################
# UnPosting Rekap #
###################   
def save_request5(request, rowd=None):
    rowd = ARInvoice()
    #request.session.flash('Rekap Piutang sudah di Un-Jurnal.')
    return rowd
    
@view_config(route_name='ak-arinvoice-unposting1', renderer='templates/ak-arinvoice/unposting1.pt',
             permission='unposting') 
def view_edit_unposting1(request):
    req    = request
    params = req.params
    
    t       = 'tanggal' in params and params['tanggal'] or 0
    #tanggal = datetime.strftime(datetime.now(),'%Y-%m-%d')
    tanggal = t
    kode    = "Piutang-%s" % tanggal
    #row     = self.query_id().first()
    
    rekaps = DBSession.query(ARInvoice.id.label('ar_id1'),
                            ).filter(ARInvoice.tgl_terima==tanggal,
                                     ARInvoice.posted1==1,
                                     ARInvoice.nilai!=0,
                                     ARInvoice.disabled==0,
                            ).group_by(ARInvoice.id.label('ar_id1'),
                            ).all()
    if not rekaps:
        request.session.flash('Data rekap tidak dapat di Un-Jurnal, karena belum dibuat jurnal.', 'error')
        return route_list(request)
        
    form = Form(colander.Schema(), buttons=('un-jurnal','cancel'))
    
    if request.POST:
        if 'un-jurnal' in request.POST: 
            
            rekaps = DBSession.query(ARInvoice.id.label('ar_id1'),
                            ).filter(ARInvoice.tgl_terima==tanggal,
                                     ARInvoice.posted1==1,
                                     ARInvoice.nilai!=0,
                                     ARInvoice.disabled==0,
                            ).group_by(ARInvoice.id.label('ar_id1'),
                            ).all()
            for row in rekaps:
                a = row.ar_id1
                #Update posted1 pada ARInvoice
                rowd = DBSession.query(ARInvoice).filter(ARInvoice.id==a).first()
                rowd.posted1=0
                save_request5(request,rowd)
            
            request.session.flash('Rekap Piutang sudah di Un-Jurnal.')           
            
            r = DBSession.query(AkJurnal.id).filter(AkJurnal.source_no==kode,AkJurnal.source=='Rekap-inv',AkJurnal.tgl_source==tanggal).first()
            #Menghapus Item Jurnal
            DBSession.query(AkJurnalItem).filter(AkJurnalItem.ak_jurnal_id==r).delete()
            DBSession.flush()
                
            #Menghapus PIUTANG yang sudah menjadi jurnal
            DBSession.query(AkJurnal).filter(AkJurnal.source_no==kode,AkJurnal.source=='Rekap-inv',AkJurnal.tgl_source==tanggal).delete()
            DBSession.flush()
            
        return route_list(request)
    return dict(form=form.render())  