import os
import uuid
from osipkd.tools import row2dict, xls_reader
from datetime import datetime
from sqlalchemy import *
from pyramid.view import (view_config,)
from pyramid.httpexceptions import ( HTTPFound, )
import colander
from deform import (Form, widget, ValidationFailure, )
from osipkd.models import DBSession
from osipkd.models.apbd_anggaran import Kegiatan, KegiatanSub, KegiatanItem
from osipkd.models.pemda_model import Unit, Rekening, RekeningSap, Sap
from osipkd.models.apbd_tu import Sts, StsItem, AkJurnal, AkJurnalItem
    
from datatables import ColumnDT, DataTables
from osipkd.views.base_view import BaseViews

SESS_ADD_FAILED = 'Tambah ak-sts-ppkd gagal'
SESS_EDIT_FAILED = 'Edit ak-sts-ppkd gagal'

def deferred_jenis_id(node, kw):
    values = kw.get('jenis_id', [])
    return widget.SelectWidget(values=values)
    
JENIS_ID = (
    (1, 'Pendapatan Bendahara Penerimaan'),
    (2, 'Pendapatan Piutang'),
    (3, 'Pendapatan Non Piutang'),
    (4, 'Kontra Pos'),
    (5, 'Lainnya'))
    
class view_ak_sts(BaseViews):

    @view_config(route_name="ak-sts-ppkd", renderer="templates/ak-sts-ppkd/list.pt",
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
    @view_config(route_name='ak-sts-ppkd-act', renderer='json',
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
                columns.append(ColumnDT('tgl_sts', filter=self._DTstrftime))
                columns.append(ColumnDT('tgl_validasi', filter=self._DTstrftime))
                columns.append(ColumnDT('jenis'))
                columns.append(ColumnDT('nama'))
                columns.append(ColumnDT('nominal'))
                columns.append(ColumnDT('posted'))
                columns.append(ColumnDT('posted1'))
                
                query = DBSession.query(Sts).filter(
                          Sts.tahun_id == ses['tahun'],
                          Sts.unit_id == ses['unit_id'],
                          )
                rowTable = DataTables(req, Sts, query, columns)
                return rowTable.output_result()
                
        
def route_list(request):
    return HTTPFound(location=request.route_url('ak-sts-ppkd'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
def query_id(request):
    return DBSession.query(Sts).filter(Sts.id==request.matchdict['id'])
    
def id_not_found(request):    
    msg = 'User ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

###########
# Posting #
###########     
def save_request2(request, row=None):
    row = Sts()
    request.session.flash('STS sudah diposting dan dibuat Jurnalnya.')
    return row
    
@view_config(route_name='ak-sts-ppkd-posting', renderer='templates/ak-sts-ppkd/posting.pt',
             permission='posting')
def view_edit_posting(request):
    row    = query_id(request).first()
    id_sts = row.id
    gi     = row.jenis
    g      = '%s' % gi
    nam    = row.nama
    kod    = row.kode
    tgl    = row.tgl_sts
    
    if not row:
        return id_not_found(request)
    if not row.tgl_validasi:
        request.session.flash('Data tidak dapat diposting jurnal, karena belum divalidasi.', 'error')
        return route_list(request)
    if not row.nominal:
        request.session.flash('Data tidak dapat diposting jurnal, karena bernilai 0.', 'error')
        return route_list(request)
    if row.posted1:
        request.session.flash('Data sudah diposting jurnal PPKD', 'error')
        return route_list(request)
        
    form = Form(colander.Schema(), buttons=('jurnal','cancel'))
    
    if request.POST:
        if 'jurnal' in request.POST: 
            #Update posted pada STS
            row.posted1=1
            save_request2(request, row)
            
            if g == '1':
                #Tambah ke Jurnal PPKD (Kas di Kasda ke RK-SKPD)
                nama    = nam
                kode    = kod
                tanggal = tgl
                tipe    = Sts.get_tipe(row.id)
                periode = Sts.get_periode(row.id)
                
                row = AkJurnal()
                row.created    = datetime.now()
                row.create_uid = request.user.id
                row.updated    = datetime.now()
                row.update_uid = request.user.id
                row.tahun_id   = request.session['tahun']
                row.unit_id    = request.session['unit_id']
                row.nama       = "Diterima STS %s" % tipe + " %s" % nama
                row.notes      = nama
                row.periode    = request.session['bulan']
                row.posted     = 0
                row.disabled   = 0
                row.is_skpd    = 0
                row.jv_type    = 1
                row.source     = "STS-%s" % tipe
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
                rows = DBSession.query(KegiatanItem.rekening_id.label('rekening_id1'),
                                           Sap.nama.label('nama1'),
                                           KegiatanItem.kegiatan_sub_id.label('kegiatan_sub_id1'),
                                           Sts.nominal.label('nilai1'),
                                           RekeningSap.db_lra_sap_id.label('sap1'),
                                           RekeningSap.kr_lra_sap_id.label('sap2'),
                                           Rekening.id.label('rek'),
                                    ).join(Rekening
                                    ).outerjoin(KegiatanItem,RekeningSap,KegiatanSub,
                                    ).filter(Sts.id==id_sts,
                                           StsItem.ar_sts_id==Sts.id,
                                           StsItem.kegiatan_item_id==KegiatanItem.id,
                                           KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                                           KegiatanItem.rekening_id==RekeningSap.rekening_id,
                                           RekeningSap.rekening_id==Rekening.id,
                                           RekeningSap.db_lra_sap_id==Sap.id
                                    ).group_by(KegiatanItem.rekening_id.label('rekening_id1'),
                                           Sap.nama.label('nama1'),
                                           KegiatanItem.kegiatan_sub_id.label('kegiatan_sub_id1'),
                                           Sts.nominal.label('nilai1'),
                                           RekeningSap.db_lra_sap_id.label('sap1'),
                                           RekeningSap.kr_lra_sap_id.label('sap2'),
                                           Rekening.id.label('rek'),
                                    ).first()
                    
                ji1 = AkJurnalItem()
                ji1.ak_jurnal_id = "%d" % jui
                ji1.kegiatan_sub_id = 0
                ji1.rekening_id  = 0
                s=DBSession.query(Sap.id).filter(Sap.kode=='1.1.1.01.01').first()
                ji1.sap_id       = s
                ji1.amount       = rows.nilai1
                ji1.notes        = ""
                DBSession.add(ji1)
                DBSession.flush()
                
                ji2 = AkJurnalItem()
                ji2.ak_jurnal_id = "%d" % jui
                ji2.kegiatan_sub_id = 0
                ji2.rekening_id  = 0
                s=DBSession.query(Sap.id).filter(Sap.kode=='1.1.8.01.01').first()
                ji2.sap_id       = s
                n = rows.nilai1
                ji2.amount       = n * -1
                ji2.notes        = ""
                DBSession.add(ji2)
                DBSession.flush()
            
            elif g == '2':
                #Tambah ke Jurnal PPKD (Kas di Kasda ke RK-SKPD)
                nama    = nam
                kode    = kod
                tanggal = tgl
                tipe    = Sts.get_tipe(row.id)
                periode = Sts.get_periode(row.id)
                
                row = AkJurnal()
                row.created    = datetime.now()
                row.create_uid = request.user.id
                row.updated    = datetime.now()
                row.update_uid = request.user.id
                row.tahun_id   = request.session['tahun']
                row.unit_id    = request.session['unit_id']
                row.nama       = "Diterima STS %s" % tipe + " %s" % nama
                row.notes      = nama
                row.periode    = request.session['bulan']
                row.posted     = 0
                row.disabled   = 0
                row.is_skpd    = 0
                row.jv_type    = 1
                row.source     = "STS-%s" % tipe
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
                rows = DBSession.query(KegiatanItem.rekening_id.label('rekening_id1'),
                                           Sap.nama.label('nama1'),
                                           KegiatanItem.kegiatan_sub_id.label('kegiatan_sub_id1'),
                                           Sts.nominal.label('nilai1'),
                                           RekeningSap.db_lra_sap_id.label('sap1'),
                                           RekeningSap.kr_lra_sap_id.label('sap2'),
                                           Rekening.id.label('rek'),
                                    ).join(Rekening
                                    ).outerjoin(KegiatanItem,RekeningSap,KegiatanSub,
                                    ).filter(Sts.id==id_sts,
                                           StsItem.ar_sts_id==Sts.id,
                                           StsItem.kegiatan_item_id==KegiatanItem.id,
                                           KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                                           KegiatanItem.rekening_id==RekeningSap.rekening_id,
                                           RekeningSap.rekening_id==Rekening.id,
                                           RekeningSap.db_lra_sap_id==Sap.id
                                    ).group_by(KegiatanItem.rekening_id.label('rekening_id1'),
                                           Sap.nama.label('nama1'),
                                           KegiatanItem.kegiatan_sub_id.label('kegiatan_sub_id1'),
                                           Sts.nominal.label('nilai1'),
                                           RekeningSap.db_lra_sap_id.label('sap1'),
                                           RekeningSap.kr_lra_sap_id.label('sap2'),
                                           Rekening.id.label('rek'),
                                    ).first()
                    
                ji1 = AkJurnalItem()
                ji1.ak_jurnal_id = "%d" % jui
                ji1.kegiatan_sub_id = 0
                ji1.rekening_id  = 0
                s=DBSession.query(Sap.id).filter(Sap.kode=='1.1.1.01.01').first()
                ji1.sap_id       = s
                ji1.amount       = rows.nilai1
                ji1.notes        = ""
                DBSession.add(ji1)
                DBSession.flush()
                
                ji2 = AkJurnalItem()
                ji2.ak_jurnal_id = "%d" % jui
                ji2.kegiatan_sub_id = 0
                ji2.rekening_id  = 0
                s=DBSession.query(Sap.id).filter(Sap.kode=='1.1.8.01.01').first()
                ji2.sap_id       = s
                n = rows.nilai1
                ji2.amount       = n * -1
                ji2.notes        = ""
                DBSession.add(ji2)
                DBSession.flush()
                
            elif g == '3':
                #Tambah ke Jurnal PPKD (Kas di Kasda ke RK-SKPD)
                nama    = nam
                kode    = kod
                tanggal = tgl
                tipe    = Sts.get_tipe(row.id)
                periode = Sts.get_periode(row.id)
                
                row = AkJurnal()
                row.created    = datetime.now()
                row.create_uid = request.user.id
                row.updated    = datetime.now()
                row.update_uid = request.user.id
                row.tahun_id   = request.session['tahun']
                row.unit_id    = request.session['unit_id']
                row.nama       = "Diterima STS %s" % tipe + " %s" % nama
                row.notes      = nama
                row.periode    = request.session['bulan']
                row.posted     = 0
                row.disabled   = 0
                row.is_skpd    = 0
                row.jv_type    = 1
                row.source     = "STS-%s" % tipe
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
                rows = DBSession.query(KegiatanItem.rekening_id.label('rekening_id1'),
                                           Sap.nama.label('nama1'),
                                           KegiatanItem.kegiatan_sub_id.label('kegiatan_sub_id1'),
                                           Sts.nominal.label('nilai1'),
                                           RekeningSap.db_lra_sap_id.label('sap1'),
                                           RekeningSap.kr_lra_sap_id.label('sap2'),
                                           Rekening.id.label('rek'),
                                    ).join(Rekening
                                    ).outerjoin(KegiatanItem,RekeningSap,KegiatanSub,
                                    ).filter(Sts.id==id_sts,
                                           StsItem.ar_sts_id==Sts.id,
                                           StsItem.kegiatan_item_id==KegiatanItem.id,
                                           KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                                           KegiatanItem.rekening_id==RekeningSap.rekening_id,
                                           RekeningSap.rekening_id==Rekening.id,
                                           RekeningSap.db_lra_sap_id==Sap.id
                                    ).group_by(KegiatanItem.rekening_id.label('rekening_id1'),
                                           Sap.nama.label('nama1'),
                                           KegiatanItem.kegiatan_sub_id.label('kegiatan_sub_id1'),
                                           Sts.nominal.label('nilai1'),
                                           RekeningSap.db_lra_sap_id.label('sap1'),
                                           RekeningSap.kr_lra_sap_id.label('sap2'),
                                           Rekening.id.label('rek'),
                                    ).first()
                    
                ji1 = AkJurnalItem()
                ji1.ak_jurnal_id = "%d" % jui
                ji1.kegiatan_sub_id = 0
                ji1.rekening_id  = 0
                s=DBSession.query(Sap.id).filter(Sap.kode=='1.1.1.01.01').first()
                ji1.sap_id       = s
                ji1.amount       = rows.nilai1
                ji1.notes        = ""
                DBSession.add(ji1)
                DBSession.flush()
                
                ji2 = AkJurnalItem()
                ji2.ak_jurnal_id = "%d" % jui
                ji2.kegiatan_sub_id = 0
                ji2.rekening_id  = 0
                s=DBSession.query(Sap.id).filter(Sap.kode=='1.1.8.01.01').first()
                ji2.sap_id       = s
                n = rows.nilai1
                ji2.amount       = n * -1
                ji2.notes        = ""
                DBSession.add(ji2)
                DBSession.flush()
                
            elif g == '4':
                re = DBSession.query(func.substr(Rekening.kode,1,1)
                             ).filter(Sts.id==id_sts,
                                      StsItem.ar_sts_id==Sts.id,
                                      StsItem.kegiatan_item_id==KegiatanItem.id,
                                      KegiatanItem.rekening_id==Rekening.id,
                                      func.substr(Rekening.kode,1,1)=='5',
                             ).first()
                rek = '%s' % re
                print 'XOI------------------------------',rek
                
                if rek == '5':
                    #Tambah ke Jurnal PPKD
                    nama    = nam
                    kode    = kod
                    tanggal = tgl
                    tipe    = Sts.get_tipe(row.id)
                    periode = Sts.get_periode(row.id)
                    
                    row = AkJurnal()
                    row.created    = datetime.now()
                    row.create_uid = request.user.id
                    row.updated    = datetime.now()
                    row.update_uid = request.user.id
                    row.tahun_id   = request.session['tahun']
                    row.unit_id    = request.session['unit_id']
                    row.nama       = "Diterima STS %s" % tipe + " %s" % nama
                    row.notes      = nama
                    row.periode    = request.session['bulan']
                    row.posted     = 0
                    row.disabled   = 0
                    row.is_skpd    = 0
                    row.jv_type    = 1
                    row.source     = "STS-%s" % tipe
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
                    
                    #Tambah ke Item Jurnal
                    jui   = row.id
                    rows = DBSession.query(KegiatanItem.rekening_id.label('rekening_id1'),
                                               Sap.nama.label('nama1'),
                                               Sts.nominal.label('nilai1'),
                                               RekeningSap.db_lra_sap_id.label('sap1'),
                                               RekeningSap.kr_lra_sap_id.label('sap2'),
                                               Rekening.id.label('rek'),
                                        ).join(Rekening
                                        ).outerjoin(KegiatanItem,RekeningSap,KegiatanSub,
                                        ).filter(Sts.id==id_sts,
                                               StsItem.ar_sts_id==Sts.id,
                                               StsItem.kegiatan_item_id==KegiatanItem.id,
                                               KegiatanItem.rekening_id==RekeningSap.rekening_id,
                                               RekeningSap.rekening_id==Rekening.id,
                                               RekeningSap.db_lra_sap_id==Sap.id,
                                        ).group_by(KegiatanItem.rekening_id.label('rekening_id1'),
                                               Sap.nama.label('nama1'),
                                               Sts.nominal.label('nilai1'),
                                               RekeningSap.db_lra_sap_id.label('sap1'),
                                               RekeningSap.kr_lra_sap_id.label('sap2'),
                                               Rekening.id.label('rek'),
                                        ).first()
                        
                    ji1 = AkJurnalItem()
                    ji1.ak_jurnal_id = "%d" % jui
                    ji1.kegiatan_sub_id = 0
                    ji1.rekening_id  = 0
                    s=DBSession.query(Sap.id).filter(Sap.kode=='1.1.1.01.01').first()
                    ji1.sap_id       = s
                    ji1.amount       = rows.nilai1
                    ji1.notes        = ""
                    DBSession.add(ji1)
                    DBSession.flush()
                    
                    ji2 = AkJurnalItem()
                    ji2.ak_jurnal_id = "%d" % jui
                    ji2.kegiatan_sub_id = 0
                    ji2.rekening_id  = 0
                    s=DBSession.query(Sap.id).filter(Sap.kode=='1.1.8.01.01').first()
                    ji2.sap_id       = s
                    n = rows.nilai1
                    ji2.amount       = n * -1
                    ji2.notes        = ""
                    DBSession.add(ji2)
                    DBSession.flush()
                    
                else:
                    #Tambah ke Jurnal PPKD
                    nama    = nam
                    kode    = kod
                    tanggal = tgl
                    tipe    = Sts.get_tipe(row.id)
                    periode = Sts.get_periode(row.id)
                    
                    row = AkJurnal()
                    row.created    = datetime.now()
                    row.create_uid = request.user.id
                    row.updated    = datetime.now()
                    row.update_uid = request.user.id
                    row.tahun_id   = request.session['tahun']
                    row.unit_id    = request.session['unit_id']
                    row.nama       = "Diterima STS %s" % tipe + " %s" % nama
                    row.notes      = nama
                    row.periode    = request.session['bulan']
                    row.posted     = 0
                    row.disabled   = 0
                    row.is_skpd    = 0
                    row.jv_type    = 1
                    row.source     = "STS-%s" % tipe
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
                    
                    #Tambah ke Item Jurnal
                    jui   = row.id
                    rows = DBSession.query(KegiatanItem.rekening_id.label('rekening_id1'),
                                               Sap.nama.label('nama1'),
                                               KegiatanItem.kegiatan_sub_id.label('kegiatan_sub_id1'),
                                               Sts.nominal.label('nilai1'),
                                               RekeningSap.db_lra_sap_id.label('sap1'),
                                               RekeningSap.kr_lra_sap_id.label('sap2'),
                                               Rekening.id.label('rek'),
                                        ).join(Rekening
                                        ).outerjoin(KegiatanItem,RekeningSap,KegiatanSub,
                                        ).filter(Sts.id==id_sts,
                                               StsItem.ar_sts_id==Sts.id,
                                               StsItem.kegiatan_item_id==KegiatanItem.id,
                                               KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                                               KegiatanItem.rekening_id==RekeningSap.rekening_id,
                                               RekeningSap.rekening_id==Rekening.id,
                                               RekeningSap.db_lra_sap_id==Sap.id
                                        ).group_by(KegiatanItem.rekening_id.label('rekening_id1'),
                                               Sap.nama.label('nama1'),
                                               KegiatanItem.kegiatan_sub_id.label('kegiatan_sub_id1'),
                                               Sts.nominal.label('nilai1'),
                                               RekeningSap.db_lra_sap_id.label('sap1'),
                                               RekeningSap.kr_lra_sap_id.label('sap2'),
                                               Rekening.id.label('rek'),
                                        ).first()
                        
                    ji1 = AkJurnalItem()
                    ji1.ak_jurnal_id = "%d" % jui
                    ji1.kegiatan_sub_id = 0
                    ji1.rekening_id  = 0
                    s=DBSession.query(Sap.id).filter(Sap.kode=='1.1.1.01.01').first()
                    ji1.sap_id       = s
                    ji1.amount       = rows.nilai1
                    ji1.notes        = ""
                    DBSession.add(ji1)
                    DBSession.flush()
                    
                    ji2 = AkJurnalItem()
                    ji2.ak_jurnal_id = "%d" % jui
                    ji2.kegiatan_sub_id = 0
                    ji2.rekening_id  = 0
                    s=DBSession.query(Sap.id).filter(Sap.kode=='1.1.8.01.01').first()
                    ji2.sap_id       = s
                    n = rows.nilai1
                    ji2.amount       = n * -1
                    ji2.notes        = ""
                    DBSession.add(ji2)
                    DBSession.flush()
            
            else:
                #Tambah ke Jurnal PPKD
                nama    = nam
                kode    = kod
                tanggal = tgl
                tipe    = Sts.get_tipe(row.id)
                periode = Sts.get_periode(row.id)
                
                row = AkJurnal()
                row.created    = datetime.now()
                row.create_uid = request.user.id
                row.updated    = datetime.now()
                row.update_uid = request.user.id
                row.tahun_id   = request.session['tahun']
                row.unit_id    = request.session['unit_id']
                row.nama       = "Diterima STS %s" % tipe + " %s" % nama
                row.notes      = nama
                row.periode    = request.session['bulan']
                row.posted     = 0
                row.disabled   = 0
                row.is_skpd    = 0
                row.jv_type    = 1
                row.source     = "STS-%s" % tipe
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
                rows = DBSession.query(KegiatanItem.rekening_id.label('rekening_id1'),
                                           Sap.nama.label('nama1'),
                                           KegiatanItem.kegiatan_sub_id.label('kegiatan_sub_id1'),
                                           Sts.nominal.label('nilai1'),
                                           RekeningSap.db_lra_sap_id.label('sap1'),
                                           RekeningSap.kr_lra_sap_id.label('sap2'),
                                           Rekening.id.label('rek'),
                                    ).join(Rekening
                                    ).outerjoin(KegiatanItem,RekeningSap,KegiatanSub,
                                    ).filter(Sts.id==id_sts,
                                           StsItem.ar_sts_id==Sts.id,
                                           StsItem.kegiatan_item_id==KegiatanItem.id,
                                           KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                                           KegiatanItem.rekening_id==RekeningSap.rekening_id,
                                           RekeningSap.rekening_id==Rekening.id,
                                           RekeningSap.db_lra_sap_id==Sap.id
                                    ).group_by(KegiatanItem.rekening_id.label('rekening_id1'),
                                           Sap.nama.label('nama1'),
                                           KegiatanItem.kegiatan_sub_id.label('kegiatan_sub_id1'),
                                           Sts.nominal.label('nilai1'),
                                           RekeningSap.db_lra_sap_id.label('sap1'),
                                           RekeningSap.kr_lra_sap_id.label('sap2'),
                                           Rekening.id.label('rek'),
                                    ).first()
                    
                ji1 = AkJurnalItem()
                ji1.ak_jurnal_id = "%d" % jui
                ji1.kegiatan_sub_id = 0
                ji1.rekening_id  = 0
                s=DBSession.query(Sap.id).filter(Sap.kode=='1.1.1.01.01').first()
                ji1.sap_id       = s
                ji1.amount       = rows.nilai1
                ji1.notes        = ""
                DBSession.add(ji1)
                DBSession.flush()
                
                ji2 = AkJurnalItem()
                ji2.ak_jurnal_id = "%d" % jui
                ji2.kegiatan_sub_id = 0
                ji2.rekening_id  = 0
                s=DBSession.query(Sap.id).filter(Sap.kode=='1.1.8.01.01').first()
                ji2.sap_id       = s
                n = rows.nilai1
                ji2.amount       = n * -1
                ji2.notes        = ""
                DBSession.add(ji2)
                DBSession.flush()
                        
        return route_list(request)
    return dict(row=row, form=form.render())       

#############
# UnPosting #
#############   
def save_request3(request, row=None):
    row = Sts()
    request.session.flash('STS sudah di Unposting jurnal.')
    return row
    
@view_config(route_name='ak-sts-ppkd-unposting', renderer='templates/ak-sts-ppkd/unposting.pt',
             permission='unposting') 
def view_edit_unposting(request):
    row = query_id(request).first()
    
    if not row:
        return id_not_found(request)
    if not row.posted1:
        request.session.flash('Data tidak dapat di Unposting jurnal, karena belum diposting jurnal PPKD.', 'error')
        return route_list(request)
    if row.disabled:
        request.session.flash('Data jurnal STS sudah diposting.', 'error')
        return route_list(request)
        
    form = Form(colander.Schema(), buttons=('un-jurnal','cancel'))
    
    if request.POST:
        if 'un-jurnal' in request.POST: 
        
            #Update status posted pada STS
            row.posted1=0
            save_request3(request, row)
            
            kode = row.kode
            ji   = row.jenis
            j    = '%s' % ji
            
            if j=='1':
                s='BP'
                x='STS-%s' % s
            if j=='2':
                s='P'
                x='STS-%s' % s
            if j=='3':
                s='NP'
                x='STS-%s' % s
            if j=='4':
                s='CP'
                x='STS-%s' % s
            if j=='5':
                s='L'
                x='STS-%s' % s
                
            r = DBSession.query(AkJurnal.id.label('di')).filter(AkJurnal.source_no==kode,AkJurnal.source==x,AkJurnal.is_skpd==0).all()
            for row in r:
                #Menghapus Item Jurnal
                DBSession.query(AkJurnalItem).filter(AkJurnalItem.ak_jurnal_id==row.di).delete()
                DBSession.flush()
            
            #Menghapus STS yang sudah menjadi jurnal
            DBSession.query(AkJurnal).filter(AkJurnal.source_no==kode, AkJurnal.source==x,AkJurnal.is_skpd==0).delete()
            DBSession.flush()
            
        return route_list(request)
    return dict(row=row, form=form.render()) 
    