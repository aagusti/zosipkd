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
from osipkd.models.apbd_tu import Spp, SppItem, Spm
    
from datatables import ColumnDT, DataTables
from osipkd.views.base_view import BaseViews

SESS_ADD_FAILED = 'Tambah ap-spm gagal'
SESS_EDIT_FAILED = 'Edit ap-spm gagal'

def deferred_ap_type(node, kw):
    values = kw.get('ap_type', [])
    return widget.SelectWidget(values=values)
    
AP_TYPE = (
    ('1', 'UP'),
    ('2', 'TU'),
    ('3', 'GU'),
    ('4', 'LS'),
    )

class view_ap_spm(BaseViews):

    @view_config(route_name="ap-spm", renderer="templates/ap-spm/list.pt")
    def view_list(self):
        ses = self.request.session
        req = self.request
        params = req.params
        url_dict = req.matchdict
        return dict(project='EIS', #row = row
        )
        
    ##########                    
    # Action #
    ##########    
    @view_config(route_name='ap-spm-act', renderer='json',
                 permission='read')
    def view_act(self):
        ses = self.request.session
        req = self.request
        params = req.params
        url_dict = req.matchdict
        if url_dict['act']=='grid':
            pk_id = 'id' in params and params['id'] and int(params['id']) or 0
            if url_dict['act']=='grid':
                # defining columns
                columns = []
                columns.append(ColumnDT('id'))
                columns.append(ColumnDT('kode'))
                columns.append(ColumnDT('tanggal', filter=self._DTstrftime))
                columns.append(ColumnDT('jenis'))
                columns.append(ColumnDT('nama'))
                columns.append(ColumnDT('nominal'))
                query = DBSession.query(Spm.id,
                                        Spm.kode,
                                        Spm.tanggal,
                                        Spp.jenis,
                                        Spm.nama,
                                        Spp.nominal
                                        )\
                            .filter(Spm.ap_spp_id==Spp.id,
                                    Spp.tahun_id==ses['tahun'],
                                    Spp.unit_id==ses['unit_id'])\

                rowTable = DataTables(req, Spm, query, columns)
                return rowTable.output_result()

        elif url_dict['act']=='headofkode':
            term = 'term' in params and params['term'] or ''
            q = DBSession.query(Spm.id, Spm.kode.label('spm_kd'), Spm.nama.label('spm_nm')
                      ).join(Spp).filter(Spp.unit_id == ses['unit_id'],
                           Spp.tahun_id==ses['tahun'],
                           Spm.kode.ilike('%s%%' % term))        
            rows = q.all()
            r = []
            for k in rows:
                d={}
                d['id']          = k[0]
                d['value']       = k[1]
                d['kode']        = k[1]
                d['nama']        = k[2]
                r.append(d)    
            return r
            
        elif url_dict['act']=='headofnama':
            term = 'term' in params and params['term'] or ''
            q = DBSession.query(Spm.id, Spm.kode.label('spm_kd'), Spm.nama.label('spm_nm')).join(Spp
                      ).filter(
                      Spp.unit_id == ses['unit_id'],
                      Spp.tahun_id==ses['tahun'],
                      Spm.nama.ilike('%s%%' % term))
            rows = q.all()
            r = []
            for k in rows:
                d={}
                d['id']          = k[0]
                d['value']       = k[2]
                d['kode']        = k[1]
                d['nama']        = k[2]
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
        schema = schema.bind(ap_type=AP_TYPE)
        schema.request = self.request
        return Form(schema, buttons=('simpan','batal'))
        
    def save(self, values, row=None):
        if not row:
            row = Spm()
            row.created = datetime.now()
            row.create_uid = self.request.user.id
        row.from_dict(values)
        row.updated = datetime.now()
        row.update_uid = self.request.user.id
        row.posted=0
        row.disabled=0   
        DBSession.add(row)
        DBSession.flush()

        return row

    def save_request(self, values, row=None):
        if 'id' in self.request.matchdict:
            values['id'] = self.request.matchdict['id']
        row = self.save(values, row)
        self.request.session.flash('SPM sudah disimpan.')
        return row
            
    def route_list(self):
        return HTTPFound(location=self.request.route_url('ap-spm'))
        
    def session_failed(request, session_name):
        r = dict(form=request.session[session_name])
        del request.session[session_name]
        return r
        
    @view_config(route_name='ap-spm-add', renderer='templates/ap-spm/add.pt',
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
                return HTTPFound(location=request.route_url('ap-spm-edit', 
                                          id=row.id))
            return self.route_list()
        elif SESS_ADD_FAILED in request.session:
            del request.session[SESS_ADD_FAILED]
        return dict(form=form)

    ########
    # Edit #
    ########
    def query_id(self):
        return DBSession.query(Spm).filter(Spm.id==self.request.matchdict['id'])
        
    def id_not_found(request):    
        msg = 'User ID %s not found.' % request.matchdict['id']
        request.session.flash(msg, 'error')
        return self.route_list()

    @view_config(route_name='ap-spm-edit', renderer='templates/ap-spm/add.pt',
                 permission='edit')
    def view_edit(self):
        request = self.request
        row = self.query_id().first()
        if not row:
            return id_not_found(request)
        if row.posted:
            request.session.flash('data sudah diposting', 'error')
            return self.route_list()
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
        values['spp_kd']=row.spps.kode
        values['spp_nm']=row.spps.nama
        form.set_appstruct(values) 
        return dict(form=form)

    ##########
    # Delete #
    ##########    
    @view_config(route_name='ap-spm-delete', renderer='templates/ap-spm/delete.pt',
                 permission='delete')
    def view_delete(self):
        q = self.query_id()
        row = q.first()
        request=self.request
        if not row:
            return id_not_found(request)
        if row.posted:
            request.session.flash('data sudah diposting', 'error')
            return self.route_list()
        form = Form(colander.Schema(), buttons=('hapus','cancel'))
        values= {}
        if request.POST:
            if 'hapus' in request.POST:
                msg = '%s Kode %s  No. %s %s sudah dihapus.' % (request.title, row.kode, row.kode, row.nama)
                DBSession.query(Spm).filter(Spm.id==request.matchdict['id']).delete()
                DBSession.flush()
                request.session.flash(msg)
            return self.route_list()
        return dict(row=row,
                     form=form.render())

class AddSchema(colander.Schema):

    ap_spp_id       = colander.SchemaNode(
                          colander.Integer(),
                          missing=colander.drop,
                          oid="ap_spp_id")
    spp_kd          = colander.SchemaNode(
                          colander.String(),
                          title = "SPP",
                          oid="spp_kd")
    spp_nm          = colander.SchemaNode(
                          colander.String(),
                          oid='spp_nm')
                          
    kode            = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="No. SPM")
    nama            = colander.SchemaNode(
                          colander.String(),
                          title = "Uraian"
                          )
    tanggal         = colander.SchemaNode(
                          colander.Date(),
                          )
    nama            = colander.SchemaNode(
                          colander.String(),
                          title = "Uraian"
                          )
    ttd_uid         = colander.SchemaNode(
                          colander.Integer(),
                          missing=colander.drop,
                          title = "TTD",
                          oid = "ttd_uid"
                          )
    ttd_nip         = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          oid = "ttd_nip"
                          )
    ttd_nama        = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          oid = "ttd_nama")
    verified_uid    = colander.SchemaNode(
                          colander.Integer(),
                          missing=colander.drop,
                          title = "Verified",
                          oid = "verified_uid"
                          )
    verified_nip    = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          oid = "verified_nip"
                          )
    verified_nama   = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          oid = "verified_nama"
                          )

class EditSchema(AddSchema):
    id             = colander.SchemaNode(
                          colander.Integer(),
                          oid="id")
                     