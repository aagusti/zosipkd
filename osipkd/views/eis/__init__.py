from pyramid.view import (
    view_config,
    )
from pyramid.httpexceptions import (
    HTTPFound,
    )
from osipkd.views.base_view import BaseViews
from osipkd.models import DBSession
from osipkd.models.eis import Eis
from osipkd.tools import row2dict
########
# APP Home #
########
class eis(BaseViews):
    def cek_value(self,value,devider,simbol):
        if value<devider:
            return "{0:,.0f}".format(value)
        else:
            return "{0:,.2f} {1}".format(value/devider,simbol) 
        
    @view_config(route_name='eis', renderer='templates/home.pt')
    def view_app(self):
        tahun = self.session['tahun']
        rows = DBSession.query(Eis).filter(Eis.tahun==tahun, Eis.disabled==0).order_by(Eis.order_id)
        datas = []
        for row in rows:
            row_dicted = row2dict(row)
            amt_hari   =  float(row_dicted['amt_hari'])
            amt_minggu =  float(row_dicted['amt_minggu'])+amt_hari
            amt_bulan  =  float(row_dicted['amt_bulan'])+amt_hari
            amt_tahun  =  float(row_dicted['amt_tahun'])+amt_bulan
            
            row_dicted['amt_tahun'] = self.cek_value(amt_tahun,1000000000, 'M')
            row_dicted['amt_bulan'] = self.cek_value(amt_bulan,1000000000, 'M')
            row_dicted['amt_minggu'] = self.cek_value(amt_minggu,1000000000, 'M')
            row_dicted['amt_hari'] = self.cek_value(amt_hari,1000000000, 'M')
            datas.append(row_dicted)
                
        print datas
        if not datas:
            datas = {}
        return dict(project='EIS', datas=datas)#, datas=Eis.sum_order_id('2014'))
        