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
from osipkd.models.apbd_tu import AkJurnal, AkJurnalItem, Sp2d, ARInvoice, Sts
    
from datatables import ColumnDT, DataTables
from osipkd.views.base_view import BaseViews

SESS_ADD_FAILED = 'Tambah ak-jurnal-skpd gagal'
SESS_EDIT_FAILED = 'Edit ak-jurnal-skpd gagal'

def deferred_jv_type(node, kw):
    values = kw.get('jv_type', [])
    return widget.SelectWidget(values=values)
    
JV_TYPE = (
    (1, 'LRA'),
    (2, 'LO'),
    (3, 'Jurnal Umum'),
    )
    
def deferred_is_skpd(node, kw):
    values = kw.get('is_skpd', [])
    return widget.SelectWidget(values=values)
    
IS_SKPD = (
    (0, 'PPKD'),
    (1, 'SKPD'))      
    
class AddSchema(colander.Schema):
    unit_kd_widget = widget.AutocompleteInputWidget(
            values = '/unit/act/headofkode',
            min_length=1)
  
    unit_nm_widget = widget.AutocompleteInputWidget(
            values = '/unit/act/headofnama',
            min_length=1)
            
          
    tahun_id  = colander.SchemaNode(
                    colander.Integer(),
                    oid='tahun_id',
                    title="Tahun")

    unit_id  = colander.SchemaNode(
                    colander.Integer(),
                    oid='unit_id',
                    title="SKPD ID")

    unit_kd  = colander.SchemaNode(
                    colander.String(),
                    oid='unit_kd',
                    title="SKPD",
                    widget = unit_kd_widget,)

    unit_nm  = colander.SchemaNode(
                    colander.String(),
                    oid='unit_nm',
                    title="SKPD NM",
                    widget = unit_nm_widget)
    kode        = colander.SchemaNode(
                    colander.String(),
                    missing = colander.drop,
                    title="No. Jurnal"
                    )
                    
    nama        = colander.SchemaNode(
                    colander.String(),
                    title="Uraian"
                    )
    tanggal     = colander.SchemaNode(
                  colander.Date(),
                  )
               
    jv_type     = colander.SchemaNode(
                    colander.String(),
                    widget=widget.SelectWidget(values=JV_TYPE),
                    title="Tipe"
                    )
    source_no   = colander.SchemaNode(
                    colander.String(),
                    validator=colander.Length(max=32),
                    title = "Referensi"
                    )
    source      = colander.SchemaNode(
                    colander.String(),
                    validator=colander.Length(max=64),
                    )
    tgl_source  = colander.SchemaNode(
                    colander.Date(),
                    title = "Tgl. Ref"
                )
    
    notes       = colander.SchemaNode(
                    colander.String(),
                    missing = colander.drop
                    )
    is_skpd     = colander.SchemaNode(
                    colander.Integer(),
                    title="Jurnal",
                    oid = "is_skpd",
                    widget=widget.SelectWidget(values=IS_SKPD)
                  )
                    
                    
class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.String(),
            missing=colander.drop,
            widget=widget.HiddenWidget(readonly=True),
            oid="id")
            
class view_ak_jurnal_skpd(BaseViews):
    ########                    
    # List #
    ########    
    @view_config(route_name='ak-jurnal-skpd', renderer='templates/ak-jurnal-skpd/list.pt',
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
    @view_config(route_name='ak-jurnal-skpd-act', renderer='json',
                 permission='read')
    def ak_jurnal_skpd_act(self):
        ses = self.request.session
        req = self.request
        params = req.params
        url_dict = req.matchdict
        if url_dict['act']=='grid':
            columns = []
            columns.append(ColumnDT('id'))
            columns.append(ColumnDT('tanggal', filter=self._DTstrftime))
            columns.append(ColumnDT('kode'))
            columns.append(ColumnDT('jv_type'))
            columns.append(ColumnDT('nama'))
            columns.append(ColumnDT('source'))
            columns.append(ColumnDT('amount',  filter=self._number_format))
            columns.append(ColumnDT('posted'))
            
            query = DBSession.query(AkJurnal.id, AkJurnal.tanggal, AkJurnal.kode, AkJurnal.jv_type,
                      AkJurnal.nama, AkJurnal.source, AkJurnal.posted,
                      func.coalesce(func.sum(AkJurnalItem.amount),0).label('amount')).\
                    outerjoin(AkJurnalItem).\
                    group_by(AkJurnal.id, AkJurnal.tanggal, AkJurnal.kode, AkJurnal.jv_type,
                             AkJurnal.nama, AkJurnal.source, ).\
                    filter(AkJurnal.tahun_id == ses['tahun'],
                           AkJurnal.unit_id == ses['unit_id'],)
                      
            rowTable = DataTables(req, AkJurnal, query, columns)
            return rowTable.output_result()
        
    #######    
    # Add #
    #######
    def form_validator(self, form, value):
        if 'id' in form.request.matchdict:
            uid = form.request.matchdict['id']
            q = DBSession.query(AkJurnal).filter_by(id=uid)
            row = q.first()
        else:
            row = None
                
    def get_form(self, class_form, row=None):
        schema = class_form(validator=self.form_validator)
        schema = schema.bind(jv_type=JV_TYPE, is_skpd=IS_SKPD)
        schema.request = self.request
        if row:
          schema.deserialize(row)
        return Form(schema, buttons=('simpan','batal'))
        
    def save(self, values, user, row=None):
        if not row:
            row = AkJurnal()
            row.created = datetime.now()
            row.create_uid = user.id
        row.from_dict(values)
        tanggal           = datetime.strptime(values['tanggal'], '%Y-%m-%d')
        row.tahun_id      = tanggal.year
        row.periode       = tanggal.month
        row.updated       = datetime.now()
        row.update_uid    = user.id
        row.disable       = 'disable' in values and values['disable'] and 1 or 0
        row.posted        = 'posted'  in values and values['posted']  and 1 or 0
        row.tgl_transaksi = datetime.now()
        
        if not row.kode:
            tahun    = self.session['tahun']
            unit_kd  = self.session['unit_kd']
            is_skpd  = row.is_skpd
            jv_type  = row.jv_type
            tipe     = AkJurnal.get_tipe(jv_type)
            no_urut  = AkJurnal.get_norut(row.id)+1
            row.kode = "%d" % tahun + "-%s" % is_skpd + "-%s" % unit_kd + "-%s" % tipe + "-%d" % no_urut
        
        DBSession.add(row)
        DBSession.flush()
        return row
        
    def save_request(self, values, row=None):
        if 'id' in self.request.matchdict:
            values['id'] = self.request.matchdict['id']
        row = self.save(values, self.request.user, row)
        self.request.session.flash('Jurnal sudah disimpan.')
        return row
            
    def route_list(self):
        return HTTPFound(location=self.request.route_url('ak-jurnal-skpd'))
        
    def session_failed(self, session_name):
        del self.session[session_name]
        
    @view_config(route_name='ak-jurnal-skpd-add', renderer='templates/ak-jurnal-skpd/add.pt',
                 permission='add')
    def view_ak_jurnal_skpd_add(self):
        req = self.request
        ses = self.session
        form = self.get_form(AddSchema)
        if req.POST:
            if 'simpan' in req.POST:
                controls = req.POST.items()
                try:
                    c = form.validate(controls)
                except ValidationFailure, e:
                    return dict(form=form)
                id = self.save_request(dict(controls))
            return self.route_list()  
        elif SESS_ADD_FAILED in req.session:
            return dict(form=form)
        return dict(form=form)

        
    ########
    # Edit #
    ########
    def query_id(self):
        return DBSession.query(AkJurnal).filter_by(id=self.request.matchdict['id'])
        
    def id_not_found(self):    
        msg = 'Jurnal ID %s Tidak Ditemukan.' % self.request.matchdict['id']
        request.session.flash(msg, 'error')
        return route_list()

    @view_config(route_name='ak-jurnal-skpd-edit', renderer='templates/ak-jurnal-skpd/add.pt',
                 permission='edit')
    def view_ak_jurnal_skpd_edit(self):
        request = self.request
        row = self.query_id().first()
        
        if not row:
            return id_not_found(request)
        if row.posted:
            request.session.flash('Data sudah diposting', 'error')
            return self.route_list()

        rowd={}
        rowd['id']            = row.id
        rowd['unit_id']       = row.unit_id
        rowd['unit_nm']       = row.units.nama
        rowd['unit_kd']       = row.units.kode
        rowd['kode']          = row.kode
        rowd['nama']          = row.nama
        rowd['source_no']     = row.source_no
        rowd['source']        = row.source
        rowd['tgl_source']    = row.tgl_source
        rowd['tanggal']       = row.tanggal
        rowd['jv_type']       = row.jv_type
        rowd['disabled']      = row.disabled
        rowd['notes']         = row.notes
        rowd['is_skpd']       = row.is_skpd
        
        form = self.get_form(EditSchema)
        form.set_appstruct(rowd)
        if request.POST:
            if 'simpan' in request.POST:
                controls = request.POST.items()
                print controls
                try:
                    c = form.validate(controls)
                except ValidationFailure, e:
                    return dict(form=form)
                self.save_request(dict(controls),row)
            return self.route_list()
        elif SESS_EDIT_FAILED in request.session:
            return self.session_failed(SESS_EDIT_FAILED)
        return dict(form=form)

    ##########
    # Delete #
    ##########    
    @view_config(route_name='ak-jurnal-skpd-delete', renderer='templates/ak-jurnal-skpd/delete.pt',
                 permission='delete')
    def view_ak_jurnal_skpd_delete(self):
        request = self.request
        q = self.query_id()
        row = q.first()
        kode = row.source_no
        
        if not row:
            return self.id_not_found(request)
            
        form = Form(colander.Schema(), buttons=('hapus','batal'))
        if request.POST:
            if 'hapus' in request.POST:
                
                #Untuk hapus jurnal 
                msg = '%s dengan kode %s telah berhasil.' % (request.title, row.kode)
                q.delete()
                DBSession.flush()
                request.session.flash(msg)  
                
                #Untuk update status disabled dan posted SP2D    
                row = DBSession.query(Sp2d).filter(Sp2d.kode==kode).first()
                if not row:
                    #Untuk update status disabled dan posted PIUTANG
                    row = DBSession.query(ARInvoice).filter(ARInvoice.kode==kode).first()
                    if not row:  
                        #Untuk update status disabled dan posted STS
                        row = DBSession.query(Sts).filter(Sts.kode==kode).first()
                        row.disabled=0
                        row.posted=0
                        self.save_request6(row)
                    row.disabled=0
                    row.posted=0
                    self.save_request5(row)
                row.disabled=0
                row.posted=0
                self.save_request4(row)
                
            return self.route_list()
        return dict(row=row, form=form.render())

    ###########
    # Posting #
    ###########   
    def save_request2(self, row=None):
        row = AkJurnal()
        self.request.session.flash('Jurnal sudah diposting.')
        return row
    def save_request4(self, row=None):
        row = Sp2d()
        return row
    def save_request5(self, row=None):
        row = ARInvoice()
        return row
    def save_request6(self, row=None):
        row = Sts()
        return row
        
    @view_config(route_name='ak-jurnal-skpd-posting', renderer='templates/ak-jurnal-skpd/posting.pt',
                 permission='posting')
    def view_edit_posting(self):
        request = self.request
        row = self.query_id().first()
        kode = row.source_no
        
        if not row:
            return id_not_found(request)
        if row.posted:
            request.session.flash('Data sudah diposting', 'error')
            return self.route_list()
            
        form = Form(colander.Schema(), buttons=('posting','cancel'))
        
        if request.POST:
            if 'posting' in request.POST: 
                
                #Update status posted pada Jurnal
                row.posted=1
                row.posted_date=datetime.now()
                self.save_request2(row)
                
                #Untuk update status disabled SP2D    
                row = DBSession.query(Sp2d).filter(Sp2d.kode==kode).first()
                if not row:
                    #Untuk update status disabled PIUTANG
                    row = DBSession.query(ARInvoice).filter(ARInvoice.kode==kode).first()
                    if not row:  
                        #Untuk update status disabled STS
                        row = DBSession.query(Sts).filter(Sts.kode==kode).first()
                        row.disabled=1
                        self.save_request6(row)
                    row.disabled=1
                    self.save_request5(row)
                row.disabled=1
                self.save_request4(row)
    
            return self.route_list()
        return dict(row=row, form=form.render())                       
            
    #############
    # UnPosting #
    #############   
    def save_request3(self, row=None):
        row = AkJurnal()
        self.request.session.flash('Jurnal sudah di UnPosting.')
        return row
        
    @view_config(route_name='ak-jurnal-skpd-unposting', renderer='templates/ak-jurnal-skpd/unposting.pt',
                 permission='unposting') 
    def view_edit_unposting(self):
        request = self.request
        row = self.query_id().first()
        kode = row.source_no
        
        if not row:
            return id_not_found(request)
        if not row.posted:
            request.session.flash('Data tidak dapat di Unposting, karena belum diposting.', 'error')
            return self.route_list()
            
        form = Form(colander.Schema(), buttons=('unposting','cancel'))
        
        if request.POST:
            if 'unposting' in request.POST: 
                                
                kode = row.source_no
                #Update status posted pada Jurnal
                row.posted=0
                row.posted_date=datetime.now()
                self.save_request3(row)

                #Untuk update status disabled SP2D    
                row = DBSession.query(Sp2d).filter(Sp2d.kode==kode).first()
                if not row:
                    #Untuk update status disabled PIUTANG
                    row = DBSession.query(ARInvoice).filter(ARInvoice.kode==kode).first()
                    if not row:  
                        #Untuk update status disabled STS
                        row = DBSession.query(Sts).filter(Sts.kode==kode).first()
                        row.disabled=0
                        self.save_request6(row)
                    row.disabled=0
                    self.save_request5(row)
                row.disabled=0
                self.save_request4(row)
                
            return self.route_list()
        return dict(row=row, form=form.render())       
