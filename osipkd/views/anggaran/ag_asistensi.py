import os
import uuid
from osipkd.tools import row2dict, xls_reader
from datetime import datetime
from sqlalchemy import not_, func, or_, cast, BigInteger
from pyramid.view import (view_config,)
from pyramid.httpexceptions import ( HTTPFound, )
import colander
from deform import (Form, widget, ValidationFailure, )
from osipkd.models import DBSession
from osipkd.models.apbd_anggaran import Kegiatan, KegiatanSub, KegiatanItem, KegiatanIndikator, KegiatanAsistensi
from osipkd.models.pemda_model import Rekening, Unit
from datatables import ColumnDT, DataTables
from osipkd.views.base_view import BaseViews

SESS_ADD_FAILED = 'Tambah ag-asistensi gagal'
SESS_EDIT_FAILED = 'Edit ag-asistensi gagal'

class view_ag_asistensi(BaseViews):
    @view_config(route_name="ag-asistensi", renderer="templates/ag-asistensi/list.pt",
                 permission='read')
    def view_list(self):
        ses = self.request.session
        req = self.request
        params = req.params
        url_dict = req.matchdict
        kegiatan_sub_id =  url_dict['kegiatan_sub_id']
        row = KegiatanSub.query_id(kegiatan_sub_id).filter(KegiatanSub.unit_id==ses['unit_id']).first()
        return dict(project='OSIPKD', row = row)
        
    ##########                    
    # Action #
    ##########              
    @view_config(route_name='ag-asistensi-act', renderer='json',
                 permission='read')
    def ag_asistensi_act(self):
        ses = self.request.session
        req = self.request
        params = req.params
        url_dict = req.matchdict
        if url_dict['act']=='grid':
            ag_step_id  = ses['ag_step_id']
            kegiatan_sub_id = 'kegiatan_sub_id' in params and params['kegiatan_sub_id'] or 0
            columns = []
            columns.append(ColumnDT('id'))
            columns.append(ColumnDT('units.nama'))
            columns.append(ColumnDT('catatan_%s' %ag_step_id))

            query = DBSession.query(KegiatanAsistensi)\
                .join(KegiatanSub,Unit)\
                .filter(KegiatanSub.id==kegiatan_sub_id,
                        KegiatanSub.unit_id==ses['unit_id'])
            rowTable = DataTables(req, KegiatanAsistensi, query, columns)
            return rowTable.output_result()

#######    
# Add #
#######
def form_validator(form, value):
    def err_kegiatan():
        raise colander.Invalid(form,
            'Kegiatan dengan no urut tersebut sudah ada')
                
class AddSchema(colander.Schema):

    kegiatan_sub_id    = colander.SchemaNode(
                          colander.String(),
                          )
                          
    unit_asistensi_id  = colander.SchemaNode(
                          colander.String(),
                          oid = "unit_asistensi_id")
    unit_asistensi_kd  = colander.SchemaNode(
                          colander.String(),
                          title="SKPD Asistensi",
                          oid = "unit_asistensi_kd")
    unit_asistensi_nm  = colander.SchemaNode(
                          colander.String(),
                          oid = "unit_asistensi_nm")

    catatan_1        = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          widget=widget.TextAreaWidget(rows=10, cols=60),
                          title="Asistensi RKA",
                          oid = "catatan_1")
    catatan_2        = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          widget=widget.TextAreaWidget(rows=10, cols=60),
                          title="Asistensi DPA",
                          oid = "catatan_2")
    catatan_3        = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          widget=widget.TextAreaWidget(rows=10, cols=60),
                          title="Asistensi RDPPA",
                          oid = "catatan_3")
    catatan_4        = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          widget=widget.TextAreaWidget(rows=10, cols=60),
                          title="Asistensi DPPA",
                          oid = "catatan_4")
                          
    ttd_nip_1        = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="Kabid",
                          oid = "ttd_nip_1")
    ttd_nip_2        = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="Kasubid",
                          oid = "ttd_nip_2")
    ttd_nip_3        = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="Pelaksana",
                          oid = "ttd_nip_3")
    ttd_nama_1        = colander.SchemaNode(
                          colander.String(),
                          oid = "ttd_nama_1")
    ttd_nama_2        = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          oid = "ttd_nama_2")
    ttd_nama_3        = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          oid = "ttd_nama_3")
                          
                          
class EditSchema(AddSchema):
    id             = colander.SchemaNode(
                          colander.Integer(),)

def get_form(request, class_form):
    schema = class_form(validator=form_validator)
    schema = schema.bind()
    schema.request = request
    return Form(schema, buttons=('simpan','batal'))
    
def save(values, request, row=None):
    if not row:
        row = KegiatanAsistensi()
    ag_step_id = request.session['ag_step_id']
    
    if not values['catatan_1']: 
        values['catatan_1']='-'
    if not values['catatan_2']: 
        values['catatan_2']='-'
    if not values['catatan_3']: 
        values['catatan_3']='-'
    if not values['catatan_4']: 
        values['catatan_4']='-'
        
    
        
    row.from_dict(values)
    
    DBSession.add(row)
    DBSession.flush()
    return row
                                      
def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(values, request, row)
    request.session.flash('Kegiatan Asistensi sudah disimpan.')
        
def route_list(request,kegiatan_sub_id):
    return HTTPFound(location=request.route_url('ag-asistensi',kegiatan_sub_id=kegiatan_sub_id))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
@view_config(route_name='ag-asistensi-add', renderer='templates/ag-asistensi/add.pt',
             permission='add')
def view_add(request):
    form = get_form(request, AddSchema)
    kegiatan_sub_id = request.matchdict['kegiatan_sub_id']
    
    ## Cek sudah Posting atau belum    
    q = DBSession.query(KegiatanSub.disabled).filter(KegiatanSub.id==request.matchdict['kegiatan_sub_id'])
    rowsub = q.first()
    if rowsub.disabled:
        request.session.flash('Data tidak dapat ditambah karena sudah Posting', 'error')
        return route_list(request, kegiatan_sub_id)
    
    ses = request.session
    rows = KegiatanSub.query_id(kegiatan_sub_id).filter(KegiatanSub.unit_id == ses['unit_id']).first()
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            controls_dicted = dict(controls)
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                return dict(form=form, row=rows)
            save_request(controls_dicted, request)
        return route_list(request,kegiatan_sub_id)
    elif SESS_ADD_FAILED in request.session:
        del request.session[SESS_ADD_FAILED]
    return dict(form=form, row=rows)

########
# Edit #
########
def query_id(request):
    return DBSession.query(KegiatanAsistensi).filter(KegiatanAsistensi.id==request.matchdict['id'])
    
def id_not_found(request,kegiatan_sub_id):    
    msg = 'ITEM ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request,kegiatan_sub_id)

@view_config(route_name='ag-asistensi-edit', renderer='templates/ag-asistensi/add.pt',
             permission='edit')
def view_edit(request):
    form = get_form(request, EditSchema)
    ses = request.session
    kegiatan_sub_id = request.matchdict['kegiatan_sub_id']
    row = query_id(request).first()
    if not row:
        return id_not_found(request,kegiatan_sub_id)
        
    ## Cek sudah Posting atau belum    
    q = DBSession.query(KegiatanSub.disabled).filter(KegiatanSub.id==request.matchdict['kegiatan_sub_id'])
    rowsub = q.first()
    if rowsub.disabled:
        request.session.flash('Data tidak dapat diupdate karena sudah Posting', 'error')
        return route_list(request, kegiatan_sub_id)
        
    rows = KegiatanSub.query_id(kegiatan_sub_id).filter(KegiatanSub.unit_id==ses['unit_id']).first()
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()  
            save_request(dict(controls), request, row)
        return route_list(request,kegiatan_sub_id)
    elif SESS_EDIT_FAILED in request.session:
        del request.session[SESS_EDIT_FAILED]
        return dict(form=form)
    values = row.to_dict()
    values['unit_asistensi_kd']=row.units.kode
    values['unit_asistensi_nm']=row.units.nama
    form.set_appstruct(values) 
    return dict(form=form, row=rows)

##########
# Delete #
##########    
@view_config(route_name='ag-asistensi-delete', renderer='templates/ag-asistensi/delete.pt',
             permission='delete')
def view_delete(request):
    q = query_id(request)
    kegiatan_sub_id = request.matchdict['kegiatan_sub_id']
    row = q.first()
        
    if not row:
        return id_not_found(request,kegiatan_sub_id)
        
    ## Cek sudah Posting atau belum    
    q = DBSession.query(KegiatanSub.disabled).filter(KegiatanSub.id==request.matchdict['kegiatan_sub_id'])
    rowsub = q.first()
    if rowsub.disabled:
        request.session.flash('Data tidak dapat dihapus karena sudah Posting', 'error')
        return route_list(request, kegiatan_sub_id)
    
    form = Form(colander.Schema(), buttons=('hapus','cancel'))
    values= {}
    
    if request.POST:
        if 'hapus' in request.POST:
            msg = '%s berhasil.' % (request.title)
            DBSession.query(KegiatanAsistensi).filter(KegiatanAsistensi.id==request.matchdict['id']).delete()
            DBSession.flush()
            request.session.flash(msg)
        return route_list(request,kegiatan_sub_id)
    return dict(row=row, form=form.render())

            
                        