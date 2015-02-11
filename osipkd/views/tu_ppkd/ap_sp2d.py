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
from osipkd.models.apbd_tu import Sp2d, Spm, Spp
    
from datatables import ColumnDT, DataTables
from osipkd.views.base_view import BaseViews

SESS_ADD_FAILED = 'Tambah ap-sp2d gagal'
SESS_EDIT_FAILED = 'Edit ap-sp2d gagal'

class view_ap_sp2d_ppkd(BaseViews):

    @view_config(route_name="ap-sp2d", renderer="templates/ap-sp2d/list.pt")
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
    @view_config(route_name='ap-sp2d-act', renderer='json',
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
                columns.append(ColumnDT('tanggal', filter=self._DTstrftime))
                columns.append(ColumnDT('kode1'))
                columns.append(ColumnDT('nama1'))
                columns.append(ColumnDT('nominal1'))
                columns.append(ColumnDT('posted'))
                query = DBSession.query(Sp2d.id, 
                                        Sp2d.kode, 
                                        Sp2d.tanggal,
                                        Spm.kode.label('kode1'), 
                                        Spm.nama.label('nama1'), 
                                        Spp.nominal.label('nominal1'),
                                        Sp2d.posted,
                        ).join(Spm 
                        ).outerjoin(Spp
                        ).filter(Spp.tahun_id==ses['tahun'],
                                 Spp.unit_id==ses['unit_id'],
                                 Sp2d.ap_spm_id==Spm.id,
                        )
                           
                rowTable = DataTables(req, Sp2d, query, columns)
                return rowTable.output_result()
            
        elif url_dict['act']=='grid2':
            ap_spm_id = 'ap_spm_id' in params and params['ap_spm_id'] or 0
            # defining columns
            columns = []
            columns.append(ColumnDT('id'))
            columns.append(ColumnDT('kode'))
            columns.append(ColumnDT('tanggal', filter=self._DTstrftime))
            columns.append(ColumnDT('jenis'))
            columns.append(ColumnDT('nama'))
            columns.append(ColumnDT('nominal'))
            columns.append(ColumnDT('posted'))
            query = DBSession.query(Sp2d.id,
                                    Spm.kode.label('kode'),
                                    Spm.tanggal.label('tanggal'),
                                    Spp.jenis.label('jenis'),
                                    Spm.nama.label('nama'),
                                    Spp.nominal.label('nominal'),
                                    Spm.posted.label('posted'),
                            ).join(Spm 
                            ).outerjoin(Spp
                            ).filter(Sp2d.ap_spm_id==ap_spm_id,
                                    Sp2d.ap_spm_id==Spm.id,
                                    Spm.ap_spp_id==Spp.id,
                                    #Spp.tahun_id==ses['tahun'],
                                    #Spp.unit_id==ses['unit_id'],
                            ).group_by(Sp2d.id,
                                    Spm.kode.label('kode'),
                                    Spm.tanggal.label('tanggal'),
                                    Spp.jenis.label('jenis'),
                                    Spm.nama.label('nama'),
                                    Spp.nominal.label('nominal'),
                                    Spm.posted.label('posted'),
                            )
                                  
            rowTable = DataTables(req, Sp2d, query, columns)
            return rowTable.output_result()
                
        elif url_dict['act']=='headofkode':
            term = 'term' in params and params['term'] or ''
            q = DBSession.query(Sp2d.id, Sp2d.kode.label('sp2d_kd'), Sp2d.nama.label('sp2d_nm')
                      ).join(Spm,
                      ).outerjoin(Spp, 
                      ).filter(Spp.unit_id == ses['unit_id'],
                            Spp.tahun_id==ses['tahun'],
                            Sp2d.kode.ilike('%s%%' % term))        
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
            q = DBSession.query(Sp2d.id, Sp2d.kode.label('sp2d_kd'), Sp2d.nama.label('sp2d_nm')
                      ).join(Spm,
                      ).outerjoin(Spp, 
                      ).filter(
                            Spp.unit_id == ses['unit_id'],
                            Spp.tahun_id==ses['tahun'],
                            Sp2d.nama.ilike('%s%%' % term))
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
            
        elif url_dict['act']=='headofkode1':
            term = 'term' in params and params['term'] or ''
            q = DBSession.query(Sp2d.id, Sp2d.kode.label('kode1'),Sp2d.nama.label('nama1'),Spp.nominal.label('amount1'),
                                )\
                                .join(Spm,)\
                                .outerjoin(Spp,)\
                                .filter(Spp.unit_id == ses['unit_id'],
                                        Spp.tahun_id == ses['tahun'],
                                        Sp2d.posted == 0,
                                        Sp2d.kode.ilike('%s%%' % term))
            rows = q.all()                               
            r = []
            for k in rows:
                d={}
                d['id']      = k[0]
                d['value']   = k[1]
                d['kode']    = k[1]
                d['nama']    = k[2]
                d['amount']  = k[3]
                r.append(d)
            print '---****----',r              
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
        schema.request = self.request
        return Form(schema, buttons=('simpan','batal'))
        
    def save(self, values, row=None):
        if not row:
            row = Sp2d()
            row.created = datetime.now()
            row.create_uid = self.request.user.id
        row.from_dict(values)
        row.updated = datetime.now()
        row.update_uid = self.request.user.id
        row.posted=0
        row.disabled = 'disabled' in values and 1 or 0  

        if not row.kode:
            tahun    = self.session['tahun']
            unit_kd  = self.session['unit_kd']
            no_urut  = Sp2d.get_norut(row.id)+1
            row.kode = "SP2D%d" % tahun + "-%s" % unit_kd + "-%d" % no_urut
            
        DBSession.add(row)
        DBSession.flush()
        
        #Untuk update status disabled pada SPM
        row = DBSession.query(Spm).filter(Spm.id==row.ap_spm_id).first()   
        row.disabled=1
        self.save_request3(row)
                
        return row
                                          
    def save_request(self, values, row=None):
        if 'id' in self.request.matchdict:
            values['id'] = self.request.matchdict['id']
        row = self.save(values, row)
        self.request.session.flash('SP2D sudah disimpan.')
        return row
            
    def route_list(self):
        return HTTPFound(location=self.request.route_url('ap-sp2d'))
        
    def session_failed(request, session_name):
        r = dict(form=request.session[session_name])
        del request.session[session_name]
        return r
        
    @view_config(route_name='ap-sp2d-add', renderer='templates/ap-sp2d/add.pt',
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
        return DBSession.query(Sp2d).filter(Sp2d.id==self.request.matchdict['id'])
        
    def id_not_found(request):    
        msg = 'User ID %s not found.' % request.matchdict['id']
        request.session.flash(msg, 'error')
        return self.route_list()

    @view_config(route_name='ap-sp2d-edit', renderer='templates/ap-sp2d/add.pt',
                 permission='edit')
    def view_edit(self):
        request = self.request
        row = self.query_id().first()
        
        if not row:
            return id_not_found(request)
        if row.posted:
            request.session.flash('Data sudah diposting', 'error')
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
        values['spm_nm']=row.spms.nama
        values['spm_kd']=row.spms.kode
        values['spm_n'] =row.spms.spps.nominal
        form.set_appstruct(values) 
        return dict(form=form)

       
    ##########
    # Delete #
    ##########    
    def save_request3(self, row=None):
        row = Spm()
        return row
        
    @view_config(route_name='ap-sp2d-delete', renderer='templates/ap-sp2d/delete.pt',
                 permission='delete')
    def view_delete(self):
        q = self.query_id()
        row = q.first()
        request=self.request
        
        if not row:
            return id_not_found(request)
        if row.posted:
            request.session.flash('Data sudah diposting', 'error')
            return self.route_list()
            
        form = Form(colander.Schema(), buttons=('hapus','cancel'))
        values= {}
        if request.POST:
            if 'hapus' in request.POST:
          
                #Untuk menghapus SP2D
                msg = '%s dengan kode %s telah berhasil.' % (request.title, row.kode)
                DBSession.query(Sp2d).filter(Sp2d.id==request.matchdict['id']).delete()
                DBSession.flush()
                request.session.flash(msg)
                
                #Untuk update status posted dan disabled pada SPM
                row = DBSession.query(Spm).filter(Spm.id==row.ap_spm_id).first()   
                row.posted=0
                row.disabled=0
                self.save_request3(row)
                
            return self.route_list()
        return dict(row=row,form=form.render())

    ###########
    # Posting #
    ###########     
    def save_request2(self, row=None):
        row = Sp2d()
        self.request.session.flash('SP2D sudah diposting.')
        return row
        
    @view_config(route_name='ap-sp2d-posting', renderer='templates/ap-sp2d/posting.pt',
                 permission='posting')
    def view_edit_posting(self):
        request = self.request
        row = self.query_id().first()
        
        if not row:
            return id_not_found(request)
        if row.posted:
            request.session.flash('Data sudah diposting', 'error')
            return self.route_list()
            
        form = Form(colander.Schema(), buttons=('posting','cancel'))
        
        if request.POST:
            if 'posting' in request.POST: 
                row.posted=1
                self.save_request2(row)
            return self.route_list()
        return dict(row=row, form=form.render()) 

class AddSchema(colander.Schema):
            
    ap_spm_id       = colander.SchemaNode(
                          colander.Integer(),
                          title="Spm",
                          oid = "ap_spm_id")
    spm_kd          = colander.SchemaNode(
                          colander.String(),
                          oid='spm_kd',
                          title="No. SPM")
    spm_n           = colander.SchemaNode(
                          colander.String(),
                          oid='spm_n',
                          title="Nilai")
    spm_nm          = colander.SchemaNode(
                          colander.String(),
                          oid='spm_nm')
                            
    kode            = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="No. SP2D")
    nama            = colander.SchemaNode(
                          colander.String(),
                          title = "Uraian"
                          )
    tanggal         = colander.SchemaNode(
                          colander.Date(),
                          title = "Tanggal"
                          #default = datetime.date()
                          )
    bud_uid         = colander.SchemaNode(
                          colander.Integer(),
                          missing=colander.drop,
                          title = "BUD",
                          oid="bud_uid"
                          )
    bud_nip         = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title = "BUD",
                          oid="bud_nip"
                          )
    bud_nama        = colander.SchemaNode(
                          colander.String(),
                          #missing=colander.drop,
                          title="BUD Nama",
                          oid="bud_nama")
    verified_uid    = colander.SchemaNode(
                          colander.Integer(),
                          missing=colander.drop,
                          title = "Verified",
                          oid="verified_uid"
                          )
    verified_nip    = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title = "Verified",
                          oid="verified_nip"
                          )
    verified_nama   = colander.SchemaNode(
                          colander.String(),
                          #missing=colander.drop,
                          title="Verified Nama",
                          oid="verified_nama")


class EditSchema(AddSchema):
    id             = colander.SchemaNode(
                          colander.Integer(),
                          oid="id")
                     