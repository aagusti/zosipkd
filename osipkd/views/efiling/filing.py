import os
import uuid
from osipkd.tools import row2dict, xls_reader
from datetime import datetime
from sqlalchemy import not_, func
from pyramid.view import (
    view_config,
    )
from pyramid.httpexceptions import (
    HTTPFound,
    )
import colander
from deform import (
    Form,
    widget,
    ValidationFailure,
    FileData
    )
from osipkd.models import (
    DBSession,
    Group
    )
from osipkd.models.efiling_models import Filing

from datatables import ColumnDT, DataTables
from osipkd.views.base_view import BaseViews
    
class MemoryTmpStore(dict):
    """ Instances of this class implement the
    :class:`deform.interfaces.FileUploadTempStore` interface"""
    def preview_url(self, uid):
        return None

tmpstore = MemoryTmpStore()

SESS_ADD_FAILED = 'Tambah filing gagal'
SESS_EDIT_FAILED = 'Edit filing gagal'

kat_widget = widget.AutocompleteInputWidget(
        size=60,
        values = '/efiling/kategori/headofnama/act',
        min_length=1)
        
lok_widget = widget.AutocompleteInputWidget(
        size=60,
        values = '/efiling/lokasi/headofnama/act',
        min_length=1)
        
class UploadSequence(colander.SequenceSchema):
    upload = colander.SchemaNode(
        FileData(),
        widget=widget.FileUploadWidget(tmpstore)
        )
                
class AddSchema(colander.Schema):
    nama = colander.SchemaNode(
                    colander.String(),
                    title='Judul')
    tag  = colander.SchemaNode(
                    colander.String(),
                    title='Tag')                    
    kategori_id  = colander.SchemaNode(
                    colander.Integer(),
                    oid="kategori_id",
                    widget=widget.HiddenWidget()
                    )    
    kategori_nm  = colander.SchemaNode(
                    colander.String(),
                    widget = kat_widget,
                    title='Kategori',
                    oid="kategori_nm")    
    lokasi_id   = colander.SchemaNode(
                    colander.Integer(),
                    oid="lokasi_id",
                    widget=widget.HiddenWidget()
                    )
    lokasi_nm  = colander.SchemaNode(
                    colander.String(),
                    widget = lok_widget,
                    title='Lokasi',
                    oid="lokasi_nm")    
                    
    disabled = colander.SchemaNode(
                    colander.Boolean())
    upload = UploadSequence()
    
class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.String(),
            missing=colander.drop,
            widget=widget.HiddenWidget(readonly=True))
            
class view_filing(BaseViews):
    ########                    
    # List #
    ########    
    @view_config(route_name='efiling-filing', renderer='templates/filing/list.pt',
                 permission='read')
    def view_list(self):
        return dict(a={})
        
    ##########                    
    # Action #
    ##########    
    @view_config(route_name='efiling-filing-act', renderer='json',
                 permission='read')
    def view_act(self):
        ses = self.request.session
        req = self.request
        params = req.params
        url_dict = req.matchdict
        
        if url_dict['act']=='grid':
            columns = []
            columns.append(ColumnDT('id'))
            columns.append(ColumnDT('nama'))
            columns.append(ColumnDT('tag'))
            columns.append(ColumnDT('disabled'))
            
            query = DBSession.query(Filing)
            rowTable = DataTables(req, Filing, query, columns)
            return rowTable.output_result()
 
    #######    
    # Add #
    #######
    def form_validator(self, form, value):
        if 'id' in form.request.matchdict:
            uid = form.request.matchdict['id']
            q = DBSession.query(Filing).filter_by(id=uid)
            filing = q.first()
        else:
            filing = None
                
    def get_form(self, class_form, row=None):
        schema = class_form(validator=self.form_validator)
        schema = schema.bind()
        schema.request = self.request
        if row:
          schema.deserialize(row)
        return Form(schema, buttons=('simpan','batal'))
        
    def save(self, values, user, row=None):
        if not row:
            row = Filing()
            row.created = datetime.now()
            row.create_uid = user.id
        row.from_dict(values)
        row.updated = datetime.now()
        row.update_uid = user.id
        row.disabled = 'disabled' in values and values['disabled'] and 1 or 0
        DBSession.add(row)
        DBSession.flush()
        return row
        
    def save_request(self, values, row=None):
        if 'id' in self.request.matchdict:
            values['id'] = self.request.matchdict['id']
        row = self.save(values, self.request.user, row)
        self.request.session.flash('filing sudah disimpan.')
            
    def route_list(self):
        return HTTPFound(location=self.request.route_url('efiling-filing'))
        
    def session_failed(self, session_name):
        r = dict(form=self.session[session_name])
        del self.session[session_name]
        return r
        
    @view_config(route_name='efiling-filing-add', renderer='templates/filing/add.pt',
                 permission='add')
    def view_filing_add(self):
        req = self.request
        ses = self.session
        form = self.get_form(AddSchema)
        if req.POST:
            if 'simpan' in req.POST:
                controls = req.POST.items()
                try:
                    c = form.validate(controls)
                except ValidationFailure, e:
                    return dict(form=form)
                    
                self.save_request(dict(controls))
            return self.route_list()
        return dict(form=form)

        
    ########
    # Edit #
    ########
    def query_id(self):
        return DBSession.query(Filing).filter_by(id=self.request.matchdict['id'])
        
    def id_not_found(self):    
        msg = 'filing ID %s Tidak Ditemukan.' % self.request.matchdict['id']
        request.session.flash(msg, 'error')
        return route_list()

    @view_config(route_name='efiling-filing-edit', renderer='templates/filing/add.pt',
                 permission='edit')
    def view_filing_edit(self):
        request = self.request
        row = self.query_id().first()
        if not row:
            return id_not_found(request)
        form = self.get_form(EditSchema)
        if request.POST:
            if 'simpan' in request.POST:
                controls = request.POST.items()
                print controls
                try:
                    c = form.validate(controls)
                except ValidationFailure, e:
                    request.session[SESS_EDIT_FAILED] = e.render()               
                    return HTTPFound(location=request.route_url('filing-edit',
                                      id=row.id))
                self.save_request(dict(controls), row)
            return self.route_list()
        elif SESS_EDIT_FAILED in request.session:
            return self.session_failed(SESS_EDIT_FAILED)
        values = row.to_dict()
        values['kategori_nm']= row.kategoris and row.kategoris.nama or ""
        values['lokasi_nm']= row.lokasis and row.lokasis.nama or ""
        #for f in row.files:
        #    values[]
        form.set_appstruct(values)
        return dict(form=form)

    ##########
    # Delete #
    ##########    
    @view_config(route_name='efiling-filing-delete', renderer='templates/filing/delete.pt',
                 permission='delete')
    def view_delete(self):
        request = self.request
        q = self.query_id()
        row = q.first()
        
        if not row:
            return self.id_not_found(request)
        form = Form(colander.Schema(), buttons=('hapus','batal'))
        if request.POST:
            if 'hapus' in request.POST:
                msg = 'filing ID %d %s sudah dihapus.' % (row.id, row.nama)
                try:
                  q.delete()
                  DBSession.flush()
                except:
                  msg = 'filing ID %d %s tidak dapat dihapus.' % (row.id, row.nama)
                request.session.flash(msg)
            return self.route_list()
        return dict(row=row,
                     form=form.render())
