import os
import uuid
from osipkd.tools import row2dict, xls_reader
from datetime import datetime
from sqlalchemy import not_, func, or_
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
from osipkd.models.aset_models import AsetKategori, AsetKib, AsetPemilik
from datatables import ColumnDT, DataTables
from osipkd.views.base_view import BaseViews
from osipkd.models.pemda_model import Unit    

SESS_ADD_FAILED = 'Tambah kibg gagal'
SESS_EDIT_FAILED = 'Edit kibg gagal'
KAT_PREFIX = '07'

kat_widget = widget.AutocompleteInputWidget(
        size=60,
        values = '/aset/kibg/headofnama/act',
        min_length=1)

def deferred_jenis_barang(node, kw):
    values = kw.get('jenis_barang', [])
    return widget.SelectWidget(values=values)
    
jenis_barang = (
    ('Buku / Perpustakaan', 'Buku / Perpustakaan'),
    ('Barang Bercorak Kesenian', 'Barang Bercorak Kesenian'),
    ('Hewan Ternak dan Tumbuhan', 'Hewan Ternak dan Tumbuhan'),
    ('Aset Tidak Berwujud / Software', 'Aset Tidak Berwujud / Software'),
    )
    
        
class AddSchema(KibSchema):
    kib             = colander.SchemaNode(
                          colander.String(),
                          default='G',
                          title="KIB",
                          oid="kib")
                          
    g_jenis_barang     = colander.SchemaNode(
                          colander.String(),
                          widget=widget.SelectWidget(values=jenis_barang),
                          title="Jns Barang",
                          oid = "g_jenis_barang")
    g_keterangan1      = colander.SchemaNode(
                          colander.String(),
                          missing = colander.drop,
                          title="Ket. 1")
    g_keterangan2      = colander.SchemaNode(
                          colander.String(),
                          missing = colander.drop,
                          title="Ket. 2")
    g_keterangan3      = colander.SchemaNode(
                          colander.String(),
                          missing = colander.drop,
                          title="Ket. 3")
            
class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.String(),
            missing=colander.drop,
            widget=widget.HiddenWidget(readonly=True))
            
class view_aset_kibg(BaseViews):
    # MASTER
    @view_config(route_name="aset-kibg", renderer="templates/kibs/list.pt",
                 permission="read")
    def aset_kibg(self):
        params = self.request.params
        return dict(kib='kibg')
        
    @view_config(route_name="aset-kibg-act", renderer="json",
                 permission="read")
    def aset_kibg_act(self):
        ses      = self.request.session
        req      = self.request
        params   = req.params
        url_dict = req.matchdict

        pk_id = 'id' in params and int(params['id']) or 0
        if url_dict['act']=='grid':
            # defining columns
            columns = []
            columns.append(ColumnDT('id'))
            columns.append(ColumnDT('units.kode'))
            columns.append(ColumnDT('units.nama'))
            columns.append(ColumnDT('kats.kode'))
            columns.append(ColumnDT('no_register'))
            #columns.append(ColumnDT('uraian'))
            columns.append(ColumnDT('kats.uraian'))
            #columns.append(ColumnDT('tahun'))
            columns.append(ColumnDT('tgl_perolehan', filter=self._DTstrftime))
            columns.append(ColumnDT('th_beli'))
            columns.append(ColumnDT('harga'))
            columns.append(ColumnDT('kondisi'))
            query = DBSession.query(AsetKib).\
                    join(AsetKategori, Unit).\
                    filter(AsetKib.unit_id == Unit.id,
                           #AsetKib.unit_id == ses['unit_id'], 
                           AsetKib.kategori_id==AsetKategori.id,
                           AsetKib.kib=='G', 
                           func.substr(Unit.kode,1,func.length(ses['unit_kd']))==ses['unit_kd'],
                           or_(AsetKib.disabled=='0',AsetKib.disabled==None))
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
            row.created    = datetime.now()
            row.create_uid = user.id
        row.from_dict(values)
        row.updated    = datetime.now()
        row.update_uid = user.id
        row.disabled   = 'disabled' in values and values['disabled'] and 1 or 0
        
        a = row.tahun
        b = row.unit_id
        c = row.kategori_id
        if not row.no_register:
            row.no_register = AsetKib.get_no_register(a,b,c)+1;
        row.jumlah=1
                
        DBSession.add(row)
        DBSession.flush()
        return row
        
    def save_request(self, values, row=None):
        if 'id' in self.request.matchdict:
            values['id'] = self.request.matchdict['id']
        row = self.save(values, self.request.user, row)
        self.request.session.flash('Aset Lainnya sudah disimpan.')
            
    def route_list(self):
        return HTTPFound(location=self.request.route_url('aset-kibg'))
        
    def session_failed(self, session_name):
        r = dict(form=self.session[session_name])
        del self.session[session_name]
        return r
        
    @view_config(route_name='aset-kibg-add', renderer='templates/kibs/add_kibg.pt',
                 permission='add')
    def view_kebijakan_add(self):
        req  = self.request
        ses  = self.session
        
        form = self.get_form(AddSchema)
        if req.POST:
            if 'simpan' in req.POST:
                controls = req.POST.items()
                controls_dicted = dict(controls)
                
                # Ambil value data
                units_id                    = controls_dicted['unit_id']                 
                units_nama                  = controls_dicted['unit_nm']                 
                units_kode                  = controls_dicted['unit_kd']                 
                kats_id                     = controls_dicted['kategori_id']             
                kats_kode                   = controls_dicted['kategori_kd']             
                kats_uraian                 = controls_dicted['kategori_nm']             
                no_register                 = controls_dicted['no_register']              
                pemiliks_id                 = controls_dicted['pemilik_id']              
                pemiliks_uraian             = controls_dicted['pemilik_nm']              
                masa_manfaat                = controls_dicted['masa_manfaat']              
                #uraian                      = controls_dicted['uraian']                  
                tahun                       = controls_dicted['tahun']                  
                tgl_perolehan               = controls_dicted['tgl_perolehan']           
                #cara_perolehan              = controls_dicted['cara_perolehan']          
                th_beli                     = controls_dicted['th_beli']                 
                asal_usul                   = controls_dicted['asal_usul']               
                harga                       = controls_dicted['harga']                   
                # Ambil jumlah  
                jml                         = controls_dicted['jumlah']
                jmlh                        = "%s" % jml
                jumlah                      = int(jmlh)
                controls_dicted['jumlah']   = 1
                satuan                      = controls_dicted['satuan']                  
                kondisi                     = controls_dicted['kondisi']                 
                keterangan                  = controls_dicted['keterangan']              
       
                kib                         = controls_dicted['kib']                     
                g_jenis_barang              = controls_dicted['g_jenis_barang']
                g_keterangan1               = controls_dicted['g_keterangan1'] 
                g_keterangan2               = controls_dicted['g_keterangan2'] 
                g_keterangan3               = controls_dicted['g_keterangan3'] 
                
                try:
                    c = form.validate(controls)
                except ValidationFailure, e:
                    return dict(form=form, kat_prefix=KAT_PREFIX)
                row = self.save_request(dict(controls))

                # Array insert sesuai jumlah
                a = jumlah - 1
                b = 0
                for b in range (0,a):
                    aset = AsetKib()            
                    aset.unit_id              = units_id            
                    aset.kategori_id          = kats_id             
                    aset.pemilik_id           = pemiliks_id         
                    #aset.uraian               = uraian              
                    aset.tahun                = tahun              
                    aset.no_register          = AsetKib.get_no_register(tahun,units_id,kats_id)+1;
                    aset.tgl_perolehan        = tgl_perolehan       
                    #aset.cara_perolehan       = cara_perolehan      
                    aset.th_beli              = th_beli             
                    aset.asal_usul            = asal_usul           
                    aset.harga                = harga               
                    aset.jumlah               = 1              
                    aset.satuan               = satuan              
                    aset.kondisi              = kondisi             
                    aset.keterangan           = keterangan          
                    aset.kib                  = kib                 
                    aset.masa_manfaat         = masa_manfaat              
                    aset.g_jenis_barang       = g_jenis_barang  
                    aset.g_keterangan1        = g_keterangan1   
                    aset.g_keterangan2        = g_keterangan2   
                    aset.g_keterangan3        = g_keterangan3   
 
                    DBSession.add(aset)
                    DBSession.flush()

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
        msg = 'Aset Lainnya ID %s Tidak Ditemukan.' % self.request.matchdict['id']
        request.session.flash(msg, 'error')
        return route_list()

    @view_config(route_name='aset-kibg-edit', renderer='templates/kibs/add_kibg.pt',
                 permission='edit')
    def view_kebijakan_edit(self):
        request = self.request
        row     = self.query_id().first()
        
        if not row:
            return id_not_found(request)

        rowd={}
        rowd['id']              = row.id
        rowd['unit_id']         = row.units.id
        rowd['unit_nm']         = row.units.nama
        rowd['unit_kd']         = row.units.kode
        rowd['kategori_id']     = row.kats.id
        rowd['kategori_kd']     = row.kats.kode
        rowd['kategori_nm']     = row.kats.uraian
        rowd['no_register']     = row.no_register
        rowd['pemilik_id']      = row.pemiliks.id
        rowd['pemilik_nm']      = row.pemiliks.uraian
        #rowd['uraian']          = row.uraian
        rowd['tgl_perolehan']   = row.tgl_perolehan
        #rowd['cara_perolehan']  = row.cara_perolehan
        rowd['th_beli']         = row.th_beli
        rowd['asal_usul']       = row.asal_usul
        rowd['harga']           = row.harga
        rowd['jumlah']          = row.jumlah
        rowd['satuan']          = row.satuan
        rowd['kondisi']         = row.kondisi
        rowd['keterangan']      = row.keterangan
        rowd['masa_manfaat']    = row.masa_manfaat

        rowd['kib']                  = row.kib
        rowd['g_jenis_barang']   = row.g_jenis_barang
        rowd['g_keterangan1']    = row.g_keterangan1
        rowd['g_keterangan2']    = row.g_keterangan2
        rowd['g_keterangan3']    = row.g_keterangan3

        form = self.get_form(EditSchema)
        form.set_appstruct(rowd)
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
            return self.session_failed(SESS_EDIT_FAILED)
        return dict(form=form)

    ##########
    # Delete #
    ##########    
    @view_config(route_name='aset-kibg-delete', renderer='templates/kibs/delete.pt',
                 permission='delete')
    def view_delete(self):
        request = self.request
        q       = self.query_id()
        row     = q.first()
        
        if not row:
            return self.id_not_found(request)
            
        form = Form(colander.Schema(), buttons=('hapus','batal'))
        if request.POST:
            if 'hapus' in request.POST:
                msg = 'Aset Lainnya ID %d %s sudah dihapus.' % (row.id, row.kats.uraian)
                try:
                  q.delete()
                  DBSession.flush()
                except:
                  msg = 'Aset Lainnya ID %d %s tidak dapat dihapus.' % (row.id, row.kats.uraian)
                request.session.flash(msg)
            return self.route_list()
        return dict(row=row,form=form.render())
        
    ##########                    
    # CSV #
    ##########    
    @view_config(route_name='aset-kibg-csv', renderer='csv',
                 permission='read')
    def export_csv(self):
        request = self.request
        ses     = self.request.session
        
        query = DBSession.query(Unit.kode.label('Kode_Unit'), Unit.nama.label('Nama_Unit'),
                AsetKategori.kode.label('Kode_Kategori'), AsetKib.no_register.label('No_Register'), AsetKategori.uraian.label('Nama_Kategori'),
                AsetPemilik.uraian.label('Pemilik'), AsetKib.keterangan.label('Keterangan'),
                AsetKib.tgl_perolehan.label('Tgl_Perolehan'), AsetKib.asal_usul.label('Asal_Usul'), AsetKib.harga.label('Harga'),
                AsetKib.jumlah.label('Jumlah'), AsetKib.kondisi.label('Kondisi'), AsetKib.kib.label('Kib'), AsetKib.masa_manfaat.label('Masa_Manfaat'),
                AsetKib.g_jenis_barang.label('Jenis_Barang'), AsetKib.g_keterangan1.label('Keterangan_1'),
                AsetKib.g_keterangan2.label('Keterangan_2'), AsetKib.g_keterangan3.label('Keterangan_3')
                ).filter(AsetKib.unit_id == Unit.id,
                       AsetKib.pemilik_id == AsetPemilik.id, 
                       AsetKib.kategori_id==AsetKategori.id, 
                       AsetKib.kib=='G', 
                       func.substr(Unit.kode,1,func.length(ses['unit_kd']))==ses['unit_kd'],
                       or_(AsetKib.disabled=='0',AsetKib.disabled==None)
                ).order_by(Unit.kode, AsetKategori.kode, AsetKib.no_register
                )
                                          
        r = query.first()
        if not r:
            request.session.flash('Data tidak ada')
            return self.route_list()
            
        header = r.keys()
        query = query.all()
        rows = []
        for item in query:
            rows.append(list(item))

        # override attributes of response
        filename = 'AsetLainnya%s.csv' % datetime.now().strftime('%Y%m%d%H%M%S')

        self.request.response.content_disposition = 'attachment;filename=' + filename

        return {
          'header': header,
          'rows': rows,
        }
