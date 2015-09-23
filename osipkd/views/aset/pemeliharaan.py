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
from osipkd.models.aset_models import AsetPemeliharaan, AsetKib, AsetKategori
from osipkd.models.pemda_model import Unit
from datatables import ColumnDT, DataTables
from osipkd.views.base_view import BaseViews
    
SESS_ADD_FAILED = 'Tambah aset-pemeliharaan gagal'
SESS_EDIT_FAILED = 'Edit aset-pemeliharaan gagal'

class AddSchema(colander.Schema):
    unit_id         = colander.SchemaNode(
                        colander.Integer(),
                        #widget = widget.HiddenWidget(),
                        oid = "unit_id")
    unit_kd         = colander.SchemaNode(
                        colander.String(),
                        #widget = unit_kd_widget,
                        oid = "unit_kd",
                        title = "SKPD")
    unit_nm         = colander.SchemaNode(
                        colander.String(),
                        #widget = unit_nm_widget,
                        oid = "unit_nm",
                        title = "SKPD Uraian")
    kategori_id     = colander.SchemaNode(
                        colander.Integer(),
                        oid = "kategori_id")
    kategori_kd     = colander.SchemaNode(
                        colander.String(),
                        oid = "kategori_kd",
                        title = "Kategori")
    kategori_nm     = colander.SchemaNode(
                        colander.String(),
                        oid = "kategori_nm",
                        title = "Kategori Uraian")
    kib_id          = colander.SchemaNode(
                        colander.Integer(),
                        oid = "kib_id",
                        title = "Aset ID")
    kib_nm          = colander.SchemaNode(
                        colander.String(),
                        oid = "kib_nm",
                        title = "Kib")
    th_pemeliharaan = colander.SchemaNode(
                        colander.Integer(),
                        oid = "tahun")
    nilai           = colander.SchemaNode(
                        colander.Integer(),
                        oid = "nilai",
                        missing=colander.drop)
    masa_manfaat    = colander.SchemaNode(
                        colander.Integer(),
                        oid = "masa_manfaat",
                        missing=colander.drop)
    no_sp2d         = colander.SchemaNode(
                        colander.String(),
                        oid = "no_sp2d",
                        title = "No. SP2D",
                        missing=colander.drop)
    no_bast         = colander.SchemaNode(
                        colander.String(),
                        oid = "no_bast",
                        title = "No. BAST",
                        missing=colander.drop)
    no_kontrak      = colander.SchemaNode(
                        colander.String(),
                        oid = "no_kontrak",
                        title = "No. Kontrak",
                        missing=colander.drop)
    tgl_bast        = colander.SchemaNode(
                        colander.Date(),
                        missing=colander.drop,
                        title="Tanggal BAST")
    keterangan      = colander.SchemaNode(
                        colander.String(),
                        oid = "keterangan",
                        title = "Keterangan",
                        missing=colander.drop)
                        
    uraian          = colander.SchemaNode(
                        colander.String(),
                        oid = "uraian",
                        title = "Uraian",
                        missing=colander.null)
    tgl_perolehan   = colander.SchemaNode(
                        colander.Date(),
                        missing=colander.drop,
                        title="Tgl. Perolehan")
    cara_perolehan  = colander.SchemaNode(
                        colander.String(),
                        oid = "cara_perolehan",
                        title = "Cara Perolehan",
                        missing=colander.drop)
    th_beli         = colander.SchemaNode(
                        colander.String(),
                        oid = "th_beli",
                        title = "Tahun Beli",
                        missing=colander.drop)
    asal_usul        = colander.SchemaNode(
                        colander.String(),
                        oid = "asal_usul",
                        title = "Asal Usul",
                        missing=colander.drop)
    harga            = colander.SchemaNode(
                        colander.Integer(),
                        oid = "harga",
                        missing=colander.drop)
    jumlah            = colander.SchemaNode(
                        colander.Integer(),
                        oid = "jumlah",
                        missing=colander.drop)
    satuan            = colander.SchemaNode(
                        colander.String(),
                        oid = "satuan",
                        missing=colander.drop)
    kondisi            = colander.SchemaNode(
                        colander.String(),
                        oid = "kondisi",
                        missing=colander.drop)
    kib                = colander.SchemaNode(
                        colander.String(),
                        oid = "kib",
                        missing=colander.drop)

class EditSchema(AddSchema):
    id             = colander.SchemaNode(
                          colander.Integer(),
                          oid="id")

class view_aset_pemeliharaan(BaseViews):
    @view_config(route_name="aset-pemeliharaan", renderer="templates/pemeliharaan/list.pt", permission='read')
    def view_list(self):
        ses = self.request.session
        req = self.request
        params   = req.params
        url_dict = req.matchdict
        return dict(project='EIS',
        )
        
    ##########                    
    # Action #
    ##########    
    @view_config(route_name='aset-pemeliharaan-act', renderer='json',
                 permission='read')
    def view_act(self):
        ses = self.request.session
        req = self.request
        params   = req.params
        url_dict = req.matchdict
        print ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
        pk_id = 'id' in params and params['id'] and int(params['id']) or 0
        if url_dict['act']=='grid':
            columns = []
            columns.append(ColumnDT('id'))
            columns.append(ColumnDT('tahun'))
            columns.append(ColumnDT('kategori_kd'))
            columns.append(ColumnDT('no_register'))
            columns.append(ColumnDT('kategori_nm'))
            columns.append(ColumnDT('nilai'))
            columns.append(ColumnDT('th_beli'))
            
            query = DBSession.query(AsetPemeliharaan.id,
                                    AsetPemeliharaan.th_pemeliharaan.label('tahun'),
                                    AsetKategori.kode.label('kategori_kd'),
                                    AsetKib.no_register,
                                    AsetKategori.uraian.label('kategori_nm'),
                                    AsetPemeliharaan.nilai,
                                    AsetKib.th_beli,
                    ).join(AsetKib, AsetKategori
                    ).filter(AsetPemeliharaan.unit_id==ses['unit_id']
                    )
                       
            rowTable = DataTables(req, AsetPemeliharaan, query, columns)
            return rowTable.output_result()
                     
    #######    
    # Add #
    #######
    def form_validator(self, form, value):
        def err_kegiatan():
            raise colander.Invalid(form,
                'Aset dengan no urut tersebut sudah ada')
                    
    def get_form(self, class_form):
        schema = class_form(validator=self.form_validator)
        schema.request = self.request
        return Form(schema, buttons=('simpan','batal'))
        
    def save(self, values, row=None):
        if not row:
            row = AsetPemeliharaan()
            row.created    = datetime.now()
            row.create_uid = self.request.user.id
        row.from_dict(values)
        row.updated    = datetime.now()
        row.update_uid = self.request.user.id

        #tahun    = self.session['tahun']
        unit_kd  = self.session['unit_kd']
            
        DBSession.add(row)
        DBSession.flush()
        return row
                                          
    def save_request(self, values, row=None):
        if 'id' in self.request.matchdict:
            values['id'] = self.request.matchdict['id']
        row = self.save(values, row)
        self.request.session.flash('Pemeliharaan sudah disimpan.')
        return row
            
    def route_list(self):
        return HTTPFound(location=self.request.route_url('aset-pemeliharaan'))
        
    def session_failed(request, session_name):
        r = dict(form=request.session[session_name])
        del request.session[session_name]
        return r
        
    @view_config(route_name='aset-pemeliharaan-add', renderer='templates/pemeliharaan/add.pt',
                 permission='add')
    def view_add(self):
        request = self.request
        
        form = self.get_form(AddSchema)
        if request.POST:
            if 'simpan' in request.POST:
                print ">>>>>>>>>>>>>>>>>>>>>>>>>>> LEWAT 1"
                controls = request.POST.items()
                controls_dicted = dict(controls)
                try:
                    c = form.validate(controls)
                except ValidationFailure, e:
                    return dict(form=form)
                print ">>>>>>>>>>>>>>>>>>>>>>>>>>> LEWAT 2"
                row = self.save_request(controls_dicted)
                print ">>>>>>>>>>>>>>>>>>>>>>>>>>> LEWAT 3"
                
                return HTTPFound(location=request.route_url('aset-pemeliharaan-edit',id=row.id))
            return self.route_list()
        elif SESS_ADD_FAILED in request.session:
            del request.session[SESS_ADD_FAILED]
        return dict(form=form)

    ########
    # Edit #
    ########
    def query_id(self):
        return DBSession.query(AsetPemeliharaan).filter(AsetPemeliharaan.id==self.request.matchdict['id'])
        
    def id_not_found(request):    
        msg = 'User ID %s not found.' % request.matchdict['id']
        request.session.flash(msg, 'error')
        return self.route_list()

    @view_config(route_name='aset-pemeliharaan-edit', renderer='templates/pemeliharaan/add.pt',
                 permission='edit')
    def view_edit(self):
        request = self.request
        row     = self.query_id().first()
        
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
    @view_config(route_name='aset-pemeliharaan-delete', renderer='templates/pemeliharaan/delete.pt',
                 permission='delete')
    def view_delete(self):
        request = self.request
        q       = self.query_id()
        row     = q.first()
        
        if not row:
            return id_not_found(request)
            
        form = Form(colander.Schema(), buttons=('hapus','cancel'))
        values= {}
        if request.POST:
            if 'hapus' in request.POST:
                msg = '%s dengan id %s telah berhasil.' % (request.title, row.id)
                DBSession.query(AsetPemeliharaan).filter(AsetPemeliharaan.id==request.matchdict['id']).delete()
                DBSession.flush()
                request.session.flash(msg)
            return self.route_list()
        return dict(row=row,form=form.render())

