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
from osipkd.models.apbd import Jurnal, JurnalItem
    
from datatables import ColumnDT, DataTables
from osipkd.views.base_view import BaseViews

SESS_ADD_FAILED = 'Tambah ak-jurnal gagal'
SESS_EDIT_FAILED = 'Edit ak-jurnal gagal'

def deferred_jv_type(node, kw):
    values = kw.get('jv_type', [])
    return widget.SelectWidget(values=values)
    
JV_TYPE = (
    (1, 'LRA'),
    (2, 'LO'),
    (3, 'Jurnal Umum'),
    )

class AddSchema(colander.Schema):
    unit_kd_widget = widget.AutocompleteInputWidget(
            values = '/unit/act/headofkode',
            min_length=1)
  
    unit_nm_widget = widget.AutocompleteInputWidget(
            values = '/unit/act/headofnama',
            min_length=1)
            
          
    unit_id  = colander.SchemaNode(
                    colander.Integer(),
                    oid='unit_id',
                    title="SKPD ID")

    unit_kd  = colander.SchemaNode(
                    colander.String(),
                    oid='unit_kd',
                    title="SKPD",
                    widget = unit_kd_widget,)

    unit_nm  = colander.SchemaNode(
                    colander.String(),
                    oid='unit_nm',
                    title="SKPD NM",
                    widget = unit_nm_widget)
    kode        = colander.SchemaNode(
                    colander.String(),
                    )
                    
    nama        = colander.SchemaNode(
                    colander.String(),
                    )
    tanggal     = colander.SchemaNode(
                  colander.Date(),
                  )
               
    jv_type     = colander.SchemaNode(
                    colander.String(),
                    widget=widget.SelectWidget(values=JV_TYPE),
                    title="Tipe"
                    )
    source_no   = colander.SchemaNode(
                    colander.String(),
                    validator=colander.Length(max=32),
                    title = "Referensi"
                    )
    source      = colander.SchemaNode(
                    colander.String(),
                    validator=colander.Length(max=64),
                    )
    tgl_source  = colander.SchemaNode(
                    colander.Date(),
                    title = "Tgl"
                )
    
    notes       = colander.SchemaNode(
                    colander.String(),
                    missing = colander.drop
                    )
    is_skpd     = colander.SchemaNode(
                    colander.Boolean()
                  )
                    
                    
class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.String(),
            missing=colander.drop,
            widget=widget.HiddenWidget(readonly=True),
            oid="id")
            
class view_ak_jurnal(BaseViews):
    ########                    
    # List #
    ########    
    @view_config(route_name='ak-jurnal', renderer='templates/ak-jurnal/list.pt',
                 permission='read')
    def view_list(self):
        ses = self.request.session
        req = self.request
        params = req.params
        url_dict = req.matchdict
        return dict(project='EIS')
        
    ##########                    
    # Action #
    ##########    
    @view_config(route_name='ak-jurnal-act', renderer='json',
                 permission='read')
    def ak_jurnal_act(self):
        ses = self.request.session
        req = self.request
        params = req.params
        url_dict = req.matchdict
        if url_dict['act']=='grid':
            columns = []
            columns.append(ColumnDT('id'))
            columns.append(ColumnDT('tanggal', filter=self._DTstrftime))
            columns.append(ColumnDT('kode'))
            columns.append(ColumnDT('nama'))
            columns.append(ColumnDT('amount',  filter=self._number_format))
            columns.append(ColumnDT('posted'))
            
            query = DBSession.query(Jurnal.id, Jurnal.tanggal, Jurnal.kode, 
                      Jurnal.nama, Jurnal.posted,
                      func.div(func.coalesce(func.sum(JurnalItem.amount),0),2).label('amount')).\
                    outerjoin(JurnalItem).\
                    group_by(Jurnal.id, Jurnal.tanggal, Jurnal.kode, 
                             Jurnal.nama, ).\
                    filter(Jurnal.tahun_id == ses['tahun'],
                           Jurnal.unit_id == ses['unit_id'],)
                      
            rowTable = DataTables(req, Jurnal, query, columns)
            return rowTable.output_result()
        
    #######    
    # Add #
    #######
    def form_validator(self, form, value):
        if 'id' in form.request.matchdict:
            uid = form.request.matchdict['id']
            q = DBSession.query(Jurnal).filter_by(id=uid)
            row = q.first()
        else:
            row = None
                
    def get_form(self, class_form, row=None):
        schema = class_form(validator=self.form_validator)
        schema = schema.bind(jv_type=JV_TYPE)
        schema.request = self.request
        if row:
          schema.deserialize(row)
        return Form(schema, buttons=('simpan','batal'))
        
    def save(self, values, user, row=None):
        if not row:
            row = Jurnal()
            row.created = datetime.now()
            row.create_uid = user.id
        row.from_dict(values)
        tanggal    = datetime.strptime(values['tanggal'], '%Y-%m-%d')
        row.tahun_id  = tanggal.year
        row.periode  = tanggal.month
        row.hari   = tanggal.day
        
        row.updated = datetime.now()
        row.update_uid = user.id
        row.disable   = 'disable' in values and values['disable'] and 1 or 0
        row.is_skpd   = 'is_skpd' in values and values['is_skpd'] and 1 or 0
        row.posted    = 'posted' in values and values['posted'] and 1 or 0
        DBSession.add(row)
        DBSession.flush()
        return row
        
    def save_request(self, values, row=None):
        if 'id' in self.request.matchdict:
            values['id'] = self.request.matchdict['id']
        row = self.save(values, self.request.user, row)
        self.request.session.flash('Jurnal sudah disimpan.')
        return row
            
    def route_list(self, id):
        if id:
            return HTTPFound(location=self.request.route_url('ak-jurnal-edit', id=id) )
        else:
            return HTTPFound(location=self.request.route_url('ak-jurnal', id=id) )
        
    def session_failed(self, session_name):
        #r = dict(form=self.session[session_name])
        del self.session[session_name]
        #return r
        
    @view_config(route_name='ak-jurnal-add', renderer='templates/ak-jurnal/add.pt',
                 permission='add')
    def view_ak_jurnal_add(self):
        req = self.request
        ses = self.session
        form = self.get_form(AddSchema)
        if req.POST:
            if 'simpan' in req.POST:
                controls = req.POST.items()
                try:
                    c = form.validate(controls)
                except ValidationFailure, e:
                    #req.session[SESS_ADD_FAILED] = e.render()     
                    #form.set_appstruct(rowd)
                    return dict(form=form)
                    #return HTTPFound(location=req.route_url('ak-jurnal-add'))
                id = self.save_request(dict(controls)).id
            return self.route_list(id)
            
        elif SESS_ADD_FAILED in req.session:
            return dict(form=form)
        
            #return self.session_failed(SESS_ADD_FAILED)
        return dict(form=form)

        
    ########
    # Edit #
    ########
    def query_id(self):
        return DBSession.query(Jurnal).filter_by(id=self.request.matchdict['id'])
        
    def id_not_found(self):    
        msg = 'Jurnal ID %s Tidak Ditemukan.' % self.request.matchdict['id']
        request.session.flash(msg, 'error')
        return route_list()

    @view_config(route_name='ak-jurnal-edit', renderer='templates/ak-jurnal/add.pt',
                 permission='edit')
    def view_ak_jurnal_edit(self):
        request = self.request
        row = self.query_id().first()
        if not row:
            return id_not_found(request)
        #values = row.to_dict()
        rowd={}
        rowd['id']            = row.id
        rowd['unit_id']       = row.unit_id
        rowd['unit_nm']       = row.units.nama
        rowd['unit_kd']       = row.units.kode
        rowd['kode']          = row.kode
        rowd['nama']          = row.nama
        rowd['source_no']     = row.source_no
        rowd['source']        = row.source
        rowd['tgl_source']    = row.tgl_source
        rowd['tanggal']       = row.tanggal
        rowd['jv_type']       = row.jv_type
        rowd['disabled']      = row.disabled
        
        form = self.get_form(EditSchema)
        form.set_appstruct(rowd)
        if request.POST:
            if 'simpan' in request.POST:
                controls = request.POST.items()
                print controls
                try:
                    c = form.validate(controls)
                except ValidationFailure, e:
                    return dict(form=form)
                    #request.session[SESS_EDIT_FAILED] = e.render()               
                    #return HTTPFound(location=request.route_url('ak-jurnal-edit',
                    #                  id=row.id))
                id = self.save_request(dict(controls)).id
            return self.route_list(id)
        elif SESS_EDIT_FAILED in request.session:
            return self.session_failed(SESS_EDIT_FAILED)
        return dict(form=form)

    ##########
    # Delete #
    ##########    
    @view_config(route_name='ak-jurnal-delete', renderer='templates/ak-jurnal/delete.pt',
                 permission='delete')
    def view_ak_jurnal_delete(self):
        request = self.request
        q = self.query_id()
        row = q.first()
        
        if not row:
            return self.id_not_found(request)
        form = Form(colander.Schema(), buttons=('hapus','batal'))
        if request.POST:
            if 'hapus' in request.POST:
                msg = 'Jurnal ID %d %s sudah dihapus.' % (row.id, row.nama)
                try:
                  q.delete()
                  DBSession.flush()
                except:
                  msg = 'Jurnal ID %d %s tidak dapat dihapus.' % (row.id, row.nama)
                request.session.flash(msg)
            return self.route_list()
        return dict(row=row,
                     form=form.render())

