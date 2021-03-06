import os
import uuid
from osipkd.tools import row2dict, xls_reader
from datetime import datetime
from sqlalchemy import not_, func, or_, cast, BigInteger, case
from pyramid.view import (view_config,)
from pyramid.httpexceptions import ( HTTPFound, )
import colander
from deform import (Form, widget, ValidationFailure, )
from osipkd.models import DBSession, Group, UserGroup
from osipkd.models.apbd_anggaran import Kegiatan, KegiatanSub, KegiatanItem
from osipkd.models.pemda_model import Rekening
from datatables import ColumnDT, DataTables
from osipkd.views.base_view import BaseViews
from osipkd.models.apbd_tu import  APInvoiceItem 

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

def deferred_sdana(node, kw):
    values = kw.get('sdana', [])
    return widget.SelectWidget(values=values)
    
SDANA = (
    ('DAU', 'DAU'),
    ('DAK', 'DAK'),
    ('PAD', 'PAD'),
    #('APBD Provinsi', 'APBD Provinsi'),
    ('APBD Banten', 'APBD Banten'),
    ('APBD Non Banten', 'APBD Non Banten'),
    ('APBN', 'APBN'),
    ('LOAN', 'LOAN'),
    ('Transfer Pusat', 'Transfer Pusat'),
    ('Bagi Hasil', 'Bagi Hasil'),
    ('Cukai Rokok', 'Cukai Rokok'),
    ('Dana Desa (ADD)', 'Dana Desa (ADD)'),
    ('Kapitasi', 'Kapitasi'),
    ('Dana Insentif Daerah (DID)', 'Dana Insentif Daerah (DID)'),
    ('Retribusi BLUD', 'Retribusi BLUD'),
    ('Lain-lain', 'Lain-lain'),
    )
    
class view_ak_jurnal(BaseViews):
    @view_config(route_name="ag-kegiatan-item", renderer="templates/ag-kegiatan-item/list.pt",
                 permission='read')
    def view_list(self):
        ses = self.request.session
        req = self.request
        params = req.params
        url_dict = req.matchdict
        kegiatan_sub_id =  url_dict['kegiatan_sub_id']
        
        row = KegiatanSub.query_id(kegiatan_sub_id).filter(KegiatanSub.unit_id==ses['unit_id']).first()
        rek_head = 5
        return dict(project='OSIPKD', row = row, rek_head=rek_head)
        
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
                  (KegiatanItem.vol_4_1*KegiatanItem.vol_4_2*KegiatanItem.hsat_4).label('amount_4'),
                  (KegiatanItem.hsat_1).label('harga_1'),
                  (KegiatanItem.hsat_2).label('harga_2'),
                  (KegiatanItem.hsat_3).label('harga_3'),
                  (KegiatanItem.hsat_4).label('harga_4'),
                  KegiatanSub.approval,
                  KegiatanSub.disabled
                  ).join(Rekening).join(KegiatanSub)
                  
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
            columns.append(ColumnDT('harga_1', filter=self._number_format))
            columns.append(ColumnDT('amount_1', filter=self._number_format))
            columns.append(ColumnDT('harga_2', filter=self._number_format))
            columns.append(ColumnDT('amount_2', filter=self._number_format))
            columns.append(ColumnDT('harga_3', filter=self._number_format))
            columns.append(ColumnDT('amount_3', filter=self._number_format))
            columns.append(ColumnDT('harga_4', filter=self._number_format))
            columns.append(ColumnDT('amount_4', filter=self._number_format))
            columns.append(ColumnDT('rekening_nm'))
            columns.append(ColumnDT('rekening_id'))
            columns.append(ColumnDT('approval'))
            columns.append(ColumnDT('disabled'))
            query = self.get_row_item().filter(KegiatanItem.kegiatan_sub_id==kegiatan_sub_id
                      ).order_by(Rekening.kode.asc(),KegiatanItem.no_urut)
            rowTable = DataTables(req, KegiatanItem,  query, columns)
            return rowTable.output_result()
            
        elif url_dict['act']=='headofnama':
            term = 'term' in params and params['term'] or ''
            kegiatan_sub_id =  'kegiatan_sub_id' in params and params['kegiatan_sub_id'] or 0
            q = DBSession.query(KegiatanItem.id, Rekening.kode, 
                                KegiatanItem.no_urut, KegiatanItem.nama, 
                                cast(KegiatanItem.hsat_4*KegiatanItem.vol_4_1*KegiatanItem.vol_4_2,BigInteger).label('amount')
                                )\
                         .join(Rekening)\
                         .join(KegiatanSub)\
                         .filter(KegiatanSub.unit_id  == ses['unit_id'],
                                 KegiatanSub.tahun_id == ses['tahun'],
                                 KegiatanItem.kegiatan_sub_id==kegiatan_sub_id,
                                 KegiatanItem.nama.ilike('%%%s%%' % term),
                                 #KegiatanItem.hsat_4*KegiatanItem.vol_4_1*KegiatanItem.vol_4_2>0
                                 )
            rows = q.all()
            r = []
            for k in rows:
                d={}
                d['id']          = k[0]
                d['value']       = ''.join([k[1],'-',str(k[2]),'-',k[3],' Rp.',str(k[4])])
                d['kode']        = ''.join([k[1]])
                d['nama']        = k[3]
                d['amount']      = k[4]
                
                r.append(d)    
            return r            
        
        elif url_dict['act']=='headofkode1':
            term = 'term' in params and params['term'] or ''
            kegiatan_sub = 'kegiatan_sub_id' in params and params['kegiatan_sub_id'] or 0
            q = DBSession.query(KegiatanItem.id, Kegiatan.kode.label('kegiatan_kd'),
                                Kegiatan.nama.label('kegiatan_nm'),
                                KegiatanSub.no_urut.label('kegiatan_no'),
                                Rekening.kode.label('rekening_kd'),
                                Rekening.nama.label('rekening_nm'),
                                KegiatanItem.no_urut.label('item_no'),
                                cast(KegiatanItem.hsat_4*KegiatanItem.vol_4_1*KegiatanItem.vol_4_2,BigInteger).label('amount')
                                ).\
                          join(KegiatanSub, Rekening).\
                          outerjoin(Kegiatan).\
                          filter(KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                                        #KegiatanSub.id==kegiatan_sub,
                                        KegiatanSub.unit_id == ses['unit_id'],
                                        KegiatanSub.tahun_id == ses['tahun'],
                                        KegiatanSub.kegiatan_id==Kegiatan.id,
                                        KegiatanItem.rekening_id==Rekening.id,
                                        #Kegiatan.kode=='0.00.00.10', 
                                        Rekening.kode.ilike('%%%s%%' % term))\
                      
            rows = q.all()                               
            r = []
            for k in rows:
                d={}
                d['id']      = k[0]
                d['value']   = '{kegiatan_kd}-{kegiatan_no}-{rekening_kd}-{item_no}'.\
                                format(kegiatan_kd=k[1], kegiatan_no=k[3], 
                                       rekening_kd=k[4], item_no=k[6])
                d['kode']    = '{kegiatan_kd}-{kegiatan_no}-{rekening_kd}-{item_no}'.\
                                format(kegiatan_kd=k[1], kegiatan_no=k[3], 
                                       rekening_kd=k[4], item_no=k[6])
                d['nama']    = k[5]
                d['amount']  = k[7]
                r.append(d)
            return r            
        
        elif url_dict['act']=='headofnama1':
            term = 'term' in params and params['term'] or ''
            kegiatan_sub = 'kegiatan_sub_id' in params and params['kegiatan_sub_id'] or 0
            q = DBSession.query(KegiatanItem.id, Kegiatan.kode.label('kegiatan_kd'),
                                Kegiatan.nama.label('kegiatan_nm'),
                                KegiatanSub.no_urut.label('kegiatan_no'),
                                Rekening.kode.label('rekening_kd'),
                                Rekening.nama.label('rekening_nm'),
                                KegiatanItem.no_urut.label('item_no'),
                                cast(KegiatanItem.hsat_4*KegiatanItem.vol_4_1*KegiatanItem.vol_4_2,BigInteger).label('amount')
                                ).\
                          join(KegiatanSub, Rekening).\
                          outerjoin(Kegiatan).\
                          filter(KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                                        #KegiatanSub.id==kegiatan_sub,
                                        KegiatanSub.unit_id == ses['unit_id'],
                                        KegiatanSub.tahun_id == ses['tahun'],
                                        KegiatanSub.kegiatan_id==Kegiatan.id,
                                        KegiatanItem.rekening_id==Rekening.id,
                                        #Kegiatan.kode=='0.00.00.10', 
                                        #Rekening.kode.ilike('%%%s%%' % term))\
                                        KegiatanItem.nama.ilike('%%%s%%' % term))\
                      
            rows = q.all()                               
            r = []
            for k in rows:
                d={}
                d['id']      = k[0]
                d['value']   = ''.join([k[1],'-',str(k[3]),'-',k[4],'-',str(k[6]),' ',k[5],' Rp.',str(k[7])])
                                #format(kegiatan_kd=k[1], kegiatan_no=k[3], 
                                #       rekening_kd=k[4], item_no=k[6])
                d['kode']    = '{kegiatan_kd}-{kegiatan_no}-{rekening_kd}-{item_no}'.\
                                format(kegiatan_kd=k[1], kegiatan_no=k[3], 
                                       rekening_kd=k[4], item_no=k[6])
                d['nama']    = k[5]
                d['amount']  = k[7]
                r.append(d)
            return r            
            
        elif url_dict['act']=='headofnama3':
            term = 'term' in params and params['term'] or ''
            q = DBSession.query(KegiatanItem.id, KegiatanItem.nama.label('ap_kegiatankd'),KegiatanSub.id,KegiatanSub.nama).\
                          join(KegiatanSub).\
                          outerjoin(Kegiatan).\
                          filter(KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                                 KegiatanSub.unit_id == ses['unit_id'],
                                 KegiatanSub.tahun_id == ses['tahun'],
                                 KegiatanSub.kegiatan_id==Kegiatan.id,
                                 Kegiatan.kode!='0.00.00.10', 
                                 Kegiatan.kode!='0.00.00.21',
                                 Kegiatan.kode!='0.00.00.31',
                                 Kegiatan.kode!='0.00.00.32',
                                 KegiatanItem.nama.ilike('%%%s%%' % term))\
                                 
            rows = q.all()                               
            r = []
            for k in rows:
                d={}
                d['id']      = k[0]
                d['value']   = k[1]
                d['nama']    = k[1]
                d['nama1']   = k[3]
                r.append(d)
                print "XCXCXCXC",r
            return r            


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
        kegiatan_sub_id  = 'kegiatan_sub_id'  in params and params['kegiatan_sub_id']  or None
        rekening_id      = 'rekening_id'      in params and params['rekening_id']      or None
        kegiatan_item_id = 'kegiatan_item_id' in params and params['kegiatan_item_id'] or None
        print'++++++++++++++kegiatan_item_id++++++++++++++++++++++++',kegiatan_item_id 
        
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
            
        ### Sum dari APInvoiceItem sesuai APInvoiceItem.id 
        q_ai = DBSession.query(func.sum(APInvoiceItem.amount).label('jumlah')
                    ).filter(APInvoiceItem.kegiatan_item_id==kegiatan_item_id
                    ).first()
        q_aia = '%s' % q_ai 
        #q_aiaa = int(q_aia)
        if q_aia=='None':
            q_aia=0
        print'++++++++++++++Realisasi Sum APInvoiceItem++++++++++++++++++++++',q_aia

        if q_aia:
            q_aiaa = int(q_aia)
            vol_3_1 = row_dict['vol_3_1']
            vol_3_2 = row_dict['vol_3_2']
            hsat_3  = row_dict['hsat_3'] = amount
            vol_4_1 = row_dict['vol_4_1']
            vol_4_2 = row_dict['vol_4_2']
            hsat_4  = row_dict['hsat_4'] = amount 
            rdppa   = (vol_3_1*vol_3_2)*int(hsat_3)
            rdppa1  = int(float(rdppa))
            dppa    = (vol_4_1*vol_4_2)*int(hsat_4)
            dppa1   = int(float(dppa)) 
            print'xxxxxxxxxxxxxxxxhsat3 xxxxxxxxxxxxxxxxxx',rdppa1
            print'xxxxxxxxxxxxxxxxhsat4 xxxxxxxxxxxxxxxxxx',dppa1
            if rdppa1 < q_aiaa and dppa1 < q_aiaa:
                print'xxxxxxxxxxxxxxxxAPInvoiceItemxxxxxxxxxxx',q_aiaa
                return {'success':False, 'msg':'Gagal Update Data, Karena kurang dari nilai yang sudah terealisasi %s' % q_aiaa }
        
        if ag_step_id<2:
            row_dict['hsat_1'] = amount 
        if ag_step_id<3:
            row_dict['hsat_2'] = amount 
        if ag_step_id<4:
            row_dict['hsat_3'] = amount 
        if ag_step_id<5:
            row_dict['hsat_4'] = amount

        print "---------------------->>", row_dict
        row.from_dict(row_dict)

        print "------------------------<<", row.disabled
        ## Cek sudah Posting atau belum    

        #q = DBSession.query(KegiatanSub.disabled).filter(KegiatanSub.id==row_dict['kegiatan_sub_id'])
        #rowsub = q.first()
        #if rowsub.disabled:
        #    return {'success':False, 'msg':'Data tidak dapat diupdate karena sudah Posting'}

            #ses.flash('Data tidak dapat diupdate karena sudah diposting', 'error')
            #return route_list(req, kegiatan_sub_id)
        
        DBSession.add(row)
        DBSession.flush()
        return {"success": True, 'id': row.id, "msg":'Success Tambah Data'}
        
        try:
          pass
        except:
            return {'success':False, 'msg':'Gagal Tambah Data'}

#######    
# Add #
#######
def form_validator(form, value):
    def err_kegiatan():
        raise colander.Invalid(form,
            'Kegiatan dengan no urut tersebut sudah ada')
                
class AddSchema(colander.Schema):

    kegiatan_sub_id = colander.SchemaNode(
                          colander.String(),
                          )
    rekening_id      = colander.SchemaNode(
                          colander.String(),
                          oid="rekening_id"
                          )
    rekening_kd      = colander.SchemaNode(
                          colander.String(),
                          title="Rekening",
                          oid="rekening_kd"
                          )
    rekening_nm      = colander.SchemaNode(
                          colander.String(),
                          oid="rekening_nm"
                          )
    kode             = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          )
    nama             = colander.SchemaNode(
                          colander.String(),
                          oid="nama",
                          )
    no_urut          = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="No.Item",
                          )
    header_id        = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          )
    vol_1_1          = colander.SchemaNode(
                          colander.Float(),
                          missing=colander.drop,
                          default=1,
                          oid="vol_1_1",
                          title="Volume 1"
                          )
    sat_1_1          = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="Satuan 2"
                          )
    vol_1_2          = colander.SchemaNode(
                          colander.Float(),
                          missing=colander.drop,
                          default=1,
                          oid="vol_1_2",
                          title="Volume 2")
    sat_1_2          = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="Satuan 2"
                          )
    hsat_1           = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          default=0,
                          oid="hsat_1",
                          title="Harga")
    vol_2_1          = colander.SchemaNode(
                          colander.Float(),
                          missing=colander.drop,
                          default=1,
                          oid="vol_2_1",
                          title="Volume 1")
    sat_2_1          = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="Satuan 1"
                          )
    vol_2_2          = colander.SchemaNode(
                          colander.Float(),
                          missing=colander.drop,
                          default=1,
                          oid="vol_2_2",
                          title="Volume 2")
    sat_2_2          = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="Satuan 2"
                          )
    hsat_2           = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          default=0,
                          oid="hsat_2",
                          title="Harga")
    vol_3_1          = colander.SchemaNode(
                          colander.Float(),
                          missing=colander.drop,
                          default=1,
                          oid="vol_3_1",
                          title="Volume 1")
    sat_3_1          = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="Satuan 1"
                          )
    vol_3_2          = colander.SchemaNode(
                          colander.Float(),
                          missing=colander.drop,
                          default=1,
                          oid="vol_3_2",
                          title="Volume 2")
    sat_3_2          = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="Satuan 2"
                          )
    hsat_3           = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          default=0,
                          oid="hsat_3",
                          title="Harga")
    vol_4_1          = colander.SchemaNode(
                          colander.Float(),
                          missing=colander.drop,
                          default=1,
                          oid="vol_4_1",
                          title="Volume 1")
    sat_4_1          = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="Satuan 1"
                          )
    vol_4_2          = colander.SchemaNode(
                          colander.Float(),
                          missing=colander.drop,
                          default=1,
                          oid="vol_4_2",
                          title="Volume 2")
    sat_4_2          = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="Satuan 2"
                          )
    hsat_4           = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          default=0,
                          oid="hsat_4",
                          title="Harga")
    pelaksana        = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          )
    mulai            = colander.SchemaNode(
                        colander.Date(),
                        missing = colander.drop)
    selesai          = colander.SchemaNode(
                        colander.Date(),
                        missing = colander.drop)
    bln01            = colander.SchemaNode(
                          colander.Integer(),
                          missing=colander.drop,
                          oid="bln01",
                          default=0,
                          title="Jan")
    bln02            = colander.SchemaNode(
                          colander.Integer(),
                          missing=colander.drop,
                          oid="bln02",
                          default=0,
                          title="Feb")
    bln03            = colander.SchemaNode(
                          colander.Integer(),
                          missing=colander.drop,
                          oid="bln03",
                          default=0,
                          title="Mar")
    bln04            = colander.SchemaNode(
                          colander.Integer(),
                          oid="bln04",
                          missing=colander.drop,
                          default=0,
                          title="Apr")
    bln05            = colander.SchemaNode(
                          colander.Integer(),
                          oid="bln05",
                          missing=colander.drop,
                          default=0,
                          title="Mei")
    bln06            = colander.SchemaNode(
                          colander.Integer(),
                          missing=colander.drop,
                          oid="bln06",
                          default=0,
                          title="Jun")
    bln07            = colander.SchemaNode(
                          colander.Integer(),
                          missing=colander.drop,
                          oid="bln07",
                          default=0,
                          title="Jul")
    bln08            = colander.SchemaNode(
                          colander.Integer(),
                          oid="bln08",
                          missing=colander.drop,
                          default=0,
                          title="Agt")
    bln09            = colander.SchemaNode(
                          colander.Integer(),
                          oid="bln09",
                          missing=colander.drop,
                          default=0,
                          title="Sep")
    bln10            = colander.SchemaNode(
                          colander.Integer(),
                          oid="bln10",
                          missing=colander.drop,
                          default=0,
                          title="Okt")
    bln11            = colander.SchemaNode(
                          colander.Integer(),
                          oid="bln11",
                          missing=colander.drop,
                          default=0,
                          title="Nov")
    bln12            = colander.SchemaNode(
                          colander.Integer(),
                          missing=colander.drop,
                          oid="bln12",
                          default=0,
                          title="Des")
    ssh_id           = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          )
    is_summary       = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          )
    is_apbd          = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          )
    keterangan       = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          )
    sdana       = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          widget=widget.SelectWidget(values=SDANA),
                          oid="sdana",
                          title="Sumber Dana"
                          )

class EditSchema(AddSchema):
    id             = colander.SchemaNode(
                          colander.Integer(),
                          oid="id")

def get_form(request, class_form):
    schema = class_form(validator=form_validator)
    schema = schema.bind(sdana=SDANA)
    schema.request = request
    return Form(schema, buttons=('simpan','batal'))
    
def save(values, request, user, row=None):
    if not row:
        row = KegiatanItem()
        row.created = datetime.now()
        row.create_uid = user.id
        
    row.from_dict(values)
    # isikan user update dan tanggal update
    row.updated = datetime.now()
    row.update_uid = user.id
        
    ag_step_id = request.session['ag_step_id']
    if ag_step_id<2:
        values['vol_2_1'] = values['vol_%s_1' % ag_step_id] 
        values['vol_2_2'] = values['vol_%s_2' % ag_step_id] 
        values['sat_2_1'] = values['sat_%s_1' % ag_step_id] 
        values['sat_2_2'] = values['sat_%s_2' % ag_step_id] 
        values['hsat_2'] = values['hsat_%s' % ag_step_id] 
    if ag_step_id<4:
        values['vol_3_1'] = values['vol_%s_1' % ag_step_id] 
        values['vol_3_2'] = values['vol_%s_2' % ag_step_id] 
        values['sat_3_1'] = values['sat_%s_1' % ag_step_id] 
        values['sat_3_2'] = values['sat_%s_2' % ag_step_id] 
        values['hsat_3'] = values['hsat_%s' % ag_step_id] 
    if ag_step_id<5:
        values['vol_4_1'] = values['vol_%s_1' % ag_step_id] 
        values['vol_4_2'] = values['vol_%s_2' % ag_step_id] 
        values['sat_4_1'] = values['sat_%s_1' % ag_step_id] 
        values['sat_4_2'] = values['sat_%s_2' % ag_step_id] 
        values['hsat_4'] = values['hsat_%s' % ag_step_id] 
        
    if not row.no_urut:
          row.no_urut = KegiatanItem.max_no_urut(values['kegiatan_sub_id'],values['rekening_id'])+1;

    DBSession.add(row)
    DBSession.flush()
    return row
                                      
def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']

    #values["vol_1_1"]=values["vol_1_1"].replace('.','') 
    #values["vol_1_2"]=values["vol_1_2"].replace('.','') 
    values["hsat_1"]=values["hsat_1"].replace('.','') 

    #values["vol_2_1"]=values["vol_2_1"].replace('.','') 
    #values["vol_2_2"]=values["vol_2_2"].replace('.','') 
    values["hsat_2"]=values["hsat_2"].replace('.','') 

    #values["vol_3_1"]=values["vol_3_1"].replace('.','') 
    #values["vol_3_2"]=values["vol_3_2"].replace('.','') 
    values["hsat_3"]=values["hsat_3"].replace('.','') 

    #values["vol_4_1"]=values["vol_4_1"].replace('.','') 
    #values["vol_4_2"]=values["vol_4_2"].replace('.','') 
    values["hsat_4"]=values["hsat_4"].replace('.','') 

    row = save(values, request, request.user, row)
    request.session.flash('Kegiatan sudah disimpan.')
        
def route_list(request, kegiatan_sub_id):
    kegiatan_sub_id
    q = DBSession.query(Kegiatan.kode.label('kegiatan_kd')
    #).join(KegiatanSub, KegiatanItem, Kegiatan
    ).filter(Kegiatan.id==KegiatanSub.kegiatan_id, 
    KegiatanItem.kegiatan_sub_id==KegiatanSub.id, 
    KegiatanItem.kegiatan_sub_id==kegiatan_sub_id)
    rows = q.all()
    for k in rows:
        a =k[0]
        
        if a =='0.00.00.10':
            return HTTPFound(location=request.route_url('ag-pendapatan',kegiatan_sub_id=kegiatan_sub_id))
        elif a =='0.00.00.21':
            return HTTPFound(location=request.route_url('ag-btl',kegiatan_sub_id=kegiatan_sub_id))
        elif a =='0.00.00.31':
            return HTTPFound(location=request.route_url('ag-penerimaan',kegiatan_sub_id=kegiatan_sub_id))
        elif a =='0.00.00.32':
            return HTTPFound(location=request.route_url('ag-pengeluaran',kegiatan_sub_id=kegiatan_sub_id))
        #elif a =='0.00.00.20':
            #return HTTPFound(location=request.route_url('ag-kegiatan-item',kegiatan_sub_id=kegiatan_sub_id))
    return HTTPFound(location=request.route_url('ag-kegiatan-item',kegiatan_sub_id=kegiatan_sub_id))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
@view_config(route_name='ag-kegiatan-item-add', renderer='templates/ag-kegiatan-item/add.pt',
             permission='add')
def view_add(request):
    form = get_form(request, AddSchema)
    kegiatan_sub_id = request.matchdict['kegiatan_sub_id']
    
    ## Cek sudah Posting atau belum    
    q = DBSession.query(KegiatanSub.disabled).filter(KegiatanSub.id==request.matchdict['kegiatan_sub_id'])
    rowsub = q.first()
    if rowsub.disabled:
        request.session.flash('Data tidak dapat ditambah karena sudah Posting', 'error')
        return route_list(request, kegiatan_sub_id)
    
    ses = request.session
    rows = KegiatanSub.query_id(kegiatan_sub_id).filter(KegiatanSub.unit_id == ses['unit_id']).first()
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            controls_dicted = dict(controls)
            
            b    = form.validate(controls)
            vol_1_1 = b['vol_1_1']
            vol_1_2 = b['vol_1_2']
            hsat_1  = b['hsat_1'].replace('.','') 
            vol_2_1 = b['vol_2_1']
            vol_2_2 = b['vol_2_2']
            hsat_2  = b['hsat_2'].replace('.','') 
            vol_3_1 = b['vol_3_1']
            vol_3_2 = b['vol_3_2']
            hsat_3  = b['hsat_3'].replace('.','') 
            vol_4_1 = b['vol_4_1']
            vol_4_2 = b['vol_4_2']
            hsat_4  = b['hsat_4'].replace('.','') 
            bln01    = b['bln01']
            bln02    = b['bln02']
            bln03    = b['bln03']
            bln04    = b['bln04']
            bln05    = b['bln05']
            bln06    = b['bln06']
            bln07    = b['bln07']
            bln08    = b['bln08']
            bln09    = b['bln09']
            bln10    = b['bln10']
            bln11    = b['bln11']
            bln12    = b['bln12']
            rka  =  (vol_1_1*vol_1_2)*int(hsat_1)
            rka1 = int(float(rka))
            dpa  =  (vol_2_1*vol_2_2)*int(hsat_2)
            dpa1 = int(float(dpa))
            rdppa =  (vol_3_1*vol_3_2)*int(hsat_3)
            rdppa1 = int(float(rdppa))
            dppa =  (vol_4_1*vol_4_2)*int(hsat_4)
            dppa1 = int(float(dppa))
            bln  = bln01+bln02+bln03+bln04+bln05+bln06+bln07+bln08+bln09+bln10+bln11+bln12
            ag_step_id = request.session['ag_step_id']
            if ag_step_id==1:
                if bln>rka1:
                    request.session.flash('Tidak boleh melebihi jumlah RKA', 'error')
                    return HTTPFound(location=request.route_url('ag-kegiatan-item-edit',kegiatan_sub_id=row.kegiatan_sub_id,id=row.id))
            elif ag_step_id==2:
                if bln!=dpa1:
                    request.session.flash('Jumlah DPA dengan Rencana Biaya tidak sama', 'error')
                    return HTTPFound(location=request.route_url('ag-kegiatan-item-edit',kegiatan_sub_id=row.kegiatan_sub_id,id=row.id))
            elif ag_step_id==3:
                if bln!=rdppa1:
                    request.session.flash('Jumlah RDPPA dengan Rencana Biaya tidak sama', 'error')
                    return HTTPFound(location=request.route_url('ag-kegiatan-item-edit',kegiatan_sub_id=row.kegiatan_sub_id,id=row.id))
            elif ag_step_id==4:
                if bln!=dppa1:
                    request.session.flash('Jumlah pagu anggaran dengan Rencana Biaya tidak sama', 'error')
                    return HTTPFound(location=request.route_url('ag-kegiatan-item-edit',kegiatan_sub_id=row.kegiatan_sub_id,id=row.id))

            #return dict(form=form.render(appstruct=controls_dicted))
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                return dict(form=form, row=rows, rek_head=5)
            save_request(controls_dicted, request)
            #print "--------------------------",id
            #return HTTPFound(location=request.route_url('ag-kegiatan-item-edit',kegiatan_sub_id=kegiatan_sub_id,pid=id))
        return route_list(request,kegiatan_sub_id)
    elif SESS_ADD_FAILED in request.session:
        del request.session[SESS_ADD_FAILED]
        #return session_failed(request, SESS_ADD_FAILED)
    return dict(form=form, row=rows, rek_head=5)

########
# Edit #
########
def query_id(request):
    return DBSession.query(KegiatanItem).filter(KegiatanItem.id==request.matchdict['id'],
                                                KegiatanItem.kegiatan_sub_id==request.matchdict['kegiatan_sub_id'])
    
def id_not_found(request,kegiatan_sub_id):    
    msg = 'ITEM ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request,kegiatan_sub_id)

@view_config(route_name='ag-kegiatan-item-edit', renderer='templates/ag-kegiatan-item/add.pt',
             permission='edit')
def view_edit(request):
    ses = request.session
    req = request
    kegiatan_sub_id = request.matchdict['kegiatan_sub_id']
    row = query_id(request).first()
    ui=row.id

    if not row:
        return id_not_found(request,kegiatan_sub_id)

    ## variabel ag_step_id
    #ag_step_id = ses['ag_step_id']
    
    ## kondisi group ppkd (semua unit)
    #grp = DBSession.query(func.lower(Group.group_name)).filter(UserGroup.user_id==request.user.id, Group.id==UserGroup.group_id).first()
    #grps = '%s' % grp
    ##
 
    form = get_form(request, EditSchema)
    rows = KegiatanSub.query_id(kegiatan_sub_id).filter(KegiatanSub.unit_id==ses['unit_id']).first()
    if request.POST:
        if 'simpan' in request.POST:
            ## variabel group name
            grp1 = 'kasubag perencanaan skpd'
            grp2 = 'kepala bidang bapeda (tapd)'
            grp3 = 'kepala bidang p3 dispenda (tapd)'
            grp4 = 'kepala bidang anggaran (tapd)'
            grp5 = 'admin bpkad'
            
            ## variabel ag_step_id
            ag_step_id = ses['ag_step_id']        
            
            ## kondisi group ppkd (semua unit)
            grp = DBSession.query(case([(func.lower(Group.group_name)==grp1,1),(func.lower(Group.group_name)==grp2,2),
                  (func.lower(Group.group_name)==grp3,3), (func.lower(Group.group_name)==grp4,4), (func.lower(Group.group_name)==grp5,5)], 
                  else_=0)
                  ).filter(UserGroup.user_id==req.user.id, Group.id==UserGroup.group_id).first()
            grps_kd = '%s' % grp
          
            ## Cek sudah Posting atau belum    
            q = DBSession.query(KegiatanSub.disabled).filter(KegiatanSub.id==request.matchdict['kegiatan_sub_id'])
            rowsub = q.first()
            if rowsub.disabled:
                request.session.flash('Data tidak dapat diupdate karena sudah Posting', 'error')
                return route_list(request, kegiatan_sub_id)
        
            ## Cek Grup
            if grps_kd == '2' or grps_kd == '3' or grps_kd == '4' :
                request.session.flash('Anda tidak mempunyai hak akses untuk mengupdate data', 'error')
                return route_list(request, kegiatan_sub_id)
                
            if rows.disabled==1 and rows.approval==4:
                request.session.flash('Data tidak dapat diupdate karena sudah diposting BPKAD', 'error')
                return route_list(request, kegiatan_sub_id)
            if rows.approval==3:
                request.session.flash('Data tidak dapat diupdate karena sudah diposting Dispenda', 'error')
                return route_list(request, kegiatan_sub_id)
            if rows.approval==2:
                request.session.flash('Data tidak dapat diupdate karena sudah diposting Bappeda', 'error')
                return route_list(request, kegiatan_sub_id)
                    
            controls = request.POST.items()
            a    = form.validate(controls)
            vol_1_1 = a['vol_1_1']
            vol_1_2 = a['vol_1_2']
            hsat_1  = a['hsat_1'].replace('.','') 
            vol_2_1 = a['vol_2_1']
            vol_2_2 = a['vol_2_2']
            hsat_2  = a['hsat_2'].replace('.','') 
            vol_3_1 = a['vol_3_1']
            vol_3_2 = a['vol_3_2']
            hsat_3  = a['hsat_3'].replace('.','') 
            vol_4_1 = a['vol_4_1']
            vol_4_2 = a['vol_4_2']
            hsat_4  = a['hsat_4'].replace('.','') 
            bln01    = a['bln01']
            bln02    = a['bln02']
            bln03    = a['bln03']
            bln04    = a['bln04']
            bln05    = a['bln05']
            bln06    = a['bln06']
            bln07    = a['bln07']
            bln08    = a['bln08']
            bln09    = a['bln09']
            bln10    = a['bln10']
            bln11    = a['bln11']
            bln12    = a['bln12']
            rka      = (vol_1_1*vol_1_2)*int(hsat_1)
            rka1     = int(float(rka))
            dpa      = (vol_2_1*vol_2_2)*int(hsat_2)
            dpa1     = int(float(dpa))
            rdppa    = (vol_3_1*vol_3_2)*int(hsat_3)
            rdppa1   = int(float(rdppa))
            dppa     = (vol_4_1*vol_4_2)*int(hsat_4)
            dppa1    = int(float(dppa))
            bln      = bln01+bln02+bln03+bln04+bln05+bln06+bln07+bln08+bln09+bln10+bln11+bln12
            
            ### Sum dari APInvoiceItem sesuai APInvoiceItem.id 
            q_ai = DBSession.query(func.sum(APInvoiceItem.amount).label('jumlah')
                        ).filter(APInvoiceItem.kegiatan_item_id==ui
                        ).first()
            q_aia = '%s' % q_ai 
        
            if q_aia == 'None':
                q_aia=0
            print'++++++++++++++Sum APInvoiceItem++++++++++++++++++++++',q_aia

            if q_aia:
                q_aiaa = int(q_aia)
                if rdppa1 < q_aiaa and dppa1 < q_aiaa:
                    print'xxxxxxxxxxxxxxxxTILU3 xxxxxxxxxxxxxxxxxx',rdppa1
                    print'xxxxxxxxxxxxxxxxOPAT4 xxxxxxxxxxxxxxxxxx',dppa1
                    print'xxxxxxxxxxxxxxxxGAGALxxxxxxxxxxx'
                    request.session.flash('Gagal Update Data', 'error')
                    return HTTPFound(location=request.route_url('ag-kegiatan-item-edit',kegiatan_sub_id=row.kegiatan_sub_id,id=row.id))
            print'saveeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee'
            

            ag_step_id = request.session['ag_step_id']
            if ag_step_id==1:
                if bln>rka1:
                    request.session.flash('Tidak boleh melebihi jumlah RKA', 'error')
                    return HTTPFound(location=request.route_url('ag-kegiatan-item-edit',kegiatan_sub_id=row.kegiatan_sub_id,id=row.id))
            elif ag_step_id==2:
                if bln!=dpa1:
                    request.session.flash('Jumlah DPA dengan Rencana Biaya tidak sama', 'error')
                    return HTTPFound(location=request.route_url('ag-kegiatan-item-edit',kegiatan_sub_id=row.kegiatan_sub_id,id=row.id))
            elif ag_step_id==3:
                if bln!=rdppa1:
                    request.session.flash('Jumlah RDPPA dengan Rencana Biaya tidak sama', 'error')
                    return HTTPFound(location=request.route_url('ag-kegiatan-item-edit',kegiatan_sub_id=row.kegiatan_sub_id,id=row.id))
            elif ag_step_id==4:
                print "---------------------------------->>>>",bln
                print "---------------------------------->>>>",dppa1
                if bln!=dppa1:
                    request.session.flash('Jumlah pagu anggaran dengan Rencana Biaya tidak sama', 'error')
                    return HTTPFound(location=request.route_url('ag-kegiatan-item-edit',kegiatan_sub_id=row.kegiatan_sub_id,id=row.id))

            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                return dict(form=form, row=rows, rek_head=5)
            save_request(dict(controls), request, row)
            return HTTPFound(location=request.route_url('ag-kegiatan-item-edit',kegiatan_sub_id=row.kegiatan_sub_id,id=row.id))
        return route_list(request,kegiatan_sub_id)
    elif SESS_EDIT_FAILED in request.session:
        del request.session[SESS_EDIT_FAILED]
        return dict(form=form)
    values = row.to_dict() #dict(zip(row.keys(), row))
    values['rekening_kd']=row.rekenings.kode
    values['rekening_nm']=row.rekenings.nama
    form.set_appstruct(values) 
    return dict(form=form, row=rows, rek_head=5)

##########
# Delete #
##########    
@view_config(route_name='ag-kegiatan-item-delete', renderer='templates/ag-kegiatan-item/delete.pt',
             permission='delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    kegiatan_sub_id = request.matchdict['kegiatan_sub_id']
    if not row:
        return {'success':False, "msg":self.id_not_found()}

    ## Cek sudah Posting atau belum    
    q = DBSession.query(KegiatanSub).filter(KegiatanSub.id==request.matchdict['kegiatan_sub_id'])
    rowsub = q.first()
    #if rowsub.disabled:
    #    request.session.flash('Data tidak dapat dihapus karena sudah Posting', 'error')
    #    return route_list(request, kegiatan_sub_id)

    ## variabel ag_step_id
    ses = request.session
    ag_step_id = ses['ag_step_id']        
            
    if rowsub.disabled == 1 and rowsub.approval==4:
        request.session.flash('Data tidak dapat dihapus karena sudah Posting', 'error')
        return route_list(request, kegiatan_sub_id)
    if rowsub.approval==3:
        request.session.flash('Data tidak dapat dihapus karena sudah di Approval oleh Dispenda', 'error')
        return route_list(request, kegiatan_sub_id)
    if rowsub.approval==2:
        request.session.flash('Data tidak dapat dihapus karena sudah di Approval oleh Bappeda', 'error')
        return route_list(request, kegiatan_sub_id)
            
    form = Form(colander.Schema(), buttons=('hapus','cancel'))
    values= {}
    if request.POST:
        if 'hapus' in request.POST:
            msg = 'Data sudah dihapus'
            DBSession.query(KegiatanItem).filter(KegiatanItem.id==request.matchdict['id']).delete()
            DBSession.flush()
            request.session.flash(msg)
        return route_list(request,kegiatan_sub_id)
    return dict(row=row,form=form.render())

            
                        