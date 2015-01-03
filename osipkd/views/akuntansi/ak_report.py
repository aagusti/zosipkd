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
from osipkd.models.apbd import Jurnal, JurnalItem
    
from datatables import ColumnDT, DataTables
from osipkd.views.base_view import BaseViews

SESS_ADD_FAILED = 'Tambah ak-report gagal'
SESS_EDIT_FAILED = 'Edit ak-report gagal'
            
class view_ak_jurnal_item(BaseViews):
    ########                    
    # List #
    ########    
    @view_config(route_name='ak-report', renderer='templates/ak-report/list.pt',
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
    @view_config(route_name='ak-report-act', renderer='json',
                 permission='read')
    def view_act(self):
        ses = self.request.session
        req = self.request
        params = req.params
        url_dict = req.matchdict
        if url_dict['act']=='grid':
            columns = []
            columns.append(ColumnDT('id'))
            columns.append(ColumnDT('kegiatan_subs.kegiatans.kode'))
            columns.append(ColumnDT('kegiatan_subs.no_urut'))
            columns.append(ColumnDT('rekenings.kode'))
            columns.append(ColumnDT('rekenings.nama'))
            columns.append(ColumnDT('amount',  filter=self._number_format))
            columns.append(ColumnDT('kegiatan_subs.nama'))
            columns.append(ColumnDT('jurnal_id'))
            columns.append(ColumnDT('notes'))
            columns.append(ColumnDT('kegiatan_subs.id'))
            columns.append(ColumnDT('rekening_id'))
            
            query = DBSession.query(JurnalItem)
            rowTable = DataTables(req, JurnalItem, query, columns)
            return rowTable.output_result()
        
