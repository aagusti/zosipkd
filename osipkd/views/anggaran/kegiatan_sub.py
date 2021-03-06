import os
import uuid
from osipkd.tools import row2dict, xls_reader
from datetime import datetime
from sqlalchemy import not_, func, cast, BigInteger, or_, join, case
from pyramid.view import (view_config,)
from pyramid.httpexceptions import ( HTTPFound, )
import colander
from deform import (Form, widget, ValidationFailure, )
from osipkd.models import DBSession, Group, UserGroup
from osipkd.models.apbd_anggaran import Program, Kegiatan, KegiatanSub, KegiatanItem
from osipkd.models.pemda_model import Urusan
from osipkd.models.apbd_tu import Spd, SpdItem
    
from datatables import ColumnDT, DataTables
from osipkd.views.base_view import BaseViews

SESS_ADD_FAILED = 'Tambah ag-kegiatan-sub gagal'
SESS_EDIT_FAILED = 'Edit ag-kegiatan-sub gagal'

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

class view_kegiatan_sub(BaseViews):
    @view_config(route_name="ag-bl", renderer="templates/ag-bl/list.pt",
                 permission='read')
    def view_list(self):
        ses = self.request.session
        req = self.request
        params = req.params
        url_dict = req.matchdict
        #row = {}
        #row['rekening_kd'] = '0.00.00.21'
        #row['rekening_nm'] = 'BELANJA TIDAK LANGSUNG'
        #row['rekeninghead'] = 52
        return dict(project='EIS', #row = row
        )
        
    ##########                    
    # Action #
    ##########    
    @view_config(route_name='ag-bl-act', renderer='json',
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
                columns.append(ColumnDT('no_urut'))
                columns.append(ColumnDT('nama'))
                columns.append(ColumnDT('prg_nm'))
                columns.append(ColumnDT('rka', filter=self._number_format))
                columns.append(ColumnDT('dpa', filter=self._number_format))
                columns.append(ColumnDT('rdppa', filter=self._number_format))
                columns.append(ColumnDT('dppa', filter=self._number_format))
                columns.append(ColumnDT('approval'))
                columns.append(ColumnDT('disabled'))
                #columns.append(ColumnDT('pegawai_nama'))

                query = DBSession.query(KegiatanSub.id,
                          KegiatanSub.kode,
                          KegiatanSub.no_urut,
                        KegiatanSub.nama,
                        #PegawaiModel.nama.label('pegawai_nama'),
                        Program.nama.label('prg_nm'),
                    func.coalesce(func.sum(KegiatanItem.vol_1_1*KegiatanItem.vol_1_2*KegiatanItem.hsat_1),0).label('rka'),       
                    func.coalesce(func.sum(KegiatanItem.vol_2_1*KegiatanItem.vol_2_2*KegiatanItem.hsat_2),0).label('dpa'),                      
                    func.coalesce(func.sum(KegiatanItem.vol_3_1*KegiatanItem.vol_3_2*KegiatanItem.hsat_3),0).label('rdppa'),                      
                    func.coalesce(func.sum(KegiatanItem.vol_4_1*KegiatanItem.vol_4_2*KegiatanItem.hsat_4),0).label('dppa'),
                        KegiatanSub.approval,
                        KegiatanSub.disabled)\
                    .join(Kegiatan)\
                    .join(Program)\
                    .join(Urusan)\
                    .outerjoin(KegiatanItem)\
                    .filter(
                            KegiatanSub.unit_id==self.unit_id,
                            KegiatanSub.tahun_id==self.tahun,
                            KegiatanSub.tahun_id==self.tahun,
                            #KegiatanSub.ttd1nip==PegawaiModel.kode,
                            Program.kode<>'0.00.00')\
                    .group_by(KegiatanSub.id,
                            KegiatanSub.no_urut,
                            KegiatanSub.nama,
                            Program.kode, Program.nama,
                            Kegiatan.kode, Urusan.kode, 
                            #PegawaiModel.kode, PegawaiModel.nama
                            )
                rowTable = DataTables(req, KegiatanSub, query, columns)
                # returns what is needed by DataTable
                #session.query(Table.column, func.count(Table.column)).group_by(Table.column).all()
                return rowTable.output_result()

        elif url_dict['act']=='reload':
            #if not kegiatan_kd:
            #    return {'success':False}
            query = DBSession.query(KegiatanSub).join(Kegiatan).join(Program).filter(
                       KegiatanSub.unit_id == ses['unit_id'],
                       KegiatanSub.tahun_id == ses['tahun'],
                       Program.kode<>'0.00.00'
                       ).first()
                       
            #if not query:
            #    return {'success':False, 'msg':'Data Kegiatan Tidak Ditemukan'}

            return {"success": True}
                
       
    @view_config(route_name='ag-kegiatan-sub-act', renderer='json',
                 permission='read')
    def view_act2(self):
        ses = self.request.session
        req = self.request
        params = req.params
        url_dict = req.matchdict
        
        if url_dict['act']=='reload':
            kegiatan_kd = 'kegiatan_kd' in params and  params['kegiatan_kd'] or None
            if not kegiatan_kd:
                return {'success':False}
            query = DBSession.query(KegiatanSub).join(Kegiatan).filter(
                       KegiatanSub.unit_id == ses['unit_id'],
                       KegiatanSub.tahun_id == ses['tahun'],
                       Kegiatan.kode == kegiatan_kd
                       ).first()
                       
            if not query:
                return {'success':False, 'msg':'Data Sub Kegiatan Tidak Ditemukan'}
                       
            return {"success": True, 'kegiatan_sub_id': query.id, 'msg':''}
            
        elif url_dict['act']=='headofkode':
            term = 'term' in params and params['term'] or ''
            q = DBSession.query(KegiatanSub.id, Kegiatan.kode, KegiatanSub.no_urut,
                                KegiatanSub.nama
                      ).join(Kegiatan).filter(KegiatanSub.unit_id == ses['unit_id'],
                           KegiatanSub.tahun_id==ses['tahun'],
                           Kegiatan.kode.ilike('%%%s%%' % term))
                           
            rows = q.all()
            r = []
            for k in rows:
                d={}
                d['id']          = k[0]
                d['value']       = ''.join([k[1],'-',str(k[2])])
                d['kode']        = ''.join([k[1],'-',str(k[2])])
                d['nama']        = k[3]
                r.append(d)    
            return r
        elif url_dict['act']=='headofnama':
            term = 'term' in params and params['term'] or ''
            q = DBSession.query(KegiatanSub.id, Kegiatan.kode, KegiatanSub.no_urut,
                                KegiatanSub.nama).join(Kegiatan).filter(
                      KegiatanSub.unit_id == ses['unit_id'],
                      KegiatanSub.tahun_id==ses['tahun'],
                      Kegiatan.nama.ilike('%%%s%%' % term))
            rows = q.all()
            r = []
            for k in rows:
                d={}
                d['id']          = k[0]
                d['value']       = k[3]
                d['kode']        = ''.join([k[1],'-',str(k[2])])
                d['nama']        = k[3]
                r.append(d)    
            return r
            
        elif url_dict['act']=='headofkode1':
            term = 'term' in params and params['term'] or ''
            q = DBSession.query(KegiatanSub.id, Kegiatan.kode, KegiatanSub.no_urut,
                                KegiatanSub.nama
                        ).join(Kegiatan
                        ).filter(KegiatanSub.unit_id == ses['unit_id'],
                                 KegiatanSub.tahun_id==ses['tahun'],
                                 Kegiatan.kode!='0.00.00.10',
                                 Kegiatan.kode!='0.00.00.31',
                                 Kegiatan.kode!='0.00.00.32',
                                 Kegiatan.kode.ilike('%%%s%%' % term))
                           
            rows = q.all()
            r = []
            for k in rows:
                d={}
                d['id']          = k[0]
                d['value']       = ''.join([k[1],'-',str(k[2])])
                d['kode']        = k[1]
                d['nama']        = k[3]
                r.append(d)
            print '****----****',r                
            return r

        elif url_dict['act']=='headofnama1':
            term = 'term' in params and params['term'] or ''
            q = DBSession.query(KegiatanSub.id, Kegiatan.kode, KegiatanSub.no_urut,
                                KegiatanSub.nama
                        ).join(Kegiatan
                        ).filter(KegiatanSub.unit_id ==ses['unit_id'],
                                 KegiatanSub.tahun_id==ses['tahun'],
                                 Kegiatan.kode!='0.00.00.10',
                                 Kegiatan.kode!='0.00.00.31',
                                 Kegiatan.kode!='0.00.00.32',
                                 KegiatanSub.nama.ilike('%%%s%%' % term))
                           
            rows = q.all()
            r = []
            for k in rows:
                d={}
                d['id']          = k[0]
                d['value']       = k[3]
                d['kode']        = ''.join([k[1],'-',str(k[2])])
                d['nama']        = k[3]
                r.append(d)
            print '****----****',r                
            return r
            

        elif url_dict['act']=='headofkode2':
            term = 'term' in params and params['term'] or ''
            unit_id    = 'unit_id' in params and params['unit_id'] or 0
            q = DBSession.query(KegiatanSub.id, Kegiatan.kode, KegiatanSub.no_urut,
                                KegiatanSub.nama
                      ).join(Kegiatan).filter(KegiatanSub.unit_id == unit_id,
                           KegiatanSub.tahun_id==ses['tahun'],
                           KegiatanSub.kegiatan_id==Kegiatan.id,
                           Kegiatan.kode.ilike('%%%s%%' % term))
                           
            rows = q.all()
            r = []
            for k in rows:
                d={}
                d['id']          = k[0]
                d['value']       = k[1]
                d['kode']        = k[1]
                d['nama']        = k[3]
                r.append(d)
            print '****----****',r                
            return r

        elif url_dict['act']=='headofnama2':
            term = 'term' in params and params['term'] or ''
            unit_id    = 'unit_id' in params and params['unit_id'] or 0
            q = DBSession.query(KegiatanSub.id, Kegiatan.kode, KegiatanSub.no_urut,
                                KegiatanSub.nama).join(Kegiatan).filter(
                      KegiatanSub.unit_id == unit_id,
                      KegiatanSub.tahun_id==ses['tahun'],
                      Kegiatan.kode=='0.00.00.10', 
                      Kegiatan.nama.ilike('%%%s%%' % term))
            rows = q.all()
            r = []
            for k in rows:
                d={}
                d['id']          = k[0]
                d['value']       = k[3]
                d['kode']        = ''.join([k[1],'-',str(k[2])])
                d['nama']        = k[3]
                r.append(d)    
            return r

        elif url_dict['act']=='headofkode3':
            term         = 'term' in params and params['term'] or ''
            ap_spd_id    = 'ap_spd_id' in params and params['ap_spd_id'] or 0
            unit_id    = 'unit_id' in params and params['unit_id'] or 0
            
            q = DBSession.query(KegiatanSub.id.label('kegiatan_sub_id'), Kegiatan.kode.label('kode'), KegiatanSub.nama.label('nama'),
                                func.sum(KegiatanItem.vol_4_1*KegiatanItem.vol_4_2*KegiatanItem.hsat_4).label('anggaran'),
                                func.sum(KegiatanItem.bln01+KegiatanItem.bln02+KegiatanItem.bln03).label('trw1'),
                                func.sum(KegiatanItem.bln04+KegiatanItem.bln05+KegiatanItem.bln06).label('trw2'),
                                func.sum(KegiatanItem.bln07+KegiatanItem.bln08+KegiatanItem.bln09).label('trw3'),
                                func.sum(KegiatanItem.bln10+KegiatanItem.bln11+KegiatanItem.bln12).label('trw4')
                        ).join(Kegiatan).join(KegiatanItem
                        ).filter(KegiatanSub.unit_id == unit_id,
                               KegiatanSub.tahun_id==ses['tahun'],
                               Kegiatan.kode.ilike('%%%s%%' % term)
                        ).group_by(KegiatanSub.id, Kegiatan.kode, KegiatanSub.nama)
                    
            rows = q.all()

            r = []
            for k in rows:
                d={}
                d['id']       = k[0]
                d['kode']     = k[1]
                d['nama']     = k[2]
                d['anggaran'] = k[3]
                spds  = DBSession.query(Spd).filter(Spd.id==ap_spd_id).first()
                spd_tanggal = spds.tanggal
                rows2 =  DBSession.query(func.sum(SpdItem.nominal).label('lalu')
                            ).join(Spd
                            ).filter(SpdItem.kegiatan_sub_id==d['id'],
                            Spd.tanggal<=spd_tanggal).first()
                        
                d['lalu']     = rows2.lalu or 0
                        
                d['nominal'] = spds.triwulan_id==1 and k[4] or\
                               spds.triwulan_id==2 and k[5] or\
                               spds.triwulan_id==3 and k[6] or\
                               spds.triwulan_id==4 and k[7] 
                if d['nominal']==0:
                   d['nominal'] = d['anggaran'] // 4
            
                d['value']       = d['kode']
                d['kode']        = d['kode']
                d['nama']        = d['nama']
                d['anggaran']    = "%d" % d['anggaran']
                d['lalu']        = "%d" % d['lalu']
                d['nominal']     = "%d" % d['nominal']
                r.append(d)
            print '****----****',r                
            return r

        elif url_dict['act']=='headofnama3':
            term         = 'term' in params and params['term'] or ''
            ap_spd_id    = 'ap_spd_id' in params and params['ap_spd_id'] or 0
            unit_id    = 'unit_id' in params and params['unit_id'] or 0
            q = DBSession.query(KegiatanSub.id.label('kegiatan_sub_id'), Kegiatan.kode.label('kode'), KegiatanSub.nama.label('nama'),
                                func.sum(KegiatanItem.vol_4_1*KegiatanItem.vol_4_2*KegiatanItem.hsat_4).label('anggaran'),
                                func.sum(KegiatanItem.bln01+KegiatanItem.bln02+KegiatanItem.bln03).label('trw1'),
                                func.sum(KegiatanItem.bln04+KegiatanItem.bln05+KegiatanItem.bln06).label('trw2'),
                                func.sum(KegiatanItem.bln07+KegiatanItem.bln08+KegiatanItem.bln09).label('trw3'),
                                func.sum(KegiatanItem.bln10+KegiatanItem.bln11+KegiatanItem.bln12).label('trw4')
                        ).join(Kegiatan).join(KegiatanItem
                        ).filter(KegiatanSub.unit_id == unit_id,
                               KegiatanSub.tahun_id==ses['tahun'],
                               KegiatanSub.nama.ilike('%%%s%%' % term)
                        ).group_by(KegiatanSub.id, Kegiatan.kode, KegiatanSub.nama)
                    
            rows = q.all()

            r = []
            for k in rows:
                d={}
                d['id']       = k[0]
                d['kode']     = k[1]
                d['nama']     = k[2]
                d['anggaran'] = k[3]
                spds  = DBSession.query(Spd).filter(Spd.id==ap_spd_id).first()
                spd_tanggal = spds.tanggal
                rows2 =  DBSession.query(func.sum(SpdItem.nominal).label('lalu')
                            ).join(Spd
                            ).filter(SpdItem.kegiatan_sub_id==d['id'],
                            Spd.tanggal<=spd_tanggal).first()
                        
                d['lalu']     = rows2.lalu or 0
                        
                d['nominal'] = spds.triwulan_id==1 and k[4] or\
                               spds.triwulan_id==2 and k[5] or\
                               spds.triwulan_id==3 and k[6] or\
                               spds.triwulan_id==4 and k[7] 
                if d['nominal']==0:
                   d['nominal'] = d['anggaran'] // 4
            
                d['value']       = d['nama']
                d['kode']        = d['kode']
                d['nama']        = d['nama']
                d['anggaran']    = "%d" % d['anggaran']
                d['lalu']        = "%d" % d['lalu']
                d['nominal']     = "%d" % d['nominal']
                r.append(d)
            print '****----****',r                
            return r
            
            
    ###############                    
    # Tambah  Data#
    ###############    
    @view_config(route_name='ag-kegiatan-sub-add-fast', renderer='json',
                 permission='add')
    def ak_kegiatan_sub_add_fast(self):
        ses = self.request.session
        req = self.request
        params = req.params
        url_dict = req.matchdict
        kegiatan_kd = 'kegiatan_kd' in params and params['kegiatan_kd'] or None
        
        kegiatan = DBSession.query(Kegiatan).filter(Kegiatan.kode==kegiatan_kd).first()
        if not kegiatan:
            return {"success": False, 'msg':'Kegiatan tidak ditemukan'}
            
        row = KegiatanSub()
        row.kegiatan_id = kegiatan.id
        row.nama  = kegiatan.nama
        row.created = datetime.now()
        row.tahun_id = ses['tahun']
        row.unit_id = ses['unit_id']
        row.no_urut = 1
        try:
          DBSession.add(row)
          DBSession.flush()
          return {"success": True, 'id': row.id, "msg":'Success Tambah Kegiatan'}
        except:
            return {'success':False, 'msg':'Gagal Tambah Kegiatan'}
            

#######    
# Add #
#######
def form_validator(form, value):
    def err_kegiatan():
        raise colander.Invalid(form,
            'Kegiatan dengan no urut tersebut sudah ada')
                
class AddSchema(colander.Schema):
    kegiatan_widget = widget.AutocompleteInputWidget(
            size=60,
            values = '/kegiatan/act/headofkode',
            min_length=1)
    kegiatannm_widget = widget.AutocompleteInputWidget(
            size=60,
            values = '/kegiatan/act/headofnama',
            min_length=1)
            
    tahun_id         = colander.SchemaNode(
                          colander.String(),
                          oid = "tahun_id",
                          title="Tahun")
    unit_id          = colander.SchemaNode(
                          colander.String(),
                          oid = "unit_id")
    unit_kd          = colander.SchemaNode(
                          colander.String(),
                          title="SKPD",
                          oid = "unit_kd")
    unit_nm          = colander.SchemaNode(
                          colander.String(),
                          oid = "unit_nm")

                          
    kegiatan_id      = colander.SchemaNode(
                          colander.Integer(),
                          oid="kegiatan_id")
                          
    kode             = colander.SchemaNode(
                          colander.String(),
                          widget = kegiatan_widget,
                          oid="kode",
                          title="Kegiatan")
                          
    kegiatan_nm          = colander.SchemaNode(
                          colander.String(),
                          widget = kegiatannm_widget,
                          oid="kegiatan_nm",)

    no_urut          = colander.SchemaNode(
                          colander.Integer(),
                          missing=colander.drop,
                          title="No. Item")
                          
    nama             = colander.SchemaNode(
                          colander.String(),
                          title="Uraian",
                          oid = "nama")

    lokasi           = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop)
                          
    sifat            = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop)
    bagian           = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop)
    kondisi          = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop)
    waktu            = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title = 'Waktu Pelaks.')
    amt_lalu         = colander.SchemaNode(
                          colander.Integer(),
                          default = 0,
                          missing=colander.drop,
                          title = 'Anggaran Lalu')
    amt_yad          = colander.SchemaNode(
                          colander.Integer(),
                          default = 0,
                          missing=colander.drop,
                          title = 'Anggaran YAD')
    sdana            = colander.SchemaNode(
                          colander.String(),
                          widget=widget.SelectWidget(values=SDANA),
                          missing=colander.drop,
                          title = 'Sumber Dana')
    ttd1nip          = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="Pejabat 1")
    ttd2nip          = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="Pejabat 2")
    notes            = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="Catatan")
    target           = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,)
    sasaran          = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,)
    perubahan        = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="Alasan Perubahan")
    ppa              = colander.SchemaNode(
                          colander.Integer(),
                          default = 0,
                          missing=colander.drop,
                          title = 'PPA',)
    ppas             = colander.SchemaNode(
                          colander.Integer(),
                          default = 0,
                          missing=colander.drop,
                          title = 'PPAS',)
    ppa_rev          = colander.SchemaNode(
                          colander.Integer(),
                          default = 0,
                          missing=colander.drop,
                          title = 'Perubahan PPA',)
    ppas_rev         = colander.SchemaNode(
                          colander.Integer(),
                          default = 0,
                          missing=colander.drop,
                          title = 'Perubahan PPAS',)
    volume           = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,)
    tgl_bahas_1      = colander.SchemaNode(
                          colander.Date(),
                          missing=colander.drop,
                          title="Tanggal RKA")
    tgl_bahas_2      = colander.SchemaNode(
                          colander.Date(),
                          missing=colander.drop,
                          title="Tanggal DPA")
    tgl_bahas_3      = colander.SchemaNode(
                          colander.Date(),
                          missing=colander.drop,
                          title="Tanggal RDPPA")
    tgl_bahas_4      = colander.SchemaNode(
                          colander.Date(),
                          missing=colander.drop,
                          title="Tanggal DPPA")
    catatan_1        = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="Catatan")
    catatan_2        = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="Catatan")
    catatan_3        = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="Catatan")
    catatan_4        = colander.SchemaNode(
                          colander.String(),
                          missing=colander.drop,
                          title="Catatan")
    pending          = colander.SchemaNode(
                          colander.Integer(),
                          default = 0,
                          missing=colander.drop,
                          )
    tahunke          = colander.SchemaNode(
                          colander.Integer(),
                          missing=colander.drop,
                          )
    h0yl             = colander.SchemaNode(
                          colander.Integer(),
                          default = 0,
                          missing=colander.drop,
                          title = "Anggaran 1"
                          )
    p0yl             = colander.SchemaNode(
                          colander.Integer(),
                          default = 0,
                          missing=colander.drop,
                          title = "Perubahan 1",)
    r0yl             = colander.SchemaNode(
                          colander.Integer(),
                          default = 0,
                          missing=colander.drop,
                          title = "Realisasi 1",)
    h1yl             = colander.SchemaNode(
                          colander.Integer(),
                          default = 0,
                          missing=colander.drop,
                          title = "Anggaran 1",)
    p1yl             = colander.SchemaNode(
                          colander.Integer(),
                          default = 0,
                          missing=colander.drop,
                          title = "Perubahan 2",)
    r1yl             = colander.SchemaNode(
                          colander.Integer(),
                          default = 0,
                          missing=colander.drop,
                          title = "Realisasi 2",)
    h2yl             = colander.SchemaNode(
                          colander.Integer(),
                          default = 0,
                          missing=colander.drop,
                          title = "Anggaran 3",)
    p2yl             = colander.SchemaNode(
                          colander.Integer(),
                          default = 0,
                          missing=colander.drop,
                          title = "Perubahan 3",)
    r2yl             = colander.SchemaNode(
                          colander.Integer(),
                          default = 0,
                          missing=colander.drop,
                          title = "Realisasi 3",)
    disabled         = colander.SchemaNode(
                          colander.Boolean(),
                          default = 0,
                          missing=colander.drop,)
    approval         = colander.SchemaNode(
                          colander.Integer(),
                          default = 0,
                          missing=colander.drop,
                          )
                    
class EditSchema(AddSchema):
    id             = colander.SchemaNode(
                          colander.Integer(),)

def get_form(request, class_form):
    schema = class_form(validator=form_validator)
    schema = schema.bind(sdana=SDANA)
    schema.request = request
    return Form(schema, buttons=('simpan','batal'))
    
def save(values, user, row=None):
    if not row:
        row = KegiatanSub()
        row.created = datetime.now()
        row.create_uid = user.id
        
    row.from_dict(values)
    
    # isikan user update dan tanggal update
    row.updated = datetime.now()
    row.update_uid = user.id

    if not row.no_urut:
          row.no_urut = KegiatanSub.max_no_urut(row.tahun_id,row.unit_id,row.kegiatan_id)+1;
    DBSession.add(row)
    DBSession.flush()
    return row
                                      
def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(values, request.user, row)
    request.session.flash('Kegiatan sudah disimpan.')
        
def route_list(request):
    return HTTPFound(location=request.route_url('ag-bl'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
@view_config(route_name='ag-bl-add', renderer='templates/ag-bl/add.pt',
             permission='add')
def view_add(request):
    form = get_form(request, AddSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            controls_dicted = dict(controls)
            #return dict(form=form.render(appstruct=controls_dicted))
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                return dict(form=form)
                #request.session[SESS_ADD_FAILED] = e.render()               
                #return HTTPFound(location=request.route_url('ag-bl-add'))
            save_request(controls_dicted, request)
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        del request.session[SESS_ADD_FAILED]
        #return session_failed(request, SESS_ADD_FAILED)
    return dict(form=form)

########
# Edit #
########
def query_id(request):
    return DBSession.query(KegiatanSub).filter(KegiatanSub.id==request.matchdict['id'])
    
def id_not_found(request):    
    msg = 'User ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='ag-bl-edit', renderer='templates/ag-bl/add.pt',
             permission='edit')
def view_edit(request):
    row = query_id(request).first()
    if not row:
        return id_not_found(request)
        
    ####### dibuat kondisi agar posted sesuai kebutuhan yang telah ditentukan group
    ses = request.session
    req = request
    params   = req.params
    url_dict = req.matchdict
    
    form = get_form(request, EditSchema)
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
            
            ## Cek Grup
            if grps_kd == '2' or grps_kd == '3' or grps_kd == '4' :
                request.session.flash('Anda tidak mempunyai hak akses untuk mengupdate data', 'error')
                return route_list(request)
                
            if row.disabled==1 and row.approval==4 and grps_kd<'4':
                request.session.flash('Data tidak dapat diupdate karena sudah diposting BPKAD', 'error')
                return route_list(request)
            if row.approval==3 and grps_kd<'3':
                request.session.flash('Data tidak dapat diupdate karena sudah diposting Dispenda', 'error')
                return route_list(request)
            if row.approval==2  and grps_kd<'2':
                request.session.flash('Data tidak dapat diupdate karena sudah diposting Bappeda', 'error')
                return route_list(request)
                
            controls = request.POST.items()
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                print e.render()
                return dict(form=form)
                #request.session[SESS_EDIT_FAILED] = e.render()               
                #return HTTPFound(location=request.route_url('ag-bl-edit',
                #                  id=row.id))
            save_request(dict(controls), request, row)
        return route_list(request)
    elif SESS_EDIT_FAILED in request.session:
        del request.session[SESS_EDIT_FAILED]
        return dict(form=form)
    values = row.to_dict() #dict(zip(row.keys(), row))
    values['kegiatan_nm']=row.kegiatans.nama
    form.set_appstruct(values) 
    return dict(form=form)

##########
# Delete #
##########    
@view_config(route_name='ag-bl-delete', renderer='templates/ag-bl/delete.pt',
             permission='delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    if not row:
        return id_not_found(request)
    # Cek posting
    #if row.disabled:
    #    request.session.flash('Data tidak dapat dihapus karena sudah Posting', 'error')
    #    return route_list(request)

    ses = request.session
    ## variabel ag_step_id
    ag_step_id = ses['ag_step_id']        
            
    if row.disabled == 1 and row.approval==4:
        request.session.flash('Data tidak dapat dihapus karena sudah Posting', 'error')
        return route_list1(request,row.id)
    if row.approval==3:
        request.session.flash('Data tidak dapat dihapus karena sudah di Approval oleh Dispenda', 'error')
        return route_list1(request,row.id)
    if row.approval==2:
        request.session.flash('Data tidak dapat dihapus karena sudah di Approval oleh Bappeda', 'error')
        return route_list1(request,row.id)
    
    form = Form(colander.Schema(), buttons=('hapus','cancel'))
    values= {}
    if request.POST:
        if 'hapus' in request.POST:
            msg = '%s Kode %s  No. %s %s sudah dihapus.' % (request.title, row.kode, row.no_urut, row.nama)
            DBSession.query(KegiatanSub).filter(KegiatanSub.id==request.matchdict['id']).delete()
            DBSession.flush()
            request.session.flash(msg)
        return route_list(request)
    return dict(row=row,
                 form=form.render())

###########
# Posting #
###########   

def route_list1(request, kegiatan_sub_id):
    kegiatan_sub_id
    q = DBSession.query(Kegiatan.kode.label('kegiatan_kd')
    ).filter(Kegiatan.id==KegiatanSub.kegiatan_id, 
    KegiatanSub.id==kegiatan_sub_id)
    print "-----------------------------------", kegiatan_sub_id
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
    return HTTPFound(location=request.route_url('ag-bl'))

def save_request2(request, row=None):
    row = KegiatanSub()
    #request.session.flash('Kegiatan sudah diposting.')
    return row
    
@view_config(route_name='ag-bl-posting', renderer='templates/ag-bl/posting.pt', permission='posting')
def view_edit_posting(request):
    q = query_id(request)
    row = q.first()
    
    if not row:
        return id_not_found(request)
    #if row.disabled:
    #    request.session.flash('Data sudah diposting', 'error')
    #    return route_list1(request,row.id)

    ####### dibuat kondisi agar posted sesuai kebutuhan yang telah ditentukan group
    ses = request.session
    req = request
    params   = req.params
    url_dict = req.matchdict
    
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
    
    print "----------------------------------->>>>",grp
            
    ## variabel ag_step_id
    #ag_step_id = ses['ag_step_id']
    #print'********************ag_step_id********************',ag_step_id
    
    ## kondisi group ppkd (semua unit)
    #grp = DBSession.query(func.lower(Group.group_name)).filter(UserGroup.user_id==req.user.id, Group.id==UserGroup.group_id).first()
    #grps = '%s' % grp
    #print'********************group********************',grps
    
    ## kondisi saat group skpd
    if grps_kd == '0' :
       request.session.flash('User tidak punya hak akses posting kegiatan', 'error')
       return route_list1(request,row.id)
    
    ## kondisi saat group skpd pempinan
    elif grps_kd == '1':
        if row.approval > 0 :
            request.session.flash('Data sudah di approval/posting', 'error')
            return route_list1(request,row.id)

    ## kondisi saat group bappeda
    elif grps_kd == '2':
        if not row.approval or row.approval<1:
            request.session.flash('Data tidak bisa diposting, karena harus diposting terlebih dahulu di Kasubag Perencanaan SKPD', 'error')
            return route_list1(request,row.id)
        if row.approval > 2:
            request.session.flash('Data sudah di approval/posting', 'error')
            return route_list1(request,row.id)

    ## kondisi saat group dispenda
    elif grps_kd == '3':
        if not row.approval or row.approval<2:
            request.session.flash('Data tidak bisa diposting, karena harus diposting terlebih dahulu di Kasubag Perencanaan SKPD/di Kabid BAPPEDA', 'error')
            return route_list1(request,row.id)
        if row.approval > 3:
            request.session.flash('Data sudah di approval/posting', 'error')
            return route_list1(request,row.id)
                
    ## kondisi saat group bpkad
    elif grps_kd == '4':
        if row.kode == '0.00.00.10' :
            if not row.approval or row.approval<3:
                request.session.flash('Data tidak bisa diposting, karena harus diposting terlebih dahulu di Kasubag Perencanaan SKPD/di Kabid BAPPEDA/di Kabid DISPENDA', 'error')
                return route_list1(request,row.id)
        else :
            if not row.approval or row.approval<2:
                request.session.flash('Data tidak bisa diposting, karena harus diposting terlebih dahulu di Kasubag Perencanaan SKPD/di Kabid BAPPEDA', 'error')
                return route_list1(request,row.id)
        if row.approval > 4:
            request.session.flash('Data sudah di approval/posting', 'error')
            return route_list1(request,row.id)
    
    form = Form(colander.Schema(), buttons=('posting','cancel'))
    
    if request.POST:
        ## kondisi simpan group kasubag perencanaan skpd
        if grps_kd == '1':
            if 'posting' in request.POST: 
                row.approval=1
                save_request2(row)
            return route_list1(request,row.id)
                
        ## kondisi simpan group bappeda
        if grps_kd == '2':
            if 'posting' in request.POST: 
                row.approval=2
                save_request2(row)
            return route_list1(request,row.id)
                
        ## kondisi simpan group dispenda
        if grps_kd == '3':
            if 'posting' in request.POST: 
                row.approval=3
                save_request2(row)
            return route_list1(request,row.id)

        ## kondisi simpan group bpkad
        if grps_kd == '4':
            if 'posting' in request.POST: 
                row.disabled=1
                row.approval=4
                save_request2(row)
            return route_list1(request,row.id)

        ## kondisi simpan group Admin
        if grps_kd == '5' or grps_kd == "None" :
            if 'posting' in request.POST: 
                row.disabled=1
                row.approval=4
                save_request2(row)
            return route_list1(request,row.id)
        
    return dict(row=row, form=form.render())                       
        

#############
# UnPosting #
#############

def save_request3(request, row=None):
    row = KegiatanSub()
    #request.session.flash('Kegiatan sudah di UnPosting.')
    return row
    
@view_config(route_name='ag-bl-unposting', renderer='templates/ag-bl/unposting.pt', permission='unposting') 
def view_edit_unposting(request):
    q = query_id(request)
    row = q.first()
    if not row:
        return id_not_found(request)

    ####### dibuat kondisi agar posted sesuai kebutuhan yang telah ditentukan group
    ses = request.session
    req = request
    params   = req.params
    url_dict = req.matchdict
    
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
    
    ## kondisi unposting group skpd
    if grps_kd == '0' :
       request.session.flash('User tidak punya hak akses unposting kegiatan', 'error')
       return route_list1(request,row.id)
            
    ## kondisi unposting group kasubag perencanaan skpd
    elif grps_kd == '1':
        if not row.approval or row.approval<1:
            request.session.flash('Data tidak dapat di Unposting, karena belum diposting.', 'error')
            return route_list1(request, row.id)
        elif row.approval>1 :
            request.session.flash('Data sudah di approval/posting', 'error')
            return route_list1(request, row.id)

    ## kondisi unposting group ppkd bappeda
    elif grps_kd == '2':
        if not row.approval or row.approval<2 :
            request.session.flash('Data tidak dapat di Unposting, karena belum diposting.', 'error')
            return route_list1(request, row.id)
        elif row.approval>2 :
            request.session.flash('Data tidak dapat di Unposting, karena sudah di approval/posting', 'error')
            return route_list1(request, row.id)
            
    ## kondisi unposting group ppkd dispenda
    elif grps_kd == '3':
        if not row.approval or row.approval<3 :
            request.session.flash('Data tidak dapat di Unposting, karena belum diposting.', 'error')
            return route_list1(request, row.id)
        elif row.approval>3 :
            request.session.flash('Data tidak dapat di Unposting, karena sudah di approval/posting', 'error')
            return route_list1(request, row.id)
    
    ## kondisi unposting group ppkd bpkad
    elif grps_kd == '4':
        if not row.approval or row.approval<4 :
            request.session.flash('Data tidak dapat di Unposting, karena belum diposting.', 'error')
            return route_list1(request, row.id)

    ## kondisi unposting group admin
    elif grps_kd == '5':
        if not row.disabled or row.disabled==0:
            request.session.flash('Data tidak dapat di Unposting, karena belum diposting.', 'error')
            return route_list1(request, row.id)

    form = Form(colander.Schema(), buttons=('unposting','cancel'))
    
    if request.POST:
        ## kondisi simpan group kasubag perencanaan skpd
        if grps_kd == '1':
            if 'unposting' in request.POST: 
                row.approval=0
                save_request3(row)
            return route_list1(request,row.id)
                
        ## kondisi simpan group ppkd bappeda
        elif grps_kd == '2':
            if 'unposting' in request.POST: 
                row.approval=1
                save_request3(row)
            return route_list1(request,row.id)

        ## kondisi simpan group ppkd dispenda
        elif grps_kd == '3':
            if 'unposting' in request.POST: 
                row.approval=2
                save_request3(row)
            return route_list1(request,row.id)
                
        ## kondisi simpan group ppkd bpkad
        elif grps_kd == '4':
            if 'unposting' in request.POST: 
                row.approval=0
                row.disabled=0
                save_request3(row)
            return route_list1(request,row.id)
                
        ## kondisi simpan group Admin
        elif grps_kd == '5' or grps_kd == "None" :
            if 'unposting' in request.POST: 
                row.approval=0
                row.disabled=0
                save_request3(row)
            return route_list1(request,row.id)
        
    return dict(row=row, form=form.render())                       
            
            