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
from osipkd.models.apbd_tu import Sts, StsItem
    
from datatables import ColumnDT, DataTables
from osipkd.views.base_view import BaseViews
    

SESS_ADD_FAILED = 'Tambah ar-sts gagal'
SESS_EDIT_FAILED = 'Edit ar-sts gagal'

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
            
                    
    kegiatan_nm_widget = widget.AutocompleteInputWidget(
            size=60,
            values = '/ag-kegiatan-sub/act/headofnama1',
            min_length=1)
  
    kegiatan_kd_widget = widget.AutocompleteInputWidget(
            size=60,
            values = '/ag-kegiatan-sub/act/headofkode1',
            min_length=1)

    tahun_id         = colander.SchemaNode(
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
    kegiatan_sub_id  = colander.SchemaNode(
                    colander.Integer(),
                    oid='kegiatan_sub_id',
                    title="SKPD")
    kegiatan_kd  = colander.SchemaNode(
                    colander.String(),
                    oid='kegiatan_sub_kd',
                    title="Kegiatan",
                    widget = kegiatan_kd_widget,)

    kegiatan_nm  = colander.SchemaNode(
                    colander.String(),
                    oid='kegiatan_sub_nm',
                    widget = kegiatan_nm_widget)

    no_urut         = colander.SchemaNode(
                          colander.Integer(),
                          missing=colander.drop,
                          )
    kode            = colander.SchemaNode(
                          colander.String(),
                          title = "No. STS"
                          )
    nama            = colander.SchemaNode(
                          colander.String(),
                          title = "Uraian"
                          )
    jenis  =  colander.SchemaNode(
                    colander.String(),
                    validator=colander.Length(max=32),
                    widget=widget.SelectWidget(values=JENIS_ID)) 
                    
    nominal         = colander.SchemaNode(
                          colander.String(),
                          default = 0,
                          oid="jml_total",
                          title="Nominal"
                          )
    ttd_uid         = colander.SchemaNode(
                          colander.Integer(),
                          missing=colander.drop,
                          oid="ttd_uid"
                          )
    ttd_nip         = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          oid="ttd_nip",
                          title="TTD"
                          )
    ttd_nama        = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          oid="ttd_nama",
                          title="Nama")
    ttd_jab         = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          oid="ttd_jab",
                          title="Jabatan")
    bank_nama         = colander.SchemaNode(
                          colander.String(),
                          title="Bank"
                          )
    bank_account     = colander.SchemaNode(
                          colander.String(),
                          title="Rekening"
                          )
    tgl_sts       = colander.SchemaNode(
                          colander.Date(),
                          title="Tgl.STS")
    tgl_validasi     = colander.SchemaNode(
                          colander.Date(),
                          title="Validasi")

                    
class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.String(),
            missing=colander.drop,
            widget=widget.HiddenWidget(readonly=True))
            
class view_ar_sts(BaseViews):
    ########                    
    # List #
    ########    
    @view_config(route_name='ar-sts', renderer='templates/ar-sts/list.pt',
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
    @view_config(route_name='ar-sts-act', renderer='json',
                 permission='read')
    def ar_sts_act(self):
        ses = self.request.session
        req = self.request
        params = req.params
        url_dict = req.matchdict
        kegiatan_sub_id = 'kegiatan_sub_id' in params and params['kegiatan_sub_id'] or 0
        if url_dict['act']=='grid':
            columns = []
            columns.append(ColumnDT('id'))
            columns.append(ColumnDT('kode'))
            columns.append(ColumnDT('tgl_sts', filter=self._DTstrftime))
            columns.append(ColumnDT('tgl_validasi', filter=self._DTstrftime))
            columns.append(ColumnDT('jenis'))
            columns.append(ColumnDT('nama'))
            columns.append(ColumnDT('kegiatansubs.nama'))
            columns.append(ColumnDT('nominal'))
            
            query = DBSession.query(Sts).filter(
                      Sts.tahun_id == ses['tahun'],
                      Sts.unit_id == ses['unit_id']
                      )
            rowTable = DataTables(req, Sts, query, columns)
            return rowTable.output_result()
        
    #######    
    # Add #
    #######
    def form_validator(self, form, value):
        if 'id' in form.request.matchdict:
            uid = form.request.matchdict['id']
            q = DBSession.query(Sts).filter_by(id=uid)
            row = q.first()
        else:
            row = None
                
    def get_form(self, class_form, row=None):
        schema = class_form(validator=self.form_validator)
        schema = schema.bind(jenis_id=JENIS_ID)
        schema.request = self.request
        if row:
          schema.deserialize(row)
        return Form(schema, buttons=('simpan','batal'))
        
    def save(self, values, user, row=None):
        if not row:
            row = Sts()
        row.created = datetime.now()
        row.create_uid = user.id
        row.from_dict(values)
        row.updated = datetime.now()
        row.update_uid = user.id
        if not row.no_urut:
           row.no_urut = Sts.max_no_urut(row.tahun_id,row.unit_id)+1;
        #tanggal    = datetime.strptime(values['tanggal'], '%Y-%m-%d')
        #row.tahun  = tanggal.year
        #row.bulan  = tanggal.month
        #row.hari   = tanggal.day
        #row.minggu = tanggal.isocalendar()[1]
        #row.disable   = 'disable' in values and values['disable'] and 1 or 0
        #row.is_kota   = 'is_kota' in values and values['is_kota'] and 1 or 0
        DBSession.add(row)
        DBSession.flush()
        return row
        
    def save_request(self, values, row=None):
        if 'id' in self.request.matchdict:
            values['id'] = self.request.matchdict['id']
        row = self.save(values, self.request.user, row)
        self.request.session.flash('STS sudah disimpan.')
            
    def route_list(self):
        return HTTPFound(location=self.request.route_url('ar-sts') )
        
    def session_failed(self, session_name):
            
        #r = dict(form=self.session[session_name])
        del self.session[session_name]
        #return r
        
    @view_config(route_name='ar-sts-add', renderer='templates/ar-sts/add.pt',
                 permission='add')
    def view_ar_sts_add(self):
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
                    #return HTTPFound(location=req.route_url('ar-sts-add'))
                self.save_request(dict(controls))
            return self.route_list()
        elif SESS_ADD_FAILED in req.session:
            return dict(form=form)
        
            #return self.session_failed(SESS_ADD_FAILED)
        return dict(form=form)

        
    ########
    # Edit #
    ########
    def query_id(self):
        return DBSession.query(Sts).filter_by(id=self.request.matchdict['id'])
        
    def id_not_found(self):    
        msg = 'STS ID %s Tidak Ditemukan.' % self.request.matchdict['id']
        request.session.flash(msg, 'error')
        return route_list()

    @view_config(route_name='ar-sts-edit', renderer='templates/ar-sts/add.pt',
                 permission='edit')
    def view_ar_sts_edit(self):
        request = self.request
        row = self.query_id().first()
        if not row:
            return id_not_found(request)
        #values = row.to_dict()
        #rowd={}
        #rowd['id']          = row.id
        #rowd['unit_id']     = row.unit_id
        #rowd['unit_nm']     = row.units.nama
        #rowd['unit_kd']     = row.units.kode
        #rowd['kegiatan_sub_id'] =row.kegiatansubs.id
        #rowd['kegiatan_sub_kd'] =row.kegiatansubs.kode
        #rowd['kegiatan_sub_nm'] =row.kegiatansubs.nama
        #rowd['kode']        = row.kode
        #rowd['nama']        = row.nama
        #rowd['disabled']    = row.disabled
        #rowd['jenis_id']    = row.jenis_id
        
        form = self.get_form(EditSchema)
        #form.set_appstruct(rowd)
        if request.POST:
            if 'simpan' in request.POST:
                controls = request.POST.items()
                print controls
                try:
                    c = form.validate(controls)
                except ValidationFailure, e:
                    return dict(form=form)
                    #request.session[SESS_EDIT_FAILED] = e.render()               
                    #return HTTPFound(location=request.route_url('ar-sts-edit',
                    #                  id=row.id))
                self.save_request(dict(controls), row)
            return self.route_list()
        elif SESS_EDIT_FAILED in request.session:
            return self.session_failed(SESS_EDIT_FAILED)
            return dict(form=form)
        values = row.to_dict()
        values['kegiatan_nm']=row.kegiatansubs.nama
        values['kegiatan_kd']=row.kegiatansubs.kode
        form.set_appstruct(values) 
        return dict(form=form)

    ##########
    # Delete #
    ##########    
    @view_config(route_name='ar-sts-delete', renderer='templates/ar-sts/delete.pt',
                 permission='delete')
    def view_ar_sts_delete(self):
        request = self.request
        q = self.query_id()
        row = q.first()
        
        if not row:
            return self.id_not_found(request)
        form = Form(colander.Schema(), buttons=('hapus','batal'))
        if request.POST:
            if 'hapus' in request.POST:
                msg = 'STS ID %d %s sudah dihapus.' % (row.id, row.nama)
                try:
                  q.delete()
                  DBSession.flush()
                except:
                  msg = 'STS ID %d %s tidak dapat dihapus.' % (row.id, row.nama)
                request.session.flash(msg)
            return self.route_list()
        return dict(row=row,
                     form=form.render())

