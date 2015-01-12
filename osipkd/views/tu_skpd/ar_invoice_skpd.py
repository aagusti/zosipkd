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
from osipkd.models.pemda_model import Unit
from osipkd.models.apbd_tu import ARInvoice, ARInvoiceItem
    
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
        return dict(project='EIS', #row = row
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

                query = DBSession.query(ARInvoice.id,
                          ARInvoice.kode,
                          ARInvoice.tgl_terima,
                          ARInvoice.tgl_validasi,
                          ARInvoice.bendahara_nm,
                          ARInvoice.penyetor,
                          ARInvoice.nama,
                          ARInvoice.nilai,
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
    bendahara_nm     = colander.SchemaNode(
                          colander.String(),
                          oid="bendahara_nm") 

    nama             = colander.SchemaNode(
                          colander.String(),
                          title="Uraian")
    kode             = colander.SchemaNode(
                          colander.String(),
                          title="Kode")
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
    
def save(values, row=None):
    if not row:
        row = ARInvoice()
    row.from_dict(values)
    #if not row.no_urut:
    #      row.no_urut = ARInvoice.max_no_urut(row.tahun_id,row.unit_id)+1;
    DBSession.add(row)
    DBSession.flush()
    return row
                                      
def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    values["nilai"]=values["nilai"].replace('.','')  
    row = save(values, row)
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
            return HTTPFound(location=request.route_url('ar-invoice-skpd-edit', 
                                      id=row.id))
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
    values = row.to_dict() #dict(zip(row.keys(), row))
    values['kegiatan_nm']=row.kegiatansubs.nama
    values['kegiatan_kd']=row.kegiatansubs.kode
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
    form = Form(colander.Schema(), buttons=('hapus','cancel'))
    values= {}
    if request.POST:
        if 'hapus' in request.POST:
            msg = '%s Kode %s %s sudah dihapus.' % (request.title, row.kode, row.nama)
            DBSession.query(ARInvoice).filter(ARInvoice.id==request.matchdict['id']).delete()
            DBSession.flush()
            request.session.flash(msg)
        return route_list(request)
    return dict(row=row,
                 form=form.render())