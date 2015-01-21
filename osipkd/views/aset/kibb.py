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
    )
from osipkd.models import (
    DBSession,
    Group
    )
from kibs import KibSchema    
from osipkd.models.aset_models import AsetKategori, AsetKib
from datatables import ColumnDT, DataTables
from osipkd.views.base_view import BaseViews
    

SESS_ADD_FAILED = 'Tambah kibb gagal'
SESS_EDIT_FAILED = 'Edit kibb gagal'
KAT_PREFIX = '02'

kat_widget = widget.AutocompleteInputWidget(
        size=60,
        values = '/aset/kibb/headofnama/act',
        min_length=1)
                
class AddSchema(KibSchema):
    kib             = colander.SchemaNode(
                          colander.String(),
                          default='B',
                          title="KIB",
                              oid="kib")
    b_kd_ruang       = colander.SchemaNode(
                          colander.Integer(),
                          missing=colander.drop,
                          title="Ruang")
    b_merk           = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="Merk")
    b_type           = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="Type")
    b_cc             = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="CC")
    b_bahan          = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="Bahan")
    b_nomor_pabrik   = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="No. Pabrik")
    b_nomor_rangka   = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="No. Rangk")
    b_nomor_mesin    = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="No. Mesin")
    b_nomor_polisi   = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="No. Pol")
    b_nomor_bpkb     = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="No. BPKB")
    b_ukuran         = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="Ukuran")
    b_warna          = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="Warna")
    b_thbuat         = colander.SchemaNode(
                          colander.Integer(),
                          missing=colander.drop,
                          title="Th. Buat")
                    
class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.String(),
            missing=colander.drop,
            widget=widget.HiddenWidget(readonly=True))
            
class view_aset_kibb(BaseViews):
    # MASTER
    @view_config(route_name="aset-kibb", renderer="templates/kibs/list.pt",
                 permission="read")
    def aset_kibb(self):
        params = self.request.params
        return dict(kib='kibb')
        
    @view_config(route_name="aset-kibb-act", renderer="json",
                 permission="read")
    def aset_kibb_act(self):
        req    = self.request
        params = req.params
        url_dict = req.matchdict

        pk_id = 'id' in params and int(params['id']) or 0
        if url_dict['act']=='grid':
            # defining columns
            columns = []
            columns.append(ColumnDT('id'))
            columns.append(ColumnDT('units.kode'))
            columns.append(ColumnDT('kats.kode'))
            columns.append(ColumnDT('no_register'))
            columns.append(ColumnDT('uraian'))
            columns.append(ColumnDT('tahun'))
            columns.append(ColumnDT('th_beli'))
            columns.append(ColumnDT('harga'))
            columns.append(ColumnDT('kondisi'))
            query = DBSession.query(AsetKib).\
                    join(AsetKategori).\
                    filter(AsetKib.kategori_id==AsetKategori.id,
                           AsetKib.kib=='B')
            rowTable = DataTables(req, AsetKib, query, columns)
            return rowTable.output_result()

    #######    
    # Add #
    #######
    def form_validator(self, form, value):
        if 'id' in form.request.matchdict:
            uid = form.request.matchdict['id']
            q = DBSession.query(AsetKib).filter_by(id=uid)
            kebijakan = q.first()
        else:
            kebijakan = None
                
    def get_form(self, class_form, row=None):
        schema = class_form(validator=self.form_validator)
        schema = schema.bind()
        schema.request = self.request
        if row:
          schema.deserialize(row)
        return Form(schema, buttons=('simpan','batal'))
        
    def save(self, values, user, row=None):
        if not row:
            row = AsetKib()
            row.created = datetime.now()
            row.create_uid = user.id
            values['no_register'] = AsetKib.get_no_register(values) or 1
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
        self.request.session.flash('Kebijakan sudah disimpan.')
            
    def route_list(self):
        return HTTPFound(location=self.request.route_url('aset-kibb'))
        
    def session_failed(self, session_name):
        r = dict(form=self.session[session_name])
        del self.session[session_name]
        return r
        
    @view_config(route_name='aset-kibb-add', renderer='templates/kibs/add_kibb.pt',
                 permission='add')
    def view_kebijakan_add(self):
        req = self.request
        ses = self.session
        form = self.get_form(AddSchema)
        if req.POST:
            if 'simpan' in req.POST:
                controls = req.POST.items()
                try:
                    c = form.validate(controls)
                except ValidationFailure, e:
                    return dict(form=form, kat_prefix=KAT_PREFIX)
                    #req.session[SESS_ADD_FAILED] = e.render()               
                    #return HTTPFound(location=req.route_url('kebijakan-add'))
                self.save_request(dict(controls))
            return self.route_list()
        elif SESS_ADD_FAILED in req.session:
            return self.session_failed(SESS_ADD_FAILED)
        return dict(form=form, kat_prefix=KAT_PREFIX)

        
    ########
    # Edit #
    ########
    def query_id(self):
        return DBSession.query(AsetKib).filter_by(id=self.request.matchdict['id'])
        
    def id_not_found(self):    
        msg = 'Kebijakan ID %s Tidak Ditemukan.' % self.request.matchdict['id']
        request.session.flash(msg, 'error')
        return route_list()

    @view_config(route_name='aset-kibb-edit', renderer='templates/kibb/edit.pt',
                 permission='edit')
    def view_kebijakan_edit(self):
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
                    return HTTPFound(location=request.route_url('kebijakan-edit',
                                      id=row.id))
                self.save_request(dict(controls), row)
            return self.route_list()
        elif SESS_EDIT_FAILED in request.session:
            return self.session_failed(SESS_EDIT_FAILED)
        values = row.to_dict()
        values['kibb_nm']= row.kibbs and row.kibbs.uraian or ""
        return dict(form=form.render(appstruct=values))

    ##########
    # Delete #
    ##########    
    @view_config(route_name='aset-kibb-delete', renderer='templates/kibb/delete.pt',
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
                msg = 'Kebijakan ID %d %s sudah dihapus.' % (row.id, row.uraian)
                try:
                  q.delete()
                  DBSession.flush()
                except:
                  msg = 'Kebijakan ID %d %s tidak dapat dihapus.' % (row.id, row.uraian)
                request.session.flash(msg)
            return self.route_list()
        return dict(row=row,
                     form=form.render())