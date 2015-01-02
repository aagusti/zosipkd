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
from osipkd.models.pemda_model import Rekening
from datatables import ColumnDT, DataTables
from osipkd.views.base_view import BaseViews

SESS_ADD_FAILED = 'Tambah ag-kegiatan-sub gagal'
SESS_EDIT_FAILED = 'Edit ag-kegiatan-sub gagal'

def deferred_jv_type(node, kw):
    values = kw.get('jv_type', [])
    return widget.SelectWidget(values=values)
    
JV_TYPE = (
    ('lra', 'LRA'),
    ('lo', 'LO'),
    ('ju', 'Jurnal Umum'),
    )

class view_ak_jurnal(BaseViews):
    ##########                    
    # Action #
    ##########    
    def get_row_item(self):
        return DBSession.query(KegiatanItem.id, KegiatanItem.rekening_id, 
                  Rekening.kode.label('rekening_kd'), Rekening.nama.label('rekening_nm'), 
                  KegiatanItem.nama, KegiatanItem.no_urut,
                  (KegiatanItem.vol_1_1*KegiatanItem.vol_1_2*KegiatanItem.hsat_1).label('amount_1'),
                  (KegiatanItem.vol_2_1*KegiatanItem.vol_2_2*KegiatanItem.hsat_2).label('amount_2'),
                  (KegiatanItem.vol_3_1*KegiatanItem.vol_3_2*KegiatanItem.hsat_3).label('amount_3'),
                  (KegiatanItem.vol_4_1*KegiatanItem.vol_4_2*KegiatanItem.hsat_4).label('amount_4')).join(Rekening)
                  
    @view_config(route_name='ag-kegiatan-item-act', renderer='json',
                 permission='read')
    def ak_jurnal_act(self):
        ses = self.request.session
        req = self.request
        params = req.params
        url_dict = req.matchdict
        if url_dict['act']=='grid':
            ag_step_id = ses['ag_step_id']
            kegiatan_sub_id = 'kegiatan_sub_id' in params and params['kegiatan_sub_id'] or 0
            columns = []
            columns.append(ColumnDT('id'))
            columns.append(ColumnDT('rekening_kd'))
            columns.append(ColumnDT('no_urut'))
            columns.append(ColumnDT('nama'))
            columns.append(ColumnDT('amount_%s' %ag_step_id, filter=self._number_format))
            columns.append(ColumnDT('rekening_nm'))
            columns.append(ColumnDT('rekening_id'))
            query = self.get_row_item().filter(
                      KegiatanItem.kegiatan_sub_id==kegiatan_sub_id)
            rowTable = DataTables(req, KegiatanItem,  query, columns)
            return rowTable.output_result()
            
        
    ###############                    
    # Tambah  Data#
    ###############    
    @view_config(route_name='ag-kegiatan-item-add-fast', renderer='json',
                 permission='add')
    def ak_kegiatan_item_add_fast(self):
        ses = self.request.session
        req = self.request
        params = req.params
        url_dict = req.matchdict
        kegiatan_sub_id = 'kegiatan_sub_id' in params and params['kegiatan_sub_id'] or None
        rekening_id     = 'rekening_id' in params and params['rekening_id'] or None
        kegiatan_item_id = 'kegiatan_item_id' in params and params['kegiatan_item_id'] or None
        if not kegiatan_item_id:
            row = KegiatanItem()
            row_dict = {}
        else:
            row = DBSession.query(KegiatanItem).filter(KegiatanItem.id==kegiatan_item_id).first()
            if not row:
                return {'success':False, 'msg':'Data Tidak Ditemukan'}
            row_dict = row.to_dict()
            
        row_dict['no_urut']         = 'no_urut' in params and params['no_urut'] or \
                                      KegiatanItem.max_no_urut(kegiatan_sub_id,rekening_id)+1
        row_dict['kegiatan_sub_id'] = kegiatan_sub_id
        row_dict['rekening_id']     = rekening_id
        row_dict['nama']            = 'nama' in params and params['nama'] or None
        row_dict['kode']            = 'kode' in params and params['kode'] or None
        
        ag_step_id = ses['ag_step_id']
        amount = 'amount' in params and params['amount'].replace('.', '') or 0
        
        if ag_step_id<2:
            row_dict['hsat_1'] = amount 
        if ag_step_id<3:
            row_dict['hsat_2'] = amount 
        if ag_step_id<4:
            row_dict['hsat_3'] = amount 
        if ag_step_id<5:
            row_dict['hsat_4'] = amount 
            
        row.from_dict(row_dict)
        DBSession.add(row)
        DBSession.flush()
        return {"success": True, 'id': row.id, "msg":'Success Tambah Data'}
        
        try:
          pass
        except:
            return {'success':False, 'msg':'Gagal Tambah Data'}
            