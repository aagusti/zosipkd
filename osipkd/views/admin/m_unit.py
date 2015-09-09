import os
import uuid
from osipkd.tools import row2dict, xls_reader
from datetime import datetime
from sqlalchemy import not_, func, or_
from sqlalchemy.sql.expression import and_
from ziggurat_foundations.models import groupfinder
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
    Group,
    UserGroup
    )
from osipkd.models.pemda_model import Unit, Urusan, UserUnit
from datatables import ColumnDT, DataTables
from osipkd.views.base_view import BaseViews

SESS_ADD_FAILED = 'Tambah unit gagal'
SESS_EDIT_FAILED = 'Edit unit gagal'

class AddSchema(colander.Schema):
    urusan_widget = widget.AutocompleteInputWidget(
                    size=60,
                    values = '/urusan/act/headofnama',
                    min_length=1)
                  
    kode      = colander.SchemaNode(
                    colander.String(),
                    oid = "kode",
                    title = "Kode")
    urusan_nm = colander.SchemaNode(
                    colander.String(),
                    #widget=urusan_widget,
                    oid = "urusan_nm",
                    title = "Urusan")
    urusan_id = colander.SchemaNode(
                    colander.Integer(),
                    #widget=widget.HiddenWidget(),
                    oid = "urusan_id")
    nama     = colander.SchemaNode(
                    colander.String(),
                    oid = "nama",
                    title = "Nama")
    alamat   = colander.SchemaNode(
                    colander.String(),
                    oid = "alamat",
                    title = "Alamat",
                    missing = colander.drop,)
    kategori = colander.SchemaNode(
                    colander.String(),
                    oid = "kategori",
                    title = "Kategori",
                    missing = colander.drop,)
    singkat  = colander.SchemaNode(
                    colander.String(),
                    oid = "singkat",
                    title = "Singkat",
                    missing = colander.drop,)
    disabled = colander.SchemaNode(
                    colander.Boolean())
                    
class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.String(),
            missing=colander.drop,
            widget=widget.HiddenWidget(readonly=True))
            
class view_unit(BaseViews):
    ########                    
    # List #
    ########    
    @view_config(route_name='unit', renderer='templates/unit/list.pt',
                 permission='read')
    def view_list(self):
        return dict(a={})
        
    ##########                    
    # Action #
    ##########    
    @view_config(route_name='unit-act', renderer='json',
                 permission='view')
    def gaji_unit_act(self):
        ses = self.request.session
        req = self.request
        params   = req.params
        url_dict = req.matchdict
        
        if url_dict['act']=='grid':
            columns = []
            columns.append(ColumnDT('id'))
            columns.append(ColumnDT('kode'))
            columns.append(ColumnDT('nama'))
            columns.append(ColumnDT('alamat'))
            columns.append(ColumnDT('disabled'))
            
            groups = groupfinder(req.user, req)
            ids = []
            if req.user.id==1 or 'group:admin' in groups:
                query = Unit.query() #DBSession.query(Unit)
            else:
                units = DBSession.query(UserUnit.unit_id, 
                             UserUnit.sub_unit, Unit.kode
                             ).join(Unit).filter(Unit.id==UserUnit.unit_id,
                                    UserUnit.user_id==req.user.id).all() 

                for unit in units:
                    if unit.sub_unit:
                        rows = DBSession.query(Unit.id).filter(Unit.kode.ilike('%s%%' % unit.kode)).all()
                    else:
                        rows = DBSession.query(Unit.id).filter(Unit.kode==unit.kode).all()
                    for i in range(len(rows)):
                        ids.append(rows[i])
                query = DBSession.query(Unit).filter((Unit.id).in_(ids))
            rowTable = DataTables(req, Unit, query, columns)
            return rowTable.output_result()
            
        elif url_dict['act']=='changeid':
            ids  = UserUnit.unit_granted(req.user.id, params['unit_id'])
            
            ## kondisi group TAPD (semua unit)
            if req.user.id>1 and 'g:admin' not in groupfinder(req.user, req) and not ids :
               grp = DBSession.query(func.lower(Group.group_name).label('group_nama'), 
                 func.substr(func.lower(Group.group_name),func.length(Group.group_name)-5,6).label('group_singkat')
                 ).filter(UserGroup.user_id==req.user.id, Group.id==UserGroup.group_id).first()
               grps_nm = '%s' % grp.group_nama 
               grps    = '%s' % grp.group_singkat
            
            ## Pembatasan unit all
            if req.user.id>1 and 'g:admin' not in groupfinder(req.user, req)\
                    and not ids and grps !='(tapd)' and grps_nm !='admin bpkad'  and grps_nm !='akuntansi'\
                    and  grps_nm !='perbendaharaan blbtl' and  grps_nm !='kasda' :
                return {'success':False, 'msg':'Anda tidak boleh mengubah ke unit yang bukan hak akses anda'}

            row = Unit.get_by_id('unit_id' in params and params['unit_id'] or 0)
            if row:
                ses['unit_id']=row.id
                ses['unit_kd']=row.kode
                ses['unit_nm']=row.nama
                return {'success':True, 'msg':'Sukses ubah SKPD'}
                
        elif url_dict['act']=='headofnama':
            term = 'term' in params and params['term'] or '' 
            rows = DBSession.query(Unit.id, Unit.kode, Unit.nama
                      ).filter(
                      Unit.nama.ilike('%%%s%%' % term) ).all()
            r = []
            for k in rows:
                d={}
                d['id']          = k[0]
                d['value']       = k[2]
                d['kode']        = k[1]
                d['nama']        = k[2]
                r.append(d)
            return r
            
        elif url_dict['act']=='headofkode':
            term = 'term' in params and params['term'] or '' 
            rows = DBSession.query(Unit.id, Unit.kode, Unit.nama
                      ).filter(
                      Unit.kode.ilike('%%%s%%' % term) ).all()
            r = []
            for k in rows:
                d={}
                d['id']          = k[0]
                d['value']       = k[1]
                d['kode']        = k[1]
                d['nama']        = k[2]
                r.append(d)
            return r
            
        elif url_dict['act']=='headofnama_asistensi':
            term = 'term' in params and params['term'] or '' 
            rows = DBSession.query(Unit.id, Unit.kode, Unit.nama
                      ).filter(or_(Unit.kode=='1.20.09',
                                   Unit.kode=='1.20.05',
                                   Unit.kode=='1.06.01'),
                               Unit.nama.ilike('%%%s%%' % term) ).all()
            r = []
            for k in rows:
                d={}
                d['id']          = k[0]
                d['value']       = k[2]
                d['kode']        = k[1]
                d['nama']        = k[2]
                r.append(d)
            print '-------------------Unit-----------------',r
            return r
            
        elif url_dict['act']=='import':
            rows = DBSession.execute("""SELECT a.kode, a.nama, a.passwd, b.unit_id 
                                        FROM admin.users2 a
                                        INNER JOIN admin.user_units2 b
                                        ON a.id = b.id""").all()
            for kode,nama,passwd, unit_id in rows:
                user = Users()
                user.user_name = nama
                user.user_password = passwd
                user.email = ''.join([nama,'@tangerangkab.org'])
                user.status = 1
                DBSession.add(user)
                DBSession.flush()
                if user.id:
                    user_unit=UserUnit()
                    user_unit.user_id = user.id
                    user_unit.unit_id = unit_id
                    user_unit.status  = 1
                    DBSession.add(user_unit)
                    DBSession.flush()
                    
################################################################
    def form_validator(self, form, value):
        if 'id' in form.request.matchdict:
            uid = form.request.matchdict['id']
            q = DBSession.query(Unit).filter_by(id=uid)
            unit = q.first()
        else:
            unit = None
    def get_form(self, class_form, row=None):
        schema = class_form(validator=self.form_validator)
        schema = schema.bind()
        schema.request = self.request
        if row:
          schema.deserialize(row)
        return Form(schema, buttons=('simpan','batal'))
    def save(self, values, user, row=None):
        if not row:
            row = Unit()
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
        self.request.session.flash('Unit sudah disimpan.')
    def route_list(self):
        return HTTPFound(location=self.request.route_url('unit'))
    def session_failed(self, session_name):
        r = dict(form=self.session[session_name])
        del self.session[session_name]
        return r
    
    #######    
    # Add #
    #######    
    @view_config(route_name='unit-add', renderer='templates/unit/add.pt',
                 permission='add')
    def view_unit_add(self):
        req  = self.request
        ses  = self.session
        form = self.get_form(AddSchema)
        if req.POST:
            if 'simpan' in req.POST:
                controls = req.POST.items()
                controls_dicted = dict(controls)
                
                #Cek Kode Sama ato tidak
                if not controls_dicted['kode']=='':
                    a = form.validate(controls)
                    b = a['kode']
                    c = "%s" % b
                    cek  = DBSession.query(Unit).filter(Unit.kode==c).first()
                    if cek :
                        self.request.session.flash('Kode sudah ada.', 'error')
                        return HTTPFound(location=self.request.route_url('unit-add'))
                        
                try:
                    c = form.validate(controls)
                except ValidationFailure, e:
                    return dict(form=form)              
                    return HTTPFound(location=req.route_url('unit-add'))
                self.save_request(dict(controls))
            return self.route_list()
        elif SESS_ADD_FAILED in req.session:
            return self.session_failed(SESS_ADD_FAILED)
        return dict(form=form)
        
    ########
    # Edit #
    ########
    def query_id(self):
        return DBSession.query(Unit).filter_by(id=self.request.matchdict['id'])
    def id_not_found(self):    
        msg = 'unit ID %s Tidak Ditemukan.' % self.request.matchdict['id']
        request.session.flash(msg, 'error')
        return route_list()
        
    @view_config(route_name='unit-edit', renderer='templates/unit/add.pt',
                 permission='edit')
    def view_unit_edit(self):
        request = self.request
        row     = self.query_id().first()
        uid     = row.id
        kode    = row.kode
        
        if not row:
            return id_not_found(request)
            
        form = self.get_form(EditSchema)
        if request.POST:
            if 'simpan' in request.POST:
                controls = request.POST.items()
                
                #Cek Kode Sama ato tidak
                a = form.validate(controls)
                b = a['kode']
                c = "%s" % b
                cek = DBSession.query(Unit).filter(Unit.kode==c).first()
                if cek:
                    kode1 = DBSession.query(Unit).filter(Unit.id==uid).first()
                    d     = kode1.kode
                    if d!=c:
                        self.request.session.flash('Data sudah ada', 'error')
                        return HTTPFound(location=request.route_url('unit-edit',id=row.id))
                        
                try:
                    c = form.validate(controls)
                except ValidationFailure, e:
                    request.session[SESS_EDIT_FAILED] = e.render()               
                    return HTTPFound(location=request.route_url('unit-edit',
                                      id=row.id))
                self.save_request(dict(controls), row)
            return self.route_list()
        elif SESS_EDIT_FAILED in request.session:
            return self.session_failed(SESS_EDIT_FAILED)
        values = row.to_dict()
        values['urusan_nm'] = row.urusans.nama
        form.set_appstruct(values)
        return dict(form=form)
        
    ##########
    # Delete #
    ##########    
    @view_config(route_name='unit-delete', renderer='templates/unit/delete.pt',
                 permission='delete')
    def view_unit_delete(self):
        request = self.request
        q       = self.query_id()
        row     = q.first()
        
        if not row:
            return self.id_not_found(request)
            
        form = Form(colander.Schema(), buttons=('hapus','batal'))
        if request.POST:
            if 'hapus' in request.POST:
                msg = 'Unit ID %d %s sudah dihapus.' % (row.id, row.nama)
                try:
                  q.delete()
                  DBSession.flush()
                except:
                  msg = 'Unit ID %d %s tidak dapat dihapus.' % (row.id, row.nama)
                request.session.flash(msg)
            return self.route_list()
        return dict(row=row, form=form.render())
        