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
from osipkd.models.apbd_tu import APInvoice, APInvoiceItem, SppItem, Spp
    
from datatables import ColumnDT, DataTables
from osipkd.views.base_view import BaseViews

SESS_ADD_FAILED = 'Tambah ap-invoice-skpd gagal'
SESS_EDIT_FAILED = 'Edit ap-invoice-skpd gagal'

def deferred_ap_type(node, kw):
    values = kw.get('ap_type', [])
    return widget.SelectWidget(values=values)
    
AP_TYPE = (
    ('1', 'UP'),
    ('2', 'TU'),
    ('3', 'GU'),
    ('4', 'LS'),
    )

class view_ap_invoice_skpd(BaseViews):

    @view_config(route_name="ap-invoice-skpd", renderer="templates/ap-invoice-skpd/list.pt")
    def view_list(self):
        ses = self.request.session
        req = self.request
        params = req.params
        url_dict = req.matchdict
        return dict(project='EIS', #row = row
        )
        
    ##########                    
    # Action #
    ##########    
    @view_config(route_name='ap-invoice-skpd-act', renderer='json',
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
                columns.append(ColumnDT('posted'))

                query = DBSession.query(APInvoice.id,
                          APInvoice.kode,
                          APInvoice.jenis,                          
                          APInvoice.tanggal,
                          KegiatanSub.nama.label('kegiatan_sub_nm'),
                          APInvoice.nama,
                          APInvoice.amount,
                          APInvoice.posted,
                        ).outerjoin(APInvoiceItem
                        ).filter(APInvoice.tahun_id==ses['tahun'],
                              APInvoice.unit_id==ses['unit_id'],
                              APInvoice.kegiatan_sub_id==KegiatanSub.id,
                        ).order_by(APInvoice.no_urut.desc()
                        ).group_by(APInvoice.id,
                          APInvoice.kode,
                          APInvoice.jenis,
                          APInvoice.tanggal,
                          KegiatanSub.nama.label('kegiatan_sub_nm'),
                          APInvoice.nama,
                          APInvoice.amount,
                          APInvoice.posted,
                        )
                rowTable = DataTables(req, APInvoice, query, columns)
                return rowTable.output_result()

        elif url_dict['act']=='headofnama':
            query = DBSession.query(APInvoice.id, 
                                    APInvoice.no_urut,
                                    APInvoice.nama,
                                    func.sum(APInvoiceItem.amount).label('amount'),
                                    func.sum(APInvoiceItem.ppn).label('ppn'),
                                    func.sum(APInvoiceItem.pph).label('pph'),
                                    )\
                        .filter(APInvoice.tahun_id==ses['tahun'],
                                APInvoice.unit_id==ses['unit_id'],
                                APInvoice.posted==0)\
                        .join(APInvoiceItem)\
                        .group_by(APInvoice.id, APInvoice.no_urut,
                                  APInvoice.nama)
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
            q = DBSession.query(APInvoice.id,APInvoice.kode.label('kode1'),APInvoice.nama.label('nama1'),APInvoice.amount.label('amount1'),
                                )\
                                .filter(APInvoice.unit_id == ses['unit_id'],
                                        APInvoice.tahun_id == ses['tahun'],
                                        APInvoice.posted == 0,
                                        #APInvoice.jenis == jenis1,
                                        APInvoice.kode.ilike('%s%%' % term))
            rows = q.all()                               
            r = []
            for k in rows:
                d={}
                d['id']      = k[0]
                d['value']   = k[1]
                d['kode']    = k[1]
                d['nama']    = k[2]
                d['amount']  = k[3]
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
                          missing=colander.drop)
    kode            = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="No. Utang")
    jenis           = colander.SchemaNode(
                          colander.String(),
                          widget=widget.SelectWidget(values=AP_TYPE),
                          title="Jenis")
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

    ap_nomor        = colander.SchemaNode(
                          colander.String(),
                          title="Nomor")
    ap_nama         = colander.SchemaNode(
                          colander.String(),
                          title="Nama")
    ap_tanggal      = colander.SchemaNode(
                          colander.Date(),
                          title="Tanggal")
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
                          title="Jml. Tagihan"
                          )

class EditSchema(AddSchema):
    id             = colander.SchemaNode(
                          colander.Integer(),
                          oid="id")

def get_form(request, class_form):
    schema = class_form(validator=form_validator)
    schema = schema.bind()
    schema.request = request
    return Form(schema, buttons=('simpan','batal'))
    
def save(values, row=None):
    if not row:
        row = APInvoice()
    row.from_dict(values)
    
    if not row.no_urut:
        row.no_urut = APInvoice.max_no_urut(row.tahun_id,row.unit_id)+1;
            
    if not row.kode:
        tahun    = request.session['tahun']
        unit_kd  = request.session['unit_kd']
        no_urut  = row.no_urut
        row.kode = "UTANG%d" % tahun + "-%s" % unit_kd + "-%d" % no_urut
        
    DBSession.add(row)
    DBSession.flush()
    return row
                                      
def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    values["amount"]=values["amount"].replace('.','') 
    row = save(values, row)
    request.session.flash('Tagihan sudah disimpan.')
    return row
        
def route_list(request):
    return HTTPFound(location=request.route_url('ap-invoice-skpd'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
@view_config(route_name='ap-invoice-skpd-add', renderer='templates/ap-invoice-skpd/add.pt',
             permission='add')
def view_add(request):
    form = get_form(request, AddSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            controls_dicted = dict(controls)
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                return dict(form=form)
            row = save_request(controls_dicted, request)
            return route_list(request)
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        del request.session[SESS_ADD_FAILED]
    return dict(form=form)

########
# Edit #
########
def query_id(request):
    return DBSession.query(APInvoice).filter(APInvoice.id==request.matchdict['id'])
    
def id_not_found(request):    
    msg = 'User ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='ap-invoice-skpd-edit', renderer='templates/ap-invoice-skpd/add.pt',
             permission='edit')
def view_edit(request):
    row = query_id(request).first()

    if not row:
        return id_not_found(request)
    if row.posted:
        request.session.flash('Data sudah diposting', 'error')
        return route_list(request)

    form = get_form(request, EditSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            
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
    
    form.set_appstruct(values) 
    return dict(form=form)

##########
# Delete #
##########    
@view_config(route_name='ap-invoice-skpd-delete', renderer='templates/ap-invoice-skpd/delete.pt',
             permission='delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    if not row:
        return id_not_found(request)
    if row.posted:
        request.session.flash('Data sudah diposting', 'error')
        return route_list(request)
    if row.amount:
        request.session.flash('Data tidak bisa dihapus, karena memiliki data items')
        return route_list(request)
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