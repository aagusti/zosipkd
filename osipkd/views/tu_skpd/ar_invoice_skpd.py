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
from osipkd.models.pemda_model import Unit
from osipkd.models.apbd_tu import ARInvoice, ARInvoiceItem, AkJurnal
    
from datatables import ColumnDT, DataTables
from osipkd.views.base_view import BaseViews

SESS_ADD_FAILED  = 'Tambah ar-invoice-skpd gagal'
SESS_EDIT_FAILED = 'Edit ar-invoice-skpd gagal'


class view_ar_invoice_skpd(BaseViews):

    @view_config(route_name="ar-invoice-skpd", renderer="templates/ar-invoice-skpd/list.pt")
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
    @view_config(route_name='ar-invoice-skpd-act', renderer='json',
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
                columns.append(ColumnDT('tgl_validasi', filter=self._DTstrftime))
                columns.append(ColumnDT('bendahara_nm'))
                columns.append(ColumnDT('penyetor'))
                columns.append(ColumnDT('nama'))
                columns.append(ColumnDT('nilai'))
                columns.append(ColumnDT('posted'))

                query = DBSession.query(ARInvoice.id,
                          ARInvoice.kode,
                          ARInvoice.tgl_terima,
                          ARInvoice.tgl_validasi,
                          ARInvoice.bendahara_nm,
                          ARInvoice.penyetor,
                          ARInvoice.nama,
                          ARInvoice.nilai,
                          ARInvoice.posted,
                        ).filter(ARInvoice.tahun_id==ses['tahun'],
                                 ARInvoice.unit_id==ses['unit_id']
                        ).order_by(ARInvoice.id.asc()
                        )
                rowTable = DataTables(req, ARInvoice, query, columns)
                return rowTable.output_result()
                
  
#######    
# Add #
#######
def form_validator(form, value):
    def err_kegiatan():
        raise colander.Invalid(form,
            'Kegiatan dengan no urut tersebut sudah ada')      
                
class AddSchema(colander.Schema):
    unit_id          = colander.SchemaNode(
                          colander.String(),
                          oid = "unit_id")
    tahun_id         = colander.SchemaNode(
                          colander.String(),
                          oid = "tahun_id",
                          title="Tahun")
                          
    kegiatan_sub_id  = colander.SchemaNode(
                          colander.Integer(),
                          oid="kegiatan_sub_id")
    kegiatan_kd      = colander.SchemaNode(
                          colander.String(),
                          title = "Kegiatan",
                          oid="kegiatan_kd")                      
    kegiatan_nm      = colander.SchemaNode(
                          colander.String(),
                          oid="kegiatan_nm")
 
    bendahara_uid    = colander.SchemaNode(
                          colander.Integer(),
                          oid="bendahara_uid",
                          title="Bendahara") 
    bendahara_nip    = colander.SchemaNode(
                          colander.String(),
                          oid="bendahara_nip",
                          missing=colander.drop,
                          title="Bendahara")                          
    bendahara_nm     = colander.SchemaNode(
                          colander.String(),
                          oid="bendahara_nm") 

    nama             = colander.SchemaNode(
                          colander.String(),
                          title="Uraian")
    kode             = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="No. Piutang")
    penyetor         = colander.SchemaNode(
                          colander.String(),
                          title="Penyetor")
    tgl_terima       = colander.SchemaNode(
                          colander.Date(),
                          title="Tgl.Terima")
    tgl_validasi     = colander.SchemaNode(
                          colander.Date(),
                          title="Validasi")
    alamat           = colander.SchemaNode(
                          colander.String(),
                          title="Alamat")
    nilai            = colander.SchemaNode(
                          colander.String(),
                          default=0,
                          oid="jml_total",
                          title="Nilai")

class EditSchema(AddSchema):
    id             = colander.SchemaNode(
                          colander.Integer(),
                          oid="id")

def get_form(request, class_form):
    schema = class_form(validator=form_validator)
    schema = schema.bind()
    schema.request = request
    return Form(schema, buttons=('simpan','batal'))
    
def save(request, values, row=None):
    if not row:
        row = ARInvoice()
    row.from_dict(values)
    
    if not row.kode:
        tahun    = request.session['tahun']
        unit_kd  = request.session['unit_kd']
        no_urut  = ARInvoice.get_norut(row.id)+1
        row.kode = "PIUTANG%d" % tahun + "-%s" % unit_kd + "-%d" % no_urut
        
    DBSession.add(row)
    DBSession.flush()
    return row
                                      
def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    values["nilai"]=values["nilai"].replace('.','')  
    row = save(request, values, row)
    request.session.flash('Tagihan sudah disimpan.')
    return row
        
def route_list(request):
    return HTTPFound(location=request.route_url('ar-invoice-skpd'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
@view_config(route_name='ar-invoice-skpd-add', renderer='templates/ar-invoice-skpd/add.pt',
             permission='add')
def view_add(request):
    form = get_form(request, AddSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items() 
            controls_dicted = dict(controls)
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                return dict(form=form)
            row = save_request(controls_dicted, request)
            return route_list(request)
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        del request.session[SESS_ADD_FAILED]
    return dict(form=form)

########
# Edit #
########
def query_id(request):
    return DBSession.query(ARInvoice).filter(ARInvoice.id==request.matchdict['id'])
    
def id_not_found(request):    
    msg = 'User ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='ar-invoice-skpd-edit', renderer='templates/ar-invoice-skpd/add.pt',
             permission='edit')
def view_edit(request):
    row = query_id(request).first()

    if not row:
        return id_not_found(request)
    if row.posted:
        request.session.flash('Data sudah diposting', 'error')
        return route_list(request)

    form = get_form(request, EditSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                return dict(form=form)
            save_request(dict(controls), request, row)
        return route_list(request)
    elif SESS_EDIT_FAILED in request.session:
        del request.session[SESS_EDIT_FAILED]
        return dict(form=form)
    values = row.to_dict() 
    
    #Ketika pas edit, kode sama nama muncul sesuai id kegiatansub
    values['kegiatan_nm']=row.kegiatansubs.nama
    kd=row.kegiatansubs.kode
    ur=row.kegiatansubs.no_urut
    values['kegiatan_kd']="%s" % kd + "-%d" % ur
    
    form.set_appstruct(values) 
    return dict(form=form)

##########
# Delete #
##########    
@view_config(route_name='ar-invoice-skpd-delete', renderer='templates/ar-invoice-skpd/delete.pt',
             permission='delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    
    if not row:
        return id_not_found(request)
    if row.posted:
        request.session.flash('Data sudah diposting', 'error')
        return route_list(request)
    if row.nilai:
        request.session.flash('Data tidak bisa dihapus, karena memiliki data items')
        return route_list(request)
        
    form = Form(colander.Schema(), buttons=('hapus','cancel'))
    values= {}
    if request.POST:
        if 'hapus' in request.POST:
            msg = '%s dengan kode %s telah berhasil.' % (request.title, row.kode)
            DBSession.query(ARInvoice).filter(ARInvoice.id==request.matchdict['id']).delete()
            DBSession.flush()
            request.session.flash(msg)
        return route_list(request)
    return dict(row=row,form=form.render())
    
###########
# Posting #
###########     
def save_request2(request, row=None):
    row = ARInvoice()
    request.session.flash('Tagihan sudah diposting dan dibuat Jurnalnya.')
    return row
    
@view_config(route_name='ar-invoice-skpd-posting', renderer='templates/ar-invoice-skpd/posting.pt',
             permission='posting')
def view_edit_posting(request):
    row = query_id(request).first()
    
    if not row:
        return id_not_found(request)
    if not row.nilai:
        request.session.flash('Data tidak dapat diposting, karena bernilai 0.', 'error')
        return route_list(request)
    if row.posted:
        request.session.flash('Data sudah diposting', 'error')
        return route_list(request)
        
    form = Form(colander.Schema(), buttons=('posting','cancel'))
    
    if request.POST:
        if 'posting' in request.POST: 
            #Update posted pada ARInvoice
            row.posted=1
            save_request2(request, row)
            
            #Tambah ke Jurnal SKPD
            nama    = row.nama
            kode    = row.kode
            tanggal = row.tgl_terima
            periode = ARInvoice.get_periode(row.id)
            
            row = AkJurnal()
            row.created    = datetime.now()
            row.create_uid = request.user.id
            row.updated    = datetime.now()
            row.update_uid = request.user.id
            row.tahun_id   = request.session['tahun']
            row.unit_id    = request.session['unit_id']
            row.nama       = "Diterima Piutang %s" % nama
            row.notes      = nama
            row.periode    = periode
            row.posted     = 0
            row.disabled   = 0
            row.is_skpd    = 1
            row.jv_type    = 1
            row.source     = "PIUTANG"
            row.source_no  = kode
            row.tgl_source = tanggal
            row.tanggal    = datetime.now()
            row.tgl_transaksi = datetime.now()
            
            if not row.kode:
                tahun    = request.session['tahun']
                unit_kd  = request.session['unit_kd']
                is_skpd  = row.is_skpd
                tipe     = AkJurnal.get_tipe(row.jv_type)
                no_urut  = AkJurnal.get_norut(row.id)+1
                row.kode = "%d" % tahun + "-%s" % is_skpd + "-%s" % unit_kd + "-%s" % tipe + "-%d" % no_urut
            
            DBSession.add(row)
            DBSession.flush()
            
        return route_list(request)
    return dict(row=row, form=form.render())    
    
#############
# UnPosting #
#############   
def save_request3(request, row=None):
    row = ARInvoice()
    request.session.flash('PIUTANG sudah di UnPosting.')
    return row
    
@view_config(route_name='ar-invoice-skpd-unposting', renderer='templates/ar-invoice-skpd/unposting.pt',
             permission='unposting') 
def view_edit_unposting(request):
    row = query_id(request).first()
    
    if not row:
        return id_not_found(request)
    if not row.posted:
        request.session.flash('Data tidak dapat di Unposting, karena belum diposting.', 'error')
        return route_list(request)
    if row.disabled:
        request.session.flash('Data jurnal PIUTANG sudah diposting.', 'error')
        return route_list(request)
        
    form = Form(colander.Schema(), buttons=('unposting','cancel'))
    
    if request.POST:
        if 'unposting' in request.POST: 
        
            #Update status posted pada PIUTANG
            row.posted=0
            save_request3(request, row)
            
            #Menghapus PIUTANG yang sudah menjadi jurnal
            DBSession.query(AkJurnal).filter(AkJurnal.source_no==row.kode).delete()
            DBSession.flush()
            
        return route_list(request)
    return dict(row=row, form=form.render())
    
    