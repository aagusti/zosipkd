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
from osipkd.models.pemda_model import Rekening
from osipkd.models.apbd_anggaran import KegiatanSub, Kegiatan, KegiatanItem
    
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
        pk_id = 'id' in params and params['id'] and int(params['id']) or 0
        
        if url_dict['act']=='grid':
            ak_jurnal_id = url_dict['ak_jurnal_id'].isdigit() and url_dict['ak_jurnal_id'] or 0
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
            columns.append(ColumnDT('ak_jurnal_id'))
            
            query = DBSession.query(AkJurnalItem.id,
                                    KegiatanSub.kode.label('subkd'),
                                    KegiatanSub.nama.label('subnm'),
                                    Rekening.kode.label('rekkd'),
                                    Rekening.nama.label('reknm'),
                                    AkJurnalItem.amount,
                                    AkJurnalItem.notes,
                                    AkJurnalItem.kegiatan_sub_id,
                                    AkJurnalItem.rekening_id,
                                    AkJurnalItem.ak_jurnal_id,
                                ).join(AkJurnal, KegiatanSub, Kegiatan, Rekening, KegiatanItem
                                ).filter(AkJurnalItem.ak_jurnal_id==ak_jurnal_id,
                                         AkJurnalItem.kegiatan_sub_id==KegiatanSub.id,
                                         AkJurnalItem.rekening_id==Rekening.id,
                                         AkJurnalItem.ak_jurnal_id==AkJurnal.id
                                ).group_by(AkJurnalItem.id,
                                           KegiatanSub.kode.label('subkd'),
                                           KegiatanSub.nama.label('subnm'),
                                           Rekening.kode.label('rekkd'),
                                           Rekening.nama.label('reknm'),
                                           AkJurnalItem.amount,
                                           AkJurnalItem.notes,
                                           AkJurnalItem.kegiatan_sub_id,
                                           AkJurnalItem.rekening_id,
                                           AkJurnalItem.ak_jurnal_id,
                                )
            rowTable = DataTables(req, AkJurnalItem, query, columns)
            return rowTable.output_result()
        
    ################                    
    # Tambah  Cepat#
    ################    
    @view_config(route_name='ak-jurnal-skpd-item-add', renderer='json',
                 permission='add')
    def view_add(self):
        ses = self.request.session
        req = self.request
        params   = req.params
        url_dict = req.matchdict
        ak_jurnal_id = 'ak_jurnal_id' in url_dict and url_dict['ak_jurnal_id'] or 0
        controls = dict(req.POST.items())
        
        jurnal_item_id = 'jurnal_item_id' in controls and controls['jurnal_item_id'] or 0        
        
        if jurnal_item_id:
            row = DBSession.query(AkJurnalItem)\
                      .join(AkJurnal)\
                      .filter(AkJurnalItem.id==jurnal_item_id,
                              AkJurnal.unit_id==ses['unit_id'],
                              AkJurnalItem.ak_jurnal_id==ak_jurnal_id).first()
            if not row:
                return {"success": False, 'msg':'Jurnal tidak ditemukan'}
        else:
            row = AkJurnalItem()
            
        row.ak_jurnal_id    = ak_jurnal_id
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
