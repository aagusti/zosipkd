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
from osipkd.models.apbd_tu import APInvoice, APInvoiceItem 
    
from datatables import ColumnDT, DataTables
from osipkd.views.base_view import BaseViews

SESS_ADD_FAILED = 'Tambah ap-invoice-skpd-item gagal'
SESS_EDIT_FAILED = 'Edit ap-invoice-skpd-item gagal'

class view_ap_invoice_skpd_item(BaseViews):
    ##########                    
    # Action #
    ##########    
    @view_config(route_name='ap-invoice-skpd-item-act', renderer='json',
                 permission='read')
    def view_act(self):
        ses = self.request.session
        req = self.request
        params = req.params
        url_dict = req.matchdict
        if url_dict['act']=='grid':
            pk_id = 'id' in params and params['id'] and int(params['id']) or 0
            if url_dict['act']=='grid':
                # defining columns
                ap_invoice_id = url_dict['ap_invoice_id'].isdigit() and url_dict['ap_invoice_id'] or 0
                columns = []
                columns.append(ColumnDT('id'))
                columns.append(ColumnDT('no_urut'))
                columns.append(ColumnDT('nama'))
                columns.append(ColumnDT('kegiatanitems.rekenings.kode'))
                columns.append(ColumnDT('amount',filter=self._number_format))
                columns.append(ColumnDT('ppn',filter=self._number_format))
                columns.append(ColumnDT('pph',filter=self._number_format))
                columns.append(ColumnDT('vol_1'))
                columns.append(ColumnDT('vol_2'))
                columns.append(ColumnDT('harga'))
                columns.append(ColumnDT('kegiatanitems.nama'))
                query = DBSession.query(APInvoiceItem).\
                          filter(APInvoiceItem.ap_invoice_id==ap_invoice_id)
                rowTable = DataTables(req, APInvoiceItem, query, columns)
                return rowTable.output_result()
#######    
# Add #
#######
@view_config(route_name='ap-invoice-skpd-item-add', renderer='json',
             permission='add')
def view_add(request):
    req = request
    ses = req.session
    params = req.params
    url_dict = req.matchdict
    ap_invoice_id = 'ap_invoice_id' in url_dict and url_dict['ap_invoice_id'] or 0
    controls = dict(request.POST.items())
    
    ap_invoice_item_id = 'ap_invoice_item_id' in controls and controls['ap_invoice_item_id'] or 0
    #Cek dulu ada penyusup gak dengan mengecek sessionnya
    ap_invoice = DBSession.query(APInvoice)\
                  .filter(APInvoice.unit_id==ses['unit_id'],
                          APInvoice.id==ap_invoice_id).first()
    if not ap_invoice:
        return {"success": False, 'msg':'Invoice tidak ditemukan'}
    
    #Cek lagi ditakutkan skpd ada yang iseng inject script
    if ap_invoice_item_id:
        row = DBSession.query(APInvoiceItem)\
                  .join(APInvoice)\
                  .filter(APInvoiceItem.id==ap_invoice_item_id,
                          APInvoice.unit_id==ses['unit_id'],
                          APInvoiceItem.ap_invoice_id==ap_invoice_id).first()
        if not row:
            return {"success": False, 'msg':'Invoice tidak ditemukan'}
    else:
        row = APInvoiceItem()
            
    row.ap_invoice_id    = ap_invoice_id
    row.kegiatan_item_id = controls['kegiatan_item_id']
    if not controls['no_urut'] or controls['no_urut'].split()=='':
        controls['no_urut'] = APInvoiceItem.max_no_urut(ap_invoice_id)+1
    row.no_urut          = controls['no_urut']
    row.nama             = controls['nama']
    row.vol_1            = controls['vol_1'].replace('.','')
    row.vol_2            = controls['vol_2'].replace('.','')
    row.harga            = controls['harga'].replace('.','')
    row.ppn              = controls['ppn'].replace('.','')
    row.pph              = controls['pph'].replace('.','')
    row.amount           = float(controls['vol_1'].replace('.',''))*float(controls['vol_2'].replace('.',''))*float(controls['harga'].replace('.',''))
    
    try:
        DBSession.add(row)
        DBSession.flush()
        return {"success": True, 'id': row.id, "msg":'Success Tambah Item Invoice'}
    except:
        return {'success':False, 'msg':'Gagal Tambah Item Invoice'}


########
# Edit #
########
def query_id(request):
    return DBSession.query(APInvoice).filter(APInvoice.id==request.matchdict['id'])
    
def id_not_found(request):    
    msg = 'User ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

##########
# Delete #
##########    
@view_config(route_name='ap-invoice-skpd-item-delete', renderer='templates/ap-invoice-skpd-item/delete.pt',
             permission='delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    if not row:
        return id_not_found(request)
    form = Form(colander.Schema(), buttons=('hapus','cancel'))
    values= {}
    if request.POST:
        if 'hapus' in request.POST:
            msg = '%s Kode %s  No. %s %s sudah dihapus.' % (request.title, row.kode, row.no_urut, row.nama)
            DBSession.query(APInvoice).filter(APInvoice.id==request.matchdict['id']).delete()
            DBSession.flush()
            request.session.flash(msg)
        return route_list(request)
    return dict(row=row,
                 form=form.render())