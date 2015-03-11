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
from osipkd.models.pemda_model import Rekening
from osipkd.models.apbd_anggaran import KegiatanSub, Kegiatan, KegiatanItem
    
from datatables import ColumnDT, DataTables
from osipkd.views.base_view import BaseViews

SESS_ADD_FAILED = 'Tambah ak-jurnal-item gagal'
SESS_EDIT_FAILED = 'Edit ak-jurnal-item gagal'
            
class view_ak_jurnal_item(BaseViews):
    ########                    
    # List #
    ########    
    @view_config(route_name='ak-jurnal-item', renderer='templates/ak-jurnal-item/list.pt',
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
    @view_config(route_name='ak-jurnal-item-act', renderer='json',
                 permission='read')
    def ak_jurnal_item_act(self):
        ses = self.request.session
        req = self.request
        params = req.params
        url_dict = req.matchdict
        
        if url_dict['act']=='grid':
            jurnal_id = url_dict['jurnal_id'].isdigit() and url_dict['jurnal_id'] or 0
            print'XXXXXXXXXXXXXXXXXXXXXXX',jurnal_id
            columns = []
            columns.append(ColumnDT('id'))
            columns.append(ColumnDT('subkd'))
            columns.append(ColumnDT('subnm'))
            columns.append(ColumnDT('rekkd'))
            columns.append(ColumnDT('reknm'))
            columns.append(ColumnDT('amount',  filter=self._number_format))
            columns.append(ColumnDT('notes'))
            columns.append(ColumnDT('kegiatan_sub_id'))
            columns.append(ColumnDT('rekening_id'))
            columns.append(ColumnDT('jurnal_id'))
            
            query = DBSession.query(JurnalItem.id,
                                    KegiatanSub.kode.label('subkd'),
                                    KegiatanSub.nama.label('subnm'),
                                    Rekening.kode.label('rekkd'),
                                    Rekening.nama.label('reknm'),
                                    JurnalItem.amount,
                                    JurnalItem.notes,
                                    JurnalItem.kegiatan_sub_id,
                                    JurnalItem.rekening_id,
                                    JurnalItem.jurnal_id,
                                ).join(Jurnal, KegiatanSub, Kegiatan, Rekening, KegiatanItem
                                ).filter(JurnalItem.jurnal_id==jurnal_id,
                                         JurnalItem.kegiatan_sub_id==KegiatanSub.id,
                                         JurnalItem.rekening_id==Rekening.id,
                                         JurnalItem.jurnal_id==Jurnal.id
                                ).group_by(JurnalItem.id,
                                           KegiatanSub.kode.label('subkd'),
                                           KegiatanSub.nama.label('subnm'),
                                           Rekening.kode.label('rekkd'),
                                           Rekening.nama.label('reknm'),
                                           JurnalItem.amount,
                                           JurnalItem.notes,
                                           JurnalItem.kegiatan_sub_id,
                                           JurnalItem.rekening_id,
                                           JurnalItem.jurnal_id,
                                )
            rowTable = DataTables(req, JurnalItem, query, columns)
            return rowTable.output_result()
        
    ################                    
    # Tambah  Cepat#
    ################    
    @view_config(route_name='ak-jurnal-item-add', renderer='json',
                 permission='add')
    def ak_jurnal_item_add(self):
        ses = self.request.session
        req = self.request
        params   = req.params
        url_dict = req.matchdict
        jurnal_id = 'jurnal_id' in url_dict and url_dict['jurnal_id'] or 0
        controls = dict(req.POST.items())
        
        jurnal_item_id = 'jurnal_item_id' in controls and controls['jurnal_item_id'] or 0        
        
        if jurnal_item_id:
            row = DBSession.query(JurnalItem)\
                      .join(Jurnal)\
                      .filter(JurnalItem.id==jurnal_item_id,
                              Jurnal.unit_id==ses['unit_id'],
                              JurnalItem.jurnal_id==jurnal_id).first()
            if not row:
                return {"success": False, 'msg':'Jurnal tidak ditemukan'}
        else:
            row = JurnalItem()
            
        row.jurnal_id       = jurnal_id
        row.kegiatan_sub_id = controls['kegiatan_sub_id']
        row.rekening_id     = controls['rekening_id']
        row.amount          = controls['amount'].replace('.','')
        row.notes           = controls['notes'].replace('.','')
        
        DBSession.add(row)
        DBSession.flush()
        return {"success": True, 'id': row.id, "msg":'Success Tambah Data'}
        
        try:
          pass
        except:
            return {'success':False, 'msg':'Gagal Tambah Data'}      
            
    def query_id(self):
        return DBSession.query(JurnalItem).filter_by(id=self.request.matchdict['id'])
        
    def id_not_found(self):    
        msg = 'Jurnal Item ID %s Tidak Ditemukan.' % self.request.matchdict['id']
        return {'success': False, 'msg':msg}

        
    ##########
    # Delete #
    ##########    
    @view_config(route_name='ak-jurnal-item-delete', renderer='json',
                 permission='delete')
    def view_delete(self):
        request = self.request
        ses     = self.session
        
        q = self.query_id().join(Jurnal).filter(Jurnal.unit_id==ses['unit_id'])
        row = q.first()
        if not row:
            return self.id_not_found()
        q = self.query_id()
        q.delete()
        DBSession.flush()
        return {'success': True, 'msg':'Sukses Hapus Data'}
