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
from osipkd.models.pemda_model import Unit, Rekening, RekeningSap, Sap
from osipkd.models.apbd_tu import APInvoice, APInvoiceItem, APPayment, APPaymentItem,SppItem, Spp, AkJurnal, AkJurnalItem
    
from datatables import ColumnDT, DataTables
from osipkd.views.base_view import BaseViews

SESS_ADD_FAILED = 'Tambah ap-payment gagal'
SESS_EDIT_FAILED = 'Edit ap-payment gagal'

def deferred_ap_type(node, kw):
    values = kw.get('ap_type', [])
    return widget.SelectWidget(values=values)
    
AP_TYPE = (
    ('1', 'UP'),
    ('2', 'TU'),
    ('3', 'GU'),
    ('4', 'LS'),
    ('5', 'SP2B'),
    )

def deferred_kontrak_type(node, kw):
    values = kw.get('kontrak_type', [])
    return widget.SelectWidget(values=values)
    
KONTRAK_TYPE = (
    ('1', 'PT / NV'),
    ('2', 'CV'),
    ('3', 'FIRMA'),
    ('4', 'Lain-lain'),
    )
    
def deferred_bayar(node, kw):
    values = kw.get('is_bayar', [])
    return widget.SelectWidget(values=values)
    
IS_BAYAR = (
    ('0', 'Lunas'),
    ('1', 'Cicilan'),
    )

def deferred_uang(node, kw):
    values = kw.get('is_uang', [])
    return widget.SelectWidget(values=values)
    
IS_UANG = (
    ('0', 'Uang Muka'),
    ('1', 'Panjar'),
    )
    
class view_ap_payment(BaseViews):

    @view_config(route_name="ap-payment", renderer="templates/ap-payment/list.pt",
                 permission='read')
    def view_list(self):
        ses = self.request.session
        req = self.request
        params = req.params
        url_dict = req.matchdict
        return dict(project='EIS', 
        )
        
    ##########                    
    # Action #
    ##########    
    @view_config(route_name='ap-payment-act', renderer='json',
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
                columns = []
                columns.append(ColumnDT('id'))
                columns.append(ColumnDT('kode'))
                columns.append(ColumnDT('jenis'))
                columns.append(ColumnDT('tanggal', filter=self._DTstrftime))
                columns.append(ColumnDT('kegiatan_sub_nm'))
                columns.append(ColumnDT('nama'))
                columns.append(ColumnDT('amount'))

                query = DBSession.query(APPayment.id,
                          APPayment.kode,
                          APPayment.jenis,                          
                          APPayment.tanggal,
                          KegiatanSub.nama.label('kegiatan_sub_nm'),
                          APPayment.nama,
                          APPayment.amount,
                        ).outerjoin(APPaymentItem
                        ).filter(APPayment.tahun_id==ses['tahun'],
                              APPayment.unit_id==ses['unit_id'],
                              APPayment.kegiatan_sub_id==KegiatanSub.id,
                        ).order_by(APPayment.no_urut.desc()
                        ).group_by(APPayment.id,
                          APPayment.kode,
                          APPayment.jenis,
                          APPayment.tanggal,
                          KegiatanSub.nama.label('kegiatan_sub_nm'),
                          APPayment.nama,
                          APPayment.amount,
                        )
                rowTable = DataTables(req, APPayment, query, columns)
                return rowTable.output_result()

        elif url_dict['act']=='headofnama':
            query = DBSession.query(APPayment.id, 
                                    APPayment.no_urut,
                                    APPayment.nama,
                                    func.sum(APPaymentItem.amount).label('amount'),
                                    func.sum(APPaymentItem.ppn).label('ppn'),
                                    func.sum(APPaymentItem.pph).label('pph'),
                                    )\
                        .filter(APPayment.tahun_id==ses['tahun'],
                                APPayment.unit_id==ses['unit_id'],
                                APPayment.disabled==0)\
                        .join(APPaymentItem)\
                        .group_by(APPayment.id, APPayment.no_urut,
                                  APPayment.nama)
            rows = query.all()
            r = []
            for k in rows:
                d={}
                d['id']          = k[0]
                d['value']       = ''.join([str(k[1]),' - ',str(k[2])])
                d['amount']      = int(k[3])
                d['ppn']         = int(k[4])
                d['pph']         = int(k[5])
                r.append(d) 
            print r
            return r
            
        elif url_dict['act']=='headofkode1':
            term  = 'term'  in params and params['term'] or ''
            #jenis = 'jenis' in params and params['jenis'] or ''
            #jenis1= "%d" % jenis
            q = DBSession.query(APPayment.id,
                                APPayment.kode.label('kode1'),
                                APPayment.nama.label('nama1'),
                                APPayment.amount.label('amount1'),
                                APPayment.no_bku.label('nbku'),
                                APPayment.tgl_bku.label('tbku'),
                                )\
                                .filter(APPayment.unit_id == ses['unit_id'],
                                        APPayment.tahun_id == ses['tahun'],
                                        APPayment.status_spp == 0,
                                        APPayment.amount != 0,
                                        #APPayment.jenis == jenis1,
                                        APPayment.kode.ilike('%s%%' % term))
            rows = q.all()                               
            r = []
            for k in rows:
                d={}
                d['id']      = k[0]
                d['value']   = k[1]
                d['kode']    = k[1]
                d['nama']    = k[2]
                d['amount']  = k[3]
                d['no_bku']  = k[4]
                d['tgl_bku'] = "%s" % k[5]
                r.append(d)
            print '---****----',r              
            return r
            
#######    
# Add #
#######
def form_validator(form, value):
    def err_kegiatan():
        raise colander.Invalid(form,
            'Kegiatan dengan no urut tersebut sudah ada')
                
class AddSchema(colander.Schema):
    unit_id         = colander.SchemaNode(
                          colander.String(),
                          oid = "unit_id")
    tahun_id        = colander.SchemaNode(
                          colander.String(),
                          oid = "tahun_id",
                          title="Tahun")
    no_urut         = colander.SchemaNode(
                          colander.Integer(),
                          oid = "no_urut",
                          missing=colander.drop)
    kode            = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="No.Payment")
    jenis           = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          widget=widget.SelectWidget(values=AP_TYPE),
                          oid="jenis",
                          title="Jenis")
    is_bayar        = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          widget=widget.SelectWidget(values=IS_BAYAR),
                          oid="is_bayar",
                          title="Dibayar")
    is_uang        = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          widget=widget.SelectWidget(values=IS_UANG),
                          oid="is_uang",
                          title="U.M/Panjar")
    tanggal         = colander.SchemaNode(
                          colander.Date())
                          
    kegiatan_sub_id = colander.SchemaNode(
                          colander.Integer(),
                          oid="kegiatan_sub_id")
    kegiatan_kd     = colander.SchemaNode(
                          colander.String(),
                          title = "Kegiatan",
                          oid="kegiatan_kd")
                          
    kegiatan_nm     = colander.SchemaNode(
                          colander.String(),
                          oid="kegiatan_nm")
                          
    nama            = colander.SchemaNode(
                          colander.String(),
                          title="Uraian")
    """
    ap_nomor        = colander.SchemaNode(
                          colander.String(),
                          title="No.Kwitansi")
    ap_tanggal      = colander.SchemaNode(
                          colander.Date(),
                          title="Tgl. Kwitansi")
    """
    ap_nama         = colander.SchemaNode(
                          colander.String(),
                          title="Nama")
    ap_rekening     = colander.SchemaNode(
                          colander.String(),
                          title="Rekening")
    ap_npwp         = colander.SchemaNode(
                          colander.String(),
                          title="NPWP")
    amount          = colander.SchemaNode(
                          colander.String(),
                          default=0,
                          oid="jml_total",
                          title="Jml. Tagihan")
    no_bast         = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="No. BAST")
    tgl_bast        = colander.SchemaNode(
                          colander.Date(),
                          missing=colander.drop,
                          title="Tgl. BAST")
    no_bku          = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
						  oid="no_bku",
                          title="No. BKU")
    tgl_bku         = colander.SchemaNode(
                          colander.Date(),
                          missing=colander.drop, 
                          oid="tgl_bku",
                          title="Tgl. BKU")
    ap_bentuk       = colander.SchemaNode(
                          colander.String(),
                          widget=widget.SelectWidget(values=KONTRAK_TYPE),
                          title="Bentuk"
                          )
    ap_alamat       = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="Alamat"
                          )
    ap_pemilik      = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="Pemimpin Perusahaan"
                          )
    ap_kontrak      = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="No Kontrak"
                          )
    ap_waktu        = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="Waktu"
                          )
    ap_nilai        = colander.SchemaNode(
                          colander.Integer(),
                          oid="ap_nilai",
                          missing=colander.drop,
                          title="Nilai Kontrak",
                          default=0
                          )
    ap_tgl_kontrak  = colander.SchemaNode(
                          colander.Date(),
                          missing=colander.drop,
                          title="Tgl Kontrak"
                          )
    """
    ap_kegiatankd   = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          oid="ap_kegiatankd"
                          )
    ap_kegiatannm   = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          oid="ap_kegiatannm",
                          title="Kegiatan"
                          )
    """
    ap_uraian       = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="Pekerjaan"
                          )

    ap_bap_no       = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="No BAP"
                          )
    ap_bap_tgl      = colander.SchemaNode(
                          colander.Date(),
                          missing=colander.drop,
                          title="Tgl BAP"
                          )
    ap_kwitansi_no  = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="No.Kwitansi"
                          )
    ap_kwitansi_tgl = colander.SchemaNode(
                          colander.Date(),
                          missing=colander.drop,
                          title="Tgl Kwitansi"
                          )
    ap_kwitansi_nilai        = colander.SchemaNode(
                          colander.Integer(),
                          oid="ap_kwitansi_nilai",
                          missing=colander.drop,
                          title="Nilai Kwitansi",
                          default=0
                          )      
      
class EditSchema(AddSchema):
    id             = colander.SchemaNode(
                          colander.Integer(),
                          oid="id")

def get_form(request, class_form):
    schema = class_form(validator=form_validator)
    schema = schema.bind(kontrak_type=KONTRAK_TYPE,is_bayar=IS_BAYAR,is_uang=IS_UANG)
    schema.request = request
    return Form(schema, buttons=('simpan','batal'))
    
def save(request, values, row=None):
    if not row:
        row = APPayment()
    row.from_dict(values)
    
    if not row.no_urut:
        row.no_urut = APPayment.max_no_urut(row.tahun_id,row.unit_id)+1;
    
    if not row.kode:
        tahun    = request.session['tahun']
        unit_kd  = request.session['unit_kd']
        no_urut  = row.no_urut
        no       = "0000%d" % no_urut
        nomor    = no[-5:]     
        row.kode = "%d" % tahun + "-%s" % unit_kd + "-%s" % nomor
        
    j='3'
    j1 = row.jenis
    if j1 != j:
        row.no_bku  = None
        row.tgl_bku = None        
    
    DBSession.add(row)
    DBSession.flush()
    return row
                                      
def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    values["amount"]=values["amount"].replace('.','') 
    row = save(request, values, row)
    request.session.flash('Pembayaran tagihan sudah disimpan.')
    return row
        
def route_list(request):
    return HTTPFound(location=request.route_url('ap-payment'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
@view_config(route_name='ap-payment-add', renderer='templates/ap-payment/add.pt',
             permission='add')
def view_add(request):
    form = get_form(request, AddSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            controls_dicted = dict(controls)
            
            #Cek Kode Sama ato tidak
            if not controls_dicted['kode']=='':
                a = form.validate(controls)
                b = a['kode']
                c = "%s" % b
                cek  = DBSession.query(APPayment).filter(APPayment.kode==c).first()
                if cek :
                    request.session.flash('Kode pembayaran tagihan sudah ada.', 'error')
                    return HTTPFound(location=self.request.route_url('ap-payment-add'))

            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                return dict(form=form)
            row = save_request(controls_dicted, request)
            return HTTPFound(location=request.route_url('ap-payment-edit',id=row.id))
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        del request.session[SESS_ADD_FAILED]
    return dict(form=form)

########
# Edit #
########
def query_id(request):
    return DBSession.query(APPayment).filter(APPayment.id==request.matchdict['id'])
    
def id_not_found(request):    
    msg = 'User ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='ap-payment-edit', renderer='templates/ap-payment/add.pt',
             permission='edit')
def view_edit(request):
    row  = query_id(request).first()
    uid  = row.id
    kode = row.kode
        
    if not row:
        return id_not_found(request)
    if row.status_spp:
        request.session.flash('Data sudah di SPP', 'error')
        return route_list(request)
    if row.posted:
        request.session.flash('Data sudah diposting', 'error')
        return route_list(request)

    form = get_form(request, EditSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            
            #Cek Kode Sama ato tidak
            a = form.validate(controls)
            b = a['kode']
            c = "%s" % b
            cek = DBSession.query(APPayment).filter(APPayment.kode==c).first()
            if cek:
                kode1 = DBSession.query(APPayment).filter(APPayment.id==uid).first()
                d     = kode1.kode
                if d!=c:
                    request.session.flash('Kode pembayaran tagihan sudah ada', 'error')
                    return HTTPFound(location=request.route_url('ap-payment-edit',id=row.id))

            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                return dict(form=form)
            save_request(dict(controls), request, row)
        return route_list(request)
    elif SESS_EDIT_FAILED in request.session:
        del request.session[SESS_EDIT_FAILED]
        return dict(form=form)
    values = row.to_dict()

    #Ketika pas edit, kode sama nama muncul sesuai id kegiatansub
    values['kegiatan_nm']=row.kegiatansubs.nama
    kd=row.kegiatansubs.kode
    ur=row.kegiatansubs.no_urut
    values['kegiatan_kd']="%s" % kd + "-%d" % ur
    
    """
    if values['ap_kegiatankd']:
        r = DBSession.query(Kegiatan).filter(Kegiatan.id==values['ap_kegiatankd']).first()
        nama = r.nama
        values['ap_kegiatannm']=nama
    """   
    form.set_appstruct(values) 
    return dict(form=form)

##########
# Delete #
##########    
@view_config(route_name='ap-payment-delete', renderer='templates/ap-payment/delete.pt',
             permission='delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    
    if not row:
        return id_not_found(request)
    if row.posted:
        request.session.flash('Data sudah diposting', 'error')
        return route_list(request)
    if row.status_spp:
        request.session.flash('Data sudah di SPP', 'error')
        return route_list(request)
    if row.amount:
        request.session.flash('Data tidak bisa dihapus, karena memiliki data items', 'error')
        return route_list(request)
        
    form = Form(colander.Schema(), buttons=('hapus','cancel'))
    values= {}
    if request.POST:
        if 'hapus' in request.POST:
            msg = '%s dengan kode %s telah berhasil.' % (request.title, row.kode)
            DBSession.query(APPayment).filter(APPayment.id==request.matchdict['id']).delete()
            DBSession.flush()
            request.session.flash(msg)
        return route_list(request)
    return dict(row=row, form=form.render())
    