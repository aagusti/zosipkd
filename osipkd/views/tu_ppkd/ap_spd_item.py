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
from osipkd.models.pemda_model import Unit
from osipkd.models.apbd_tu import Spd, SpdItem
    
from datatables import ColumnDT, DataTables
from osipkd.views.base_view import BaseViews

SESS_ADD_FAILED = 'Tambah ap-spd-item gagal'
SESS_EDIT_FAILED = 'Edit ap-spd-item gagal'

class view_ap_spd_item(BaseViews):
    ##########                    
    # Action #
    ##########    
    @view_config(route_name='ap-spd-item-act', renderer='json',
                 permission='read')
    def view_act(self):
        ses = self.request.session
        req = self.request
        params = req.params
        url_dict = req.matchdict
        if url_dict['act']=='grid':
            if url_dict['act']=='grid':
                # defining columns
                ap_spd_id = url_dict['ap_spd_id'].isdigit() and url_dict['ap_spd_id'] or 0
                columns = []
                columns.append(ColumnDT('id'))
                columns.append(ColumnDT('kegiatansubs.kode'))
                columns.append(ColumnDT('kegiatansubs.nama'))
                columns.append(ColumnDT('anggaran'))
                columns.append(ColumnDT('lalu'))
                columns.append(ColumnDT('nominal'))
                columns.append(ColumnDT('nominal'))
                columns.append(ColumnDT('nominal'))
                
                query = DBSession.query(SpdItem
                        ).filter(SpdItem.id==ap_spd_id,
                        )
                rowTable = DataTables(req, SpdItem, query, columns)
                return rowTable.output_result()
    #######    
    # Add #
    #######
    @view_config(route_name='ap-spd-item-add', renderer='json',
                 permission='add')
    def view_add(self):
        req = self.request
        ses = req.session
        params = req.params
        url_dict = req.matchdict
        ap_spd_id = 'ap_spd_id' in url_dict and url_dict['ap_spd_id'] or 0
        controls = dict(req.POST.items())
        
        kegiatan_sub_id = 'kegiatan_sub_id' in controls and controls['kegiatan_sub_id'] or None
        if not kegiatan_sub_id:
            return {"success": False, 'msg':'Kegiatan belum dipilih'}
            
        #Cek dulu ada penyusup gak dengan mengecek sessionnya
        ap_spd = DBSession.query(Spd)\
                      .filter(Spd.unit_id==ses['unit_id'],
                              Spd.id==ap_spd_id).first()
        if not ap_spd:
            return {"success": False, 'msg':'SPD tidak ditemukan'}
        
        #Cek lagi ditakutkan skpd ada yang iseng inject script
        row = SpdItem()
        row.kegiatan_sub_id = kegiatan_sub_id
        row.ap_spd_id       = ap_spp_id
        try:
          DBSession.add(row)
          DBSession.flush()
          #row = DBSession.query(KegiatanSub).filter_by(id=ap_kegiatan_id).first()
          row.posted=1
          DBSession.add(row)
          DBSession.flush()
          return {"success": True, "msg":'Success Tambah Item SPD'}
        except:
            return {'success':False, 'msg':'Gagal Tambah Item SPD'}


    ########
    # Edit #
    ########
    def query_id(self):
        return DBSession.query(SpdItem).join(Spd)\
                        .filter(SpdItem.id==self.request.matchdict['id'],
                                SpdItem.kegiatan_sub_id==self.request.matchdict['kegiatan_sub_id'],
                                )
    def id_not_found(self):    
        msg = 'Item ID %s not found.' % request.matchdict['id']
        return msg

    ##########
    # Delete #
    ##########    
    @view_config(route_name='ap-spd-item-delete', renderer='json',
                 permission='delete')
    def view_delete(self):
        q = self.query_id().filter(Spd.unit_id==self.session['unit_id'])
        row = q.first()
        if not row:
            return {'success':False, "msg":self.id_not_found()}
        kegiatan_sub_id = row.kegiatan_sub_id
        msg = 'Data sudah dihapus'
        self.query_id().delete()
        DBSession.flush()
        #row = DBSession.query(APInvoice).filter_by(id=ap_invoice_id).first()
        row.posted=0
        DBSession.add(row)
        DBSession.flush()        
        return {'success':True, "msg":msg}
