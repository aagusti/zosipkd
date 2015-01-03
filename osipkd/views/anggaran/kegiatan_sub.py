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
    
from datatables import ColumnDT, DataTables
from osipkd.views.base_view import BaseViews

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

class view_ak_jurnal(BaseViews):
    ##########                    
    # Action #
    ##########    
       
    @view_config(route_name='ag-kegiatan-sub-act', renderer='json',
                 permission='read')
    def ak_kegiatan_sub_act(self):
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
                           Kegiatan.kode.ilike('%s%%' % term))
                           
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
                      Kegiatan.nama.ilike('%s%%' % term))
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
            