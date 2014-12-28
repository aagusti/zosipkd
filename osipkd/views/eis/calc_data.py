#!/usr/bin/python

import json
from datetime import datetime, date
from pyramid.view import (view_config,)
from pyramid.httpexceptions import (HTTPFound,)
from osipkd.views.base_view import BaseViews
from osipkd.models import DBSession
from osipkd.models.eis import Eis, Chart, ChartItem, Slide,ARPaymentDetail as AR
from osipkd.models.pemda_model import Rekening as R

from osipkd.tools import row2dict
from sqlalchemy import func

"""    tahun = Column(Integer)
    amount = Column(BigInteger)
    ref_kode = Column(String(32))
    ref_nama = Column(String(64))
    tanggal = Column(DateTime(timezone=True), nullable=True)
    kecamatan_kd = Column(String(32))
    kecamatan_nm = Column(String(64))
    kelurahan_kd = Column(String(32))
    kelurahan_nm = Column(String(64))
    is_kota      = Column(SmallInteger)
    sumber_data  = Column(String(32)) #Manual, PBB, BPHTB, PAD
    sumber_id    = Column(SmallInteger)#1, 2, 3, 4
"""
def eis_update_grid(row):
    pass
    
def eis_update_chart_item(row):
    pass
    
class eis_calc(BaseViews):
    @view_config(route_name='eis-calc-all', renderer='json')
    def eis_all(self):
        #UPDATE GRID
        req = self.request
        ses = self.session
        tahun = ses['tahun']
        
        eis_date  = datetime.now()
        eis_year  = eis_date.year
        eis_month = eis_date.month
        eis_day   = eis_date.day

        eis_year  = eis_date.year
        eis_month = 2
        eis_day   = 8

        eis_date  = date(eis_year,eis_month,eis_day) 
        eis_week   = eis_date.isocalendar()[1]
        
        rows = DBSession.query(Eis).filter(Eis.tahun==tahun).all()
        
        for row in rows:
            row_data = DBSession.query(func.sum(AR.amount).label('s')).\
                          filter(AR.tahun==tahun, AR.bulan < eis_month,
                                 AR.kode.ilike("%s%%" % row.kode)).scalar()
            if row_data:
                row.amt_tahun = row_data

            row_data = DBSession.query(func.sum(AR.amount).label('s')).\
                          filter(AR.tahun==tahun, AR.bulan == eis_month,
                                 AR.hari < eis_day,
                                 AR.kode.ilike("%s%%" % row.kode)).scalar()
            if row_data:
                row.amt_bulan = row_data

            row_data = DBSession.query(func.sum(AR.amount).label('s')).\
                          filter(AR.tahun==tahun, AR.bulan == eis_month,
                                 AR.hari == eis_day,
                                 AR.kode.ilike("%s%%" % row.kode)).scalar()
            if row_data:
                row.amt_hari = row_data
            #update mingguan
            row_data = DBSession.query(func.sum(AR.amount).label('s')).\
                          filter(AR.tahun==tahun, AR.bulan == eis_month,
                                 AR.minggu == eis_week,
                                 AR.kode.ilike("%s%%" % row.kode)).scalar()
            if row_data:
                row.amt_minggu = row_data - row.amt_hari
        DBSession.flush()
        return {"minggu":eis_week}
                
        