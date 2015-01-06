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
from osipkd.models.apbd_tu import Spp, SppItem, APInvoice, APInvoiceItem 
    
from datatables import ColumnDT, DataTables
from osipkd.views.base_view import BaseViews

SESS_ADD_FAILED = 'Tambah ap-spp-item gagal'
SESS_EDIT_FAILED = 'Edit ap-spp-item gagal'

class view_ap_spp_item(BaseViews):
    ##########                    
    # Action #
    ##########    
    @view_config(route_name='ap-spp-item-act', renderer='json',
                 permission='read')
    def view_act(self):
        ses = self.request.session
        req = self.request
        params = req.params
        url_dict = req.matchdict
        if url_dict['act']=='grid':
            if url_dict['act']=='grid':
                # defining columns
                ap_spp_id = url_dict['ap_spp_id'].isdigit() and url_dict['ap_spp_id'] or 0
                columns = []
                columns.append(ColumnDT('id'))
                columns.append(ColumnDT('no_urut'))
                columns.append(ColumnDT('nama'))
                columns.append(ColumnDT('amount',filter=self._number_format))
                columns.append(ColumnDT('ppn',filter=self._number_format))
                columns.append(ColumnDT('pph',filter=self._number_format))
                columns.append(ColumnDT('ap_invoice_id'))
                query = DBSession.query(SppItem.id, SppItem.ap_invoice_id,
                                        APInvoice.no_urut, APInvoice.nama,  
                                        func.sum(APInvoiceItem.amount).label('amount'),
                                        func.sum(APInvoiceItem.ppn).label('ppn'),
                                        func.sum(APInvoiceItem.pph).label('pph'))\
                          .join(APInvoice).join(APInvoiceItem)\
                          .filter(SppItem.ap_spp_id==ap_spp_id)\
                          .group_by(SppItem.id, SppItem.ap_invoice_id,
                                    APInvoice.no_urut, APInvoice.nama,)
                rowTable = DataTables(req, SppItem, query, columns)
                return rowTable.output_result()
    #######    
    # Add #
    #######
    @view_config(route_name='ap-spp-item-add', renderer='json',
                 permission='add')
    def view_add(self):
        req = self.request
        ses = req.session
        params = req.params
        url_dict = req.matchdict
        ap_spp_id = 'ap_spp_id' in url_dict and url_dict['ap_spp_id'] or 0
        controls = dict(req.POST.items())
        
        ap_invoice_id = 'ap_invoice_id' in controls and controls['ap_invoice_id'] or None
        if not ap_invoice_id:
            return {"success": False, 'msg':'Tagihan belum dipilih'}
            
        #Cek dulu ada penyusup gak dengan mengecek sessionnya
        ap_spp = DBSession.query(Spp)\
                      .filter(Spp.unit_id==ses['unit_id'],
                              Spp.id==ap_spp_id).first()
        if not ap_spp:
            return {"success": False, 'msg':'SPP tidak ditemukan'}
        
        #Cek lagi ditakutkan skpd ada yang iseng inject script
        row = SppItem()
        row.ap_invoice_id    = ap_invoice_id
        row.ap_spp_id    = ap_spp_id
        try:
          DBSession.add(row)
          DBSession.flush()
          row = DBSession.query(APInvoice).filter_by(id=ap_invoice_id).first()
          row.posted=1
          DBSession.add(row)
          DBSession.flush()
          return {"success": True, "msg":'Success Tambah Item SPP'}
        except:
            return {'success':False, 'msg':'Gagal Tambah Item SPP'}


    ########
    # Edit #
    ########
    def query_id(self):
        return DBSession.query(SppItem).join(Spp)\
                        .filter(SppItem.id==self.request.matchdict['id'],
                                SppItem.ap_spp_id==self.request.matchdict['ap_spp_id'],
                                )
    def id_not_found(self):    
        msg = 'Item ID %s not found.' % request.matchdict['id']
        return msg

    ##########
    # Delete #
    ##########    
    @view_config(route_name='ap-spp-item-delete', renderer='json',
                 permission='delete')
    def view_delete(self):
        q = self.query_id().filter(Spp.unit_id==self.session['unit_id'])
        row = q.first()
        if not row:
            return {'success':False, "msg":self.id_not_found()}
        ap_invoice_id = row.ap_invoice_id
        msg = 'Data sudah dihapus'
        self.query_id().delete()
        DBSession.flush()
        row = DBSession.query(APInvoice).filter_by(id=ap_invoice_id).first()
        row.posted=0
        DBSession.add(row)
        DBSession.flush()        
        return {'success':True, "msg":msg}
