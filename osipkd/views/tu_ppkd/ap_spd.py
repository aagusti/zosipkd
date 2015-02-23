import os
import uuid
from osipkd.tools import row2dict, xls_reader
from datetime import datetime,date
from sqlalchemy import not_, func
from pyramid.view import (view_config,)
from pyramid.httpexceptions import ( HTTPFound, )
import colander
from deform import (Form, widget, ValidationFailure, )
from osipkd.models import DBSession
from osipkd.models.apbd_anggaran import Kegiatan, KegiatanSub, KegiatanItem
from osipkd.models.pemda_model import Unit
from osipkd.models.apbd_tu import Spd, SpdItem
    
from datatables import ColumnDT, DataTables
from osipkd.views.base_view import BaseViews

SESS_ADD_FAILED = 'Tambah ap-spd gagal'
SESS_EDIT_FAILED = 'Edit ap-spd gagal'

def deferred_trw(node, kw):
    values = kw.get('trw_id', [])
    return widget.SelectWidget(values=values)

TRW = (
    (1, 'I'),
    (2, 'II'),
    (3, 'III'),
    (4, 'IV'),
    )

def deferred_is_bl(node, kw):
    values = kw.get('is_bl', [])
    return widget.SelectWidget(values=values)
    
IS_BL = (
    (0, 'BTL'),
    (1, 'BL'))    
    
class view_ap_spd_ppkd(BaseViews):

    @view_config(route_name="ap-spd", renderer="templates/ap-spd/list.pt")
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
    @view_config(route_name='ap-spd-act', renderer='json',
                 permission='read')
    def view_act(self):
        ses = self.request.session
        req = self.request
        params = req.params
        url_dict = req.matchdict
        if url_dict['act']=='grid':
            pk_id = 'id' in params and params['id'] and int(params['id']) or 0
            if url_dict['act']=='grid':
                columns = []
                columns.append(ColumnDT('id'))
                columns.append(ColumnDT('kode'))
                columns.append(ColumnDT('unit_nm'))
                columns.append(ColumnDT('nama'))
                columns.append(ColumnDT('triwulan_id'))
                columns.append(ColumnDT('nominal'))
                query = DBSession.query(Spd.id, Spd.kode,
                          Spd.nama, Spd.triwulan_id, Spd.units,
                          Unit.nama.label('unit_nm'),
                          func.sum(SpdItem.nominal).label('nominal')
                        ).join(Unit
                        ).outerjoin(SpdItem
                        ).filter(Spd.tahun_id==ses['tahun'],
                                 Spd.unit_id==ses['unit_id'],
                        ).group_by(Spd.id, Spd.kode,
                          Spd.nama, Spd.triwulan_id,
                          Unit.id, Unit.nama)
                rowTable = DataTables(req, Spd, query, columns)
                return rowTable.output_result()
                
        elif url_dict['act']=='headofkode1':
            term = 'term' in params and params['term'] or ''
            q = DBSession.query(Spd.id, Spd.kode.label('spd_kd'), Spd.nama.label('spd_nm'), Spd.tanggal.label('spd_tgl')
                      ).filter(Spd.unit_id == ses['unit_id'],
                           Spd.tahun_id==ses['tahun'],
                           Spd.kode.ilike('%%%s%%' % term))        
            rows = q.all()
            r = []
            for k in rows:
                d={}
                d['id']          = k[0]
                d['value']       = k[1]
                d['kode']        = k[1]
                d['nama']        = k[2]
                d['tanggal']     = "%s" % k[3]
                r.append(d)    
            return r
            
        elif url_dict['act']=='headofnama1':
            term = 'term' in params and params['term'] or ''
            q = DBSession.query(Spd.id, Spd.kode.label('spd_kd'), Spp.nama.label('spd_nm'), Spd.tanggal.label('spd_tgl')
                      ).filter(Spd.unit_id == ses['unit_id'],
                           Spd.tahun_id==ses['tahun'],
                           Spd.nama.ilike('%s%%' % term))        
            rows = q.all()
            r = []
            for k in rows:
                d={}
                d['id']          = k[0]
                d['value']       = k[2]
                d['kode']        = k[1]
                d['nama']        = k[2]
                d['tanggal']     = k[3]
                r.append(d)    
            return r

    #######    
    # Add #
    #######
    def form_validator(self, form, value):
        def err_kegiatan():
            raise colander.Invalid(form,
                'Kegiatan dengan no urut tersebut sudah ada')
                    
    def get_form(self, class_form):
        schema = class_form(validator=self.form_validator)
        schema = schema.bind(is_bl=IS_BL)
        schema.request = self.request
        return Form(schema, buttons=('simpan','batal'))
        
    def save(self, values, row=None):
        if not row:
            row = Spd()
            row.created = datetime.now()
            row.create_uid = self.request.user.id
        row.from_dict(values)
        row.updated = datetime.now()
        row.update_uid = self.request.user.id
        row.disabled = 'disabled' in values and 1 or 0     

        if not row.kode:
            tahun    = self.session['tahun']
            unit_kd  = self.session['unit_kd']
            no_urut  = Spd.get_norut(row.id)+1
            row.kode = "SPD%d" % tahun + "-%s" % unit_kd + "-%d" % no_urut
            
        DBSession.add(row)
        DBSession.flush()
        return row
                                          
    def save_request(self, values, row=None):
        if 'id' in self.request.matchdict:
            values['id'] = self.request.matchdict['id']
        row = self.save(values, row)
        self.request.session.flash('SPD sudah disimpan.')
        return row
            
    def route_list(self):
        return HTTPFound(location=self.request.route_url('ap-spd'))
        
    def session_failed(request, session_name):
        r = dict(form=request.session[session_name])
        del request.session[session_name]
        return r
        
    @view_config(route_name='ap-spd-add', renderer='templates/ap-spd/add.pt',
                 permission='add')
    def view_add(self):
        request=self.request
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
                return self.route_list()
            return self.route_list()
        elif SESS_ADD_FAILED in request.session:
            del request.session[SESS_ADD_FAILED]
        return dict(form=form)

    ########
    # Edit #
    ########
    def query_id(self):
        return DBSession.query(Spd).filter(Spd.id==self.request.matchdict['id'])
        
    def id_not_found(request):    
        msg = 'User ID %s not found.' % request.matchdict['id']
        request.session.flash(msg, 'error')
        return self.route_list()

    @view_config(route_name='ap-spd-edit', renderer='templates/ap-spd/add.pt',
                 permission='edit')
    def view_edit(self):
        request = self.request
        row = self.query_id().first()
        
        if not row:
            return id_not_found(request)
            
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
        values = row.to_dict() 
        form.set_appstruct(values) 
        return dict(form=form)

    ##########
    # Delete #
    ##########    
    @view_config(route_name='ap-spd-delete', renderer='templates/ap-spd/delete.pt',
                 permission='delete')
    def view_delete(self):
        q = self.query_id()
        row = q.first()
        request=self.request
        
        if not row:
            return id_not_found(request)
            
        form = Form(colander.Schema(), buttons=('hapus','cancel'))
        values= {}
        if request.POST:
            if 'hapus' in request.POST:
                msg = '%s dengan kode %s telah berhasil.' % (request.title, row.kode)
                DBSession.query(Spd).filter(Spd.id==request.matchdict['id']).delete()
                DBSession.flush()
                request.session.flash(msg)
            return self.route_list()
        return dict(row=row,
                     form=form.render())

class AddSchema(colander.Schema):
    unit_id          = colander.SchemaNode(
                          colander.String(),
                          oid = "unit_id")
    tahun_id         = colander.SchemaNode(
                          colander.Integer(),
                          title="Tahun",
                          oid = "tahun_id")
    kode             = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="No. SPD")
    nama             = colander.SchemaNode(
                          colander.String(),
                          title = "Uraian"
                          )
    tanggal         = colander.SchemaNode(
                          colander.Date(),
                          title = "Tanggal"
                          )
    triwulan_id      = colander.SchemaNode(
                          colander.Integer(),
                          title="Triwulan",
                          widget=widget.SelectWidget(values=TRW))
    is_bl            = colander.SchemaNode(
                          colander.Integer(),
                          title="Belanja",
                          oid = "is_bl",
                          widget=widget.SelectWidget(values=IS_BL))

class EditSchema(AddSchema):
    id             = colander.SchemaNode(
                          colander.Integer(),
                          oid="id")
                     