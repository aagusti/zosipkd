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
from osipkd.models.apbd_tu import AkJurnal, AkJurnalItem
    
from datatables import ColumnDT, DataTables
from osipkd.views.base_view import BaseViews

SESS_ADD_FAILED = 'Tambah ak-jurnal-skpd-item gagal'
SESS_EDIT_FAILED = 'Edit ak-jurnal-skpd-item gagal'
            
class view_ak_jurnal_skpd_item(BaseViews):
    ########                    
    # List #
    ########    
    @view_config(route_name='ak-jurnal-skpd-item', renderer='templates/ak-jurnal-skpd-item/list.pt',
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
    @view_config(route_name='ak-jurnal-skpd-item-act', renderer='json',
                 permission='read')
    def ak_jurnal_skpd_item_act(self):
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
            columns.append(ColumnDT('ak_jurnal_id'))
            columns.append(ColumnDT('notes'))
            columns.append(ColumnDT('kegiatan_subs.id'))
            columns.append(ColumnDT('rekening_id'))
            
            query = DBSession.query(AkJurnalItem)
            rowTable = DataTables(req, AkJurnalItem, query, columns)
            return rowTable.output_result()
        
    ################                    
    # Tambah  Cepat#
    ################    
    @view_config(route_name='ak-jurnal-skpd-item-add', renderer='json',
                 permission='add')
    def ak_jurnal_skpd_item_add(self):
        ses = self.request.session
        req = self.request
        params = req.params
        url_dict = req.matchdict
        kegiatan_sub_id = 'kegiatan_sub_id' in params and params['kegiatan_sub_id'] or None
        rekening_id     = 'rekening_id' in params and params['rekening_id'] or None
        jurnal_item_id  = 'jurnal_item_id' in params and params['jurnal_item_id'] or None
        ak_jurnal_id    = 'ak_jurnal_id' in params and params['ak_jurnal_id'] or None
        
        if not jurnal_item_id:
            row = AkJurnalItem()
            row_dict = {}
            row_dict['created'] = datetime.now()
            row_dict['create_uid'] = req.user.id
            row_dict['ak_jurnal_id']     = 'ak_jurnal_id' in params and params['ak_jurnal_id'].replace('.', '') or 0
        else:
            row = DBSession.query(AkJurnalItem).filter(AkJurnalItem.id==jurnal_item_id).first()
            if not row:
                return {'success':False, 'msg':'Data Tidak Ditemukan'}
            row.updated = datetime.now()
            row.update_uid = req.user.id
            row_dict = row.to_dict()
            
        row_dict['kegiatan_sub_id'] = kegiatan_sub_id
        row_dict['rekening_id']     = rekening_id
        row_dict['amount']          = 'amount' in params and params['amount'].replace('.', '') or 0
        row_dict['notes']           = 'notes' in params and params['notes'] or None
        row.from_dict(row_dict)
        DBSession.add(row)
        DBSession.flush()
        return {"success": True, 'id': row.id, "msg":'Success Tambah Data'}
        
        try:
          pass
        except:
            return {'success':False, 'msg':'Gagal Tambah Data'}       
            
    def query_id(self):
        return DBSession.query(AkJurnalItem).filter_by(id=self.request.matchdict['id'])
        
    def id_not_found(self):    
        msg = 'Jurnal Item ID %s Tidak Ditemukan.' % self.request.matchdict['id']
        return {'success': False, 'msg':msg}

        
    ##########
    # Delete #
    ##########    
    @view_config(route_name='ak-jurnal-skpd-item-delete', renderer='json',
                 permission='delete')
    def view_delete(self):
        request = self.request
        ses = self.session
        q = self.query_id().join(AkJurnal).filter(AkJurnal.unit_id==ses['unit_id'])
        row = q.first()
        if not row:
            return self.id_not_found()
        q = self.query_id()
        q.delete()
        DBSession.flush()
        return {'success': True, 'msg':'Sukses Hapus Data'}
