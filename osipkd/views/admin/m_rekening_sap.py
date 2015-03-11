import os
import uuid
import colander

from datetime import datetime

from sqlalchemy import not_, func
from sqlalchemy.sql.expression import and_
from sqlalchemy.orm import aliased

from ziggurat_foundations.models import groupfinder
from pyramid.view import (view_config,)
from pyramid.httpexceptions import (HTTPFound,)
from osipkd.views.base_view import BaseViews

from deform import (Form, widget,ValidationFailure,)
from datatables import ColumnDT, DataTables

from osipkd.tools import row2dict, xls_reader
from osipkd.models import (DBSession,)
from osipkd.models.pemda_model import Sap, RekeningSap, Rekening
from osipkd.models.apbd_anggaran import Kegiatan, KegiatanSub, KegiatanItem


SESS_ADD_FAILED = 'Tambah rekening sap gagal'
SESS_EDIT_FAILED = 'Edit rekening sap gagal'

@colander.deferred
def deferred_pph(node, kw):
    values = kw.get('pph', [])
    return widget.SelectWidget(values=values)
    
PPH = (
    ('-', '-'),
    ('21', '21'),
    ('22', '22'),
    ('23', '23'),
    ('4.2', '4.2'),
    )
         
class AddSchema(colander.Schema):
    rek_widget  = widget.AutocompleteInputWidget(
                    size=60,
                    values = '/rekening/act/headofkode11',
                    min_length=1)
    rekn_widget = widget.AutocompleteInputWidget(
                    size=60,
                    values = '/rekening/act/headofnama11',
                    min_length=1)
    rekening_id = colander.SchemaNode(
                    colander.Integer(),
                    widget = widget.HiddenWidget(),
                    missing = colander.drop,
                    oid = "rekening_id")
    rekening_kd = colander.SchemaNode(
                    colander.String(),
                    widget = rek_widget,
                    missing = colander.drop,
                    oid = "rekening_kd",
                    title = "Rekening")
    rekening_nm = colander.SchemaNode(
                    colander.String(),
                    widget = rekn_widget,
                    missing = colander.drop,
                    oid = "rekening_nm",
                    title = "Uraian")
    
    lo_widget   = widget.AutocompleteInputWidget(
                    size=60,
                    values = '/sap/act/headofkode1',
                    min_length=1)    
    lon_widget  = widget.AutocompleteInputWidget(
                    size=60,
                    values = '/sap/act/headofnama1',
                    min_length=1)
    lo_sap_id   = colander.SchemaNode(
                    colander.Integer(),
                    widget = widget.HiddenWidget(),
                    missing = colander.drop,
                    oid = "lo_sap_id")
    lo_sap_kd   = colander.SchemaNode(
                    colander.String(),
                    widget = lo_widget,
                    missing = colander.drop,
                    oid = "lo_sap_kd",
                    title = "LO")
    lo_sap_nm   = colander.SchemaNode(
                    colander.String(),
                    widget = lon_widget,
                    missing = colander.drop,
                    oid = "lo_sap_nm",
                    title = "Uraian LO")
      
    lra_widget  = widget.AutocompleteInputWidget(
                    size=60,
                    values = '/sap/act/headofkode2',
                    min_length=1) 
    lran_widget = widget.AutocompleteInputWidget(
                    size=60,
                    values = '/sap/act/headofnama2',
                    min_length=1)                    
    lra_sap_id  = colander.SchemaNode(
                    colander.Integer(),
                    widget = widget.HiddenWidget(),
                    missing = colander.drop,
                    oid = "lra_sap_id")
    lra_sap_kd  = colander.SchemaNode(
                    colander.String(),
                    widget = lra_widget,
                    missing = colander.drop,
                    oid = "lra_sap_kd",
                    title = "LRA")
    lra_sap_nm  = colander.SchemaNode(
                    colander.String(),
                    widget = lran_widget,
                    missing = colander.drop,
                    oid = "lra_sap_nm",
                    title = "Uraian LRA")
     
    aset_widget = widget.AutocompleteInputWidget(
                    size=60,
                    values = '/sap/act/headofkode3',
                    min_length=1)
    asetn_widget = widget.AutocompleteInputWidget(
                    size=60,
                    values = '/sap/act/headofnama3',
                    min_length=1)                    
    aset_sap_id = colander.SchemaNode(
                    colander.Integer(),
                    widget = widget.HiddenWidget(),
                    missing = colander.drop,
                    oid = "aset_sap_id")
    aset_sap_kd = colander.SchemaNode(
                    colander.String(),
                    widget = aset_widget,
                    missing = colander.drop,
                    oid = "aset_sap_kd",
                    title = "Aset")
    aset_sap_nm = colander.SchemaNode(
                    colander.String(),
                    widget = asetn_widget,
                    missing = colander.drop,
                    oid = "aset_sap_nm",
                    title = "Uraian Aset")
                    
    pph_id      = colander.SchemaNode(
                    colander.String(),
                    widget=deferred_pph,
                    title = "PPh")

                    
class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.String(),
            missing=colander.drop,
            widget=widget.HiddenWidget(readonly=True))
            
class view_rekening(BaseViews):
    ########                    
    # List #
    ########    
    @view_config(route_name='rekening-sap', renderer='templates/rekening-sap/list.pt',
                 permission='read')
    def view_list(self):
        return dict(project="osipkd")
        
    ##########                    
    # Action #
    ##########    
    @view_config(route_name='rekening-sap-act', renderer='json',
                 permission='view')
    def gaji_sap_act(self):
        ses = self.request.session
        req = self.request
        params   = req.params
        url_dict = req.matchdict
        
        if url_dict['act']=='grid':
            columns = []
            columns.append(ColumnDT('id'))
            columns.append(ColumnDT('norek'))
            columns.append(ColumnDT('nmrek'))
            columns.append(ColumnDT('nosaplo'))
            columns.append(ColumnDT('nosaplra'))
            columns.append(ColumnDT('nosapaset'))
            columns.append(ColumnDT('pph_id'))
            
            sap1 = aliased(Sap)
            sap2 = aliased(Sap)
            sap3 = aliased(Sap)
            
            query = DBSession.query(RekeningSap.id,
                                    Rekening.kode.label('norek'),
                                    Rekening.nama.label('nmrek'),
                                    sap1.kode.label('nosaplo'),
                                    sap2.kode.label('nosaplra'),
                                    sap3.kode.label('nosapaset'),
                                    RekeningSap.pph_id
                              ).outerjoin(Rekening, RekeningSap.rekening_id==Rekening.id
                              ).outerjoin(sap1, RekeningSap.lo_sap_id==sap1.id
                              ).outerjoin(sap2, RekeningSap.lra_sap_id==sap2.id
                              ).outerjoin(sap3, RekeningSap.aset_sap_id==sap3.id)
            
            rowTable = DataTables(req, RekeningSap, query, columns)
            return rowTable.output_result()
            
    #######    
    # Add #
    #######
    def form_validator(self, form, value):
        if 'id' in form.request.matchdict:
            uid = form.request.matchdict['id']
            q = DBSession.query(RekeningSap).filter_by(id=uid)
            rekeningsap = q.first()
        else:
            rekeningsap = None
            
    def get_form(self, class_form, row=None):
        schema = class_form(validator=self.form_validator)
        schema = schema.bind(pph=PPH)
        schema.request = self.request
        if row:
          schema.deserialize(row)
        return Form(schema, buttons=('simpan','batal'))
        
    def save(self, values, user, row=None):
        if not row:
            row = RekeningSap()
        row.from_dict(values)
        
        DBSession.add(row)
        DBSession.flush()
        return row
        
    def save_request(self, values, row=None):
        if 'id' in self.request.matchdict:
            values['id'] = self.request.matchdict['id']
        row = self.save(values, self.request.user, row)
        self.request.session.flash('Rekening SAP sudah disimpan.')
        
    def route_list(self):
        return HTTPFound(location=self.request.route_url('rekening-sap'))
        
    def session_failed(self, session_name):
        r = dict(form=self.session[session_name])
        del self.session[session_name]
        return r
        
    @view_config(route_name='rekening-sap-add', renderer='templates/rekening-sap/edit.pt',
                 permission='add')
    def view_sap_add(self):
        req = self.request
        ses = self.session
        
        form = self.get_form(AddSchema)
        if req.POST:
            if 'simpan' in req.POST:
                controls = req.POST.items()
                try:
                    c = form.validate(controls)
                except ValidationFailure, e:
                    req.session[SESS_ADD_FAILED] = e.render()               
                    return HTTPFound(location=req.route_url('rekening-sap-add'))
                self.save_request(dict(controls))
            return self.route_list()
        elif SESS_ADD_FAILED in req.session:
            return self.session_failed(SESS_ADD_FAILED)
        return dict(form=form.render())
        
    ########
    # Edit #
    ########
    def query_id(self):
        return DBSession.query(RekeningSap).filter_by(id=self.request.matchdict['id'])
        
    def id_not_found(self):    
        msg = 'Rekening SAP ID %s Tidak Ditemukan.' % self.request.matchdict['id']
        request.session.flash(msg, 'error')
        return route_list()
        
    @view_config(route_name='rekening-sap-edit', renderer='templates/rekening-sap/edit.pt',
                 permission='edit')
    def view_rekening_edit(self):
        request = self.request
        row     = self.query_id().first()
        
        if not row:
            return id_not_found(request)
        """           
        rowd={}
        rowd['id']          = row.id
        rowd['rekening_kd'] = row.rekenings.kode
        rowd['rekening_nm'] = row.rekenings.nama
        
        rowd['lo_sap_kd']   = row.losaps.kode
        rowd['lo_sap_nm']   = row.losaps.nama
        
        rowd['lra_sap_kd']  = row.lrasaps.kode
        rowd['lra_sap_nm']  = row.lrasaps.nama
        
        rowd['aset_sap_kd'] = row.asetsaps.kode
        rowd['aset_sap_nm'] = row.asetsaps.nama
        
        rowd['pph_id'] = row.pph_id
        """
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
            return self.session_failed(SESS_EDIT_FAILED)
        values = row.to_dict()
    
        values['rekening_kd'] = row.rekenings.kode
        values['rekening_nm'] = row.rekenings.nama
        
        values['lo_sap_kd'] = row.losaps.kode
        values['lo_sap_nm'] = row.losaps.nama
        
        values['lra_sap_kd'] = row.lrasaps.kode
        values['lra_sap_nm'] = row.lrasaps.nama
        
        values['aset_sap_kd'] = row.asetsaps.kode
        values['aset_sap_nm'] = row.asetsaps.nama
        
        r=DBSession.query(RekeningSap.pph_id).filter(RekeningSap.id==row.id).first()
        values['pph_id'] = "%s" % r
        
        return dict(form=form.render(appstruct=values))
        
    ##########
    # Delete #
    ##########    
    @view_config(route_name='rekening-sap-delete', renderer='templates/rekening-sap/delete.pt',
                 permission='delete')
    def view_sap_delete(self):
        request = self.request
        q       = self.query_id()
        row     = q.first()
        
        if not row:
            return self.id_not_found(request)
            
        form = Form(colander.Schema(), buttons=('hapus','batal'))
        if request.POST:
            if 'hapus' in request.POST:
                msg = 'Rekening SAP ID %d sudah dihapus.' % (row.id)
                try:
                  q.delete()
                  DBSession.flush()
                except:
                  msg = 'Rekening SAP ID %d tidak dapat dihapus.' % (row.id)
                request.session.flash(msg)
            return self.route_list()
        return dict(row=row, form=form.render())
        