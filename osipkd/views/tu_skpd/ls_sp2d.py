import os
import uuid
from osipkd.tools import row2dict, xls_reader
from datetime import datetime,date
from sqlalchemy import not_, func, or_
from pyramid.view import (view_config,)
from pyramid.httpexceptions import ( HTTPFound, )
import colander
from deform import (Form, widget, ValidationFailure, )
from osipkd.models import DBSession
from osipkd.models.apbd_anggaran import Kegiatan, KegiatanSub, KegiatanItem
from osipkd.models.pemda_model import Unit, Rekening, RekeningSap, Sap
from osipkd.models.apbd_tu import Sp2d, Spm, Spp, AkJurnal, AkJurnalItem, SppItem, APInvoice, APInvoiceItem
    
from datatables import ColumnDT, DataTables
from osipkd.views.base_view import BaseViews
from array import *

SESS_ADD_FAILED = 'Tambah ls-sp2d gagal'
SESS_EDIT_FAILED = 'Edit ls-sp2d gagal'

class view_ak_sp2d_ppkd(BaseViews):

    @view_config(route_name="ls-sp2d", renderer="templates/ak-sp2d/list2.pt",
                 permission='read')
    def view_list(self):
        ses = self.request.session
        req = self.request
        params = req.params
        url_dict = req.matchdict
        return dict(project='EIS',
        )
        
    ##########                    
    # Action #
    ##########    
    @view_config(route_name='ls-sp2d-act', renderer='json',
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
                columns.append(ColumnDT('nama'))
                columns.append(ColumnDT('no_validasi'))
                columns.append(ColumnDT('kode1'))
                columns.append(ColumnDT('nominal1'))
                columns.append(ColumnDT('posted'))
                query = DBSession.query(Sp2d.id, 
                                        Sp2d.kode, 
                                        Sp2d.tanggal,
                                        Sp2d.nama, 
                                        Sp2d.no_validasi, 
                                        Spm.kode.label('kode1'), 
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
        
        elif url_dict['act']=='grid1':
            cari = 'cari' in params and params['cari'] or ''
            columns = []
            columns.append(ColumnDT('id'))
            columns.append(ColumnDT('kode'))
            columns.append(ColumnDT('tanggal', filter=self._DTstrftime))
            columns.append(ColumnDT('nama'))
            columns.append(ColumnDT('no_validasi'))
            columns.append(ColumnDT('kode1'))
            columns.append(ColumnDT('nominal1'))
            columns.append(ColumnDT('posted'))
            query = DBSession.query(Sp2d.id, 
                                    Sp2d.kode, 
                                    Sp2d.tanggal,
                                    Sp2d.nama, 
                                    Sp2d.no_validasi, 
                                    Spm.kode.label('kode1'), 
                                    Spp.nominal.label('nominal1'),
                                    Sp2d.posted,
                    ).join(Spm 
                    ).outerjoin(Spp
                    ).filter(Spp.tahun_id==ses['tahun'],
                             Spp.unit_id==ses['unit_id'],
                             Sp2d.ap_spm_id==Spm.id,
                    ).filter(or_(Spm.kode.ilike('%%%s%%' % cari),
                                 Sp2d.kode.ilike('%%%s%%' % cari),
                                 Sp2d.nama.ilike('%%%s%%' % cari),
                                 Sp2d.no_validasi.ilike('%%%s%%' % cari)))
                       
            rowTable = DataTables(req, Sp2d, query, columns)
            return rowTable.output_result()        
            
    def route_list(self):
        return HTTPFound(location=self.request.route_url('ls-sp2d'))
        
    def session_failed(request, session_name):
        r = dict(form=request.session[session_name])
        del request.session[session_name]
        return r
        
    def query_id(self):
        return DBSession.query(Sp2d).filter(Sp2d.id==self.request.matchdict['id'])
        
    def id_not_found(request):    
        msg = 'User ID %s not found.' % request.matchdict['id']
        request.session.flash(msg, 'error')
        return self.route_list()

    def save_request3(self, row=None):
        row = Spm()
        return row
