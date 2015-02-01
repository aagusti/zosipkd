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
from osipkd.models.apbd_tu import Sts, StsItem
    
from datatables import ColumnDT, DataTables
from osipkd.views.base_view import BaseViews

SESS_ADD_FAILED = 'Tambah STS gagal'
SESS_EDIT_FAILED = 'Edit STS gagal'

def deferred_jenis_id(node, kw):
    values = kw.get('jenis_id', [])
    return widget.SelectWidget(values=values)
    
JENIS_ID = (
    (1, 'Penerimaan'),
    (2, 'Kontra Pos'),
    (3, 'Lainnya'))
               
class AddSchema(colander.Schema):
    unit_kd_widget = widget.AutocompleteInputWidget(
            values = '/unit/act/headofkode',
            min_length=1)
  
    unit_nm_widget = widget.AutocompleteInputWidget(
            values = '/unit/act/headofnama',
            min_length=1)
            

    tahun_id = colander.SchemaNode(
                          colander.String(),
                          oid = "tahun_id",
                          title="Tahun")
    unit_id  = colander.SchemaNode(
                    colander.Integer(),
                    oid='unit_id',
                    title="SKPD")
    unit_kd  = colander.SchemaNode(
                    colander.String(),
                    oid='unit_kd',
                    title="SKPD",
                    widget = unit_kd_widget,)
    unit_nm  = colander.SchemaNode(
                    colander.String(),
                    oid='unit_nm',
                    title="SKPD",
                    widget = unit_nm_widget)

    no_urut  = colander.SchemaNode(
                   colander.Integer(),
                   missing=colander.drop,
                   )
    kode     = colander.SchemaNode(
                   colander.String(),
                   #missing=colander.drop,
                   title = "No. STS"
                   )
    nama     = colander.SchemaNode(
                   colander.String(),
                   title = "Uraian"
                          )
    jenis    =  colander.SchemaNode(
                    colander.String(),
                    validator=colander.Length(max=32),
                    widget=widget.SelectWidget(values=JENIS_ID)) 
                    
    nominal       = colander.SchemaNode(
                       colander.String(),
                       default = 0,
                       oid="jml_total",
                       title="Nominal"
                       )
    bank_nama      = colander.SchemaNode(
                       colander.String(),
                       title="Bank"
                       )
    bank_account  = colander.SchemaNode(
                       colander.String(),
                       title="Rekening"
                       )
    tgl_sts       = colander.SchemaNode(
                          colander.Date(),
                          title="Tgl.STS")
    tgl_validasi  = colander.SchemaNode(
                       colander.Date(),
                       title="Validasi")

class EditSchema(AddSchema):
    id             = colander.SchemaNode(
                          colander.Integer(),
                          oid="id")

class view_ar_payment_sts(BaseViews):
    @view_config(route_name="ar-payment-sts", renderer="templates/ar-sts/list.pt")
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
    @view_config(route_name='ar-payment-sts-act', renderer='json',
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
                
                query = DBSession.query(Sts).filter(
                          Sts.tahun_id == ses['tahun'],
                          Sts.unit_id == ses['unit_id']
                          )
                rowTable = DataTables(req, Sts, query, columns)
                return rowTable.output_result()
                
    def get_form(self, class_form):
        schema = class_form(validator=form_validator)
        schema = schema.bind(jenis_id=JENIS_ID)
        schema.request = self.request
        return Form(schema, buttons=('simpan','batal'))
        
    def save(self, values, row=None):
        if not row:
            row = Sts()
        row.created = datetime.now()
        row.from_dict(values)
        row.updated = datetime.now()
        
        if not row.no_urut:
            row.no_urut = Sts.max_no_urut(row.tahun_id,row.unit_id)+1;
                
        DBSession.add(row)
        DBSession.flush()
        return row
                                          
    def save_request(self, values, row=None):
        request = self.request
        if 'id' in request.matchdict:
            values['id'] = self.request.matchdict['id']
        values["nominal"]=values["nominal"].replace('.','')  
        row = self.save(values, row)
        request.session.flash('STS sudah disimpan.')
        return row
            
    def route_list(self):
        return HTTPFound(location=self.request.route_url('ar-payment-sts'))
        
    def session_failed(self, session_name):
        r = dict(form=self.request.session[session_name])
        del self.request.session[session_name]
        return r
        
    @view_config(route_name='ar-payment-sts-add', renderer='templates/ar-sts/add.pt',
                 permission='add')
    def view_add(self):
        request = self.request
        form = self.get_form(AddSchema)
        if request.POST:
            if 'simpan' in request.POST:
                controls = request.POST.items() 
                controls_dicted = dict(controls)
                try:
                    c = form.validate(controls)
                except ValidationFailure, e:
                    return dict(form=form)
                row = self.save_request(controls_dicted)
                return HTTPFound(location=request.route_url('ar-payment-sts-edit', 
                                          id=row.id))
            return self.route_list()
        elif SESS_ADD_FAILED in request.session:
            del request.session[SESS_ADD_FAILED]
        return dict(form=form)

    ########
    # Edit #
    ########
    def query_id(self):
        return DBSession.query(Sts).filter(Sts.id==self.request.matchdict['id'])
        
    def id_not_found(self):    
        msg = 'User ID %s not found.' % self.request.matchdict['id']
        self.request.session.flash(msg, 'error')
        return self.route_list()

    @view_config(route_name='ar-payment-sts-edit', renderer='templates/ar-sts/add.pt',
                 permission='edit')
    def view_edit(self):
        request = self.request
        row = self.query_id().first()
        if not row:
            return self.id_not_found()
        form = self.get_form(EditSchema)
        if request.POST:
            if 'simpan' in request.POST:
                controls = request.POST.items()
                try:
                    c = form.validate(controls)
                except ValidationFailure, e:
                    return dict(form=form)
                self.save_request(dict(controls), row)
            return self.route_list()
        elif SESS_EDIT_FAILED in request.session:
            del request.session[SESS_EDIT_FAILED]
            return dict(form=form)
        values = row.to_dict() #dict(zip(row.keys(), row))
        ##values['kegiatan_nm']=row.kegiatansubs.nama
        #values['kegiatan_kd']=row.kegiatansubs.kode
        form.set_appstruct(values) 
        return dict(form=form)

    ##########
    # Delete #
    ##########    
    @view_config(route_name='ar-payment-sts-delete', renderer='templates/ar-sts/delete.pt',
                 permission='delete')
    def view_delete(self):
        request = self.request
        q = self.query_id()
        row = q.first()
        
        if not row:
            return self.id_not_found()
        form = Form(colander.Schema(), buttons=('hapus','cancel'))
        values= {}
        if request.POST:
            if 'hapus' in request.POST:
                msg = 'STS ID %d %s sudah dihapus.' % (row.id, row.nama)
                DBSession.query(Sts).filter(Sts.id==request.matchdict['id']).delete()
                DBSession.flush()
                request.session.flash(msg)
            return self.route_list()
        return dict(row=row,
                     form=form.render())
                 
#######    
# Add #
#######
def form_validator(form, value):
    def err_kegiatan():
        raise colander.Invalid(form,
            'Kegiatan dengan no urut tersebut sudah ada')      
 