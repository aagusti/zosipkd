import os
import uuid
from osipkd.tools import row2dict, xls_reader
from datetime import datetime
from sqlalchemy import not_, func, cast, BigInteger, String
from pyramid.view import (view_config,)
from pyramid.httpexceptions import ( HTTPFound, )
import colander
from deform import (Form, widget, ValidationFailure, )
from osipkd.models import DBSession
from osipkd.models.apbd_anggaran import Kegiatan, KegiatanSub, KegiatanItem
from osipkd.models.pemda_model import Unit, Rekening
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
                columns.append(ColumnDT('kode_rek'))
                columns.append(ColumnDT('amount',filter=self._number_format))
                columns.append(ColumnDT('ppn',filter=self._number_format))
                columns.append(ColumnDT('pph',filter=self._number_format))
                columns.append(ColumnDT('vol_1'))
                columns.append(ColumnDT('vol_2'))
                columns.append(ColumnDT('harga'))
                columns.append(ColumnDT('nama_kegiatan'))
                columns.append(ColumnDT('kegiatan_item_id'))
                columns.append(ColumnDT('nilai'))
                
                query = DBSession.query(APInvoiceItem.id,
                                        APInvoiceItem.no_urut,
                                        APInvoiceItem.nama,
                                        (Rekening.kode+'-'+cast(KegiatanItem.no_urut,String)).label('kode_rek'),
                                        APInvoiceItem.amount,
                                        APInvoiceItem.ppn,
                                        APInvoiceItem.pph,
                                        APInvoiceItem.vol_1,
                                        APInvoiceItem.vol_2,
                                        APInvoiceItem.harga,
                                        KegiatanItem.nama.label('nama_kegiatan'),
                                        APInvoiceItem.kegiatan_item_id,
                                        cast(KegiatanItem.hsat_4*KegiatanItem.vol_4_1*KegiatanItem.vol_4_2,BigInteger).label('nilai'),
                                        KegiatanItem.no_urut.label('no_urut_kegitem')
                                        ).join(KegiatanItem).\
                                  outerjoin(Rekening).\
                                  filter(APInvoiceItem.ap_invoice_id==ap_invoice_id
                                  ).order_by(APInvoiceItem.no_urut)
                                  
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
    
    if not controls['no_urut1'] or controls['no_urut1'].split()=='':
        controls['no_urut1'] = APInvoiceItem.max_no_urut(ap_invoice_id)+1
        
    row.no_urut          = controls['no_urut1']
    row.nama             = controls['nama']
    row.vol_1            = controls['vol_1'].replace('.','')
    row.vol_2            = controls['vol_2'].replace('.','')
    row.harga            = controls['harga'].replace('.','')
    row.ppn              = controls['ppn'].replace('.','')
    row.pph              = controls['pph'].replace('.','')
    row.amount           = float(controls['vol_1'].replace('.',''))*float(controls['vol_2'].replace('.',''))*float(controls['harga'].replace('.',''))
    
    ### Kondisi sum sesuai kegiatan_item_id 
    kegiatan_item_id = int(row.kegiatan_item_id)
    hargaa  = row.harga
    hargab  = '%s' % hargaa
    hargac  = int(hargab)
    
    a = DBSession.query(func.sum(APInvoiceItem.amount).label('jumlah')
                ).filter(APInvoiceItem.kegiatan_item_id==kegiatan_item_id
                ).first()
    b = '%s' % a
    if b == 'None':
        b = 0
    
    c = int(b)
    amount = int(c + hargac)
    
    ### Kondisi Kegiatan Item
    d = DBSession.query((KegiatanItem.vol_4_1*KegiatanItem.vol_4_2)*KegiatanItem.hsat_4
                ).filter(KegiatanItem.id==kegiatan_item_id
                ).first()
    e = '%s' % d
    f = int(float(e))
    print'****--Anggaran Terpakai--**** ',c
    print'****--Jumlah Inputan-----**** ',hargac
    print'****--Terpakai+Inputan---**** ',amount
    print'****--Pagu Anggaran------**** ',f
    
    g = f - c
    print'****--Sisa Anggaran------**** ',g
    
    ### Kondisi Belanja Tidak Langsung (Gaji), kode rekening 5.1.1.01 dan 5.1.1.02.01 dan 7... bisa melebihi anggaran
    print'****--ID Item------------**** ',kegiatan_item_id
    z = DBSession.query(func.substr(Rekening.kode,1,8).label('a')
                ).filter(KegiatanItem.id==kegiatan_item_id,
                         KegiatanItem.rekening_id==Rekening.id, 
                ).first() 
    #Cek Rek Non Anggaran 7.....                
    z1 = DBSession.query(func.substr(Rekening.kode,1,1).label('b')
                ).filter(KegiatanItem.id==kegiatan_item_id,
                         KegiatanItem.rekening_id==Rekening.id, 
                ).first()    
    y = '%s' % z
    y1 = '%s' % z1
    print'****--Kode Rekening------**** ',y
    
    if y1 != '7' :
      if y != '5.1.1.01' :
        if amount > f:
            return {"success": False, 'id': row.id, "msg":'Tidak boleh melebihi jumlah pagu anggaran, Sisa anggaran %s' % g}

    DBSession.add(row)
    DBSession.flush()
    api = row.ap_invoice_id
    print'****--Invoice ID---------**** ',api
    g = DBSession.query(func.sum(APInvoiceItem.amount)
                ).filter(APInvoiceItem.ap_invoice_id==api 
                ).first() or 0
    g1 = "%s" % g
    if g1 == 'None':
        g1 = 0
        jml = g1
    else:
        jml = g1
    
    # untuk kondisi simpan langsung nilai ke APInvoice
    if jml:
        rows = DBSession.query(APInvoice).filter(APInvoice.id==ap_invoice_id).first()
        rows.amount=jml
        DBSession.add(rows)
        DBSession.flush()
        
    print'****--Jumlah Total-------**** ',jml
    return {"success": True, 'id': row.id, "msg":'Success Tambah Item Invoice', 'jml_total':jml}


########
# Edit #
########
def route_list2(request):
    return HTTPFound(location=request.route_url('ap-invoice-skpd-edit',id=request.matchdict['ap_invoice_id']))
  
def route_list(request):
    return HTTPFound(location=request.route_url('ap-invoice-skpd'))
    
def query_id(request):
    return DBSession.query(APInvoiceItem).filter(APInvoiceItem.id==request.matchdict['id'],
                                                 APInvoiceItem.ap_invoice_id==request.matchdict['ap_invoice_id'])
    
def id_not_found(request):    
    msg = 'User ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='ap-invoice-skpd-item-edit', renderer='json',
             permission='edit')
def view_edit(request):
    req = request
    ses = req.session
    params = req.params
    url_dict = req.matchdict
    ap_invoice_id = 'ap_invoice_id' in url_dict and url_dict['ap_invoice_id'] or 0
    controls = dict(request.POST.items())
    ap_invoice_item_id = 'ap_invoice_item_id' in controls and controls['ap_invoice_item_id'] or 0
    ##Hasil Param 
    print'++++++++++++++ap_invoice id++++++++++++++++++++++++++',ap_invoice_id
    ##Hasil Dict 
    print'++++++++++++++ap_invoice_item id+++++++++++++++++++++',ap_invoice_item_id

    #Cek lagi ditakutkan skpd ada yang iseng inject script
    if ap_invoice_item_id:
        row = DBSession.query(APInvoiceItem)\
                  .join(APInvoice)\
                  .filter(APInvoiceItem.id==ap_invoice_item_id,
                          APInvoice.unit_id==ses['unit_id'],
                          APInvoiceItem.ap_invoice_id==ap_invoice_id).first()
        print'rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrroowwwww',row
        if not row:
            return {"success": False, 'msg':'Invoice tidak ditemukan'}
    else:
        row = APInvoiceItem()

    kegiatan_item_id = controls['kegiatan_item_id']
    print'++++++++++++++kegiatan_item_id+++++++++++++++++++++++',kegiatan_item_id
    ### Sum dari APInvoiceItem sesuai APInvoiceItem.id 
    a = DBSession.query(func.sum(APInvoiceItem.amount).label('jumlah')
                ).filter(APInvoiceItem.kegiatan_item_id==kegiatan_item_id
                ).first()
    b = '%s' % a
    jnai = int(b)
    print'++++++++++++++Sum APInvoiceItem++++++++++++++++++++++',jnai

    ### amount dari APInvoiceItem sesuai APInvoiceItem.id 
    am = DBSession.query(APInvoiceItem.amount.label('jumlah')
                ).filter(APInvoiceItem.kegiatan_item_id==kegiatan_item_id, APInvoiceItem.ap_invoice_id==ap_invoice_id
                ).first()
    bm = '%s' % am
    jnaim = int(bm)
    print'++++++++++++++amount APInvoiceItem++++++++++++++++++++++',jnaim
    
    ## Param Dict
    vol_1            = controls['vol_1'].replace('.','')
    vol_2            = controls['vol_2'].replace('.','')
    harga            = controls['harga'].replace('.','')
    ppn              = controls['ppn'].replace('.','')
    pph              = controls['pph'].replace('.','')
    amount           = float(controls['vol_1'].replace('.',''))*float(controls['vol_2'].replace('.',''))*float(controls['harga'].replace('.',''))
    inputharga = int(amount)
    print'++++++++++++++Hasil Inputan++++++++++++++++++++++++++',inputharga


    ## Sum dari Kegiatan Item
    x = DBSession.query((KegiatanItem.vol_4_1*KegiatanItem.vol_4_2)*KegiatanItem.hsat_4
                ).filter(KegiatanItem.id==kegiatan_item_id
                ).first()
    z = '%s' % x 
    jnki = int(float(z))
    print'++++++++++++++Sum KegiatanItem+++++++++++++++++++++++',jnki
    
    ## Cek Kode Rekening
    h = DBSession.query(func.substr(Rekening.kode,1,8).label('a')
                ).filter(KegiatanItem.id==kegiatan_item_id,
                         KegiatanItem.rekening_id==Rekening.id, 
                ).first()    
    # Cek Rek Non Anggaran 7....           
    h1 = DBSession.query(func.substr(Rekening.kode,1,1).label('b')
                ).filter(KegiatanItem.id==kegiatan_item_id,
                         KegiatanItem.rekening_id==Rekening.id, 
                ).first()    
                
    kr  = '%s' % h
    kr1 = '%s' % h1
    print'++++++++++++++Kode Rekening+++++++++++++++++++++++++++',kr
    
    sisa = jnki - jnai
    inputaan = inputharga + jnai
    seleksi = (jnai - jnaim) + inputharga
    print'++++++++++++++Seleksi++++++++++++++++++++++++++++++++',seleksi
    print'++++++++++++++Hasil Inputan++++++++++++++++++++++++++',inputharga
    print'++++++++++++++Sum APInvoiceItem++++++++++++++++++++++',jnai
    print'++++++++++++++Inputan++++++++++++++++++++++++++++++++',inputaan
    print'++++++++++++++Sum KegiatanItem+++++++++++++++++++++++',jnki
    
    ## Kondisi Kode Rekening dan Pagu Anggaran
    if kr1 != '7' :
      if kr != '5.1.1.01' :
        if seleksi > jnki:
            return {"success": False, "msg":'Tidak boleh melebihi jumlah pagu anggaran, Sisa anggaran %s' % sisa}
        #else:
            #if inputaan > jnki:
            #    return {"success": False, "msg":'Tidak boleh melebihi jumlah pagu anggaran, Sisa anggaran %s' % sisa}
        
    row.no_urut          = controls['no_urut1']
    row.nama             = controls['nama']
    row.vol_1            = controls['vol_1'].replace('.','')
    row.vol_2            = controls['vol_2'].replace('.','')
    row.harga            = controls['harga'].replace('.','')
    row.ppn              = controls['ppn'].replace('.','')
    row.pph              = controls['pph'].replace('.','')
    row.amount           = float(controls['vol_1'].replace('.',''))*float(controls['vol_2'].replace('.',''))*float(controls['harga'].replace('.',''))
    DBSession.add(row)
    DBSession.flush()

    api = row.ap_invoice_id
    print'****--Invoice ID---------**** ',api
    g = DBSession.query(func.sum(APInvoiceItem.amount)
                ).filter(APInvoiceItem.ap_invoice_id==api 
                ).first() or 0
    g1 = "%s" % g
    if g1 == 'None':
        g1 = 0
        jml = g1
    else:
        jml = g1
    
    # untuk kondisi update langsung nilai ke APInvoice
    if jml:
        rows = DBSession.query(APInvoice).filter(APInvoice.id==ap_invoice_id).first()
        rows.amount=jml
        DBSession.add(rows)
        DBSession.flush()
        
    print'****--Jumlah Total-------**** ',jml
    return {"success": True, 'id': row.id, "msg":'Success Update Item Invoice', 'jml_total':jml}
    
##########
# Delete #
##########    
@view_config(route_name='ap-invoice-skpd-item-delete', renderer='json',
             permission='delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    
    if not row:
        return {'success':False, "msg":self.id_not_found()}

    msg = 'Data sudah dihapus'
    query_id(request).delete()
    DBSession.flush()
    
    amount = "%s" % APInvoice.get_nilai(row.ap_invoice_id) 
    
    # untuk kondisi update langsung nilai ke APInvoice
    if amount =='None':
        amount=0

    rows = DBSession.query(APInvoice).filter(APInvoice.id==row.ap_invoice_id).first()
    rows.amount=amount
    DBSession.add(rows)
    DBSession.flush()    
    
    return {'success':True, "msg":msg, 'jml_total':amount}
    