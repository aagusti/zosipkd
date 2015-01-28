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
from osipkd.models.apbd_tu import Spp, SppItem
    
from datatables import ColumnDT, DataTables
from osipkd.views.base_view import BaseViews

SESS_ADD_FAILED = 'Tambah ap-spp gagal'
SESS_EDIT_FAILED = 'Edit ap-spp gagal'

def deferred_ap_type(node, kw):
    values = kw.get('ap_type', [])
    return widget.SelectWidget(values=values)
    
AP_TYPE = (
    ('1', 'UP'),
    ('2', 'TU'),
    ('3', 'GU'),
    ('4', 'LS'),
    )

class view_ap_spp(BaseViews):

    @view_config(route_name="ap-spp", renderer="templates/ap-spp/list.pt")
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
    @view_config(route_name='ap-spp-act', renderer='json',
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
                columns.append(ColumnDT('posted'))
 
                query = DBSession.query(Spp.id,
                          Spp.kode,
                          Spp.tanggal,
                          Spp.jenis,
                          Spp.nama,
                          Spp.nominal,
                          Spp.posted
                        ).filter(Spp.tahun_id==ses['tahun'],
                              Spp.unit_id==ses['unit_id'],
                        ).order_by(Spp.no_urut.desc()
                        )
 
                rowTable = DataTables(req, Spp, query, columns)
                return rowTable.output_result()
                
        elif url_dict['act']=='headofnama':
            term = 'term' in params and params['term'] or '' 
            rows = DBSession.query(Spp.id, Spp.kode, Spp.nama
                    ).filter(Spp.unit_id==ses['unit_id'],
                            Spp.tahun_id==ses['tahun_id'],
                            Spp.nama.ilike('%%%s%%' % term) ).all()
            r = []
            for k in rows:
                d={}
                d['id']          = k[0]
                d['value']       = k[2]
                d['kode']        = k[1]
                d['nama']        = k[2]
                r.append(d)
            return r
            
        elif url_dict['act']=='headofkode1':
            term = 'term' in params and params['term'] or ''
            q = DBSession.query(Spp.id, Spp.kode.label('spp_kd'), Spp.nama.label('spp_nm')
                      ).filter(Spp.unit_id == ses['unit_id'],
                           Spp.tahun_id==ses['tahun'],
                           Spp.kode.ilike('%s%%' % term))        
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
            
        elif url_dict['act']=='headofnama1':
            term = 'term' in params and params['term'] or ''
            q = DBSession.query(Spp.id, Spp.kode.label('spp_kd'), Spp.nama.label('spp_nm')
                      ).filter(Spp.unit_id == ses['unit_id'],
                           Spp.tahun_id==ses['tahun'],
                           Spp.nama.ilike('%s%%' % term))        
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
            row = Spp()
            row.created = datetime.now()
            row.create_uid = self.request.user.id
        row.from_dict(values)
        row.updated = datetime.now()
        row.update_uid = self.request.user.id
        if not row.no_urut:
              row.no_urut = Spp.max_no_urut(row.tahun_id,row.unit_id)+1;
        row.disabled = 'disabled' in values and 1 or 0      
        print('XXXXXXXXXXXXX');
        DBSession.add(row)
        DBSession.flush()
        return row
                                          
    def save_request(self, values, row=None):
        if 'id' in self.request.matchdict:
            values['id'] = self.request.matchdict['id']
        values["nominal"]=values["nominal"].replace('.','') 
        row = self.save(values, row)
        self.request.session.flash('SPP sudah disimpan.')
        return row
            
    def route_list(self):
        return HTTPFound(location=self.request.route_url('ap-spp'))
        
    def session_failed(request, session_name):
        r = dict(form=request.session[session_name])
        del request.session[session_name]
        return r
        
    @view_config(route_name='ap-spp-add', renderer='templates/ap-spp/add.pt',
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
                return HTTPFound(location=request.route_url('ap-spp-edit', 
                                          id=row.id))
            return self.route_list()
        elif SESS_ADD_FAILED in request.session:
            del request.session[SESS_ADD_FAILED]
        return dict(form=form)

    ########
    # Edit #
    ########
    def query_id(self):
        return DBSession.query(Spp).filter(Spp.id==self.request.matchdict['id'])
        
    def id_not_found(request):    
        msg = 'User ID %s not found.' % request.matchdict['id']
        request.session.flash(msg, 'error')
        return self.route_list()

    @view_config(route_name='ap-spp-edit', renderer='templates/ap-spp/add.pt',
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
        values = row.to_dict() #dict(zip(row.keys(), row))
        values['spd_nm']=row.spds.nama
        values['spd_kd']=row.spds.kode
        values['spd_tgl']=row.spds.tanggal
        form.set_appstruct(values) 
        return dict(form=form)

    ##########
    # Delete #
    ##########    
    @view_config(route_name='ap-spp-delete', renderer='templates/ap-spp/delete.pt',
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
                msg = '%s Kode %s  No. %s %s sudah dihapus.' % (request.title, row.kode, row.no_urut, row.nama)
                DBSession.query(Spp).filter(Spp.id==request.matchdict['id']).delete()
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
    kode            = colander.SchemaNode(
                          colander.String(),
                          title = "No. SPP"
                          )
    ap_spd_id       = colander.SchemaNode(
                          colander.Integer(),
                          title="Spd",
                          oid = "ap_spd_id")
    spd_kd          = colander.SchemaNode(
                          colander.String(),
                          oid='spd_kd',
                          title="No. SPD")
    spd_nm          = colander.SchemaNode(
                          colander.String(),
                          oid='spd_nm')
    spd_tgl         = colander.SchemaNode(
                          colander.String(),
                          oid='spd_tgl',
                          title="Tgl. SPD")
    no_urut         = colander.SchemaNode(
                          colander.Integer(),
                          missing=colander.drop,
                          )
    jenis           = colander.SchemaNode(
                          colander.String(),
                          widget=widget.SelectWidget(values=AP_TYPE),
                          )
    tanggal         = colander.SchemaNode(
                          colander.Date(),
                          #default = datetime.date()
                          )
    nama            = colander.SchemaNode(
                          colander.String(),
                          title = "Uraian"
                          )
    ap_nama         = colander.SchemaNode(
                          colander.String(),
                          title="Penerima"
                          )
    ap_bank         = colander.SchemaNode(
                          colander.String(),
                          title="Bank"
                          )
    ap_rekening     = colander.SchemaNode(
                          colander.String(),
                          title="Rekening"
                          )
    ap_npwp         = colander.SchemaNode(
                          colander.String(),
                          title="NPWP"
                          )
    ap_nip          = colander.SchemaNode(
                          colander.String(),
                          title="NIP"
                          )
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
    ap_bentuk       = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="Bentuk"
                          )
    ap_alamat       = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="Alamat"
                          )
    ap_pemilik      = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="Pemilik"
                          )
    ap_kontrak      = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="Kontrak"
                          )
    ap_waktu        = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="Waktu"
                          )

    ap_tgl_kontrak  = colander.SchemaNode(
                          colander.Date(),
                          missing=colander.drop,
                          title="Tanggal"
                          )
    ap_kegiatankd   = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="Kegiatan"
                          )
    ap_uraian       = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="Uraian"
                          )
    pptk_uid         = colander.SchemaNode(
                          colander.Integer(),
                          missing=colander.drop,
                          oid="pptk_uid"
                          )
    pptk_nip         = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          oid="pptk_nip",
                          title="PPTK"
                          )
    pptk_nama        = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          oid="pptk_nama",
                          title="Nama")
    barang_uid         = colander.SchemaNode(
                          colander.Integer(),
                          missing=colander.drop,
                          oid="barang_uid"
                          )
    barang_nip         = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          oid="barang_nip",
                          title="Barang"
                          )
    barang_nama        = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          oid="barang_nama",
                          title="Nama")
    barang_jab         = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          oid="barang_jab",
                          title="Jabatan")
    kasi_uid         = colander.SchemaNode(
                          colander.Integer(),
                          missing=colander.drop,
                          oid="kasi_uid"
                          )
    kasi_nip         = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          oid="kasi_nip",
                          title="Kasi"
                          )
    kasi_nama        = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          oid="kasi_nama",
                          title="Nama")
    kasi_jab         = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          oid="kasi_jab",
                          title="Jabatan")
    posted           = colander.SchemaNode(
                          colander.Integer(),
                          missing=colander.drop,
                          oid="posted"
                          )

class EditSchema(AddSchema):
    id             = colander.SchemaNode(
                          colander.Integer(),
                          oid="id")
                     