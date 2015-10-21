import os
import uuid
from osipkd.tools import row2dict, xls_reader
from datetime import datetime
from sqlalchemy import not_, func, or_, cast
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
        
def deferred_kondisi(node, kw):
    values = kw.get('kondisi', [])
    return widget.SelectWidget(values=values)
    
kondisi = (
    ('B', 'Baik'),
    ('KB', 'Kurang Baik'),
    ('RB', 'Rusak Berat'),
    )
    
def deferred_cara(node, kw):
    values = kw.get('cara', [])
    return widget.SelectWidget(values=values)
    
cara = (
    ('Pembelian', 'Pembelian'),
    ('Hibah', 'Hibah'),
    ('Mutasi', 'Mutasi'),
    ('Lainnya', 'Lainnya'),
    )
    
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
                        
    th_pemeliharaan = colander.SchemaNode(
                        colander.Integer(),
                        oid = "th_pemeliharaan",
                        title = "Thn.Pemeliharaan")
    nilai           = colander.SchemaNode(
                        colander.Integer(),
                        oid = "nilai",
                        missing=colander.drop)
    masa_manfaat    = colander.SchemaNode(
                        colander.Integer(),
                        oid = "masa_manfaat",
                        title = "Masa Manfaat",
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
    tgl_bast        = colander.SchemaNode(
                        colander.Date(),
                        missing=colander.drop,
                        title="Tgl. BAST")
    no_kontrak      = colander.SchemaNode(
                        colander.String(),
                        oid = "no_kontrak",
                        title = "No.Kontrak",
                        missing=colander.drop)
    keterangan      = colander.SchemaNode(
                        colander.String(),
                        oid = "keterangan",
                        title = "Keterangan",
                        missing=colander.drop)
                        
    ## Headof KIB ##
    kib_id          = colander.SchemaNode(
                        colander.Integer(),
                        oid = "kib_id",)
    kategori_kd     = colander.SchemaNode(
                        colander.String(),
                        oid = "kategori_kd",
                        title = "Kategori")
    kategori_nm     = colander.SchemaNode(
                        colander.String(),
                        oid = "kategori_nm",
                        title = "Kategori Uraian")
    uraian          = colander.SchemaNode(
                        colander.String(),
                        oid = "uraian",
                        title = "Uraian",
                        missing=colander.null)
    tgl_perolehan   = colander.SchemaNode(
                        colander.Date(),
                        missing=colander.drop,
                        oid = "tgl_perolehan",
                        title="Tgl.Pembelian")
    cara_perolehan  = colander.SchemaNode(
                        colander.String(),
                        widget=widget.SelectWidget(values=cara),
                        oid = "cara_perolehan",
                        title = "Perolehan",
                        missing=colander.drop)
    th_beli         = colander.SchemaNode(
                        colander.String(),
                        oid = "th_beli",
                        title = "Tahun Beli",
                        missing=colander.drop)
    asal_usul       = colander.SchemaNode(
                        colander.String(),
                        oid = "asal_usul",
                        title = "Asal-usul",
                        missing=colander.drop)
    harga           = colander.SchemaNode(
                        colander.Integer(),
                        oid = "harga",
                        missing=colander.drop)
    jumlah          = colander.SchemaNode(
                        colander.Integer(),
                        oid = "jumlah",
                        missing=colander.drop)
    satuan          = colander.SchemaNode(
                        colander.String(),
                        oid = "satuan",
                        missing=colander.drop)
    kondisi         = colander.SchemaNode(
                        colander.String(),
                        widget=widget.SelectWidget(values=kondisi),
                        oid = "kondisi",
                        missing=colander.drop)
    kib             = colander.SchemaNode(
                        colander.String(),
                        oid = "kib",
                        title = "KIB",
                        missing=colander.drop)
    pemilik_id      = colander.SchemaNode(
                        colander.Integer(),
                        widget = widget.HiddenWidget(),
                        oid = "pemilik_id",)
    pemilik_nm      = colander.SchemaNode(
                        colander.String(),
                        #widget = pemilik_widget,
                        oid = "pemilik_nm",
                        title = "Pemilik")                      
    keterangan_awal = colander.SchemaNode(
                        colander.String(),
                        oid = "keterangan_awal",
                        title = "Keterangan",
                        missing=colander.drop)
    masa_manfaat_awal = colander.SchemaNode(
                        colander.Integer(),
                        oid = "masa_manfaat_awal",
                        title = "Masa Manfaat",
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
            columns.append(ColumnDT('th_pemeliharaan'))
            columns.append(ColumnDT('kategori_kd'))
            columns.append(ColumnDT('no_register'))
            columns.append(ColumnDT('kategori_nm'))
            columns.append(ColumnDT('nilai'))
            columns.append(ColumnDT('th_beli'))
            
            query = DBSession.query(AsetPemeliharaan.id,
                                    AsetPemeliharaan.th_pemeliharaan,
                                    AsetKategori.kode.label('kategori_kd'),
                                    AsetKib.no_register,
                                    AsetKategori.uraian.label('kategori_nm'),
                                    AsetPemeliharaan.nilai,
                                    AsetKib.th_beli,
                    ).join(AsetKib, AsetKategori
                    ).filter(AsetPemeliharaan.unit_id==ses['unit_id'],
                             AsetPemeliharaan.unit_id == Unit.id,
                             AsetPemeliharaan.kib_id  == AsetKib.id,
                             AsetKib.kategori_id      == AsetKategori.id,
                    )
                       
            rowTable = DataTables(req, AsetPemeliharaan, query, columns)
            return rowTable.output_result()
            
        elif url_dict['act']=='grid1':
            cari = 'cari' in params and params['cari'] or ''
            columns = []
            columns.append(ColumnDT('id'))
            columns.append(ColumnDT('th_pemeliharaan'))
            columns.append(ColumnDT('kode'))
            columns.append(ColumnDT('no_register'))
            columns.append(ColumnDT('uraian'))
            columns.append(ColumnDT('nilai'))
            columns.append(ColumnDT('th_beli'))
            
            query = DBSession.query(AsetPemeliharaan.id,
                                    AsetPemeliharaan.th_pemeliharaan,
                                    AsetKategori.kode,
                                    AsetKib.no_register,
                                    AsetKategori.uraian,
                                    AsetPemeliharaan.nilai,
                                    AsetKib.th_beli,
                    ).join(AsetKib, AsetKategori
                    ).filter(AsetPemeliharaan.unit_id == ses['unit_id'],
                             AsetPemeliharaan.unit_id == Unit.id,
                             AsetPemeliharaan.kib_id  == AsetKib.id,
                             AsetKib.kategori_id      == AsetKategori.id,
                             or_(AsetKategori.kode.ilike('%%%s%%' % cari),
                                 AsetKategori.uraian.ilike('%%%s%%' % cari),)
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
        msg = 'Pemeliharaan ID %s not found.' % request.matchdict['id']
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
        values['kategori_kd']    = row and row.kibs.kats.kode      or ''
        values['kategori_nm']    = row and row.kibs.kats.uraian    or ''
        values['uraian']         = row and row.kibs.uraian         or ''
        values['tgl_perolehan']  = row and row.kibs.tgl_perolehan  or ''
        values['cara_perolehan'] = row and row.kibs.cara_perolehan or ''
        values['th_beli']        = row and row.kibs.th_beli        or ''
        values['asal_usul']      = row and row.kibs.asal_usul      or ''
        values['harga']          = row and row.kibs.harga          or 0
        values['jumlah']         = row and row.kibs.jumlah         or 0
        values['satuan']         = row and row.kibs.satuan         or ''
        values['kondisi']        = row and row.kibs.kondisi        or ''
        values['kib']            = row and row.kibs.kib            or ''
        values['pemilik_id']            = row and row.kibs.pemilik_id  or 0
        values['pemilik_nm']            = row and row.kibs.pemiliks.uraian            or ''
        values['masa_manfaat_awal']     = row and row.kibs.masa_manfaat            or 0
        values['keterangan_awal']       = row and row.kibs.keterangan            or ''
        
        if values['no_sp2d'] == None :
           values['no_sp2d'] = ""
           
        if values['no_bast'] == None :
           values['no_bast'] = ""
           
        if values['no_kontrak'] == None :
           values['no_kontrak'] = ""
           
        #if values['keterangan'] == None :
        #   values['keterangan'] = ""
           
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
            
        form = Form(colander.Schema(), buttons=('hapus','batal'))
        values= {}
        if request.POST:
            if 'hapus' in request.POST:
                msg = '%s dengan id %s telah berhasil.' % (request.title, row.id)
                DBSession.query(AsetPemeliharaan).filter(AsetPemeliharaan.id==request.matchdict['id']).delete()
                DBSession.flush()
                request.session.flash(msg)
            return self.route_list()
        return dict(row=row,form=form.render())

