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
from osipkd.models.apbd_anggaran import Kegiatan, KegiatanSub, KegiatanItem
    
from datatables import ColumnDT, DataTables
from osipkd.views.base_view import BaseViews

SESS_ADD_FAILED = 'Tambah ag-pendapatan gagal'
SESS_EDIT_FAILED = 'Edit ag-pendapatan gagal'

def deferred_jv_type(node, kw):
    values = kw.get('jv_type', [])
    return widget.SelectWidget(values=values)
    

class view_ak_jurnal(BaseViews):
    ########                    
    # List #
    ########    
    @view_config(route_name='ag-pendapatan', renderer='templates/ag-pendapatan/list.pt',
                 permission='read')
    def view_list(self):
        ses = self.request.session
        req = self.request
        params = req.params
        url_dict = req.matchdict
        row = {}
        row['rekening_kd'] = '0.00.00.10'
        row['rekening_nm'] = 'PENDAPATAN'
        row['rekeninghead'] = 4
        
        return dict(project='EIS', row = row)
        
