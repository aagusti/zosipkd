import os
import unittest
import os.path
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

from pyjasper import (JasperGenerator)
from pyjasper import (JasperGeneratorWithSubreport)
import xml.etree.ElementTree as ET
from pyramid.path import AssetResolver

from osipkd.models.base_model import *
from osipkd.models.pemda_model import *
from osipkd.models.apbd import * 
from osipkd.models.apbd_anggaran import * 


"""
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPForbidden
from pyramid.httpexceptions import HTTPNotFound
from pyramid.view import view_config
from pyramid.security import remember
from pyramid.security import forget
from pyramid.security import has_permission
from sqlalchemy import *
from sqlalchemy import distinct
from sqlalchemy.sql.functions import concat
from sqlalchemy.exc import DBAPIError
from osipkd.views.base_view import *
from datetime import datetime
from pyramid.renderers import render_to_response

#from anggaran import AnggaranBaseViews
"""
def get_rpath(filename):
    a = AssetResolver('osipkd')
    resolver = a.resolve(''.join(['reports/',filename]))
    return resolver.abspath()
    
class r001Generator(JasperGenerator):
    """Jasper-Generator for Greetingcards"""
    def __init__(self):
        super(r001Generator, self).__init__()
        self.reportname = get_rpath('apbd/R0001.jrxml')
        self.xpath = '/apbd/master/urusan'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        """Generates the XML File used by Jasperreports"""
        #return open('/home/aagusti/env/osipkd/osipkd/reports/apbd/xml/R001.xml').read()
        #ET.SubElement(self.root, 'generator').text = __revision__
        xml_a  =  ET.SubElement(self.root, 'master')
        for kode, uraian in tobegreeted:
            xml_greeting  =  ET.SubElement(xml_a, 'urusan')
            ET.SubElement(xml_greeting, "kode").text = unicode(kode)
            ET.SubElement(xml_greeting, "uraian").text = unicode(uraian)
        return self.root

class r002Generator(JasperGenerator):
    def __init__(self):
        super(r002Generator, self).__init__()
        self.reportname = get_rpath('apbd/R0002.jrxml')
        self.xpath = '/apbd/master/unit'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        xml_a  =  ET.SubElement(self.root, 'master')
        for urusankd, kode, uraian, kategori, singkat in tobegreeted:
            xml_greeting  =  ET.SubElement(xml_a, 'unit')
            ET.SubElement(xml_greeting, "urusankd").text = unicode(urusankd)
            ET.SubElement(xml_greeting, "kode").text = unicode(kode)
            ET.SubElement(xml_greeting, "uraian").text = unicode(uraian)
            ET.SubElement(xml_greeting, "kategori").text = unicode(kategori)
            ET.SubElement(xml_greeting, "singkat").text = unicode(singkat)
        return self.root

class r003Generator(JasperGenerator):
    def __init__(self):
        super(r003Generator, self).__init__()
        self.reportname = get_rpath('apbd/R0003.jrxml')
        self.xpath = '/apbd/master/program'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        xml_a  =  ET.SubElement(self.root, 'master')
        for kode, uraian, kegiatankd, kegiatannm in tobegreeted:
            xml_greeting  =  ET.SubElement(xml_a, 'program')
            ET.SubElement(xml_greeting, "kode").text = unicode(kode)
            ET.SubElement(xml_greeting, "uraian").text = unicode(uraian)
            ET.SubElement(xml_greeting, "kegiatankd").text = unicode(kegiatankd)
            ET.SubElement(xml_greeting, "kegiatannm").text = unicode(kegiatannm)
        return self.root

class r041Generator(JasperGenerator):
    def __init__(self):
        super(r041Generator, self).__init__()
        self.reportname = get_rpath('apbd/R0041.jrxml')
        self.xpath = '/apbd/master/rekaset'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        xml_a  =  ET.SubElement(self.root, 'master')
        for kode, uraian, level_id in tobegreeted:
            xml_greeting  =  ET.SubElement(xml_a, 'rekaset')
            ET.SubElement(xml_greeting, "kode").text = unicode(kode)
            ET.SubElement(xml_greeting, "uraian").text = unicode(uraian)
            ET.SubElement(xml_greeting, "level_id").text = unicode(level_id)
        return self.root

class r042Generator(JasperGenerator):
    def __init__(self):
        super(r042Generator, self).__init__()
        self.reportname = get_rpath('apbd/R0042.jrxml')
        self.xpath = '/apbd/master/rekangg'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        xml_a  =  ET.SubElement(self.root, 'master')
        for kode, uraian, level_id in tobegreeted:
            xml_greeting  =  ET.SubElement(xml_a, 'rekangg')
            ET.SubElement(xml_greeting, "kode").text = unicode(kode)
            ET.SubElement(xml_greeting, "uraian").text = unicode(uraian)
            ET.SubElement(xml_greeting, "level_id").text = unicode(level_id)
        return self.root

class r005Generator(JasperGenerator):
    def __init__(self):
        super(r005Generator, self).__init__()
        self.reportname = get_rpath('apbd/R0005.jrxml')
        self.xpath = '/apbd/master/pegawai'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        xml_a  =  ET.SubElement(self.root, 'master')
        for kode, uraian in tobegreeted:
            xml_greeting  =  ET.SubElement(xml_a, 'pegawai')
            ET.SubElement(xml_greeting, "kode").text = unicode(kode)
            ET.SubElement(xml_greeting, "uraian").text = unicode(uraian)
        return self.root
        
class r009Generator(JasperGenerator):
    def __init__(self):
        super(r009Generator, self).__init__()
        self.reportname = get_rpath('apbd/R0009.jrxml')
        self.xpath = '/apbd/master/fungsi'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        xml_a  =  ET.SubElement(self.root, 'master')
        for kode, uraian in tobegreeted:
            xml_greeting  =  ET.SubElement(xml_a, 'fungsi')
            ET.SubElement(xml_greeting, "kode").text = unicode(kode)
            ET.SubElement(xml_greeting, "uraian").text = unicode(uraian)
        return self.root

class r010Generator(JasperGenerator):
    def __init__(self):
        super(r010Generator, self).__init__()
        self.reportname = get_rpath('apbd/R0010.jrxml')
        self.xpath = '/apbd/master/jabatan'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        xml_a  =  ET.SubElement(self.root, 'master')
        for kode, uraian in tobegreeted:
            xml_greeting  =  ET.SubElement(xml_a, 'jabatan')
            ET.SubElement(xml_greeting, "kode").text = unicode(kode)
            ET.SubElement(xml_greeting, "uraian").text = unicode(uraian)
        return self.root

class r011Generator(JasperGenerator):
    def __init__(self):
        super(r011Generator, self).__init__()
        self.reportname = get_rpath('apbd/R0011.jrxml')
        self.xpath = '/apbd/master/pejabat'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        xml_a  =  ET.SubElement(self.root, 'master')
        for kode, uraian, jabatan, skpd, mulai, selesai in tobegreeted:
            xml_greeting  =  ET.SubElement(xml_a, 'pejabat')
            ET.SubElement(xml_greeting, "kode").text = unicode(kode)
            ET.SubElement(xml_greeting, "uraian").text = unicode(uraian)
            ET.SubElement(xml_greeting, "jabatan").text = unicode(jabatan)
            ET.SubElement(xml_greeting, "skpd").text = unicode(skpd)
            ET.SubElement(xml_greeting, "mulai").text = unicode(mulai)
            ET.SubElement(xml_greeting, "selesai").text = unicode(selesai)
        return self.root
        
class r012Generator(JasperGenerator):
    def __init__(self):
        super(r012Generator, self).__init__()
        self.reportname = get_rpath('apbd/R0012.jrxml')
        self.xpath = '/apbd/master/tahun'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        xml_a  =  ET.SubElement(self.root, 'master')
        for tahun, status_apbd, tanggal_1, tanggal_2, tanggal_3, tanggal_4 in tobegreeted:
            xml_greeting  =  ET.SubElement(xml_a, 'tahun')
            ET.SubElement(xml_greeting, "tahun").text = unicode(tahun)
            ET.SubElement(xml_greeting, "status_apbd").text = unicode(status_apbd)
            ET.SubElement(xml_greeting, "tanggal_1").text = unicode(tanggal_1)
            ET.SubElement(xml_greeting, "tanggal_2").text = unicode(tanggal_2)
            ET.SubElement(xml_greeting, "tanggal_3").text = unicode(tanggal_3)
            ET.SubElement(xml_greeting, "tanggal_4").text = unicode(tanggal_4)
        return self.root  

class r100Generator(JasperGenerator):
    def __init__(self):
        super(r100Generator, self).__init__()
        self.reportname = get_rpath('apbd/R1000.jrxml')
        self.xpath = '/apbd/rka/rekening'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        xml_a  =  ET.SubElement(self.root, 'rka')

        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(xml_a, 'rekening')
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "level_id").text = unicode(row.level_id)
            ET.SubElement(xml_greeting, "defsign").text = unicode(row.defsign)
            ET.SubElement(xml_greeting, "urusan_kd").text = row.urusan_kd
            ET.SubElement(xml_greeting, "urusan_nm").text = row.urusan_nm
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "jumlah1").text = unicode(row.jumlah1)
            ET.SubElement(xml_greeting, "jumlah2").text = unicode(row.jumlah2)
            ET.SubElement(xml_greeting, "jumlah3").text = unicode(row.jumlah3)
            ET.SubElement(xml_greeting, "jumlah4").text = unicode(row.jumlah4)
        return self.root

class r101Generator(JasperGenerator):
    def __init__(self):
        super(r101Generator, self).__init__()
        self.reportname = get_rpath('apbd/R1100.jrxml')
        self.xpath = '/apbd/rka/rekening'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        xml_a  =  ET.SubElement(self.root, 'rka')
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(xml_a, 'rekening')
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "level_id").text = unicode(row.level_id)
            ET.SubElement(xml_greeting, "defsign").text = unicode(row.defsign)
            ET.SubElement(xml_greeting, "urusan_kd").text = row.urusan_kd
            ET.SubElement(xml_greeting, "urusan_nm").text = row.urusan_nm
            ET.SubElement(xml_greeting, "rek_kd1").text = row.rek_kd1
            ET.SubElement(xml_greeting, "rek_kd2").text = row.rek_kd2
            ET.SubElement(xml_greeting, "rek_kd3").text = row.rek_kd3
            ET.SubElement(xml_greeting, "rek_kd4").text = row.rek_kd4
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "item_kd").text = row.item_kd
            ET.SubElement(xml_greeting, "item_nm").text = row.item_nm
            ET.SubElement(xml_greeting, "volume1").text = unicode(row.volume1)
            ET.SubElement(xml_greeting, "sat_1_1").text = row.sat_1_1
            ET.SubElement(xml_greeting, "sat_1_2").text = row.sat_1_2
            ET.SubElement(xml_greeting, "harga1").text = unicode(row.harga1)
            ET.SubElement(xml_greeting, "volume2").text = unicode(row.volume2)
            ET.SubElement(xml_greeting, "sat_2_1").text = row.sat_2_1
            ET.SubElement(xml_greeting, "sat_2_2").text = row.sat_2_2
            ET.SubElement(xml_greeting, "harga2").text = unicode(row.harga2)
            ET.SubElement(xml_greeting, "volume3").text = unicode(row.volume3)
            ET.SubElement(xml_greeting, "sat_3_1").text = row.sat_3_1
            ET.SubElement(xml_greeting, "sat_3_2").text = row.sat_3_2
            ET.SubElement(xml_greeting, "harga3").text = unicode(row.harga3)
            ET.SubElement(xml_greeting, "volume4").text = unicode(row.volume4)
            ET.SubElement(xml_greeting, "sat_4_1").text = row.sat_4_1
            ET.SubElement(xml_greeting, "sat_4_2").text = row.sat_4_2
            ET.SubElement(xml_greeting, "harga4").text = unicode(row.harga4)
            ET.SubElement(xml_greeting, "jumlah1").text = unicode(row.jumlah1)
            ET.SubElement(xml_greeting, "jumlah2").text = unicode(row.jumlah2)
            ET.SubElement(xml_greeting, "jumlah3").text = unicode(row.jumlah3)
            ET.SubElement(xml_greeting, "jumlah4").text = unicode(row.jumlah4)

        return self.root

class r102Generator(JasperGenerator):
    def __init__(self):
        super(r102Generator, self).__init__()
        self.reportname = get_rpath('apbd/R1210.jrxml')
        self.xpath = '/apbd/rka/rekening'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        xml_a  =  ET.SubElement(self.root, 'rka')
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(xml_a, 'rekening')
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "level_id").text = unicode(row.level_id)
            ET.SubElement(xml_greeting, "defsign").text = unicode(row.defsign)
            ET.SubElement(xml_greeting, "urusan_kd").text = row.urusan_kd
            ET.SubElement(xml_greeting, "urusan_nm").text = row.urusan_nm
            ET.SubElement(xml_greeting, "rek_kd1").text = row.rek_kd1
            ET.SubElement(xml_greeting, "rek_kd2").text = row.rek_kd2
            ET.SubElement(xml_greeting, "rek_kd3").text = row.rek_kd3
            ET.SubElement(xml_greeting, "rek_kd4").text = row.rek_kd4
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "jumlah1").text = unicode(row.jumlah1)
            ET.SubElement(xml_greeting, "jumlah2").text = unicode(row.jumlah2)
            ET.SubElement(xml_greeting, "jumlah3").text = unicode(row.jumlah3)
            ET.SubElement(xml_greeting, "jumlah4").text = unicode(row.jumlah4)
        return self.root

class r103Generator(JasperGenerator):
    def __init__(self):
        super(r103Generator, self).__init__()
        self.reportname = get_rpath('apbd/R1220.jrxml')
        self.xpath = '/apbd/master/rka'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        xml_a  =  ET.SubElement(self.root, 'master')
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(xml_a, 'rka')
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.kegiatan_subs.tahun_id)
            ET.SubElement(xml_greeting, "urusan_kd").text = row.kegiatan_subs.kegiatans.programs.urusans.kode
            ET.SubElement(xml_greeting, "urusan_nm").text = row.kegiatan_subs.kegiatans.programs.urusans.nama
            ET.SubElement(xml_greeting, "unit_id").text = unicode(row.kegiatan_subs.units.id)
            ET.SubElement(xml_greeting, "unit_kd").text = row.kegiatan_subs.units.kode
            ET.SubElement(xml_greeting, "unit_nm").text = row.kegiatan_subs.units.nama
            ET.SubElement(xml_greeting, "program_kd").text = row.kegiatan_subs.kegiatans.programs.kode
            ET.SubElement(xml_greeting, "program_nm").text = row.kegiatan_subs.kegiatans.programs.nama
            ET.SubElement(xml_greeting, "kegiatan_kd").text = row.kegiatan_subs.kegiatans.kode
            ET.SubElement(xml_greeting, "kegiatan_nm").text = row.kegiatan_subs.kegiatans.nama
            ET.SubElement(xml_greeting, "lokasi").text = row.kegiatan_subs.lokasi
            ET.SubElement(xml_greeting, "target").text = row.kegiatan_subs.target
            ET.SubElement(xml_greeting, "rek_kd").text = row.rekenings.kode
            ET.SubElement(xml_greeting, "jumlah1").text = unicode(row.vol_1_1*row.vol_1_2*row.hsat_1)
            ET.SubElement(xml_greeting, "jumlah2").text = unicode(row.vol_2_1*row.vol_2_2*row.hsat_2)
            ET.SubElement(xml_greeting, "jumlah3").text = unicode(row.vol_3_1*row.vol_3_2*row.hsat_3)
            ET.SubElement(xml_greeting, "jumlah4").text = unicode(row.vol_4_1*row.vol_4_2*row.hsat_4)
        return self.root

class r104Generator(JasperGeneratorWithSubreport):
    def __init__(self):

        self.mainreport = get_rpath('apbd/R1221.jrxml')

        self.subreportlist = []
        self.subreportlist.append(get_rpath('apbd/R1221_subreport1.jrxml'))
        self.subreportlist.append(get_rpath('apbd/R1221_subreport2.jrxml'))

        #        for filename in os.listdir(os.path.abspath(self.reportrootdir)):
        #            if filename.startswith(self.reportbase + '-subreport'):
        #                self.subreportlist.append(os.path.join(self.reportrootdir, filename))
        print self.mainreport,self.subreportlist
        self.xpath = '/apbd/kegiatan'
        
        self.root = ET.Element('apbd')

    def generate_xml(self, tobegreeted):
        xml_a  =  ET.SubElement(self.root, 'kegiatan')
        
        for row in tobegreeted:
            ET.SubElement(xml_a, "tahun").text = unicode(row.tahun_id)
            ET.SubElement(xml_a, "urusan_kd").text = row.kegiatans.programs.urusans.kode
            ET.SubElement(xml_a, "urusan_nm").text = row.kegiatans.programs.urusans.nama
            ET.SubElement(xml_a, "urusan_kd1").text = row.units.urusans.kode
            ET.SubElement(xml_a, "urusan_nm1").text = row.units.urusans.nama
            ET.SubElement(xml_a, "unit_id").text = unicode(row.unit_id)
            ET.SubElement(xml_a, "unit_kd").text = row.units.kode
            ET.SubElement(xml_a, "unit_nm").text = row.units.nama
            ET.SubElement(xml_a, "program_kd").text = row.kegiatans.programs.kode
            ET.SubElement(xml_a, "program_nm").text = row.kegiatans.programs.nama
            ET.SubElement(xml_a, "kegiatan_kd").text = row.kegiatans.kode
            ET.SubElement(xml_a, "kegiatan_nm").text = row.kegiatans.nama
            ET.SubElement(xml_a, "lokasi").text = row.lokasi
            ET.SubElement(xml_a, "target").text = row.target
            ET.SubElement(xml_a, "sasaran").text = row.sasaran
            ET.SubElement(xml_a, "amt_lalu").text = row.amt_lalu
            ET.SubElement(xml_a, "amt_yad").text = row.amt_yad
            
            ET.SubElement(xml_a, "kegiatan_sub_id").text = unicode(row.id)
            rows = DBSession.query(KegiatanIndikator)\
              .filter(KegiatanIndikator.kegitan_sub_id==row.id)\
              .order_by(KegiatanIndikator.tipe,KegiatanIndikator.no_urut)
            for row2 in rows :
                xml_b = ET.SubElement(xml_a, "indikator")
                ET.SubElement(xml_b, "tipe").text =unicode(row2.tipe)
                ET.SubElement(xml_b, "no_urut").text =unicode(row2.no_urut)
                ET.SubElement(xml_b, "tolok_ukur_1").text =row2.tolok_ukur_1
                ET.SubElement(xml_b, "volume_1").text =unicode(row2.volume_1)
                ET.SubElement(xml_b, "satuan_1").text =row2.satuan_1
            
            """rowitems = DBSession.query(KegiatanItem)\
              .filter(KegiatanItem.kegiatan_sub_id==row.id, KegiatanItem.rekening_id==Rekening.id)\
              .order_by(Rekening.kode,KegiatanItem.kode)
            """
            subq1 = DBSession.query(Rekening.kode.label('subrek_kd'),Rekening.nama.label('subrek_nm'),
                    KegiatanItem.kode.label('item_kd'), KegiatanItem.nama.label('item_nm'),
                    (KegiatanItem.vol_1_1*KegiatanItem.vol_1_2).label('volume1'),
                    KegiatanItem.hsat_1.label('harga1'),KegiatanItem.sat_1_1,KegiatanItem.sat_1_2,
                    (KegiatanItem.vol_1_1* KegiatanItem.vol_1_2*KegiatanItem.hsat_1).label('jml1'),
                    (KegiatanItem.vol_2_1*KegiatanItem.vol_2_2).label('volume2'),
                    KegiatanItem.hsat_2.label('harga2'),KegiatanItem.sat_2_1,KegiatanItem.sat_2_2,
                    (KegiatanItem.vol_2_1* KegiatanItem.vol_2_2*KegiatanItem.hsat_2).label('jml2'),
                    (KegiatanItem.vol_3_1*KegiatanItem.vol_3_2).label('volume3'),
                    KegiatanItem.hsat_3.label('harga3'),KegiatanItem.sat_3_1,KegiatanItem.sat_3_2,
                    (KegiatanItem.vol_3_1* KegiatanItem.vol_3_2*KegiatanItem.hsat_3).label('jml3'),
                    (KegiatanItem.vol_4_1*KegiatanItem.vol_4_2).label('volume4'),
                    KegiatanItem.hsat_4.label('harga4'),KegiatanItem.sat_4_1,KegiatanItem.sat_4_2,
                    (KegiatanItem.vol_4_1* KegiatanItem.vol_4_2*KegiatanItem.hsat_4).label('jml4'))\
                    .filter(KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                            KegiatanItem.rekening_id==Rekening.id,
                            KegiatanItem.kegiatan_sub_id==row.id)\
                    .subquery()

            rowitems = DBSession.query(Rekening.kode.label('rek_kd'), Rekening.nama.label('rek_nm'),Rekening.level_id,
                    subq1.c.item_kd, subq1.c.item_nm, 
                    subq1.c.volume1, subq1.c.volume2, subq1.c.volume3, subq1.c.volume4, 
                    subq1.c.harga1, subq1.c.harga2, subq1.c.harga3, subq1.c.harga4, 
                    subq1.c.sat_1_1, subq1.c.sat_1_2, subq1.c.sat_2_1, subq1.c.sat_2_2, 
                    subq1.c.sat_3_1, subq1.c.sat_3_2, subq1.c.sat_4_1, subq1.c.sat_4_2,
                    func.sum(subq1.c.jml1).label('jumlah1'),func.sum(subq1.c.jml2).label('jumlah2'),
                    func.sum(subq1.c.jml3).label('jumlah3'),func.sum(subq1.c.jml4).label('jumlah4'))\
                    .filter(Rekening.kode==func.left(subq1.c.subrek_kd, func.length(Rekening.kode)))\
                    .group_by(Rekening.kode, Rekening.nama,Rekening.level_id,
                    subq1.c.item_kd, subq1.c.item_nm, 
                    subq1.c.volume1, subq1.c.volume2, subq1.c.volume3, subq1.c.volume4, 
                    subq1.c.harga1, subq1.c.harga2, subq1.c.harga3, subq1.c.harga4, 
                    subq1.c.sat_1_1, subq1.c.sat_1_2, subq1.c.sat_2_1, subq1.c.sat_2_2, 
                    subq1.c.sat_3_1, subq1.c.sat_3_2, subq1.c.sat_4_1, subq1.c.sat_4_2)\
                    .order_by(Rekening.kode).all()                    

            for row3 in rowitems :
                xml_c = ET.SubElement(xml_a, "item")
                ET.SubElement(xml_c, "rek_kd").text =row3.rek_kd
                ET.SubElement(xml_c, "rek_nm").text =row3.rek_nm
                ET.SubElement(xml_c, "level_id").text =unicode(row3.level_id)
                ET.SubElement(xml_c, "item_kd").text =row3.item_kd
                ET.SubElement(xml_c, "item_nm").text =row3.item_nm
                ET.SubElement(xml_c, "volume1").text =unicode(row3.volume1)
                ET.SubElement(xml_c, "volume2").text =unicode(row3.volume2)
                ET.SubElement(xml_c, "volume3").text =unicode(row3.volume3)
                ET.SubElement(xml_c, "volume4").text =unicode(row3.volume4)
                ET.SubElement(xml_c, "harga1").text =unicode(row3.harga1)
                ET.SubElement(xml_c, "harga2").text =unicode(row3.harga2)
                ET.SubElement(xml_c, "harga3").text =unicode(row3.harga3)
                ET.SubElement(xml_c, "harga4").text =unicode(row3.harga4)
                ET.SubElement(xml_c, "satuan11").text =row3.sat_1_1
                ET.SubElement(xml_c, "satuan12").text =row3.sat_1_2
                ET.SubElement(xml_c, "satuan21").text =row3.sat_2_1
                ET.SubElement(xml_c, "satuan22").text =row3.sat_2_2
                ET.SubElement(xml_c, "satuan31").text =row3.sat_3_1
                ET.SubElement(xml_c, "satuan32").text =row3.sat_3_2
                ET.SubElement(xml_c, "satuan41").text =row3.sat_4_1
                ET.SubElement(xml_c, "satuan42").text =row3.sat_4_2
                ET.SubElement(xml_c, "jumlah1").text =unicode(row3.jumlah1)
                ET.SubElement(xml_c, "jumlah2").text =unicode(row3.jumlah2)
                ET.SubElement(xml_c, "jumlah3").text =unicode(row3.jumlah3)
                ET.SubElement(xml_c, "jumlah4").text =unicode(row3.jumlah4)
                """ET.SubElement(xml_c, "rek_kd").text =row3.rekenings.kode
                ET.SubElement(xml_c, "rek_nm").text =row3.rekenings.nama
                ET.SubElement(xml_c, "item_kd").text =row3.kode
                ET.SubElement(xml_c, "item_nm").text =row3.nama
                ET.SubElement(xml_c, "volume1").text =unicode(row3.vol_1_1*row3.vol_1_2)
                ET.SubElement(xml_c, "volume2").text =unicode(row3.vol_2_1*row3.vol_2_2)
                ET.SubElement(xml_c, "volume3").text =unicode(row3.vol_3_1*row3.vol_3_2)
                ET.SubElement(xml_c, "volume4").text =unicode(row3.vol_4_1*row3.vol_4_2)
                ET.SubElement(xml_c, "harga1").text =unicode(row3.hsat_1)
                ET.SubElement(xml_c, "harga2").text =unicode(row3.hsat_2)
                ET.SubElement(xml_c, "harga3").text =unicode(row3.hsat_3)
                ET.SubElement(xml_c, "harga4").text =unicode(row3.hsat_4)
                ET.SubElement(xml_c, "satuan11").text =row3.sat_1_1
                ET.SubElement(xml_c, "satuan12").text =row3.sat_1_2
                ET.SubElement(xml_c, "satuan21").text =row3.sat_2_1
                ET.SubElement(xml_c, "satuan22").text =row3.sat_2_2
                ET.SubElement(xml_c, "satuan31").text =row3.sat_3_1
                ET.SubElement(xml_c, "satuan32").text =row3.sat_3_2
                ET.SubElement(xml_c, "satuan41").text =row3.sat_4_1
                ET.SubElement(xml_c, "satuan42").text =row3.sat_4_2
                ET.SubElement(xml_c, "jumlah1").text =unicode(row3.vol_1_1*row3.vol_1_2*row3.hsat_1)
                ET.SubElement(xml_c, "jumlah2").text =unicode(row3.vol_2_1*row3.vol_2_2*row3.hsat_2)
                ET.SubElement(xml_c, "jumlah3").text =unicode(row3.vol_3_1*row3.vol_3_2*row3.hsat_3)
                ET.SubElement(xml_c, "jumlah4").text =unicode(row3.vol_4_1*row3.vol_4_2*row3.hsat_4)
                """

        return self.root

class r105Generator(JasperGenerator):
    def __init__(self):
        super(r105Generator, self).__init__()
        self.reportname = get_rpath('apbd/R1300.jrxml')
        self.xpath = '/apbd/rka/rekening'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        xml_a  =  ET.SubElement(self.root, 'rka')
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(xml_a, 'rekening')
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "level_id").text = unicode(row.level_id)
            ET.SubElement(xml_greeting, "defsign").text = unicode(row.defsign)
            ET.SubElement(xml_greeting, "urusan_kd").text = row.urusan_kd
            ET.SubElement(xml_greeting, "urusan_nm").text = row.urusan_nm
            ET.SubElement(xml_greeting, "rek_kd1").text = row.rek_kd1
            ET.SubElement(xml_greeting, "rek_kd2").text = row.rek_kd2
            ET.SubElement(xml_greeting, "rek_kd3").text = row.rek_kd3
            ET.SubElement(xml_greeting, "rek_kd4").text = row.rek_kd4
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "jumlah1").text = unicode(row.jumlah1)
            ET.SubElement(xml_greeting, "jumlah2").text = unicode(row.jumlah2)
            ET.SubElement(xml_greeting, "jumlah3").text = unicode(row.jumlah3)
            ET.SubElement(xml_greeting, "jumlah4").text = unicode(row.jumlah4)
        return self.root

class r106Generator(JasperGenerator):
    def __init__(self):
        super(r106Generator, self).__init__()
        self.reportname = get_rpath('apbd/R1310.jrxml')
        self.xpath = '/apbd/rka/rekening'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        xml_a  =  ET.SubElement(self.root, 'rka')
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(xml_a, 'rekening')
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "level_id").text = unicode(row.level_id)
            ET.SubElement(xml_greeting, "defsign").text = unicode(row.defsign)
            ET.SubElement(xml_greeting, "urusan_kd").text = row.urusan_kd
            ET.SubElement(xml_greeting, "urusan_nm").text = row.urusan_nm
            ET.SubElement(xml_greeting, "rek_kd1").text = row.rek_kd1
            ET.SubElement(xml_greeting, "rek_kd2").text = row.rek_kd2
            ET.SubElement(xml_greeting, "rek_kd3").text = row.rek_kd3
            ET.SubElement(xml_greeting, "rek_kd4").text = row.rek_kd4
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "jumlah1").text = unicode(row.jumlah1)
            ET.SubElement(xml_greeting, "jumlah2").text = unicode(row.jumlah2)
            ET.SubElement(xml_greeting, "jumlah3").text = unicode(row.jumlah3)
            ET.SubElement(xml_greeting, "jumlah4").text = unicode(row.jumlah4)
        return self.root

class r107Generator(JasperGenerator):
    def __init__(self):
        super(r107Generator, self).__init__()
        self.reportname = get_rpath('apbd/R1320.jrxml')
        self.xpath = '/apbd/rka/rekening'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        xml_a  =  ET.SubElement(self.root, 'rka')
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(xml_a, 'rekening')
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "level_id").text = unicode(row.level_id)
            ET.SubElement(xml_greeting, "defsign").text = unicode(row.defsign)
            ET.SubElement(xml_greeting, "urusan_kd").text = row.urusan_kd
            ET.SubElement(xml_greeting, "urusan_nm").text = row.urusan_nm
            ET.SubElement(xml_greeting, "rek_kd1").text = row.rek_kd1
            ET.SubElement(xml_greeting, "rek_kd2").text = row.rek_kd2
            ET.SubElement(xml_greeting, "rek_kd3").text = row.rek_kd3
            ET.SubElement(xml_greeting, "rek_kd4").text = row.rek_kd4
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "jumlah1").text = unicode(row.jumlah1)
            ET.SubElement(xml_greeting, "jumlah2").text = unicode(row.jumlah2)
            ET.SubElement(xml_greeting, "jumlah3").text = unicode(row.jumlah3)
            ET.SubElement(xml_greeting, "jumlah4").text = unicode(row.jumlah4)
        return self.root
        
class r200Generator(JasperGeneratorWithSubreport):
    def __init__(self):

        self.mainreport = get_rpath('apbd/R2000.jrxml')
        self.subreportlist = []
        self.subreportlist.append(get_rpath('apbd/R2000_subreport1.jrxml'))
        self.subreportlist.append(get_rpath('apbd/R2000_subreport2.jrxml'))
        print self.mainreport,self.subreportlist
        self.xpath = '/apbd/unit'
        
        self.root = ET.Element('apbd')

    def generate_xml(self, tobegreeted):
        xml_a  =  ET.SubElement(self.root, 'unit')

        for row in tobegreeted:
            ET.SubElement(xml_a, "tahun").text = unicode(row.tahun_id)
            ET.SubElement(xml_a, "urusan_kd").text = row.urusan_kd
            ET.SubElement(xml_a, "urusan_nm").text = row.urusan_nm
            ET.SubElement(xml_a, "unit_id").text = unicode(row.unit_id)
            ET.SubElement(xml_a, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_a, "unit_nm").text = row.unit_nm

            subq1 = DBSession.query(Rekening.kode.label('subrek_kd'),Rekening.nama.label('subrek_nm'),
                (KegiatanItem.vol_1_1* KegiatanItem.vol_1_2*KegiatanItem.hsat_1).label('jml1'),
                (KegiatanItem.vol_2_1* KegiatanItem.vol_2_2*KegiatanItem.hsat_2).label('jml2'),
                (KegiatanItem.vol_3_1* KegiatanItem.vol_3_2*KegiatanItem.hsat_3).label('jml3'),
                (KegiatanItem.vol_4_1* KegiatanItem.vol_4_2*KegiatanItem.hsat_4).label('jml4'))\
                .filter(KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                    KegiatanItem.rekening_id==Rekening.id,
                    KegiatanSub.tahun_id==row.tahun_id,
                    KegiatanSub.unit_id==row.unit_id)\
                .subquery()

            rowrek = DBSession.query(Rekening.kode.label('rek_kd'), Rekening.nama.label('rek_nm'),
                Rekening.level_id, Rekening.defsign, 
                func.sum(subq1.c.jml1).label('jumlah1'),func.sum(subq1.c.jml2).label('jumlah2'),
                func.sum(subq1.c.jml3).label('jumlah3'),func.sum(subq1.c.jml4).label('jumlah4'))\
                .filter(Rekening.kode==func.left(subq1.c.subrek_kd, func.length(Rekening.kode)))\
                .group_by(Rekening.kode, Rekening.nama,
                Rekening.level_id, Rekening.defsign)\
                .order_by(Rekening.kode).all()

            for row2 in rowrek :
                xml_b = ET.SubElement(xml_a, "rekening")
                ET.SubElement(xml_b, "rek_kd").text =row2.rek_kd
                ET.SubElement(xml_b, "rek_nm").text =row2.rek_nm
                ET.SubElement(xml_b, "level_id").text =unicode(row2.level_id)
                ET.SubElement(xml_b, "defsign").text =unicode(row2.defsign)
                ET.SubElement(xml_b, "jumlah1").text =unicode(row2.jumlah1)
                ET.SubElement(xml_b, "jumlah2").text =unicode(row2.jumlah2)
                ET.SubElement(xml_b, "jumlah3").text =unicode(row2.jumlah3)
                ET.SubElement(xml_b, "jumlah4").text =unicode(row2.jumlah4)
                
            rowtrw = DBSession.query(case([(KegiatanSub.kegiatan_id==2,1),(KegiatanSub.kegiatan_id==3,2),
                 (KegiatanSub.kegiatan_id==4,4),(KegiatanSub.kegiatan_id==5,5),
                 (KegiatanSub.kegiatan_id==6,6)], else_=3).label('kode'),
                 func.sum(KegiatanItem.bln01+KegiatanItem.bln02+KegiatanItem.bln03).label('trw1'),
                 func.sum(KegiatanItem.bln04+KegiatanItem.bln05+KegiatanItem.bln06).label('trw2'),
                 func.sum(KegiatanItem.bln07+KegiatanItem.bln08+KegiatanItem.bln09).label('trw3'),
                 func.sum(KegiatanItem.bln10+KegiatanItem.bln11+KegiatanItem.bln12).label('trw4')
                 )\
                .filter(KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                    KegiatanSub.tahun_id==row.tahun_id,
                    KegiatanSub.unit_id==row.unit_id)\
                .group_by(case([(KegiatanSub.kegiatan_id==2,1),(KegiatanSub.kegiatan_id==3,2),
                 (KegiatanSub.kegiatan_id==4,4),(KegiatanSub.kegiatan_id==5,5),
                 (KegiatanSub.kegiatan_id==6,6)], else_=3))\
                .order_by(case([(KegiatanSub.kegiatan_id==2,1),(KegiatanSub.kegiatan_id==3,2),
                 (KegiatanSub.kegiatan_id==4,4),(KegiatanSub.kegiatan_id==5,5),
                 (KegiatanSub.kegiatan_id==6,6)], else_=3))
            print "XXXXXX"
            print row.unit_id

            for row3 in rowtrw :
                xml_c = ET.SubElement(xml_a, "twl")
                ET.SubElement(xml_c, "kode").text =unicode(row3.kode)
                ET.SubElement(xml_c, "trw1").text =unicode(row3.trw1)
                ET.SubElement(xml_c, "trw2").text =unicode(row3.trw2)
                ET.SubElement(xml_c, "trw3").text =unicode(row3.trw3)
                ET.SubElement(xml_c, "trw4").text =unicode(row3.trw4)
                
        return self.root

class r201Generator(JasperGenerator):
    """Jasper-Generator for Greetingcards"""
    def __init__(self):
        super(r201Generator, self).__init__()
        self.reportname = get_rpath('apbd/R2100.jrxml')
        self.xpath = '/apbd/unit/rekening'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        """Generates the XML File used by Jasperreports"""
        xml_a  =  ET.SubElement(self.root, 'unit')
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(xml_a, 'rekening')
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "level_id").text = unicode(row.level_id)
            ET.SubElement(xml_greeting, "defsign").text = unicode(row.defsign)
            ET.SubElement(xml_greeting, "urusan_kd").text = row.urusan_kd
            ET.SubElement(xml_greeting, "urusan_nm").text = row.urusan_nm
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "item_kd").text = row.item_kd
            ET.SubElement(xml_greeting, "item_nm").text = row.item_nm
            ET.SubElement(xml_greeting, "volume1").text = unicode(row.volume1)
            ET.SubElement(xml_greeting, "sat_1_1").text = row.sat_1_1
            ET.SubElement(xml_greeting, "sat_1_2").text = row.sat_1_2
            ET.SubElement(xml_greeting, "harga1").text = unicode(row.harga1)
            ET.SubElement(xml_greeting, "volume2").text = unicode(row.volume2)
            ET.SubElement(xml_greeting, "sat_2_1").text = row.sat_2_1
            ET.SubElement(xml_greeting, "sat_2_2").text = row.sat_2_2
            ET.SubElement(xml_greeting, "harga2").text = unicode(row.harga2)
            ET.SubElement(xml_greeting, "volume3").text = unicode(row.volume3)
            ET.SubElement(xml_greeting, "sat_3_1").text = row.sat_3_1
            ET.SubElement(xml_greeting, "sat_3_2").text = row.sat_3_2
            ET.SubElement(xml_greeting, "harga3").text = unicode(row.harga3)
            ET.SubElement(xml_greeting, "volume4").text = unicode(row.volume4)
            ET.SubElement(xml_greeting, "sat_4_1").text = row.sat_4_1
            ET.SubElement(xml_greeting, "sat_4_2").text = row.sat_4_2
            ET.SubElement(xml_greeting, "harga4").text = unicode(row.harga4)
            ET.SubElement(xml_greeting, "jumlah1").text = unicode(row.jumlah1)
            ET.SubElement(xml_greeting, "jumlah2").text = unicode(row.jumlah2)
            ET.SubElement(xml_greeting, "jumlah3").text = unicode(row.jumlah3)
            ET.SubElement(xml_greeting, "jumlah4").text = unicode(row.jumlah4)
            ET.SubElement(xml_greeting, "trw1").text = unicode(row.trw1)
            ET.SubElement(xml_greeting, "trw2").text = unicode(row.trw2)
            ET.SubElement(xml_greeting, "trw3").text = unicode(row.trw3)
            ET.SubElement(xml_greeting, "trw4").text = unicode(row.trw4)

        return self.root

class r202Generator(JasperGenerator):
    """Jasper-Generator for Greetingcards"""
    def __init__(self):
        super(r202Generator, self).__init__()
        self.reportname = get_rpath('apbd/R2210.jrxml')
        self.xpath = '/apbd/unit/rekening'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        """Generates the XML File used by Jasperreports"""
        xml_a  =  ET.SubElement(self.root, 'unit')
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(xml_a, 'rekening')
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "level_id").text = unicode(row.level_id)
            ET.SubElement(xml_greeting, "defsign").text = unicode(row.defsign)
            ET.SubElement(xml_greeting, "urusan_kd").text = row.urusan_kd
            ET.SubElement(xml_greeting, "urusan_nm").text = row.urusan_nm
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "jumlah1").text = unicode(row.jumlah1)
            ET.SubElement(xml_greeting, "jumlah2").text = unicode(row.jumlah2)
            ET.SubElement(xml_greeting, "jumlah3").text = unicode(row.jumlah3)
            ET.SubElement(xml_greeting, "jumlah4").text = unicode(row.jumlah4)
            ET.SubElement(xml_greeting, "trw1").text = unicode(row.trw1)
            ET.SubElement(xml_greeting, "trw2").text = unicode(row.trw2)
            ET.SubElement(xml_greeting, "trw3").text = unicode(row.trw3)
            ET.SubElement(xml_greeting, "trw4").text = unicode(row.trw4)
        return self.root

class r203Generator(JasperGenerator):
    """Jasper-Generator for Greetingcards"""
    def __init__(self):
        super(r203Generator, self).__init__()
        self.reportname = get_rpath('apbd/R2220.jrxml')
        self.xpath = '/apbd/unit/rekening'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        """Generates the XML File used by Jasperreports"""
        xml_a  =  ET.SubElement(self.root, 'unit')
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(xml_a, 'rekening')
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "urusan_kd").text = row.urusan_kd
            ET.SubElement(xml_greeting, "urusan_nm").text = row.urusan_nm
            ET.SubElement(xml_greeting, "unit_id").text = unicode(row.unit_id)
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "program_kd").text = row.program_kd
            ET.SubElement(xml_greeting, "program_nm").text = row.program_nm
            ET.SubElement(xml_greeting, "kegiatan_kd").text = row.kegiatan_kd
            ET.SubElement(xml_greeting, "kegiatan_nm").text = row.kegiatan_nm
            ET.SubElement(xml_greeting, "lokasi").text = row.lokasi
            ET.SubElement(xml_greeting, "target").text = row.target
            ET.SubElement(xml_greeting, "trw1").text = unicode(row.trw1)
            ET.SubElement(xml_greeting, "trw2").text = unicode(row.trw2)
            ET.SubElement(xml_greeting, "trw3").text = unicode(row.trw3)
            ET.SubElement(xml_greeting, "trw4").text = unicode(row.trw4)
            print row.trw1
        return self.root

class r204Generator(JasperGeneratorWithSubreport):
    """Jasper-Generator for Greetingcards"""
    def __init__(self):
        self.mainreport = get_rpath('apbd/R2221.jrxml')

        self.subreportlist = []
        self.subreportlist.append(get_rpath('apbd/R2221_subreport1.jrxml'))
        self.subreportlist.append(get_rpath('apbd/R2221_subreport2.jrxml'))
        self.subreportlist.append(get_rpath('apbd/R2221_subreport3.jrxml'))

        print self.mainreport,self.subreportlist
        self.xpath = '/apbd/kegiatan'
        
        self.root = ET.Element('apbd')

    def generate_xml(self, tobegreeted):
        xml_a  =  ET.SubElement(self.root, 'kegiatan')
        
        for row in tobegreeted:
            ET.SubElement(xml_a, "tahun").text = unicode(row.tahun_id)
            ET.SubElement(xml_a, "urusan_kd").text = row.kegiatans.programs.urusans.kode
            ET.SubElement(xml_a, "urusan_nm").text = row.kegiatans.programs.urusans.nama
            ET.SubElement(xml_a, "urusan_kd1").text = row.units.urusans.kode
            ET.SubElement(xml_a, "urusan_nm1").text = row.units.urusans.nama
            ET.SubElement(xml_a, "unit_id").text = unicode(row.unit_id)
            ET.SubElement(xml_a, "unit_kd").text = row.units.kode
            ET.SubElement(xml_a, "unit_nm").text = row.units.nama
            ET.SubElement(xml_a, "program_kd").text = row.kegiatans.programs.kode
            ET.SubElement(xml_a, "program_nm").text = row.kegiatans.programs.nama
            ET.SubElement(xml_a, "kegiatan_kd").text = row.kegiatans.kode
            ET.SubElement(xml_a, "kegiatan_nm").text = row.kegiatans.nama
            ET.SubElement(xml_a, "lokasi").text = row.lokasi
            ET.SubElement(xml_a, "target").text = row.target
            ET.SubElement(xml_a, "sasaran").text = row.sasaran
            ET.SubElement(xml_a, "amt_lalu").text = row.amt_lalu
            ET.SubElement(xml_a, "amt_yad").text = row.amt_yad
            
            ET.SubElement(xml_a, "kegiatan_sub_id").text = unicode(row.id)
            rows = DBSession.query(KegiatanIndikator)\
              .filter(KegiatanIndikator.kegitan_sub_id==row.id)\
              .order_by(KegiatanIndikator.tipe,KegiatanIndikator.no_urut)
            for row2 in rows :
                xml_b = ET.SubElement(xml_a, "indikator")
                ET.SubElement(xml_b, "tipe").text =unicode(row2.tipe)
                ET.SubElement(xml_b, "no_urut").text =unicode(row2.no_urut)
                ET.SubElement(xml_b, "tolok_ukur_1").text =row2.tolok_ukur_1
                ET.SubElement(xml_b, "volume_1").text =unicode(row2.volume_1)
                ET.SubElement(xml_b, "satuan_1").text =row2.satuan_1
            
            """rowitems = DBSession.query(KegiatanItem)\
              .filter(KegiatanItem.kegiatan_sub_id==row.id, KegiatanItem.rekening_id==Rekening.id)\
              .order_by(Rekening.kode,KegiatanItem.kode)
            """
            subq1 = DBSession.query(Rekening.kode.label('subrek_kd'),Rekening.nama.label('subrek_nm'),
                    KegiatanItem.kode.label('item_kd'), KegiatanItem.nama.label('item_nm'),
                    (KegiatanItem.vol_1_1*KegiatanItem.vol_1_2).label('volume1'),
                    KegiatanItem.hsat_1.label('harga1'),KegiatanItem.sat_1_1,KegiatanItem.sat_1_2,
                    (KegiatanItem.vol_1_1* KegiatanItem.vol_1_2*KegiatanItem.hsat_1).label('jml1'),
                    (KegiatanItem.vol_2_1*KegiatanItem.vol_2_2).label('volume2'),
                    KegiatanItem.hsat_2.label('harga2'),KegiatanItem.sat_2_1,KegiatanItem.sat_2_2,
                    (KegiatanItem.vol_2_1* KegiatanItem.vol_2_2*KegiatanItem.hsat_2).label('jml2'),
                    (KegiatanItem.vol_3_1*KegiatanItem.vol_3_2).label('volume3'),
                    KegiatanItem.hsat_3.label('harga3'),KegiatanItem.sat_3_1,KegiatanItem.sat_3_2,
                    (KegiatanItem.vol_3_1* KegiatanItem.vol_3_2*KegiatanItem.hsat_3).label('jml3'),
                    (KegiatanItem.vol_4_1*KegiatanItem.vol_4_2).label('volume4'),
                    KegiatanItem.hsat_4.label('harga4'),KegiatanItem.sat_4_1,KegiatanItem.sat_4_2,
                    (KegiatanItem.vol_4_1* KegiatanItem.vol_4_2*KegiatanItem.hsat_4).label('jml4'))\
                    .filter(KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                            KegiatanItem.rekening_id==Rekening.id,
                            KegiatanItem.kegiatan_sub_id==row.id)\
                    .subquery()

            rowitems = DBSession.query(Rekening.kode.label('rek_kd'), Rekening.nama.label('rek_nm'),Rekening.level_id,
                    subq1.c.item_kd, subq1.c.item_nm, 
                    subq1.c.volume1, subq1.c.volume2, subq1.c.volume3, subq1.c.volume4, 
                    subq1.c.harga1, subq1.c.harga2, subq1.c.harga3, subq1.c.harga4, 
                    subq1.c.sat_1_1, subq1.c.sat_1_2, subq1.c.sat_2_1, subq1.c.sat_2_2, 
                    subq1.c.sat_3_1, subq1.c.sat_3_2, subq1.c.sat_4_1, subq1.c.sat_4_2,
                    func.sum(subq1.c.jml1).label('jumlah1'),func.sum(subq1.c.jml2).label('jumlah2'),
                    func.sum(subq1.c.jml3).label('jumlah3'),func.sum(subq1.c.jml4).label('jumlah4'))\
                    .filter(Rekening.kode==func.left(subq1.c.subrek_kd, func.length(Rekening.kode)))\
                    .group_by(Rekening.kode, Rekening.nama,Rekening.level_id,
                    subq1.c.item_kd, subq1.c.item_nm, 
                    subq1.c.volume1, subq1.c.volume2, subq1.c.volume3, subq1.c.volume4, 
                    subq1.c.harga1, subq1.c.harga2, subq1.c.harga3, subq1.c.harga4, 
                    subq1.c.sat_1_1, subq1.c.sat_1_2, subq1.c.sat_2_1, subq1.c.sat_2_2, 
                    subq1.c.sat_3_1, subq1.c.sat_3_2, subq1.c.sat_4_1, subq1.c.sat_4_2)\
                    .order_by(Rekening.kode).all()                    

            for row3 in rowitems :
                xml_c = ET.SubElement(xml_a, "item")
                ET.SubElement(xml_c, "rek_kd").text =row3.rek_kd
                ET.SubElement(xml_c, "rek_nm").text =row3.rek_nm
                ET.SubElement(xml_c, "level_id").text =unicode(row3.level_id)
                ET.SubElement(xml_c, "item_kd").text =row3.item_kd
                ET.SubElement(xml_c, "item_nm").text =row3.item_nm
                ET.SubElement(xml_c, "volume1").text =unicode(row3.volume1)
                ET.SubElement(xml_c, "volume2").text =unicode(row3.volume2)
                ET.SubElement(xml_c, "volume3").text =unicode(row3.volume3)
                ET.SubElement(xml_c, "volume4").text =unicode(row3.volume4)
                ET.SubElement(xml_c, "harga1").text =unicode(row3.harga1)
                ET.SubElement(xml_c, "harga2").text =unicode(row3.harga2)
                ET.SubElement(xml_c, "harga3").text =unicode(row3.harga3)
                ET.SubElement(xml_c, "harga4").text =unicode(row3.harga4)
                ET.SubElement(xml_c, "satuan11").text =row3.sat_1_1
                ET.SubElement(xml_c, "satuan12").text =row3.sat_1_2
                ET.SubElement(xml_c, "satuan21").text =row3.sat_2_1
                ET.SubElement(xml_c, "satuan22").text =row3.sat_2_2
                ET.SubElement(xml_c, "satuan31").text =row3.sat_3_1
                ET.SubElement(xml_c, "satuan32").text =row3.sat_3_2
                ET.SubElement(xml_c, "satuan41").text =row3.sat_4_1
                ET.SubElement(xml_c, "satuan42").text =row3.sat_4_2
                ET.SubElement(xml_c, "jumlah1").text =unicode(row3.jumlah1)
                ET.SubElement(xml_c, "jumlah2").text =unicode(row3.jumlah2)
                ET.SubElement(xml_c, "jumlah3").text =unicode(row3.jumlah3)
                ET.SubElement(xml_c, "jumlah4").text =unicode(row3.jumlah4)

            rowtrw = DBSession.query(func.sum(KegiatanItem.bln01+KegiatanItem.bln02+KegiatanItem.bln03).label('jmltrw1'),
                    func.sum(KegiatanItem.bln04+KegiatanItem.bln05+KegiatanItem.bln06).label('jmltrw2'),
                    func.sum(KegiatanItem.bln07+KegiatanItem.bln08+KegiatanItem.bln09).label('jmltrw3'),
                    func.sum(KegiatanItem.bln10+KegiatanItem.bln11+KegiatanItem.bln12).label('jmltrw4'))\
                    .filter(KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                            KegiatanSub.unit_id==row.unit_id,
                            KegiatanSub.tahun_id==row.tahun_id,
                            KegiatanItem.kegiatan_sub_id==row.id)\

            for row4 in rowtrw :
                xml_d = ET.SubElement(xml_a, "trw")
                ET.SubElement(xml_d, "jmltrw1").text =unicode(row4.jmltrw1)
                ET.SubElement(xml_d, "jmltrw2").text =unicode(row4.jmltrw2)
                ET.SubElement(xml_d, "jmltrw3").text =unicode(row4.jmltrw3)
                ET.SubElement(xml_d, "jmltrw4").text =unicode(row4.jmltrw4)

        return self.root

class r205Generator(JasperGenerator):
    """Jasper-Generator for Greetingcards"""
    def __init__(self):
        super(r205Generator, self).__init__()
        self.reportname = get_rpath('apbd/R2300.jrxml')
        self.xpath = '/apbd/unit/rekening'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        """Generates the XML File used by Jasperreports"""
        xml_a  =  ET.SubElement(self.root, 'unit')
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(xml_a, 'rekening')
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "level_id").text = unicode(row.level_id)
            ET.SubElement(xml_greeting, "defsign").text = unicode(row.defsign)
            ET.SubElement(xml_greeting, "urusan_kd").text = row.urusan_kd
            ET.SubElement(xml_greeting, "urusan_nm").text = row.urusan_nm
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "jumlah1").text = unicode(row.jumlah1)
            ET.SubElement(xml_greeting, "jumlah2").text = unicode(row.jumlah2)
            ET.SubElement(xml_greeting, "jumlah3").text = unicode(row.jumlah3)
            ET.SubElement(xml_greeting, "jumlah4").text = unicode(row.jumlah4)
            ET.SubElement(xml_greeting, "trw1").text = unicode(row.trw1)
            ET.SubElement(xml_greeting, "trw2").text = unicode(row.trw2)
            ET.SubElement(xml_greeting, "trw3").text = unicode(row.trw3)
            ET.SubElement(xml_greeting, "trw4").text = unicode(row.trw4)            
        return self.root

class r206Generator(JasperGenerator):
    """Jasper-Generator for Greetingcards"""
    def __init__(self):
        super(r206Generator, self).__init__()
        self.reportname = get_rpath('apbd/R2310.jrxml')
        self.xpath = '/apbd/unit/rekening'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        """Generates the XML File used by Jasperreports"""
        xml_a  =  ET.SubElement(self.root, 'unit')
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(xml_a, 'rekening')
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "level_id").text = unicode(row.level_id)
            ET.SubElement(xml_greeting, "defsign").text = unicode(row.defsign)
            ET.SubElement(xml_greeting, "urusan_kd").text = row.urusan_kd
            ET.SubElement(xml_greeting, "urusan_nm").text = row.urusan_nm
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "jumlah1").text = unicode(row.jumlah1)
            ET.SubElement(xml_greeting, "jumlah2").text = unicode(row.jumlah2)
            ET.SubElement(xml_greeting, "jumlah3").text = unicode(row.jumlah3)
            ET.SubElement(xml_greeting, "jumlah4").text = unicode(row.jumlah4)
            ET.SubElement(xml_greeting, "trw1").text = unicode(row.trw1)
            ET.SubElement(xml_greeting, "trw2").text = unicode(row.trw2)
            ET.SubElement(xml_greeting, "trw3").text = unicode(row.trw3)
            ET.SubElement(xml_greeting, "trw4").text = unicode(row.trw4)            
        return self.root

class r207Generator(JasperGenerator):
    """Jasper-Generator for Greetingcards"""
    def __init__(self):
        super(r207Generator, self).__init__()
        self.reportname = get_rpath('apbd/R2320.jrxml')
        self.xpath = '/apbd/unit/rekening'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        """Generates the XML File used by Jasperreports"""
        xml_a  =  ET.SubElement(self.root, 'unit')
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(xml_a, 'rekening')
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "level_id").text = unicode(row.level_id)
            ET.SubElement(xml_greeting, "defsign").text = unicode(row.defsign)
            ET.SubElement(xml_greeting, "urusan_kd").text = row.urusan_kd
            ET.SubElement(xml_greeting, "urusan_nm").text = row.urusan_nm
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "jumlah1").text = unicode(row.jumlah1)
            ET.SubElement(xml_greeting, "jumlah2").text = unicode(row.jumlah2)
            ET.SubElement(xml_greeting, "jumlah3").text = unicode(row.jumlah3)
            ET.SubElement(xml_greeting, "jumlah4").text = unicode(row.jumlah4)
            ET.SubElement(xml_greeting, "trw1").text = unicode(row.trw1)
            ET.SubElement(xml_greeting, "trw2").text = unicode(row.trw2)
            ET.SubElement(xml_greeting, "trw3").text = unicode(row.trw3)
            ET.SubElement(xml_greeting, "trw4").text = unicode(row.trw4)            
        return self.root

class r300Generator(JasperGeneratorWithSubreport):
    def __init__(self):

        self.mainreport = get_rpath('apbd/R3000.jrxml')
        self.subreportlist = []
        self.subreportlist.append(get_rpath('apbd/R3000_subreport1.jrxml'))
        self.subreportlist.append(get_rpath('apbd/R3000_subreport2.jrxml'))
        print self.mainreport,self.subreportlist
        self.xpath = '/apbd/unit'
        
        self.root = ET.Element('apbd')

    def generate_xml(self, tobegreeted):
        xml_a  =  ET.SubElement(self.root, 'unit')

        for row in tobegreeted:
            ET.SubElement(xml_a, "tahun").text = unicode(row.tahun_id)
            ET.SubElement(xml_a, "urusan_kd").text = row.urusan_kd
            ET.SubElement(xml_a, "urusan_nm").text = row.urusan_nm
            ET.SubElement(xml_a, "unit_id").text = unicode(row.unit_id)
            ET.SubElement(xml_a, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_a, "unit_nm").text = row.unit_nm

            subq1 = DBSession.query(Rekening.kode.label('subrek_kd'),Rekening.nama.label('subrek_nm'),
                (KegiatanItem.vol_1_1* KegiatanItem.vol_1_2*KegiatanItem.hsat_1).label('jml1'),
                (KegiatanItem.vol_2_1* KegiatanItem.vol_2_2*KegiatanItem.hsat_2).label('jml2'),
                (KegiatanItem.vol_3_1* KegiatanItem.vol_3_2*KegiatanItem.hsat_3).label('jml3'),
                (KegiatanItem.vol_4_1* KegiatanItem.vol_4_2*KegiatanItem.hsat_4).label('jml4'))\
                .filter(KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                    KegiatanItem.rekening_id==Rekening.id,
                    KegiatanSub.tahun_id==row.tahun_id,
                    KegiatanSub.unit_id==row.unit_id)\
                .subquery()

            rowrek = DBSession.query(Rekening.kode.label('rek_kd'), Rekening.nama.label('rek_nm'),
                Rekening.level_id, Rekening.defsign, 
                func.sum(subq1.c.jml1).label('jumlah1'),func.sum(subq1.c.jml2).label('jumlah2'),
                func.sum(subq1.c.jml3).label('jumlah3'),func.sum(subq1.c.jml4).label('jumlah4'))\
                .filter(Rekening.kode==func.left(subq1.c.subrek_kd, func.length(Rekening.kode)))\
                .group_by(Rekening.kode, Rekening.nama,
                Rekening.level_id, Rekening.defsign)\
                .order_by(Rekening.kode).all()

            for row2 in rowrek :
                xml_b = ET.SubElement(xml_a, "rekening")
                ET.SubElement(xml_b, "rek_kd").text =row2.rek_kd
                ET.SubElement(xml_b, "rek_nm").text =row2.rek_nm
                ET.SubElement(xml_b, "level_id").text =unicode(row2.level_id)
                ET.SubElement(xml_b, "defsign").text =unicode(row2.defsign)
                ET.SubElement(xml_b, "jumlah1").text =unicode(row2.jumlah1)
                ET.SubElement(xml_b, "jumlah2").text =unicode(row2.jumlah2)
                ET.SubElement(xml_b, "jumlah3").text =unicode(row2.jumlah3)
                ET.SubElement(xml_b, "jumlah4").text =unicode(row2.jumlah4)
                
            rowtrw = DBSession.query(case([(KegiatanSub.kegiatan_id==2,1),(KegiatanSub.kegiatan_id==3,2),
                 (KegiatanSub.kegiatan_id==4,4),(KegiatanSub.kegiatan_id==5,5),
                 (KegiatanSub.kegiatan_id==6,6)], else_=3).label('kode'),
                 func.sum(KegiatanItem.bln01+KegiatanItem.bln02+KegiatanItem.bln03).label('trw1'),
                 func.sum(KegiatanItem.bln04+KegiatanItem.bln05+KegiatanItem.bln06).label('trw2'),
                 func.sum(KegiatanItem.bln07+KegiatanItem.bln08+KegiatanItem.bln09).label('trw3'),
                 func.sum(KegiatanItem.bln10+KegiatanItem.bln11+KegiatanItem.bln12).label('trw4')
                 )\
                .filter(KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                    KegiatanSub.tahun_id==row.tahun_id,
                    KegiatanSub.unit_id==row.unit_id)\
                .group_by(case([(KegiatanSub.kegiatan_id==2,1),(KegiatanSub.kegiatan_id==3,2),
                 (KegiatanSub.kegiatan_id==4,4),(KegiatanSub.kegiatan_id==5,5),
                 (KegiatanSub.kegiatan_id==6,6)], else_=3))\
                .order_by(case([(KegiatanSub.kegiatan_id==2,1),(KegiatanSub.kegiatan_id==3,2),
                 (KegiatanSub.kegiatan_id==4,4),(KegiatanSub.kegiatan_id==5,5),
                 (KegiatanSub.kegiatan_id==6,6)], else_=3))
            print "XXXXXX"
            print row.unit_id

            for row3 in rowtrw :
                xml_c = ET.SubElement(xml_a, "twl")
                ET.SubElement(xml_c, "kode").text =unicode(row3.kode)
                ET.SubElement(xml_c, "trw1").text =unicode(row3.trw1)
                ET.SubElement(xml_c, "trw2").text =unicode(row3.trw2)
                ET.SubElement(xml_c, "trw3").text =unicode(row3.trw3)
                ET.SubElement(xml_c, "trw4").text =unicode(row3.trw4)
                
        return self.root

class r301Generator(JasperGenerator):
    """Jasper-Generator for Greetingcards"""
    def __init__(self):
        super(r301Generator, self).__init__()
        self.reportname = get_rpath('apbd/R3100.jrxml')
        self.xpath = '/apbd/unit/rekening'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        """Generates the XML File used by Jasperreports"""
        xml_a  =  ET.SubElement(self.root, 'unit')
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(xml_a, 'rekening')
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "level_id").text = unicode(row.level_id)
            ET.SubElement(xml_greeting, "defsign").text = unicode(row.defsign)
            ET.SubElement(xml_greeting, "urusan_kd").text = row.urusan_kd
            ET.SubElement(xml_greeting, "urusan_nm").text = row.urusan_nm
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "perubahan").text = row.perubahan
            ET.SubElement(xml_greeting, "jumlah1").text = unicode(row.jumlah1)
            ET.SubElement(xml_greeting, "jumlah2").text = unicode(row.jumlah2)
            ET.SubElement(xml_greeting, "jumlah3").text = unicode(row.jumlah3)
            ET.SubElement(xml_greeting, "jumlah4").text = unicode(row.jumlah4)
            ET.SubElement(xml_greeting, "trw1").text = unicode(row.trw1)
            ET.SubElement(xml_greeting, "trw2").text = unicode(row.trw2)
            ET.SubElement(xml_greeting, "trw3").text = unicode(row.trw3)
            ET.SubElement(xml_greeting, "trw4").text = unicode(row.trw4)            
        return self.root

class r302Generator(JasperGenerator):
    """Jasper-Generator for Greetingcards"""
    def __init__(self):
        super(r302Generator, self).__init__()
        self.reportname = get_rpath('apbd/R3210.jrxml')
        self.xpath = '/apbd/unit/rekening'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        """Generates the XML File used by Jasperreports"""
        xml_a  =  ET.SubElement(self.root, 'unit')
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(xml_a, 'rekening')
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "level_id").text = unicode(row.level_id)
            ET.SubElement(xml_greeting, "defsign").text = unicode(row.defsign)
            ET.SubElement(xml_greeting, "urusan_kd").text = row.urusan_kd
            ET.SubElement(xml_greeting, "urusan_nm").text = row.urusan_nm
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "perubahan").text = row.perubahan
            ET.SubElement(xml_greeting, "jumlah1").text = unicode(row.jumlah1)
            ET.SubElement(xml_greeting, "jumlah2").text = unicode(row.jumlah2)
            ET.SubElement(xml_greeting, "jumlah3").text = unicode(row.jumlah3)
            ET.SubElement(xml_greeting, "jumlah4").text = unicode(row.jumlah4)
            ET.SubElement(xml_greeting, "trw1").text = unicode(row.trw1)
            ET.SubElement(xml_greeting, "trw2").text = unicode(row.trw2)
            ET.SubElement(xml_greeting, "trw3").text = unicode(row.trw3)
            ET.SubElement(xml_greeting, "trw4").text = unicode(row.trw4)
        return self.root

class r303Generator(JasperGenerator):
    """Jasper-Generator for Greetingcards"""
    def __init__(self):
        super(r303Generator, self).__init__()
        self.reportname = get_rpath('apbd/R3220.jrxml')
        self.xpath = '/apbd/unit/rekening'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        """Generates the XML File used by Jasperreports"""
        xml_a  =  ET.SubElement(self.root, 'unit')
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(xml_a, 'rekening')
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "urusan_kd").text = row.urusan_kd
            ET.SubElement(xml_greeting, "urusan_nm").text = row.urusan_nm
            ET.SubElement(xml_greeting, "unit_id").text = unicode(row.unit_id)
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "program_kd").text = row.program_kd
            ET.SubElement(xml_greeting, "program_nm").text = row.program_nm
            ET.SubElement(xml_greeting, "kegiatan_kd").text = row.kegiatan_kd
            ET.SubElement(xml_greeting, "kegiatan_nm").text = row.kegiatan_nm
            ET.SubElement(xml_greeting, "lokasi").text = row.lokasi
            ET.SubElement(xml_greeting, "target").text = row.target
            ET.SubElement(xml_greeting, "jumlah1").text = unicode(row.jumlah1)
            ET.SubElement(xml_greeting, "jumlah2").text = unicode(row.jumlah2)
            ET.SubElement(xml_greeting, "jumlah3").text = unicode(row.jumlah3)
            ET.SubElement(xml_greeting, "jumlah4").text = unicode(row.jumlah4)
        return self.root

class r304Generator(JasperGeneratorWithSubreport):
    """Jasper-Generator for Greetingcards"""
    def __init__(self):
        self.mainreport = get_rpath('apbd/R3221.jrxml')

        self.subreportlist = []
        self.subreportlist.append(get_rpath('apbd/R3221_subreport1.jrxml'))
        self.subreportlist.append(get_rpath('apbd/R3221_subreport2.jrxml'))
        self.subreportlist.append(get_rpath('apbd/R3221_subreport3.jrxml'))

        print self.mainreport,self.subreportlist
        self.xpath = '/apbd/kegiatan'
        
        self.root = ET.Element('apbd')

    def generate_xml(self, tobegreeted):
        xml_a  =  ET.SubElement(self.root, 'kegiatan')
        
        for row in tobegreeted:
            ET.SubElement(xml_a, "tahun").text = unicode(row.tahun_id)
            ET.SubElement(xml_a, "urusan_kd").text = row.kegiatans.programs.urusans.kode
            ET.SubElement(xml_a, "urusan_nm").text = row.kegiatans.programs.urusans.nama
            ET.SubElement(xml_a, "urusan_kd1").text = row.units.urusans.kode
            ET.SubElement(xml_a, "urusan_nm1").text = row.units.urusans.nama
            ET.SubElement(xml_a, "unit_id").text = unicode(row.unit_id)
            ET.SubElement(xml_a, "unit_kd").text = row.units.kode
            ET.SubElement(xml_a, "unit_nm").text = row.units.nama
            ET.SubElement(xml_a, "program_kd").text = row.kegiatans.programs.kode
            ET.SubElement(xml_a, "program_nm").text = row.kegiatans.programs.nama
            ET.SubElement(xml_a, "kegiatan_kd").text = row.kegiatans.kode
            ET.SubElement(xml_a, "kegiatan_nm").text = row.kegiatans.nama
            ET.SubElement(xml_a, "lokasi").text = row.lokasi
            ET.SubElement(xml_a, "target").text = row.target
            ET.SubElement(xml_a, "sasaran").text = row.sasaran
            ET.SubElement(xml_a, "amt_lalu").text = row.amt_lalu
            ET.SubElement(xml_a, "amt_yad").text = row.amt_yad
            ET.SubElement(xml_a, "perubahan").text = row.perubahan
            
            ET.SubElement(xml_a, "kegiatan_sub_id").text = unicode(row.id)
            rows = DBSession.query(KegiatanIndikator)\
              .filter(KegiatanIndikator.kegitan_sub_id==row.id)\
              .order_by(KegiatanIndikator.tipe,KegiatanIndikator.no_urut)
            for row2 in rows :
                xml_b = ET.SubElement(xml_a, "indikator")
                ET.SubElement(xml_b, "tipe").text =unicode(row2.tipe)
                ET.SubElement(xml_b, "no_urut").text =unicode(row2.no_urut)
                ET.SubElement(xml_b, "tolok_ukur_1").text =row2.tolok_ukur_1
                ET.SubElement(xml_b, "volume_1").text =unicode(row2.volume_1)
                ET.SubElement(xml_b, "satuan_1").text =row2.satuan_1
                ET.SubElement(xml_b, "tolok_ukur_2").text =row2.tolok_ukur_2
                ET.SubElement(xml_b, "volume_2").text =unicode(row2.volume_2)
                ET.SubElement(xml_b, "satuan_2").text =row2.satuan_2
                ET.SubElement(xml_b, "tolok_ukur_3").text =row2.tolok_ukur_3
                ET.SubElement(xml_b, "volume_3").text =unicode(row2.volume_3)
                ET.SubElement(xml_b, "satuan_3").text =row2.satuan_3
                ET.SubElement(xml_b, "tolok_ukur_4").text =row2.tolok_ukur_4
                ET.SubElement(xml_b, "volume_4").text =unicode(row2.volume_4)
                ET.SubElement(xml_b, "satuan_4").text =row2.satuan_4
            
            """rowitems = DBSession.query(KegiatanItem)\
              .filter(KegiatanItem.kegiatan_sub_id==row.id, KegiatanItem.rekening_id==Rekening.id)\
              .order_by(Rekening.kode,KegiatanItem.kode)
            """
            subq1 = DBSession.query(Rekening.kode.label('subrek_kd'),Rekening.nama.label('subrek_nm'),
                    KegiatanItem.kode.label('item_kd'), KegiatanItem.nama.label('item_nm'),
                    (KegiatanItem.vol_1_1*KegiatanItem.vol_1_2).label('volume1'),
                    KegiatanItem.hsat_1.label('harga1'),KegiatanItem.sat_1_1,KegiatanItem.sat_1_2,
                    (KegiatanItem.vol_1_1* KegiatanItem.vol_1_2*KegiatanItem.hsat_1).label('jml1'),
                    (KegiatanItem.vol_2_1*KegiatanItem.vol_2_2).label('volume2'),
                    KegiatanItem.hsat_2.label('harga2'),KegiatanItem.sat_2_1,KegiatanItem.sat_2_2,
                    (KegiatanItem.vol_2_1* KegiatanItem.vol_2_2*KegiatanItem.hsat_2).label('jml2'),
                    (KegiatanItem.vol_3_1*KegiatanItem.vol_3_2).label('volume3'),
                    KegiatanItem.hsat_3.label('harga3'),KegiatanItem.sat_3_1,KegiatanItem.sat_3_2,
                    (KegiatanItem.vol_3_1* KegiatanItem.vol_3_2*KegiatanItem.hsat_3).label('jml3'),
                    (KegiatanItem.vol_4_1*KegiatanItem.vol_4_2).label('volume4'),
                    KegiatanItem.hsat_4.label('harga4'),KegiatanItem.sat_4_1,KegiatanItem.sat_4_2,
                    (KegiatanItem.vol_4_1* KegiatanItem.vol_4_2*KegiatanItem.hsat_4).label('jml4'))\
                    .filter(KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                            KegiatanItem.rekening_id==Rekening.id,
                            KegiatanItem.kegiatan_sub_id==row.id)\
                    .subquery()

            rowitems = DBSession.query(Rekening.kode.label('rek_kd'), Rekening.nama.label('rek_nm'),Rekening.level_id,
                    subq1.c.item_kd, subq1.c.item_nm, 
                    subq1.c.volume1, subq1.c.volume2, subq1.c.volume3, subq1.c.volume4, 
                    subq1.c.harga1, subq1.c.harga2, subq1.c.harga3, subq1.c.harga4, 
                    subq1.c.sat_1_1, subq1.c.sat_1_2, subq1.c.sat_2_1, subq1.c.sat_2_2, 
                    subq1.c.sat_3_1, subq1.c.sat_3_2, subq1.c.sat_4_1, subq1.c.sat_4_2,
                    func.sum(subq1.c.jml1).label('jumlah1'),func.sum(subq1.c.jml2).label('jumlah2'),
                    func.sum(subq1.c.jml3).label('jumlah3'),func.sum(subq1.c.jml4).label('jumlah4'))\
                    .filter(Rekening.kode==func.left(subq1.c.subrek_kd, func.length(Rekening.kode)))\
                    .group_by(Rekening.kode, Rekening.nama,Rekening.level_id,
                    subq1.c.item_kd, subq1.c.item_nm, 
                    subq1.c.volume1, subq1.c.volume2, subq1.c.volume3, subq1.c.volume4, 
                    subq1.c.harga1, subq1.c.harga2, subq1.c.harga3, subq1.c.harga4, 
                    subq1.c.sat_1_1, subq1.c.sat_1_2, subq1.c.sat_2_1, subq1.c.sat_2_2, 
                    subq1.c.sat_3_1, subq1.c.sat_3_2, subq1.c.sat_4_1, subq1.c.sat_4_2)\
                    .order_by(Rekening.kode).all()                    

            for row3 in rowitems :
                xml_c = ET.SubElement(xml_a, "item")
                ET.SubElement(xml_c, "rek_kd").text =row3.rek_kd
                ET.SubElement(xml_c, "rek_nm").text =row3.rek_nm
                ET.SubElement(xml_c, "level_id").text =unicode(row3.level_id)
                ET.SubElement(xml_c, "item_kd").text =row3.item_kd
                ET.SubElement(xml_c, "item_nm").text =row3.item_nm
                ET.SubElement(xml_c, "volume1").text =unicode(row3.volume1)
                ET.SubElement(xml_c, "volume2").text =unicode(row3.volume2)
                ET.SubElement(xml_c, "volume3").text =unicode(row3.volume3)
                ET.SubElement(xml_c, "volume4").text =unicode(row3.volume4)
                ET.SubElement(xml_c, "harga1").text =unicode(row3.harga1)
                ET.SubElement(xml_c, "harga2").text =unicode(row3.harga2)
                ET.SubElement(xml_c, "harga3").text =unicode(row3.harga3)
                ET.SubElement(xml_c, "harga4").text =unicode(row3.harga4)
                ET.SubElement(xml_c, "satuan11").text =row3.sat_1_1
                ET.SubElement(xml_c, "satuan12").text =row3.sat_1_2
                ET.SubElement(xml_c, "satuan21").text =row3.sat_2_1
                ET.SubElement(xml_c, "satuan22").text =row3.sat_2_2
                ET.SubElement(xml_c, "satuan31").text =row3.sat_3_1
                ET.SubElement(xml_c, "satuan32").text =row3.sat_3_2
                ET.SubElement(xml_c, "satuan41").text =row3.sat_4_1
                ET.SubElement(xml_c, "satuan42").text =row3.sat_4_2
                ET.SubElement(xml_c, "jumlah1").text =unicode(row3.jumlah1)
                ET.SubElement(xml_c, "jumlah2").text =unicode(row3.jumlah2)
                ET.SubElement(xml_c, "jumlah3").text =unicode(row3.jumlah3)
                ET.SubElement(xml_c, "jumlah4").text =unicode(row3.jumlah4)

            rowtrw = DBSession.query(func.sum(KegiatanItem.bln01+KegiatanItem.bln02+KegiatanItem.bln03).label('jmltrw1'),
                    func.sum(KegiatanItem.bln04+KegiatanItem.bln05+KegiatanItem.bln06).label('jmltrw2'),
                    func.sum(KegiatanItem.bln07+KegiatanItem.bln08+KegiatanItem.bln09).label('jmltrw3'),
                    func.sum(KegiatanItem.bln10+KegiatanItem.bln11+KegiatanItem.bln12).label('jmltrw4'))\
                    .filter(KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                            KegiatanSub.unit_id==row.unit_id,
                            KegiatanSub.tahun_id==row.tahun_id,
                            KegiatanItem.kegiatan_sub_id==row.id)\

            for row4 in rowtrw :
                xml_d = ET.SubElement(xml_a, "trw")
                ET.SubElement(xml_d, "jmltrw1").text =unicode(row4.jmltrw1)
                ET.SubElement(xml_d, "jmltrw2").text =unicode(row4.jmltrw2)
                ET.SubElement(xml_d, "jmltrw3").text =unicode(row4.jmltrw3)
                ET.SubElement(xml_d, "jmltrw4").text =unicode(row4.jmltrw4)

        return self.root

class r305Generator(JasperGenerator):
    """Jasper-Generator for Greetingcards"""
    def __init__(self):
        super(r305Generator, self).__init__()
        self.reportname = get_rpath('apbd/R3300.jrxml')
        self.xpath = '/apbd/unit/rekening'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        """Generates the XML File used by Jasperreports"""
        xml_a  =  ET.SubElement(self.root, 'unit')
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(xml_a, 'rekening')
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "level_id").text = unicode(row.level_id)
            ET.SubElement(xml_greeting, "defsign").text = unicode(row.defsign)
            ET.SubElement(xml_greeting, "urusan_kd").text = row.urusan_kd
            ET.SubElement(xml_greeting, "urusan_nm").text = row.urusan_nm
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "perubahan").text = row.perubahan
            ET.SubElement(xml_greeting, "jumlah1").text = unicode(row.jumlah1)
            ET.SubElement(xml_greeting, "jumlah2").text = unicode(row.jumlah2)
            ET.SubElement(xml_greeting, "jumlah3").text = unicode(row.jumlah3)
            ET.SubElement(xml_greeting, "jumlah4").text = unicode(row.jumlah4)
            ET.SubElement(xml_greeting, "trw1").text = unicode(row.trw1)
            ET.SubElement(xml_greeting, "trw2").text = unicode(row.trw2)
            ET.SubElement(xml_greeting, "trw3").text = unicode(row.trw3)
            ET.SubElement(xml_greeting, "trw4").text = unicode(row.trw4)            
        return self.root

class r306Generator(JasperGenerator):
    """Jasper-Generator for Greetingcards"""
    def __init__(self):
        super(r306Generator, self).__init__()
        self.reportname = get_rpath('apbd/R3310.jrxml')
        self.xpath = '/apbd/unit/rekening'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        """Generates the XML File used by Jasperreports"""
        xml_a  =  ET.SubElement(self.root, 'unit')
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(xml_a, 'rekening')
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "level_id").text = unicode(row.level_id)
            ET.SubElement(xml_greeting, "defsign").text = unicode(row.defsign)
            ET.SubElement(xml_greeting, "urusan_kd").text = row.urusan_kd
            ET.SubElement(xml_greeting, "urusan_nm").text = row.urusan_nm
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "perubahan").text = row.perubahan
            ET.SubElement(xml_greeting, "jumlah1").text = unicode(row.jumlah1)
            ET.SubElement(xml_greeting, "jumlah2").text = unicode(row.jumlah2)
            ET.SubElement(xml_greeting, "jumlah3").text = unicode(row.jumlah3)
            ET.SubElement(xml_greeting, "jumlah4").text = unicode(row.jumlah4)
            ET.SubElement(xml_greeting, "trw1").text = unicode(row.trw1)
            ET.SubElement(xml_greeting, "trw2").text = unicode(row.trw2)
            ET.SubElement(xml_greeting, "trw3").text = unicode(row.trw3)
            ET.SubElement(xml_greeting, "trw4").text = unicode(row.trw4)            
        return self.root

class r307Generator(JasperGenerator):
    """Jasper-Generator for Greetingcards"""
    def __init__(self):
        super(r307Generator, self).__init__()
        self.reportname = get_rpath('apbd/R3320.jrxml')
        self.xpath = '/apbd/unit/rekening'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        """Generates the XML File used by Jasperreports"""
        xml_a  =  ET.SubElement(self.root, 'unit')
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(xml_a, 'rekening')
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "level_id").text = unicode(row.level_id)
            ET.SubElement(xml_greeting, "defsign").text = unicode(row.defsign)
            ET.SubElement(xml_greeting, "urusan_kd").text = row.urusan_kd
            ET.SubElement(xml_greeting, "urusan_nm").text = row.urusan_nm
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "perubahan").text = row.perubahan
            ET.SubElement(xml_greeting, "jumlah1").text = unicode(row.jumlah1)
            ET.SubElement(xml_greeting, "jumlah2").text = unicode(row.jumlah2)
            ET.SubElement(xml_greeting, "jumlah3").text = unicode(row.jumlah3)
            ET.SubElement(xml_greeting, "jumlah4").text = unicode(row.jumlah4)
            ET.SubElement(xml_greeting, "trw1").text = unicode(row.trw1)
            ET.SubElement(xml_greeting, "trw2").text = unicode(row.trw2)
            ET.SubElement(xml_greeting, "trw3").text = unicode(row.trw3)
            ET.SubElement(xml_greeting, "trw4").text = unicode(row.trw4)            
        return self.root
        

class r400Generator(JasperGeneratorWithSubreport):
    def __init__(self):

        self.mainreport = get_rpath('apbd/R4000.jrxml')
        self.subreportlist = []
        self.subreportlist.append(get_rpath('apbd/R4000_subreport1.jrxml'))
        self.subreportlist.append(get_rpath('apbd/R4000_subreport2.jrxml'))
        print self.mainreport,self.subreportlist
        self.xpath = '/apbd/unit'
        
        self.root = ET.Element('apbd')

    def generate_xml(self, tobegreeted):
        xml_a  =  ET.SubElement(self.root, 'unit')

        for row in tobegreeted:
            ET.SubElement(xml_a, "tahun").text = unicode(row.tahun_id)
            ET.SubElement(xml_a, "urusan_kd").text = row.urusan_kd
            ET.SubElement(xml_a, "urusan_nm").text = row.urusan_nm
            ET.SubElement(xml_a, "unit_id").text = unicode(row.unit_id)
            ET.SubElement(xml_a, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_a, "unit_nm").text = row.unit_nm

            subq1 = DBSession.query(Rekening.kode.label('subrek_kd'),Rekening.nama.label('subrek_nm'),
                (KegiatanItem.vol_1_1* KegiatanItem.vol_1_2*KegiatanItem.hsat_1).label('jml1'),
                (KegiatanItem.vol_2_1* KegiatanItem.vol_2_2*KegiatanItem.hsat_2).label('jml2'),
                (KegiatanItem.vol_3_1* KegiatanItem.vol_3_2*KegiatanItem.hsat_3).label('jml3'),
                (KegiatanItem.vol_4_1* KegiatanItem.vol_4_2*KegiatanItem.hsat_4).label('jml4'))\
                .filter(KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                    KegiatanItem.rekening_id==Rekening.id,
                    KegiatanSub.tahun_id==row.tahun_id,
                    KegiatanSub.unit_id==row.unit_id)\
                .subquery()

            rowrek = DBSession.query(Rekening.kode.label('rek_kd'), Rekening.nama.label('rek_nm'),
                Rekening.level_id, Rekening.defsign, 
                func.sum(subq1.c.jml1).label('jumlah1'),func.sum(subq1.c.jml2).label('jumlah2'),
                func.sum(subq1.c.jml3).label('jumlah3'),func.sum(subq1.c.jml4).label('jumlah4'))\
                .filter(Rekening.kode==func.left(subq1.c.subrek_kd, func.length(Rekening.kode)))\
                .group_by(Rekening.kode, Rekening.nama,
                Rekening.level_id, Rekening.defsign)\
                .order_by(Rekening.kode).all()

            for row2 in rowrek :
                xml_b = ET.SubElement(xml_a, "rekening")
                ET.SubElement(xml_b, "rek_kd").text =row2.rek_kd
                ET.SubElement(xml_b, "rek_nm").text =row2.rek_nm
                ET.SubElement(xml_b, "level_id").text =unicode(row2.level_id)
                ET.SubElement(xml_b, "defsign").text =unicode(row2.defsign)
                ET.SubElement(xml_b, "jumlah1").text =unicode(row2.jumlah1)
                ET.SubElement(xml_b, "jumlah2").text =unicode(row2.jumlah2)
                ET.SubElement(xml_b, "jumlah3").text =unicode(row2.jumlah3)
                ET.SubElement(xml_b, "jumlah4").text =unicode(row2.jumlah4)
                
            rowtrw = DBSession.query(case([(KegiatanSub.kegiatan_id==2,1),(KegiatanSub.kegiatan_id==3,2),
                 (KegiatanSub.kegiatan_id==4,4),(KegiatanSub.kegiatan_id==5,5),
                 (KegiatanSub.kegiatan_id==6,6)], else_=3).label('kode'),
                 func.sum(KegiatanItem.bln01+KegiatanItem.bln02+KegiatanItem.bln03).label('trw1'),
                 func.sum(KegiatanItem.bln04+KegiatanItem.bln05+KegiatanItem.bln06).label('trw2'),
                 func.sum(KegiatanItem.bln07+KegiatanItem.bln08+KegiatanItem.bln09).label('trw3'),
                 func.sum(KegiatanItem.bln10+KegiatanItem.bln11+KegiatanItem.bln12).label('trw4')
                 )\
                .filter(KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                    KegiatanSub.tahun_id==row.tahun_id,
                    KegiatanSub.unit_id==row.unit_id)\
                .group_by(case([(KegiatanSub.kegiatan_id==2,1),(KegiatanSub.kegiatan_id==3,2),
                 (KegiatanSub.kegiatan_id==4,4),(KegiatanSub.kegiatan_id==5,5),
                 (KegiatanSub.kegiatan_id==6,6)], else_=3))\
                .order_by(case([(KegiatanSub.kegiatan_id==2,1),(KegiatanSub.kegiatan_id==3,2),
                 (KegiatanSub.kegiatan_id==4,4),(KegiatanSub.kegiatan_id==5,5),
                 (KegiatanSub.kegiatan_id==6,6)], else_=3))
            print "XXXXXX"
            print row.unit_id

            for row3 in rowtrw :
                xml_c = ET.SubElement(xml_a, "twl")
                ET.SubElement(xml_c, "kode").text =unicode(row3.kode)
                ET.SubElement(xml_c, "trw1").text =unicode(row3.trw1)
                ET.SubElement(xml_c, "trw2").text =unicode(row3.trw2)
                ET.SubElement(xml_c, "trw3").text =unicode(row3.trw3)
                ET.SubElement(xml_c, "trw4").text =unicode(row3.trw4)
                
        return self.root

class r401Generator(JasperGenerator):
    """Jasper-Generator for Greetingcards"""
    def __init__(self):
        super(r401Generator, self).__init__()
        self.reportname = get_rpath('apbd/R4100.jrxml')
        self.xpath = '/apbd/unit/rekening'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        """Generates the XML File used by Jasperreports"""
        xml_a  =  ET.SubElement(self.root, 'unit')
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(xml_a, 'rekening')
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "level_id").text = unicode(row.level_id)
            ET.SubElement(xml_greeting, "defsign").text = unicode(row.defsign)
            ET.SubElement(xml_greeting, "urusan_kd").text = row.urusan_kd
            ET.SubElement(xml_greeting, "urusan_nm").text = row.urusan_nm
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "perubahan").text = row.perubahan
            ET.SubElement(xml_greeting, "jumlah1").text = unicode(row.jumlah1)
            ET.SubElement(xml_greeting, "jumlah2").text = unicode(row.jumlah2)
            ET.SubElement(xml_greeting, "jumlah3").text = unicode(row.jumlah3)
            ET.SubElement(xml_greeting, "jumlah4").text = unicode(row.jumlah4)
            ET.SubElement(xml_greeting, "trw1").text = unicode(row.trw1)
            ET.SubElement(xml_greeting, "trw2").text = unicode(row.trw2)
            ET.SubElement(xml_greeting, "trw3").text = unicode(row.trw3)
            ET.SubElement(xml_greeting, "trw4").text = unicode(row.trw4)            
        return self.root

class r402Generator(JasperGenerator):
    """Jasper-Generator for Greetingcards"""
    def __init__(self):
        super(r402Generator, self).__init__()
        self.reportname = get_rpath('apbd/R4210.jrxml')
        self.xpath = '/apbd/unit/rekening'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        """Generates the XML File used by Jasperreports"""
        xml_a  =  ET.SubElement(self.root, 'unit')
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(xml_a, 'rekening')
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "level_id").text = unicode(row.level_id)
            ET.SubElement(xml_greeting, "defsign").text = unicode(row.defsign)
            ET.SubElement(xml_greeting, "urusan_kd").text = row.urusan_kd
            ET.SubElement(xml_greeting, "urusan_nm").text = row.urusan_nm
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "perubahan").text = row.perubahan
            ET.SubElement(xml_greeting, "jumlah1").text = unicode(row.jumlah1)
            ET.SubElement(xml_greeting, "jumlah2").text = unicode(row.jumlah2)
            ET.SubElement(xml_greeting, "jumlah3").text = unicode(row.jumlah3)
            ET.SubElement(xml_greeting, "jumlah4").text = unicode(row.jumlah4)
            ET.SubElement(xml_greeting, "trw1").text = unicode(row.trw1)
            ET.SubElement(xml_greeting, "trw2").text = unicode(row.trw2)
            ET.SubElement(xml_greeting, "trw3").text = unicode(row.trw3)
            ET.SubElement(xml_greeting, "trw4").text = unicode(row.trw4)
        return self.root

class r403Generator(JasperGenerator):
    """Jasper-Generator for Greetingcards"""
    def __init__(self):
        super(r403Generator, self).__init__()
        self.reportname = get_rpath('apbd/R4220.jrxml')
        self.xpath = '/apbd/unit/rekening'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        """Generates the XML File used by Jasperreports"""
        xml_a  =  ET.SubElement(self.root, 'unit')
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(xml_a, 'rekening')
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "urusan_kd").text = row.urusan_kd
            ET.SubElement(xml_greeting, "urusan_nm").text = row.urusan_nm
            ET.SubElement(xml_greeting, "unit_id").text = unicode(row.unit_id)
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "program_kd").text = row.program_kd
            ET.SubElement(xml_greeting, "program_nm").text = row.program_nm
            ET.SubElement(xml_greeting, "kegiatan_kd").text = row.kegiatan_kd
            ET.SubElement(xml_greeting, "kegiatan_nm").text = row.kegiatan_nm
            ET.SubElement(xml_greeting, "lokasi").text = row.lokasi
            ET.SubElement(xml_greeting, "target").text = row.target
            ET.SubElement(xml_greeting, "jumlah1").text = unicode(row.jumlah1)
            ET.SubElement(xml_greeting, "jumlah2").text = unicode(row.jumlah2)
            ET.SubElement(xml_greeting, "jumlah3").text = unicode(row.jumlah3)
            ET.SubElement(xml_greeting, "jumlah4").text = unicode(row.jumlah4)
        return self.root

class r404Generator(JasperGeneratorWithSubreport):
    """Jasper-Generator for Greetingcards"""
    def __init__(self):
        self.mainreport = get_rpath('apbd/R4221.jrxml')

        self.subreportlist = []
        self.subreportlist.append(get_rpath('apbd/R4221_subreport1.jrxml'))
        self.subreportlist.append(get_rpath('apbd/R4221_subreport2.jrxml'))
        self.subreportlist.append(get_rpath('apbd/R4221_subreport3.jrxml'))

        print self.mainreport,self.subreportlist
        self.xpath = '/apbd/kegiatan'
        
        self.root = ET.Element('apbd')

    def generate_xml(self, tobegreeted):
        xml_a  =  ET.SubElement(self.root, 'kegiatan')
        
        for row in tobegreeted:
            ET.SubElement(xml_a, "tahun").text = unicode(row.tahun_id)
            ET.SubElement(xml_a, "urusan_kd").text = row.kegiatans.programs.urusans.kode
            ET.SubElement(xml_a, "urusan_nm").text = row.kegiatans.programs.urusans.nama
            ET.SubElement(xml_a, "urusan_kd1").text = row.units.urusans.kode
            ET.SubElement(xml_a, "urusan_nm1").text = row.units.urusans.nama
            ET.SubElement(xml_a, "unit_id").text = unicode(row.unit_id)
            ET.SubElement(xml_a, "unit_kd").text = row.units.kode
            ET.SubElement(xml_a, "unit_nm").text = row.units.nama
            ET.SubElement(xml_a, "program_kd").text = row.kegiatans.programs.kode
            ET.SubElement(xml_a, "program_nm").text = row.kegiatans.programs.nama
            ET.SubElement(xml_a, "kegiatan_kd").text = row.kegiatans.kode
            ET.SubElement(xml_a, "kegiatan_nm").text = row.kegiatans.nama
            ET.SubElement(xml_a, "lokasi").text = row.lokasi
            ET.SubElement(xml_a, "target").text = row.target
            ET.SubElement(xml_a, "sasaran").text = row.sasaran
            ET.SubElement(xml_a, "amt_lalu").text = row.amt_lalu
            ET.SubElement(xml_a, "amt_yad").text = row.amt_yad
            ET.SubElement(xml_a, "perubahan").text = row.perubahan
            
            ET.SubElement(xml_a, "kegiatan_sub_id").text = unicode(row.id)
            rows = DBSession.query(KegiatanIndikator)\
              .filter(KegiatanIndikator.kegitan_sub_id==row.id)\
              .order_by(KegiatanIndikator.tipe,KegiatanIndikator.no_urut)
            for row2 in rows :
                xml_b = ET.SubElement(xml_a, "indikator")
                ET.SubElement(xml_b, "tipe").text =unicode(row2.tipe)
                ET.SubElement(xml_b, "no_urut").text =unicode(row2.no_urut)
                ET.SubElement(xml_b, "tolok_ukur_1").text =row2.tolok_ukur_1
                ET.SubElement(xml_b, "volume_1").text =unicode(row2.volume_1)
                ET.SubElement(xml_b, "satuan_1").text =row2.satuan_1
                ET.SubElement(xml_b, "tolok_ukur_2").text =row2.tolok_ukur_2
                ET.SubElement(xml_b, "volume_2").text =unicode(row2.volume_2)
                ET.SubElement(xml_b, "satuan_2").text =row2.satuan_2
                ET.SubElement(xml_b, "tolok_ukur_3").text =row2.tolok_ukur_3
                ET.SubElement(xml_b, "volume_3").text =unicode(row2.volume_3)
                ET.SubElement(xml_b, "satuan_3").text =row2.satuan_3
                ET.SubElement(xml_b, "tolok_ukur_4").text =row2.tolok_ukur_4
                ET.SubElement(xml_b, "volume_4").text =unicode(row2.volume_4)
                ET.SubElement(xml_b, "satuan_4").text =row2.satuan_4
            
            """rowitems = DBSession.query(KegiatanItem)\
              .filter(KegiatanItem.kegiatan_sub_id==row.id, KegiatanItem.rekening_id==Rekening.id)\
              .order_by(Rekening.kode,KegiatanItem.kode)
            """
            subq1 = DBSession.query(Rekening.kode.label('subrek_kd'),Rekening.nama.label('subrek_nm'),
                    KegiatanItem.kode.label('item_kd'), KegiatanItem.nama.label('item_nm'),
                    (KegiatanItem.vol_1_1*KegiatanItem.vol_1_2).label('volume1'),
                    KegiatanItem.hsat_1.label('harga1'),KegiatanItem.sat_1_1,KegiatanItem.sat_1_2,
                    (KegiatanItem.vol_1_1* KegiatanItem.vol_1_2*KegiatanItem.hsat_1).label('jml1'),
                    (KegiatanItem.vol_2_1*KegiatanItem.vol_2_2).label('volume2'),
                    KegiatanItem.hsat_2.label('harga2'),KegiatanItem.sat_2_1,KegiatanItem.sat_2_2,
                    (KegiatanItem.vol_2_1* KegiatanItem.vol_2_2*KegiatanItem.hsat_2).label('jml2'),
                    (KegiatanItem.vol_3_1*KegiatanItem.vol_3_2).label('volume3'),
                    KegiatanItem.hsat_3.label('harga3'),KegiatanItem.sat_3_1,KegiatanItem.sat_3_2,
                    (KegiatanItem.vol_3_1* KegiatanItem.vol_3_2*KegiatanItem.hsat_3).label('jml3'),
                    (KegiatanItem.vol_4_1*KegiatanItem.vol_4_2).label('volume4'),
                    KegiatanItem.hsat_4.label('harga4'),KegiatanItem.sat_4_1,KegiatanItem.sat_4_2,
                    (KegiatanItem.vol_4_1* KegiatanItem.vol_4_2*KegiatanItem.hsat_4).label('jml4'))\
                    .filter(KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                            KegiatanItem.rekening_id==Rekening.id,
                            KegiatanItem.kegiatan_sub_id==row.id)\
                    .subquery()

            rowitems = DBSession.query(Rekening.kode.label('rek_kd'), Rekening.nama.label('rek_nm'),Rekening.level_id,
                    subq1.c.item_kd, subq1.c.item_nm, 
                    subq1.c.volume1, subq1.c.volume2, subq1.c.volume3, subq1.c.volume4, 
                    subq1.c.harga1, subq1.c.harga2, subq1.c.harga3, subq1.c.harga4, 
                    subq1.c.sat_1_1, subq1.c.sat_1_2, subq1.c.sat_2_1, subq1.c.sat_2_2, 
                    subq1.c.sat_3_1, subq1.c.sat_3_2, subq1.c.sat_4_1, subq1.c.sat_4_2,
                    func.sum(subq1.c.jml1).label('jumlah1'),func.sum(subq1.c.jml2).label('jumlah2'),
                    func.sum(subq1.c.jml3).label('jumlah3'),func.sum(subq1.c.jml4).label('jumlah4'))\
                    .filter(Rekening.kode==func.left(subq1.c.subrek_kd, func.length(Rekening.kode)))\
                    .group_by(Rekening.kode, Rekening.nama,Rekening.level_id,
                    subq1.c.item_kd, subq1.c.item_nm, 
                    subq1.c.volume1, subq1.c.volume2, subq1.c.volume3, subq1.c.volume4, 
                    subq1.c.harga1, subq1.c.harga2, subq1.c.harga3, subq1.c.harga4, 
                    subq1.c.sat_1_1, subq1.c.sat_1_2, subq1.c.sat_2_1, subq1.c.sat_2_2, 
                    subq1.c.sat_3_1, subq1.c.sat_3_2, subq1.c.sat_4_1, subq1.c.sat_4_2)\
                    .order_by(Rekening.kode).all()                    

            for row3 in rowitems :
                xml_c = ET.SubElement(xml_a, "item")
                ET.SubElement(xml_c, "rek_kd").text =row3.rek_kd
                ET.SubElement(xml_c, "rek_nm").text =row3.rek_nm
                ET.SubElement(xml_c, "level_id").text =unicode(row3.level_id)
                ET.SubElement(xml_c, "item_kd").text =row3.item_kd
                ET.SubElement(xml_c, "item_nm").text =row3.item_nm
                ET.SubElement(xml_c, "volume1").text =unicode(row3.volume1)
                ET.SubElement(xml_c, "volume2").text =unicode(row3.volume2)
                ET.SubElement(xml_c, "volume3").text =unicode(row3.volume3)
                ET.SubElement(xml_c, "volume4").text =unicode(row3.volume4)
                ET.SubElement(xml_c, "harga1").text =unicode(row3.harga1)
                ET.SubElement(xml_c, "harga2").text =unicode(row3.harga2)
                ET.SubElement(xml_c, "harga3").text =unicode(row3.harga3)
                ET.SubElement(xml_c, "harga4").text =unicode(row3.harga4)
                ET.SubElement(xml_c, "satuan11").text =row3.sat_1_1
                ET.SubElement(xml_c, "satuan12").text =row3.sat_1_2
                ET.SubElement(xml_c, "satuan21").text =row3.sat_2_1
                ET.SubElement(xml_c, "satuan22").text =row3.sat_2_2
                ET.SubElement(xml_c, "satuan31").text =row3.sat_3_1
                ET.SubElement(xml_c, "satuan32").text =row3.sat_3_2
                ET.SubElement(xml_c, "satuan41").text =row3.sat_4_1
                ET.SubElement(xml_c, "satuan42").text =row3.sat_4_2
                ET.SubElement(xml_c, "jumlah1").text =unicode(row3.jumlah1)
                ET.SubElement(xml_c, "jumlah2").text =unicode(row3.jumlah2)
                ET.SubElement(xml_c, "jumlah3").text =unicode(row3.jumlah3)
                ET.SubElement(xml_c, "jumlah4").text =unicode(row3.jumlah4)

            rowtrw = DBSession.query(func.sum(KegiatanItem.bln01+KegiatanItem.bln02+KegiatanItem.bln03).label('jmltrw1'),
                    func.sum(KegiatanItem.bln04+KegiatanItem.bln05+KegiatanItem.bln06).label('jmltrw2'),
                    func.sum(KegiatanItem.bln07+KegiatanItem.bln08+KegiatanItem.bln09).label('jmltrw3'),
                    func.sum(KegiatanItem.bln10+KegiatanItem.bln11+KegiatanItem.bln12).label('jmltrw4'))\
                    .filter(KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                            KegiatanSub.unit_id==row.unit_id,
                            KegiatanSub.tahun_id==row.tahun_id,
                            KegiatanItem.kegiatan_sub_id==row.id)\

            for row4 in rowtrw :
                xml_d = ET.SubElement(xml_a, "trw")
                ET.SubElement(xml_d, "jmltrw1").text =unicode(row4.jmltrw1)
                ET.SubElement(xml_d, "jmltrw2").text =unicode(row4.jmltrw2)
                ET.SubElement(xml_d, "jmltrw3").text =unicode(row4.jmltrw3)
                ET.SubElement(xml_d, "jmltrw4").text =unicode(row4.jmltrw4)

        return self.root

class r405Generator(JasperGenerator):
    """Jasper-Generator for Greetingcards"""
    def __init__(self):
        super(r405Generator, self).__init__()
        self.reportname = get_rpath('apbd/R4300.jrxml')
        self.xpath = '/apbd/unit/rekening'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        """Generates the XML File used by Jasperreports"""
        xml_a  =  ET.SubElement(self.root, 'unit')
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(xml_a, 'rekening')
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "level_id").text = unicode(row.level_id)
            ET.SubElement(xml_greeting, "defsign").text = unicode(row.defsign)
            ET.SubElement(xml_greeting, "urusan_kd").text = row.urusan_kd
            ET.SubElement(xml_greeting, "urusan_nm").text = row.urusan_nm
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "perubahan").text = row.perubahan
            ET.SubElement(xml_greeting, "jumlah1").text = unicode(row.jumlah1)
            ET.SubElement(xml_greeting, "jumlah2").text = unicode(row.jumlah2)
            ET.SubElement(xml_greeting, "jumlah3").text = unicode(row.jumlah3)
            ET.SubElement(xml_greeting, "jumlah4").text = unicode(row.jumlah4)
            ET.SubElement(xml_greeting, "trw1").text = unicode(row.trw1)
            ET.SubElement(xml_greeting, "trw2").text = unicode(row.trw2)
            ET.SubElement(xml_greeting, "trw3").text = unicode(row.trw3)
            ET.SubElement(xml_greeting, "trw4").text = unicode(row.trw4)            
        return self.root

class r406Generator(JasperGenerator):
    """Jasper-Generator for Greetingcards"""
    def __init__(self):
        super(r406Generator, self).__init__()
        self.reportname = get_rpath('apbd/R4310.jrxml')
        self.xpath = '/apbd/unit/rekening'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        """Generates the XML File used by Jasperreports"""
        xml_a  =  ET.SubElement(self.root, 'unit')
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(xml_a, 'rekening')
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "level_id").text = unicode(row.level_id)
            ET.SubElement(xml_greeting, "defsign").text = unicode(row.defsign)
            ET.SubElement(xml_greeting, "urusan_kd").text = row.urusan_kd
            ET.SubElement(xml_greeting, "urusan_nm").text = row.urusan_nm
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "perubahan").text = row.perubahan
            ET.SubElement(xml_greeting, "jumlah1").text = unicode(row.jumlah1)
            ET.SubElement(xml_greeting, "jumlah2").text = unicode(row.jumlah2)
            ET.SubElement(xml_greeting, "jumlah3").text = unicode(row.jumlah3)
            ET.SubElement(xml_greeting, "jumlah4").text = unicode(row.jumlah4)
            ET.SubElement(xml_greeting, "trw1").text = unicode(row.trw1)
            ET.SubElement(xml_greeting, "trw2").text = unicode(row.trw2)
            ET.SubElement(xml_greeting, "trw3").text = unicode(row.trw3)
            ET.SubElement(xml_greeting, "trw4").text = unicode(row.trw4)            
        return self.root

class r407Generator(JasperGenerator):
    """Jasper-Generator for Greetingcards"""
    def __init__(self):
        super(r407Generator, self).__init__()
        self.reportname = get_rpath('apbd/R4320.jrxml')
        self.xpath = '/apbd/unit/rekening'
        self.root = ET.Element('apbd') 

    def generate_xml(self, tobegreeted):
        """Generates the XML File used by Jasperreports"""
        xml_a  =  ET.SubElement(self.root, 'unit')
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(xml_a, 'rekening')
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "level_id").text = unicode(row.level_id)
            ET.SubElement(xml_greeting, "defsign").text = unicode(row.defsign)
            ET.SubElement(xml_greeting, "urusan_kd").text = row.urusan_kd
            ET.SubElement(xml_greeting, "urusan_nm").text = row.urusan_nm
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "perubahan").text = row.perubahan
            ET.SubElement(xml_greeting, "jumlah1").text = unicode(row.jumlah1)
            ET.SubElement(xml_greeting, "jumlah2").text = unicode(row.jumlah2)
            ET.SubElement(xml_greeting, "jumlah3").text = unicode(row.jumlah3)
            ET.SubElement(xml_greeting, "jumlah4").text = unicode(row.jumlah4)
            ET.SubElement(xml_greeting, "trw1").text = unicode(row.trw1)
            ET.SubElement(xml_greeting, "trw2").text = unicode(row.trw2)
            ET.SubElement(xml_greeting, "trw3").text = unicode(row.trw3)
            ET.SubElement(xml_greeting, "trw4").text = unicode(row.trw4)            
        return self.root

class ViewAnggaranLap(BaseViews):
    def __init__(self, context, request):
        BaseViews.__init__(self, context, request)
        self.app = 'anggaran'

        row = DBSession.query(Tahun.status_apbd).filter(Tahun.tahun==self.tahun).first()
        self.session['status_apbd'] = row and row[0] or 0


        self.status_apbd =  'status_apbd' in self.session and self.session['status_apbd'] or 0        
        #self.status_apbd_nm =  status_apbd[str(self.status_apbd)]        
        
        self.all_unit =  'all_unit' in self.session and self.session['all_unit'] or 0        
        self.unit_id  = 'unit_id' in self.session and self.session['unit_id'] or 0
        self.unit_kd  = 'unit_kd' in self.session and self.session['unit_kd'] or "X.XX.XX"
        self.unit_nm  = 'unit_nm' in self.session and self.session['unit_nm'] or "Pilih Unit"
        self.keg_id  = 'keg_id' in self.session and self.session['keg_id'] or 0
        
        self.datas['status_apbd'] = self.status_apbd 
        #self.datas['status_apbd_nm'] = self.status_apbd_nm
        self.datas['all_unit'] = self.all_unit
        self.datas['unit_kd'] = self.unit_kd
        self.datas['unit_nm'] = self.unit_nm
        self.datas['unit_id'] = self.unit_id
        
    @view_config(route_name="anggaran_r000", renderer="osipkd:templates/apbd/anggaran/r000.pt", permission="read")
    def anggaran_r000(self):
        params = self.request.params
        return dict(datas=self.datas)
  
    @view_config(route_name="anggaran_r000_act")
    def anggaran_r000_act(self):
        req    = self.request
        params = req.params
        url_dict = req.matchdict

        if url_dict['act']=='r001' :
            query = DBSession.query(Urusan.kode, Urusan.nama).order_by(Urusan.kode).all()
            generator = r001Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
        elif url_dict['act']=='r002' :
            query = DBSession.query(Urusan.kode.label("urusankd"), Unit.kode, Unit.nama, Unit.kategori, Unit.singkat).\
                    filter(Unit.urusan_id==Urusan.id).order_by(Urusan.kode,Unit.kode).all()
            generator = r002Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
        elif url_dict['act']=='r003' :
            query = DBSession.query(Program.kode, Program.nama, Kegiatan.kode.label("kegiatankd"), Kegiatan.nama.label("kegiatannm")).\
                    filter(Kegiatan.program_id==Program.id).order_by(Program.kode,Kegiatan.kode).all()
            generator = r003Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
        elif url_dict['act']=='r041' :
            query = DBSession.query(Rekening.kode, Rekening.nama, Rekening.level_id).order_by(Rekening.kode).all()
            generator = r041Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
        elif url_dict['act']=='r042' :
            query = DBSession.query(Rekening.kode, Rekening.nama, Rekening.level_id).order_by(Rekening.kode).all()
            generator = r042Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
        elif url_dict['act']=='r005' :
            query = DBSession.query(Pegawai.kode, Pegawai.nama).order_by(Pegawai.kode).all()
            generator = r005Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
        elif url_dict['act']=='r009' :
            query = DBSession.query(Fungsi.kode, Fungsi.nama).order_by(Fungsi.kode).all()
            generator = r009Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
        elif url_dict['act']=='r010' :
            query = DBSession.query(Jabatan.kode, Jabatan.nama).order_by(Jabatan.kode).all()
            generator = r010Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)   
            return response
        elif url_dict['act']=='r011' :
            query = DBSession.query(Pegawai.kode, Pegawai.nama, Jabatan.nama.label('jabatan'), Unit.nama.label('skpd'), Pejabat.mulai, Pejabat.selesai
                  ).filter(Pejabat.pegawai_id==Pegawai.id, Pejabat.unit_id==Unit.id, Pejabat.jabatan_id==Jabatan.id
                  ).order_by(Pegawai.kode).all()
            generator = r011Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
        elif url_dict['act']=='r012' :
            query = DBSession.query(Tahun.tahun, Tahun.status_apbd, Tahun.tanggal_1, Tahun.tanggal_2, Tahun.tanggal_3, Tahun.tanggal_4
                  ).order_by(Tahun.tahun).all()
            generator = r011Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
        else:
            return HTTPNotFound() #TODO: Warning Hak Akses 


    @view_config(route_name="anggaran_r100", renderer="../../templates/apbd/anggaran/r100.pt", permission="read")
    def anggaran_r100(self):
        params = self.request.params
        return dict(datas=self.datas, 
               row=KegiatanSub.get_header(self.unit_id, self.keg_id),)

    @view_config(route_name="anggaran_r100_act", renderer="json")
    def anggaran_r100_act(self):
        req    = self.request
        params = req.params
        url_dict = req.matchdict
        pk_id = 'id' in params and params['id'] and int(params['id']) or 0
        if url_dict['act']=='grid' :
            # defining columns
            columns = []
            columns.append(ColumnDT('id'))
            columns.append(ColumnDT('tipe'))
            columns.append(ColumnDT('no_urut'))
            columns.append(ColumnDT("".join(['tolok_ukur_',str(self.status_apbd)])))
            columns.append(ColumnDT("".join(['volume_',str(self.status_apbd)])))
            columns.append(ColumnDT("".join(['satuan_',str(self.status_apbd)])))

            query = DBSession.query(KegiatanIndikator)\
                .join(KegiatanSub)\
                .filter(KegiatanSub.id==keg_id,
                        KegiatanSub.unit_id==self.unit_id)
            rowTable = DataTables(req, KegiatanIndikator, query, columns)
            return rowTable.output_result()

        elif url_dict['act']=='0' :
            subq1 = DBSession.query(Rekening.kode.label('subrek_kd'),Rekening.nama.label('subrek_nm'),
                (KegiatanItem.vol_1_1* KegiatanItem.vol_1_2*KegiatanItem.hsat_1).label('jml1'),
                (KegiatanItem.vol_2_1* KegiatanItem.vol_2_2*KegiatanItem.hsat_2).label('jml2'),
                (KegiatanItem.vol_3_1* KegiatanItem.vol_3_2*KegiatanItem.hsat_3).label('jml3'),
                (KegiatanItem.vol_4_1* KegiatanItem.vol_4_2*KegiatanItem.hsat_4).label('jml4'),
                KegiatanSub.tahun_id.label('tahun'), Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'),
                Urusan.kode.label('urusan_kd'), Urusan.nama.label('urusan_nm'))\
                .filter(KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                        KegiatanItem.rekening_id==Rekening.id,
                        KegiatanSub.unit_id==Unit.id,
                        Unit.urusan_id==Urusan.id,
                        KegiatanSub.tahun_id==self.session['tahun'],
                        KegiatanSub.unit_id==self.unit_id)\
                .subquery()

            query = DBSession.query(Rekening.kode.label('rek_kd'), Rekening.nama.label('rek_nm'),
                Rekening.level_id, Rekening.defsign, subq1.c.urusan_kd, subq1.c.urusan_nm,
                subq1.c.unit_kd, subq1.c.unit_nm, subq1.c.tahun, 
                func.sum(subq1.c.jml1).label('jumlah1'),func.sum(subq1.c.jml2).label('jumlah2'),
                func.sum(subq1.c.jml3).label('jumlah3'),func.sum(subq1.c.jml4).label('jumlah4'))\
                .filter(Rekening.kode==func.left(subq1.c.subrek_kd, func.length(Rekening.kode)))\
                .group_by(Rekening.kode, Rekening.nama,
                Rekening.level_id, Rekening.defsign, subq1.c.urusan_kd, subq1.c.urusan_nm,
                subq1.c.unit_kd, subq1.c.unit_nm, subq1.c.tahun)\
                .order_by(Rekening.kode).all()                    

            generator = r100Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
            
        elif url_dict['act']=='1' :
            subq1 = DBSession.query(Rekening.kode.label('subrek_kd'),Rekening.nama.label('subrek_nm'),
                KegiatanItem.kode.label('item_kd'), KegiatanItem.nama.label('item_nm'),
                (KegiatanItem.vol_1_1*KegiatanItem.vol_1_2).label('volume1'),KegiatanItem.sat_1_1,KegiatanItem.sat_1_2,
                KegiatanItem.hsat_1.label('harga1'),
                (KegiatanItem.vol_1_1* KegiatanItem.vol_1_2*KegiatanItem.hsat_1).label('jml1'),
                (KegiatanItem.vol_2_1*KegiatanItem.vol_2_2).label('volume2'),KegiatanItem.sat_2_1,KegiatanItem.sat_2_2,
                KegiatanItem.hsat_2.label('harga2'),
                (KegiatanItem.vol_2_1* KegiatanItem.vol_2_2*KegiatanItem.hsat_2).label('jml2'),
                (KegiatanItem.vol_3_1*KegiatanItem.vol_3_2).label('volume3'),KegiatanItem.sat_3_1,KegiatanItem.sat_3_2,
                KegiatanItem.hsat_3.label('harga3'),
                (KegiatanItem.vol_3_1* KegiatanItem.vol_3_2*KegiatanItem.hsat_3).label('jml3'),
                (KegiatanItem.vol_4_1*KegiatanItem.vol_4_2).label('volume4'),KegiatanItem.sat_4_1,KegiatanItem.sat_4_2,
                KegiatanItem.hsat_4.label('harga4'),
                (KegiatanItem.vol_4_1* KegiatanItem.vol_4_2*KegiatanItem.hsat_4).label('jml4'),
                KegiatanSub.tahun_id.label('tahun'), 
                Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'),
                Urusan.kode.label('urusan_kd'), Urusan.nama.label('urusan_nm'))\
                .filter(KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                        KegiatanItem.rekening_id==Rekening.id,
                        KegiatanSub.unit_id==Unit.id,
                        Unit.urusan_id==Urusan.id,
                        KegiatanSub.tahun_id==self.session['tahun'],
                        KegiatanSub.unit_id==self.unit_id,
                        KegiatanSub.kegiatan_id==2)\
                .subquery()

            query = DBSession.query(Rekening.kode.label('rek_kd'), Rekening.nama.label('rek_nm'),
                Rekening.level_id, Rekening.defsign, subq1.c.urusan_kd, subq1.c.urusan_nm,
                func.substr(Rekening.kode,1,1).label('rek_kd1'),func.substr(Rekening.kode,1,3).label('rek_kd2'),
                func.substr(Rekening.kode,1,5).label('rek_kd3'),func.substr(Rekening.kode,1,8).label('rek_kd4'),
                subq1.c.unit_kd, subq1.c.unit_nm, subq1.c.tahun, 
                subq1.c.item_kd, subq1.c.item_nm, 
                subq1.c.volume1, subq1.c.sat_1_1, subq1.c.sat_1_2, subq1.c.harga1,
                subq1.c.volume2, subq1.c.sat_2_1, subq1.c.sat_2_2, subq1.c.harga2,
                subq1.c.volume3, subq1.c.sat_3_1, subq1.c.sat_3_2, subq1.c.harga3,
                subq1.c.volume4, subq1.c.sat_4_1, subq1.c.sat_4_2, subq1.c.harga4,
                func.sum(subq1.c.jml1).label('jumlah1'),func.sum(subq1.c.jml2).label('jumlah2'),
                func.sum(subq1.c.jml3).label('jumlah3'),func.sum(subq1.c.jml4).label('jumlah4'))\
                .filter(Rekening.kode==func.left(subq1.c.subrek_kd, func.length(Rekening.kode)))\
                .group_by(Rekening.kode, Rekening.nama,
                Rekening.level_id, Rekening.defsign, subq1.c.urusan_kd, subq1.c.urusan_nm,
                func.substr(Rekening.kode,1,1),func.substr(Rekening.kode,1,3),
                func.substr(Rekening.kode,1,5),func.substr(Rekening.kode,1,8),
                subq1.c.unit_kd, subq1.c.unit_nm, subq1.c.tahun, 
                subq1.c.item_kd, subq1.c.item_nm, 
                subq1.c.volume1, subq1.c.sat_1_1, subq1.c.sat_1_2, subq1.c.harga1,
                subq1.c.volume2, subq1.c.sat_2_1, subq1.c.sat_2_2, subq1.c.harga2,
                subq1.c.volume3, subq1.c.sat_3_1, subq1.c.sat_3_2, subq1.c.harga3,
                subq1.c.volume4, subq1.c.sat_4_1, subq1.c.sat_4_2, subq1.c.harga4)\
                .order_by(Rekening.kode).all()                    

            generator = r101Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        elif url_dict['act']=='21' :
            subq1 = DBSession.query(Rekening.kode.label('subrek_kd'),Rekening.nama.label('subrek_nm'),
                (KegiatanItem.vol_1_1* KegiatanItem.vol_1_2*KegiatanItem.hsat_1).label('jml1'),
                (KegiatanItem.vol_2_1* KegiatanItem.vol_2_2*KegiatanItem.hsat_2).label('jml2'),
                (KegiatanItem.vol_3_1* KegiatanItem.vol_3_2*KegiatanItem.hsat_3).label('jml3'),
                (KegiatanItem.vol_4_1* KegiatanItem.vol_4_2*KegiatanItem.hsat_4).label('jml4'),
                Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'),
                Urusan.kode.label('urusan_kd'), Urusan.nama.label('urusan_nm'),
                KegiatanSub.tahun_id.label('tahun')).join(KegiatanItem).join(KegiatanSub).join(Kegiatan).join(Unit).join(Urusan)\
                .filter(
                        Unit.urusan_id==Urusan.id,
                        KegiatanSub.tahun_id==self.session['tahun'],
                        KegiatanSub.unit_id==self.session['unit_id'],
                        Kegiatan.kode=='0.00.00.21')\
                .subquery()

            query = DBSession.query(Rekening.kode.label('rek_kd'), Rekening.nama.label('rek_nm'),
                Rekening.level_id, Rekening.defsign, subq1.c.urusan_kd, subq1.c.urusan_nm,
                func.substr(Rekening.kode,1,1).label('rek_kd1'),func.substr(Rekening.kode,1,3).label('rek_kd2'),
                func.substr(Rekening.kode,1,5).label('rek_kd3'),func.substr(Rekening.kode,1,8).label('rek_kd4'),
                subq1.c.unit_kd, subq1.c.unit_nm, subq1.c.tahun, 
                func.sum(subq1.c.jml1).label('jumlah1'),func.sum(subq1.c.jml2).label('jumlah2'),
                func.sum(subq1.c.jml3).label('jumlah3'),func.sum(subq1.c.jml4).label('jumlah4'))\
                .filter(Rekening.kode==func.left(subq1.c.subrek_kd, func.length(Rekening.kode)))\
                .group_by(Rekening.kode, Rekening.nama,
                Rekening.level_id, Rekening.defsign, subq1.c.urusan_kd, subq1.c.urusan_nm,
                func.substr(Rekening.kode,1,1),func.substr(Rekening.kode,1,3),
                func.substr(Rekening.kode,1,5),func.substr(Rekening.kode,1,8),
                subq1.c.unit_kd, subq1.c.unit_nm, subq1.c.tahun)\
                .order_by(Rekening.kode).all()                    

            generator = r102Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        elif url_dict['act']=='22' :
            
            query = DBSession.query(KegiatanItem)\
                  .filter(KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                   KegiatanSub.tahun_id==self.session['tahun'],
                   KegiatanSub.unit_id==self.unit_id,
                   KegiatanSub.kegiatan_id>6)
                  
            generator = r103Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        elif url_dict['act']=='221' :
            """query = DBSession.query(KegiatanSub)\
                   .join(UnitTahun)\
                   .filter(KegiatanSub.tahun_id==UnitTahun.tahun_id,
                   KegiatanSub.unit_id==UnitTahun.unit_id,
                   KegiatanSub.tahun_id==self.session['tahun'],
                   KegiatanSub.unit_id==self.unit_id, 
                   KegiatanSub.id==self.request.params['id'])
            """       
            query = DBSession.query(KegiatanSub)\
                 .filter(KegiatanSub.tahun_id==self.session['tahun'],
                   KegiatanSub.unit_id==self.unit_id, 
                   KegiatanSub.id==self.request.params['id'])
                   
            generator = r104Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
            

        elif url_dict['act']=='3' :
            subq1 = DBSession.query(Rekening.kode.label('subrek_kd'),Rekening.nama.label('subrek_nm'),
                (KegiatanItem.vol_1_1* KegiatanItem.vol_1_2*KegiatanItem.hsat_1).label('jml1'),
                (KegiatanItem.vol_2_1* KegiatanItem.vol_2_2*KegiatanItem.hsat_2).label('jml2'),
                (KegiatanItem.vol_3_1* KegiatanItem.vol_3_2*KegiatanItem.hsat_3).label('jml3'),
                (KegiatanItem.vol_4_1* KegiatanItem.vol_4_2*KegiatanItem.hsat_4).label('jml4'),
                Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'),
                Urusan.kode.label('urusan_kd'), Urusan.nama.label('urusan_nm'),
                KegiatanSub.tahun_id.label('tahun'))\
                .filter(KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                        KegiatanItem.rekening_id==Rekening.id,
                        KegiatanSub.unit_id==Unit.id,
                        Unit.urusan_id==Urusan.id,
                        KegiatanSub.tahun_id==self.session['tahun'],
                        KegiatanSub.unit_id==self.unit_id,
                        KegiatanSub.kegiatan_id.in_([4,5]))\
                .subquery()

            query = DBSession.query(Rekening.kode.label('rek_kd'), Rekening.nama.label('rek_nm'),
                Rekening.level_id, Rekening.defsign, subq1.c.urusan_kd, subq1.c.urusan_nm,
                func.substr(Rekening.kode,1,1).label('rek_kd1'),func.substr(Rekening.kode,1,3).label('rek_kd2'),
                func.substr(Rekening.kode,1,5).label('rek_kd3'),func.substr(Rekening.kode,1,8).label('rek_kd4'),
                subq1.c.unit_kd, subq1.c.unit_nm, subq1.c.tahun, 
                func.sum(subq1.c.jml1).label('jumlah1'),func.sum(subq1.c.jml2).label('jumlah2'),
                func.sum(subq1.c.jml3).label('jumlah3'),func.sum(subq1.c.jml4).label('jumlah4'))\
                .filter(Rekening.kode==func.left(subq1.c.subrek_kd, func.length(Rekening.kode)))\
                .group_by(Rekening.kode, Rekening.nama,
                Rekening.level_id, Rekening.defsign, subq1.c.urusan_kd, subq1.c.urusan_nm,
                func.substr(Rekening.kode,1,1),func.substr(Rekening.kode,1,3),
                func.substr(Rekening.kode,1,5),func.substr(Rekening.kode,1,8),
                subq1.c.unit_kd, subq1.c.unit_nm, subq1.c.tahun)\
                .order_by(Rekening.kode).all()                    

            generator = r105Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        elif url_dict['act']=='31' :
            subq1 = DBSession.query(Rekening.kode.label('subrek_kd'),Rekening.nama.label('subrek_nm'),
                (KegiatanItem.vol_1_1* KegiatanItem.vol_1_2*KegiatanItem.hsat_1).label('jml1'),
                (KegiatanItem.vol_2_1* KegiatanItem.vol_2_2*KegiatanItem.hsat_2).label('jml2'),
                (KegiatanItem.vol_3_1* KegiatanItem.vol_3_2*KegiatanItem.hsat_3).label('jml3'),
                (KegiatanItem.vol_4_1* KegiatanItem.vol_4_2*KegiatanItem.hsat_4).label('jml4'),
                Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'),
                Urusan.kode.label('urusan_kd'), Urusan.nama.label('urusan_nm'),
                KegiatanSub.tahun_id.label('tahun'))\
                .filter(KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                        KegiatanItem.rekening_id==Rekening.id,
                        KegiatanSub.unit_id==Unit.id,
                        Unit.urusan_id==Urusan.id,
                        KegiatanSub.tahun_id==self.session['tahun'],
                        KegiatanSub.unit_id==self.unit_id,
                        KegiatanSub.kegiatan_id==4)\
                .subquery()

            query = DBSession.query(Rekening.kode.label('rek_kd'), Rekening.nama.label('rek_nm'),
                Rekening.level_id, Rekening.defsign, subq1.c.urusan_kd, subq1.c.urusan_nm,
                func.substr(Rekening.kode,1,1).label('rek_kd1'),func.substr(Rekening.kode,1,3).label('rek_kd2'),
                func.substr(Rekening.kode,1,5).label('rek_kd3'),func.substr(Rekening.kode,1,8).label('rek_kd4'),
                subq1.c.unit_kd, subq1.c.unit_nm, subq1.c.tahun, 
                func.sum(subq1.c.jml1).label('jumlah1'),func.sum(subq1.c.jml2).label('jumlah2'),
                func.sum(subq1.c.jml3).label('jumlah3'),func.sum(subq1.c.jml4).label('jumlah4'))\
                .filter(Rekening.kode==func.left(subq1.c.subrek_kd, func.length(Rekening.kode)))\
                .group_by(Rekening.kode, Rekening.nama,
                Rekening.level_id, Rekening.defsign, subq1.c.urusan_kd, subq1.c.urusan_nm,
                func.substr(Rekening.kode,1,1),func.substr(Rekening.kode,1,3),
                func.substr(Rekening.kode,1,5),func.substr(Rekening.kode,1,8),
                subq1.c.unit_kd, subq1.c.unit_nm, subq1, subq1.c.tahun)\
                .order_by(Rekening.kode).all()                    

            generator = r106Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        elif url_dict['act']=='32' :
            subq1 = DBSession.query(Rekening.kode.label('subrek_kd'),Rekening.nama.label('subrek_nm'),
                (KegiatanItem.vol_1_1* KegiatanItem.vol_1_2*KegiatanItem.hsat_1).label('jml1'),
                (KegiatanItem.vol_2_1* KegiatanItem.vol_2_2*KegiatanItem.hsat_2).label('jml2'),
                (KegiatanItem.vol_3_1* KegiatanItem.vol_3_2*KegiatanItem.hsat_3).label('jml3'),
                (KegiatanItem.vol_4_1* KegiatanItem.vol_4_2*KegiatanItem.hsat_4).label('jml4'),
                Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'),
                Urusan.kode.label('urusan_kd'), Urusan.nama.label('urusan_nm'),
                KegiatanSub.tahun_id.label('tahun'))\
                .filter(KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                        KegiatanItem.rekening_id==Rekening.id,
                        KegiatanSub.unit_id==Unit.id,
                        Unit.urusan_id==Urusan.id,
                        KegiatanSub.tahun_id==self.session['tahun'],
                        KegiatanSub.unit_id==self.unit_id,
                        KegiatanSub.kegiatan_id==5)\
                .subquery()

            query = DBSession.query(Rekening.kode.label('rek_kd'), Rekening.nama.label('rek_nm'),
                Rekening.level_id, Rekening.defsign, subq1.c.urusan_kd, subq1.c.urusan_nm,
                func.substr(Rekening.kode,1,1).label('rek_kd1'),func.substr(Rekening.kode,1,3).label('rek_kd2'),
                func.substr(Rekening.kode,1,5).label('rek_kd3'),func.substr(Rekening.kode,1,8).label('rek_kd4'),
                subq1.c.unit_kd, subq1.c.unit_nm, subq1.c.tahun, 
                func.sum(subq1.c.jml1).label('jumlah1'),func.sum(subq1.c.jml2).label('jumlah2'),
                func.sum(subq1.c.jml3).label('jumlah3'),func.sum(subq1.c.jml4).label('jumlah4'))\
                .filter(Rekening.kode==func.left(subq1.c.subrek_kd, func.length(Rekening.kode)))\
                .group_by(Rekening.kode, Rekening.nama,
                Rekening.level_id, Rekening.defsign, subq1.c.urusan_kd, subq1.c.urusan_nm,
                func.substr(Rekening.kode,1,1),func.substr(Rekening.kode,1,3),
                func.substr(Rekening.kode,1,5),func.substr(Rekening.kode,1,8),
                subq1.c.unit_kd, subq1.c.unit_nm, subq1.c.tahun)\
                .order_by(Rekening.kode).all()                    

            generator = r107Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
                
    @view_config(route_name="anggaran_r200", renderer="../../templates/apbd/anggaran/r200.pt", permission="read")
    def anggaran_r200(self):
        params = self.request.params
        return dict(datas=self.datas, 
               row=KegiatanSub.get_header(self.unit_id, self.keg_id),)

    @view_config(route_name="anggaran_r200_act", renderer="json", permission="read")
    def anggaran_r200_act(self):
        req    = self.request
        params = req.params
        url_dict = req.matchdict
        pk_id = 'id' in params and params['id'] and int(params['id']) or 0
#            keg_id = self.session['keg_id']
        if url_dict['act']=='grid' :
            # defining columns
            columns = []
            columns.append(ColumnDT('id'))
            columns.append(ColumnDT('tipe'))
            columns.append(ColumnDT('no_urut'))
            columns.append(ColumnDT("".join(['tolok_ukur_',str(self.status_apbd)])))
            columns.append(ColumnDT("".join(['volume_',str(self.status_apbd)])))
            columns.append(ColumnDT("".join(['satuan_',str(self.status_apbd)])))

            query = DBSession.query(KegiatanIndikator)\
                .join(KegiatanSub)\
                .filter(KegiatanSub.id==keg_id,
                        KegiatanSub.unit_id==self.unit_id)
            rowTable = DataTables(req, KegiatanIndikator, query, columns)
            return rowTable.output_result()

        elif url_dict['act']=='0' :
            query = DBSession.query(KegiatanSub.tahun_id,Urusan.kode.label('urusan_kd'),
               Urusan.nama.label('urusan_nm'),Unit.id.label('unit_id'),Unit.kode.label('unit_kd'),
               Unit.nama.label('unit_nm'))\
               .filter(KegiatanSub.unit_id==Unit.id,Unit.urusan_id==Urusan.id,
               KegiatanSub.tahun_id==self.session['tahun'],KegiatanSub.unit_id==self.unit_id)\
               .group_by(KegiatanSub.tahun_id,Urusan.kode,Urusan.nama,Unit.id,Unit.kode,
               Unit.nama)

            generator = r200Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
            
        elif url_dict['act']=='1' :
            subq1 = DBSession.query(Rekening.kode.label('subrek_kd'),Rekening.nama.label('subrek_nm'),
                KegiatanItem.kode.label('item_kd'), KegiatanItem.nama.label('item_nm'),
                (KegiatanItem.vol_1_1*KegiatanItem.vol_1_2).label('volume1'),
                KegiatanItem.sat_1_1,KegiatanItem.sat_1_2,KegiatanItem.hsat_1.label('harga1'),
                (KegiatanItem.vol_1_1* KegiatanItem.vol_1_2*KegiatanItem.hsat_1).label('jml1'),
                (KegiatanItem.vol_2_1*KegiatanItem.vol_2_2).label('volume2'),
                KegiatanItem.sat_2_1,KegiatanItem.sat_2_2,KegiatanItem.hsat_2.label('harga2'),
                (KegiatanItem.vol_2_1* KegiatanItem.vol_2_2*KegiatanItem.hsat_2).label('jml2'),
                (KegiatanItem.vol_3_1*KegiatanItem.vol_3_2).label('volume3'),
                KegiatanItem.sat_3_1,KegiatanItem.sat_3_2,KegiatanItem.hsat_3.label('harga3'),
                (KegiatanItem.vol_3_1* KegiatanItem.vol_3_2*KegiatanItem.hsat_3).label('jml3'),
                (KegiatanItem.vol_4_1*KegiatanItem.vol_4_2).label('volume4'),
                KegiatanItem.sat_4_1,KegiatanItem.sat_4_2,KegiatanItem.hsat_4.label('harga4'),
                (KegiatanItem.vol_4_1* KegiatanItem.vol_4_2*KegiatanItem.hsat_4).label('jml4'),
                KegiatanSub.tahun_id.label('tahun'), 
                (KegiatanItem.bln01+KegiatanItem.bln02+KegiatanItem.bln03).label('trw1'),
                (KegiatanItem.bln04+KegiatanItem.bln05+KegiatanItem.bln06).label('trw2'),
                (KegiatanItem.bln07+KegiatanItem.bln08+KegiatanItem.bln09).label('trw3'),
                (KegiatanItem.bln10+KegiatanItem.bln11+KegiatanItem.bln12).label('trw4'),
                Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'),
                Urusan.kode.label('urusan_kd'), Urusan.nama.label('urusan_nm'))\
                .filter(KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                        KegiatanItem.rekening_id==Rekening.id,
                        KegiatanSub.unit_id==Unit.id,
                        Unit.urusan_id==Urusan.id,
                        KegiatanSub.tahun_id==self.session['tahun'],
                        KegiatanSub.unit_id==self.unit_id,
                        KegiatanSub.kegiatan_id==2)\
                .subquery()

            query = DBSession.query(Rekening.kode.label('rek_kd'), Rekening.nama.label('rek_nm'),
                Rekening.level_id, Rekening.defsign, subq1.c.urusan_kd, subq1.c.urusan_nm,
                subq1.c.unit_kd, subq1.c.unit_nm, subq1.c.tahun, 
                subq1.c.item_kd, subq1.c.item_nm, 
                subq1.c.volume1, subq1.c.sat_1_1, subq1.c.sat_1_2, subq1.c.harga1,
                subq1.c.volume2, subq1.c.sat_2_1, subq1.c.sat_2_2, subq1.c.harga2,
                subq1.c.volume3, subq1.c.sat_3_1, subq1.c.sat_3_2, subq1.c.harga3,
                subq1.c.volume4, subq1.c.sat_4_1, subq1.c.sat_4_2, subq1.c.harga4,
                func.sum(subq1.c.jml1).label('jumlah1'),func.sum(subq1.c.jml2).label('jumlah2'),
                func.sum(subq1.c.jml3).label('jumlah3'),func.sum(subq1.c.jml4).label('jumlah4'),
                func.sum(subq1.c.trw1).label('trw1'),func.sum(subq1.c.trw2).label('trw2'),
                func.sum(subq1.c.trw3).label('trw3'),func.sum(subq1.c.trw4).label('trw4'))\
                .filter(Rekening.kode==func.left(subq1.c.subrek_kd, func.length(Rekening.kode)))\
                .group_by(Rekening.kode, Rekening.nama,
                Rekening.level_id, Rekening.defsign, subq1.c.urusan_kd, subq1.c.urusan_nm,
                subq1.c.unit_kd, subq1.c.unit_nm, subq1.c.tahun, 
                subq1.c.item_kd, subq1.c.item_nm, 
                subq1.c.volume1, subq1.c.sat_1_1, subq1.c.sat_1_2, subq1.c.harga1,
                subq1.c.volume2, subq1.c.sat_2_1, subq1.c.sat_2_2, subq1.c.harga2,
                subq1.c.volume3, subq1.c.sat_3_1, subq1.c.sat_3_2, subq1.c.harga3,
                subq1.c.volume4, subq1.c.sat_4_1, subq1.c.sat_4_2, subq1.c.harga4)\
                .order_by(Rekening.kode).all()                    

            generator = r201Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        elif url_dict['act']=='21' :
            subq1 = DBSession.query(Rekening.kode.label('subrek_kd'),Rekening.nama.label('subrek_nm'),
                (KegiatanItem.vol_1_1* KegiatanItem.vol_1_2*KegiatanItem.hsat_1).label('jml1'),
                (KegiatanItem.vol_2_1* KegiatanItem.vol_2_2*KegiatanItem.hsat_2).label('jml2'),
                (KegiatanItem.vol_3_1* KegiatanItem.vol_3_2*KegiatanItem.hsat_3).label('jml3'),
                (KegiatanItem.vol_4_1* KegiatanItem.vol_4_2*KegiatanItem.hsat_4).label('jml4'),
                (KegiatanItem.bln01+KegiatanItem.bln02+KegiatanItem.bln03).label('trw1'),
                (KegiatanItem.bln04+KegiatanItem.bln05+KegiatanItem.bln06).label('trw2'),
                (KegiatanItem.bln07+KegiatanItem.bln08+KegiatanItem.bln09).label('trw3'),
                (KegiatanItem.bln10+KegiatanItem.bln11+KegiatanItem.bln12).label('trw4'),
                Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'),
                Urusan.kode.label('urusan_kd'), Urusan.nama.label('urusan_nm'),
                KegiatanSub.tahun_id.label('tahun')).join(KegiatanItem).join(KegiatanSub).join(Kegiatan).join(Unit).join(Urusan)\
                .filter(
                        Unit.urusan_id==Urusan.id,
                        KegiatanSub.tahun_id==self.session['tahun'],
                        KegiatanSub.unit_id==self.session['unit_id'],
                        Kegiatan.kode=='0.00.00.21').subquery()

            query = DBSession.query(Rekening.kode.label('rek_kd'), Rekening.nama.label('rek_nm'),
                Rekening.level_id, Rekening.defsign, subq1.c.urusan_kd, subq1.c.urusan_nm,
                subq1.c.unit_kd, subq1.c.unit_nm, subq1.c.tahun, 
                func.sum(subq1.c.jml1).label('jumlah1'),func.sum(subq1.c.jml2).label('jumlah2'),
                func.sum(subq1.c.jml3).label('jumlah3'),func.sum(subq1.c.jml4).label('jumlah4'),
                func.sum(subq1.c.trw1).label('trw1'),func.sum(subq1.c.trw2).label('trw2'),
                func.sum(subq1.c.trw3).label('trw3'),func.sum(subq1.c.trw4).label('trw4'))\
                .filter(Rekening.kode==func.left(subq1.c.subrek_kd, func.length(Rekening.kode)))\
                .group_by(Rekening.kode, Rekening.nama,
                Rekening.level_id, Rekening.defsign, subq1.c.urusan_kd, subq1.c.urusan_nm,
                subq1.c.unit_kd, subq1.c.unit_nm, subq1.c.tahun)\
                .order_by(Rekening.kode).all()                    

            generator = r202Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        elif url_dict['act']=='22' :
            query = DBSession.query(KegiatanSub.tahun_id.label('tahun'), Urusan.kode.label('urusan_kd'), Urusan.nama.label('urusan_nm'),
                  Unit.id.label('unit_id'), Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'),
                  Program.kode.label('program_kd'), Program.nama.label('program_nm'), 
                  Kegiatan.kode.label('kegiatan_kd'), Kegiatan.nama.label('kegiatan_nm'), 
                  KegiatanSub.lokasi.label('lokasi'), KegiatanSub.target.label('target'), 
        func.sum(KegiatanItem.bln01+KegiatanItem.bln02+KegiatanItem.bln03).label('trw1'), 
        func.sum(KegiatanItem.bln04+KegiatanItem.bln05+KegiatanItem.bln06).label('trw2'), 
        func.sum(KegiatanItem.bln07+KegiatanItem.bln08+KegiatanItem.bln09).label('trw3'), 
        func.sum(KegiatanItem.bln10+KegiatanItem.bln11+KegiatanItem.bln12).label('trw4'))\
                  .filter(KegiatanSub.id==KegiatanItem.kegiatan_sub_id,
          KegiatanSub.unit_id==Unit.id,
          Urusan.id==Unit.urusan_id,
          Kegiatan.id==KegiatanSub.kegiatan_id, 
          Program.id==Kegiatan.program_id,
                        KegiatanSub.unit_id==self.unit_id,
                        KegiatanSub.kegiatan_id>6)\
                  .group_by(KegiatanSub.tahun_id, Urusan.kode, Urusan.nama,
                  Unit.id, Unit.kode, Unit.nama,
                  Program.kode, Program.nama, 
                  Kegiatan.kode, Kegiatan.nama, 
                  KegiatanSub.lokasi, KegiatanSub.target)\
                  .order_by(Urusan.kode, Unit.kode, Program.kode, Kegiatan.kode).all()

            generator = r203Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        elif url_dict['act']=='221' :
            query = DBSession.query(KegiatanSub)\
                 .filter(KegiatanSub.tahun_id==self.session['tahun'],
                   KegiatanSub.unit_id==self.unit_id, 
                   KegiatanSub.id==self.request.params['id'])

            generator = r204Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        elif url_dict['act']=='3' :
            subq1 = DBSession.query(Rekening.kode.label('subrek_kd'),Rekening.nama.label('subrek_nm'),
                (KegiatanItem.vol_1_1* KegiatanItem.vol_1_2*KegiatanItem.hsat_1).label('jml1'),
                (KegiatanItem.vol_2_1* KegiatanItem.vol_2_2*KegiatanItem.hsat_2).label('jml2'),
                (KegiatanItem.vol_3_1* KegiatanItem.vol_3_2*KegiatanItem.hsat_3).label('jml3'),
                (KegiatanItem.vol_4_1* KegiatanItem.vol_4_2*KegiatanItem.hsat_4).label('jml4'),
                (KegiatanItem.bln01+KegiatanItem.bln02+KegiatanItem.bln03).label('trw1'),
                (KegiatanItem.bln04+KegiatanItem.bln05+KegiatanItem.bln06).label('trw2'),
                (KegiatanItem.bln07+KegiatanItem.bln08+KegiatanItem.bln09).label('trw3'),
                (KegiatanItem.bln10+KegiatanItem.bln11+KegiatanItem.bln12).label('trw4'),
                Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'),
                Urusan.kode.label('urusan_kd'), Urusan.nama.label('urusan_nm'),
                KegiatanSub.tahun_id.label('tahun'))\
                .filter(KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                        KegiatanItem.rekening_id==Rekening.id,
                        KegiatanSub.unit_id==Unit.id,
                        Unit.urusan_id==Urusan.id,
                        KegiatanSub.tahun_id==self.session['tahun'],
                        KegiatanSub.unit_id==self.unit_id,
                        KegiatanSub.kegiatan_id.in_([4,5]))\
                .subquery()

            query = DBSession.query(Rekening.kode.label('rek_kd'), Rekening.nama.label('rek_nm'),
                Rekening.level_id, Rekening.defsign, subq1.c.urusan_kd, subq1.c.urusan_nm,
                subq1.c.unit_kd, subq1.c.unit_nm, subq1.c.tahun, 
                func.sum(subq1.c.jml1).label('jumlah1'),func.sum(subq1.c.jml2).label('jumlah2'),
                func.sum(subq1.c.jml3).label('jumlah3'),func.sum(subq1.c.jml4).label('jumlah4'),
                func.sum(subq1.c.trw1).label('trw1'),func.sum(subq1.c.trw2).label('trw2'),
                func.sum(subq1.c.trw3).label('trw3'),func.sum(subq1.c.trw4).label('trw4'))\
                .filter(Rekening.kode==func.left(subq1.c.subrek_kd, func.length(Rekening.kode)))\
                .group_by(Rekening.kode, Rekening.nama,
                Rekening.level_id, Rekening.defsign, subq1.c.urusan_kd, subq1.c.urusan_nm,
                subq1.c.unit_kd, subq1.c.unit_nm, subq1.c.tahun)\
                .order_by(Rekening.kode).all()                    

            generator = r205Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        elif url_dict['act']=='31' :
            subq1 = DBSession.query(Rekening.kode.label('subrek_kd'),Rekening.nama.label('subrek_nm'),
                (KegiatanItem.vol_1_1* KegiatanItem.vol_1_2*KegiatanItem.hsat_1).label('jml1'),
                (KegiatanItem.vol_2_1* KegiatanItem.vol_2_2*KegiatanItem.hsat_2).label('jml2'),
                (KegiatanItem.vol_3_1* KegiatanItem.vol_3_2*KegiatanItem.hsat_3).label('jml3'),
                (KegiatanItem.vol_4_1* KegiatanItem.vol_4_2*KegiatanItem.hsat_4).label('jml4'),
                (KegiatanItem.bln01+KegiatanItem.bln02+KegiatanItem.bln03).label('trw1'),
                (KegiatanItem.bln04+KegiatanItem.bln05+KegiatanItem.bln06).label('trw2'),
                (KegiatanItem.bln07+KegiatanItem.bln08+KegiatanItem.bln09).label('trw3'),
                (KegiatanItem.bln10+KegiatanItem.bln11+KegiatanItem.bln12).label('trw4'),
                Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'),
                Urusan.kode.label('urusan_kd'), Urusan.nama.label('urusan_nm'),
                KegiatanSub.tahun_id.label('tahun'))\
                .filter(KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                        KegiatanItem.rekening_id==Rekening.id,
                        KegiatanSub.unit_id==Unit.id,
                        Unit.urusan_id==Urusan.id,
                        KegiatanSub.tahun_id==self.session['tahun'],
                        KegiatanSub.unit_id==self.unit_id,
                        KegiatanSub.kegiatan_id==4)\
                .subquery()

            query = DBSession.query(Rekening.kode.label('rek_kd'), Rekening.nama.label('rek_nm'),
                Rekening.level_id, Rekening.defsign, subq1.c.urusan_kd, subq1.c.urusan_nm,
                subq1.c.unit_kd, subq1.c.unit_nm, subq1.c.tahun, 
                func.sum(subq1.c.jml1).label('jumlah1'),func.sum(subq1.c.jml2).label('jumlah2'),
                func.sum(subq1.c.jml3).label('jumlah3'),func.sum(subq1.c.jml4).label('jumlah4'),
                func.sum(subq1.c.trw1).label('trw1'),func.sum(subq1.c.trw2).label('trw2'),
                func.sum(subq1.c.trw3).label('trw3'),func.sum(subq1.c.trw4).label('trw4'))\
                .filter(Rekening.kode==func.left(subq1.c.subrek_kd, func.length(Rekening.kode)))\
                .group_by(Rekening.kode, Rekening.nama,
                Rekening.level_id, Rekening.defsign, subq1.c.urusan_kd, subq1.c.urusan_nm,
                subq1.c.unit_kd, subq1.c.unit_nm, subq1, subq1.c.tahun)\
                .order_by(Rekening.kode).all()                    

            generator = r206Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        elif url_dict['act']=='32' :
            subq1 = DBSession.query(Rekening.kode.label('subrek_kd'),Rekening.nama.label('subrek_nm'),
                (KegiatanItem.vol_1_1* KegiatanItem.vol_1_2*KegiatanItem.hsat_1).label('jml1'),
                (KegiatanItem.vol_2_1* KegiatanItem.vol_2_2*KegiatanItem.hsat_2).label('jml2'),
                (KegiatanItem.vol_3_1* KegiatanItem.vol_3_2*KegiatanItem.hsat_3).label('jml3'),
                (KegiatanItem.vol_4_1* KegiatanItem.vol_4_2*KegiatanItem.hsat_4).label('jml4'),
                (KegiatanItem.bln01+KegiatanItem.bln02+KegiatanItem.bln03).label('trw1'),
                (KegiatanItem.bln04+KegiatanItem.bln05+KegiatanItem.bln06).label('trw2'),
                (KegiatanItem.bln07+KegiatanItem.bln08+KegiatanItem.bln09).label('trw3'),
                (KegiatanItem.bln10+KegiatanItem.bln11+KegiatanItem.bln12).label('trw4'),
                Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'),
                Urusan.kode.label('urusan_kd'), Urusan.nama.label('urusan_nm'),
                KegiatanSub.tahun_id.label('tahun'))\
                .filter(KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                        KegiatanItem.rekening_id==Rekening.id,
                        KegiatanSub.unit_id==Unit.id,
                        Unit.urusan_id==Urusan.id,
                        KegiatanSub.tahun_id==self.session['tahun'],
                        KegiatanSub.unit_id==self.unit_id,
                        KegiatanSub.kegiatan_id==5)\
                .subquery()

            query = DBSession.query(Rekening.kode.label('rek_kd'), Rekening.nama.label('rek_nm'),
                Rekening.level_id, Rekening.defsign, subq1.c.urusan_kd, subq1.c.urusan_nm,
                subq1.c.unit_kd, subq1.c.unit_nm, subq1.c.tahun, 
                func.sum(subq1.c.jml1).label('jumlah1'),func.sum(subq1.c.jml2).label('jumlah2'),
                func.sum(subq1.c.jml3).label('jumlah3'),func.sum(subq1.c.jml4).label('jumlah4'),
                func.sum(subq1.c.trw1).label('trw1'),func.sum(subq1.c.trw2).label('trw2'),
                func.sum(subq1.c.trw3).label('trw3'),func.sum(subq1.c.trw4).label('trw4'))\
                .filter(Rekening.kode==func.left(subq1.c.subrek_kd, func.length(Rekening.kode)))\
                .group_by(Rekening.kode, Rekening.nama,
                Rekening.level_id, Rekening.defsign, subq1.c.urusan_kd, subq1.c.urusan_nm,
                subq1.c.unit_kd, subq1.c.unit_nm, subq1.c.tahun)\
                .order_by(Rekening.kode).all()                    

            generator = r207Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
                
    @view_config(route_name="anggaran_r300", renderer="../../templates/apbd/anggaran/r300.pt", permission="read")
    def anggaran_r300(self):
        params = self.request.params
        return dict(datas=self.datas, 
               row=KegiatanSub.get_header(self.unit_id, self.keg_id),)

    @view_config(route_name="anggaran_r300_act", renderer="json", permission="read")
    def anggaran_r300_act(self):
        req    = self.request
        params = req.params
        url_dict = req.matchdict
        pk_id = 'id' in params and params['id'] and int(params['id']) or 0
#            keg_id = self.session['keg_id']
        if url_dict['act']=='grid' :
            # defining columns
            columns = []
            columns.append(ColumnDT('id'))
            columns.append(ColumnDT('tipe'))
            columns.append(ColumnDT('no_urut'))
            columns.append(ColumnDT("".join(['tolok_ukur_',str(self.status_apbd)])))
            columns.append(ColumnDT("".join(['volume_',str(self.status_apbd)])))
            columns.append(ColumnDT("".join(['satuan_',str(self.status_apbd)])))

            query = DBSession.query(KegiatanIndikator)\
                .join(KegiatanSub)\
                .filter(KegiatanSub.id==keg_id,
                        KegiatanSub.unit_id==self.unit_id)
            rowTable = DataTables(req, KegiatanIndikator, query, columns)
            return rowTable.output_result()

        elif url_dict['act']=='0' :
            query = DBSession.query(KegiatanSub.tahun_id,Urusan.kode.label('urusan_kd'),
               Urusan.nama.label('urusan_nm'),Unit.id.label('unit_id'),Unit.kode.label('unit_kd'),
               Unit.nama.label('unit_nm'))\
               .filter(KegiatanSub.unit_id==Unit.id,Unit.urusan_id==Urusan.id,
               KegiatanSub.tahun_id==self.session['tahun'],KegiatanSub.unit_id==self.unit_id)\
               .group_by(KegiatanSub.tahun_id,Urusan.kode,Urusan.nama,Unit.id,Unit.kode,
               Unit.nama)

            generator = r300Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        elif url_dict['act']=='1' :
            subq1 = DBSession.query(Rekening.kode.label('subrek_kd'),Rekening.nama.label('subrek_nm'),
                (KegiatanItem.vol_1_1* KegiatanItem.vol_1_2*KegiatanItem.hsat_1).label('jml1'),
                (KegiatanItem.vol_2_1* KegiatanItem.vol_2_2*KegiatanItem.hsat_2).label('jml2'),
                (KegiatanItem.vol_3_1* KegiatanItem.vol_3_2*KegiatanItem.hsat_3).label('jml3'),
                (KegiatanItem.vol_4_1* KegiatanItem.vol_4_2*KegiatanItem.hsat_4).label('jml4'),
                (KegiatanItem.bln01+KegiatanItem.bln02+KegiatanItem.bln03).label('trw1'),
                (KegiatanItem.bln04+KegiatanItem.bln05+KegiatanItem.bln06).label('trw2'),
                (KegiatanItem.bln07+KegiatanItem.bln08+KegiatanItem.bln09).label('trw3'),
                (KegiatanItem.bln10+KegiatanItem.bln11+KegiatanItem.bln12).label('trw4'),
                Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'),
                Urusan.kode.label('urusan_kd'), Urusan.nama.label('urusan_nm'),
                KegiatanSub.perubahan, KegiatanSub.tahun_id.label('tahun'))\
                .filter(KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                        KegiatanItem.rekening_id==Rekening.id,
                        KegiatanSub.unit_id==Unit.id,
                        Unit.urusan_id==Urusan.id,
                        KegiatanSub.tahun_id==self.session['tahun'],
                        KegiatanSub.unit_id==self.unit_id,
                        KegiatanSub.kegiatan_id==2)\
                .subquery()

            query = DBSession.query(Rekening.kode.label('rek_kd'), Rekening.nama.label('rek_nm'),
                Rekening.level_id, Rekening.defsign, subq1.c.urusan_kd, subq1.c.urusan_nm,
                subq1.c.unit_kd, subq1.c.unit_nm, subq1.c.tahun, subq1.c.perubahan, 
                func.sum(subq1.c.jml1).label('jumlah1'),func.sum(subq1.c.jml2).label('jumlah2'),
                func.sum(subq1.c.jml3).label('jumlah3'),func.sum(subq1.c.jml4).label('jumlah4'),
                func.sum(subq1.c.trw1).label('trw1'),func.sum(subq1.c.trw2).label('trw2'),
                func.sum(subq1.c.trw3).label('trw3'),func.sum(subq1.c.trw4).label('trw4'))\
                .filter(Rekening.kode==func.left(subq1.c.subrek_kd, func.length(Rekening.kode)))\
                .group_by(Rekening.kode, Rekening.nama,
                Rekening.level_id, Rekening.defsign, subq1.c.urusan_kd, subq1.c.urusan_nm,
                subq1.c.unit_kd, subq1.c.unit_nm, subq1.c.tahun, subq1.c.perubahan)\
                .order_by(Rekening.kode).all()                    

            generator = r301Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        elif url_dict['act']=='21' :
            subq1 = DBSession.query(Rekening.kode.label('subrek_kd'),Rekening.nama.label('subrek_nm'),
                (KegiatanItem.vol_1_1* KegiatanItem.vol_1_2*KegiatanItem.hsat_1).label('jml1'),
                (KegiatanItem.vol_2_1* KegiatanItem.vol_2_2*KegiatanItem.hsat_2).label('jml2'),
                (KegiatanItem.vol_3_1* KegiatanItem.vol_3_2*KegiatanItem.hsat_3).label('jml3'),
                (KegiatanItem.vol_4_1* KegiatanItem.vol_4_2*KegiatanItem.hsat_4).label('jml4'),
                (KegiatanItem.bln01+KegiatanItem.bln02+KegiatanItem.bln03).label('trw1'),
                (KegiatanItem.bln04+KegiatanItem.bln05+KegiatanItem.bln06).label('trw2'),
                (KegiatanItem.bln07+KegiatanItem.bln08+KegiatanItem.bln09).label('trw3'),
                (KegiatanItem.bln10+KegiatanItem.bln11+KegiatanItem.bln12).label('trw4'),
                Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'),
                Urusan.kode.label('urusan_kd'), Urusan.nama.label('urusan_nm'),
                KegiatanSub.perubahan, KegiatanSub.tahun_id.label('tahun'))\
                .filter(KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                        KegiatanItem.rekening_id==Rekening.id,
                        KegiatanSub.unit_id==Unit.id,
                        Unit.urusan_id==Urusan.id,
                        KegiatanSub.tahun_id==self.session['tahun'],
                        KegiatanSub.unit_id==self.unit_id,
                        KegiatanSub.kegiatan_id==3)\
                .subquery()

            query = DBSession.query(Rekening.kode.label('rek_kd'), Rekening.nama.label('rek_nm'),
                Rekening.level_id, Rekening.defsign, subq1.c.urusan_kd, subq1.c.urusan_nm,
                subq1.c.unit_kd, subq1.c.unit_nm, subq1.c.tahun, subq1.c.perubahan,
                func.sum(subq1.c.jml1).label('jumlah1'),func.sum(subq1.c.jml2).label('jumlah2'),
                func.sum(subq1.c.jml3).label('jumlah3'),func.sum(subq1.c.jml4).label('jumlah4'),
                func.sum(subq1.c.trw1).label('trw1'),func.sum(subq1.c.trw2).label('trw2'),
                func.sum(subq1.c.trw3).label('trw3'),func.sum(subq1.c.trw4).label('trw4'))\
                .filter(Rekening.kode==func.left(subq1.c.subrek_kd, func.length(Rekening.kode)))\
                .group_by(Rekening.kode, Rekening.nama,
                Rekening.level_id, Rekening.defsign, subq1.c.urusan_kd, subq1.c.urusan_nm,
                subq1.c.unit_kd, subq1.c.unit_nm, subq1.c.tahun, subq1.c.perubahan)\
                .order_by(Rekening.kode).all()                    

            generator = r302Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        elif url_dict['act']=='22' :
            query = DBSession.query(KegiatanSub.tahun_id.label('tahun'), Urusan.kode.label('urusan_kd'), Urusan.nama.label('urusan_nm'),
                  Unit.id.label('unit_id'), Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'),
                  Program.kode.label('program_kd'), Program.nama.label('program_nm'), 
                  Kegiatan.kode.label('kegiatan_kd'), Kegiatan.nama.label('kegiatan_nm'), 
                  KegiatanSub.lokasi.label('lokasi'), KegiatanSub.target.label('target'), 
        func.sum(KegiatanItem.vol_1_1*KegiatanItem.vol_1_2*KegiatanItem.hsat_1).label('jumlah1'), 
        func.sum(KegiatanItem.vol_2_1*KegiatanItem.vol_2_2*KegiatanItem.hsat_2).label('jumlah2'), 
        func.sum(KegiatanItem.vol_3_1*KegiatanItem.vol_3_2*KegiatanItem.hsat_3).label('jumlah3'), 
        func.sum(KegiatanItem.vol_4_1*KegiatanItem.vol_4_2*KegiatanItem.hsat_4).label('jumlah4'))\
                  .filter(KegiatanSub.id==KegiatanItem.kegiatan_sub_id,
          KegiatanSub.unit_id==Unit.id,
          Urusan.id==Unit.urusan_id,
          Kegiatan.id==KegiatanSub.kegiatan_id, 
          Program.id==Kegiatan.program_id,
                        KegiatanSub.unit_id==self.unit_id,
                        KegiatanSub.kegiatan_id>6)\
                  .group_by(KegiatanSub.tahun_id, Urusan.kode, Urusan.nama,
                  Unit.id, Unit.kode, Unit.nama,
                  Program.kode, Program.nama, 
                  Kegiatan.kode, Kegiatan.nama, 
                  KegiatanSub.lokasi, KegiatanSub.target)\
                  .order_by(Urusan.kode, Unit.kode, Program.kode, Kegiatan.kode).all()

            generator = r303Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        elif url_dict['act']=='221' :
            query = DBSession.query(KegiatanSub)\
                 .filter(KegiatanSub.tahun_id==self.session['tahun'],
                   KegiatanSub.unit_id==self.unit_id, 
                   KegiatanSub.id==self.request.params['id'])

            generator = r304Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        elif url_dict['act']=='3' :
            subq1 = DBSession.query(Rekening.kode.label('subrek_kd'),Rekening.nama.label('subrek_nm'),
                (KegiatanItem.vol_1_1* KegiatanItem.vol_1_2*KegiatanItem.hsat_1).label('jml1'),
                (KegiatanItem.vol_2_1* KegiatanItem.vol_2_2*KegiatanItem.hsat_2).label('jml2'),
                (KegiatanItem.vol_3_1* KegiatanItem.vol_3_2*KegiatanItem.hsat_3).label('jml3'),
                (KegiatanItem.vol_4_1* KegiatanItem.vol_4_2*KegiatanItem.hsat_4).label('jml4'),
                (KegiatanItem.bln01+KegiatanItem.bln02+KegiatanItem.bln03).label('trw1'),
                (KegiatanItem.bln04+KegiatanItem.bln05+KegiatanItem.bln06).label('trw2'),
                (KegiatanItem.bln07+KegiatanItem.bln08+KegiatanItem.bln09).label('trw3'),
                (KegiatanItem.bln10+KegiatanItem.bln11+KegiatanItem.bln12).label('trw4'),
                Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'),
                Urusan.kode.label('urusan_kd'), Urusan.nama.label('urusan_nm'),
                KegiatanSub.perubahan, KegiatanSub.tahun_id.label('tahun'))\
                .filter(KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                        KegiatanItem.rekening_id==Rekening.id,
                        KegiatanSub.unit_id==Unit.id,
                        Unit.urusan_id==Urusan.id,
                        KegiatanSub.tahun_id==self.session['tahun'],
                        KegiatanSub.unit_id==self.unit_id,
                        KegiatanSub.kegiatan_id.in_([4,5]))\
                .subquery()

            query = DBSession.query(Rekening.kode.label('rek_kd'), Rekening.nama.label('rek_nm'),
                Rekening.level_id, Rekening.defsign, subq1.c.urusan_kd, subq1.c.urusan_nm,
                subq1.c.unit_kd, subq1.c.unit_nm, subq1.c.tahun, subq1.c.perubahan, 
                func.sum(subq1.c.jml1).label('jumlah1'),func.sum(subq1.c.jml2).label('jumlah2'),
                func.sum(subq1.c.jml3).label('jumlah3'),func.sum(subq1.c.jml4).label('jumlah4'),
                func.sum(subq1.c.trw1).label('trw1'),func.sum(subq1.c.trw2).label('trw2'),
                func.sum(subq1.c.trw3).label('trw3'),func.sum(subq1.c.trw4).label('trw4'))\
                .filter(Rekening.kode==func.left(subq1.c.subrek_kd, func.length(Rekening.kode)))\
                .group_by(Rekening.kode, Rekening.nama,
                Rekening.level_id, Rekening.defsign, subq1.c.urusan_kd, subq1.c.urusan_nm,
                subq1.c.unit_kd, subq1.c.unit_nm, subq1.c.tahun, subq1.c.perubahan)\
                .order_by(Rekening.kode).all()                    

            generator = r305Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        elif url_dict['act']=='31' :
            subq1 = DBSession.query(Rekening.kode.label('subrek_kd'),Rekening.nama.label('subrek_nm'),
                (KegiatanItem.vol_1_1* KegiatanItem.vol_1_2*KegiatanItem.hsat_1).label('jml1'),
                (KegiatanItem.vol_2_1* KegiatanItem.vol_2_2*KegiatanItem.hsat_2).label('jml2'),
                (KegiatanItem.vol_3_1* KegiatanItem.vol_3_2*KegiatanItem.hsat_3).label('jml3'),
                (KegiatanItem.vol_4_1* KegiatanItem.vol_4_2*KegiatanItem.hsat_4).label('jml4'),
                (KegiatanItem.bln01+KegiatanItem.bln02+KegiatanItem.bln03).label('trw1'),
                (KegiatanItem.bln04+KegiatanItem.bln05+KegiatanItem.bln06).label('trw2'),
                (KegiatanItem.bln07+KegiatanItem.bln08+KegiatanItem.bln09).label('trw3'),
                (KegiatanItem.bln10+KegiatanItem.bln11+KegiatanItem.bln12).label('trw4'),
                Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'),
                Urusan.kode.label('urusan_kd'), Urusan.nama.label('urusan_nm'),
                KegiatanSub.perubahan, KegiatanSub.tahun_id.label('tahun'))\
                .filter(KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                        KegiatanItem.rekening_id==Rekening.id,
                        KegiatanSub.unit_id==Unit.id,
                        Unit.urusan_id==Urusan.id,
                        KegiatanSub.tahun_id==self.session['tahun'],
                        KegiatanSub.unit_id==self.unit_id,
                        KegiatanSub.kegiatan_id==4)\
                .subquery()

            query = DBSession.query(Rekening.kode.label('rek_kd'), Rekening.nama.label('rek_nm'),
                Rekening.level_id, Rekening.defsign, subq1.c.urusan_kd, subq1.c.urusan_nm,
                subq1.c.unit_kd, subq1.c.unit_nm, subq1.c.tahun, subq1.c.perubahan, 
                func.sum(subq1.c.jml1).label('jumlah1'),func.sum(subq1.c.jml2).label('jumlah2'),
                func.sum(subq1.c.jml3).label('jumlah3'),func.sum(subq1.c.jml4).label('jumlah4'),
                func.sum(subq1.c.trw1).label('trw1'),func.sum(subq1.c.trw2).label('trw2'),
                func.sum(subq1.c.trw3).label('trw3'),func.sum(subq1.c.trw4).label('trw4'))\
                .filter(Rekening.kode==func.left(subq1.c.subrek_kd, func.length(Rekening.kode)))\
                .group_by(Rekening.kode, Rekening.nama,
                Rekening.level_id, Rekening.defsign, subq1.c.urusan_kd, subq1.c.urusan_nm,
                subq1.c.unit_kd, subq1.c.unit_nm, subq1, subq1.c.tahun, subq1.c.perubahan)\
                .order_by(Rekening.kode).all()                    

            generator = r306Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        elif url_dict['act']=='32' :
            subq1 = DBSession.query(Rekening.kode.label('subrek_kd'),Rekening.nama.label('subrek_nm'),
                (KegiatanItem.vol_1_1* KegiatanItem.vol_1_2*KegiatanItem.hsat_1).label('jml1'),
                (KegiatanItem.vol_2_1* KegiatanItem.vol_2_2*KegiatanItem.hsat_2).label('jml2'),
                (KegiatanItem.vol_3_1* KegiatanItem.vol_3_2*KegiatanItem.hsat_3).label('jml3'),
                (KegiatanItem.vol_4_1* KegiatanItem.vol_4_2*KegiatanItem.hsat_4).label('jml4'),
                (KegiatanItem.bln01+KegiatanItem.bln02+KegiatanItem.bln03).label('trw1'),
                (KegiatanItem.bln04+KegiatanItem.bln05+KegiatanItem.bln06).label('trw2'),
                (KegiatanItem.bln07+KegiatanItem.bln08+KegiatanItem.bln09).label('trw3'),
                (KegiatanItem.bln10+KegiatanItem.bln11+KegiatanItem.bln12).label('trw4'),
                Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'),
                Urusan.kode.label('urusan_kd'), Urusan.nama.label('urusan_nm'),
                KegiatanSub.perubahan, KegiatanSub.tahun_id.label('tahun'))\
                .filter(KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                        KegiatanItem.rekening_id==Rekening.id,
                        KegiatanSub.unit_id==Unit.id,
                        Unit.urusan_id==Urusan.id,
                        KegiatanSub.tahun_id==self.session['tahun'],
                        KegiatanSub.unit_id==self.unit_id,
                        KegiatanSub.kegiatan_id==5)\
                .subquery()

            query = DBSession.query(Rekening.kode.label('rek_kd'), Rekening.nama.label('rek_nm'),
                Rekening.level_id, Rekening.defsign, subq1.c.urusan_kd, subq1.c.urusan_nm,
                subq1.c.unit_kd, subq1.c.unit_nm, subq1.c.tahun, subq1.c.perubahan, 
                func.sum(subq1.c.jml1).label('jumlah1'),func.sum(subq1.c.jml2).label('jumlah2'),
                func.sum(subq1.c.jml3).label('jumlah3'),func.sum(subq1.c.jml4).label('jumlah4'),
                func.sum(subq1.c.trw1).label('trw1'),func.sum(subq1.c.trw2).label('trw2'),
                func.sum(subq1.c.trw3).label('trw3'),func.sum(subq1.c.trw4).label('trw4'))\
                .filter(Rekening.kode==func.left(subq1.c.subrek_kd, func.length(Rekening.kode)))\
                .group_by(Rekening.kode, Rekening.nama,
                Rekening.level_id, Rekening.defsign, subq1.c.urusan_kd, subq1.c.urusan_nm,
                subq1.c.unit_kd, subq1.c.unit_nm, subq1.c.tahun, subq1.c.perubahan)\
                .order_by(Rekening.kode).all()                    

            generator = r307Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
 
    @view_config(route_name="anggaran_r400", renderer="../../templates/apbd/anggaran/r400.pt", permission="read")
    def anggaran_r400(self):
        params = self.request.params
        return dict(datas=self.datas, 
               row=KegiatanSub.get_header(self.unit_id, self.keg_id),)

    @view_config(route_name="anggaran_r400_act", renderer="json", permission="read")
    def anggaran_r400_act(self):
        req    = self.request
        params = req.params
        url_dict = req.matchdict
        pk_id = 'id' in params and params['id'] and int(params['id']) or 0
#            keg_id = self.session['keg_id']
        if url_dict['act']=='grid' :
            # defining columns
            columns = []
            columns.append(ColumnDT('id'))
            columns.append(ColumnDT('tipe'))
            columns.append(ColumnDT('no_urut'))
            columns.append(ColumnDT("".join(['tolok_ukur_',str(self.status_apbd)])))
            columns.append(ColumnDT("".join(['volume_',str(self.status_apbd)])))
            columns.append(ColumnDT("".join(['satuan_',str(self.status_apbd)])))

            query = DBSession.query(KegiatanIndikator)\
                .join(KegiatanSub)\
                .filter(KegiatanSub.id==keg_id,
                        KegiatanSub.unit_id==self.unit_id)
            rowTable = DataTables(req, KegiatanIndikator, query, columns)
            return rowTable.output_result()

        elif url_dict['act']=='0' :
            query = DBSession.query(KegiatanSub.tahun_id,Urusan.kode.label('urusan_kd'),
               Urusan.nama.label('urusan_nm'),Unit.id.label('unit_id'),Unit.kode.label('unit_kd'),
               Unit.nama.label('unit_nm'))\
               .filter(KegiatanSub.unit_id==Unit.id,Unit.urusan_id==Urusan.id,
               KegiatanSub.tahun_id==self.session['tahun'],KegiatanSub.unit_id==self.unit_id)\
               .group_by(KegiatanSub.tahun_id,Urusan.kode,Urusan.nama,Unit.id,Unit.kode,
               Unit.nama)

            generator = r400Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        elif url_dict['act']=='1' :
            subq1 = DBSession.query(Rekening.kode.label('subrek_kd'),Rekening.nama.label('subrek_nm'),
                (KegiatanItem.vol_1_1* KegiatanItem.vol_1_2*KegiatanItem.hsat_1).label('jml1'),
                (KegiatanItem.vol_2_1* KegiatanItem.vol_2_2*KegiatanItem.hsat_2).label('jml2'),
                (KegiatanItem.vol_3_1* KegiatanItem.vol_3_2*KegiatanItem.hsat_3).label('jml3'),
                (KegiatanItem.vol_4_1* KegiatanItem.vol_4_2*KegiatanItem.hsat_4).label('jml4'),
                (KegiatanItem.bln01+KegiatanItem.bln02+KegiatanItem.bln03).label('trw1'),
                (KegiatanItem.bln04+KegiatanItem.bln05+KegiatanItem.bln06).label('trw2'),
                (KegiatanItem.bln07+KegiatanItem.bln08+KegiatanItem.bln09).label('trw3'),
                (KegiatanItem.bln10+KegiatanItem.bln11+KegiatanItem.bln12).label('trw4'),
                Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'),
                Urusan.kode.label('urusan_kd'), Urusan.nama.label('urusan_nm'),
                KegiatanSub.perubahan, KegiatanSub.tahun_id.label('tahun'))\
                .filter(KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                        KegiatanItem.rekening_id==Rekening.id,
                        KegiatanSub.unit_id==Unit.id,
                        Unit.urusan_id==Urusan.id,
                        KegiatanSub.tahun_id==self.session['tahun'],
                        KegiatanSub.unit_id==self.unit_id,
                        KegiatanSub.kegiatan_id==2)\
                .subquery()

            query = DBSession.query(Rekening.kode.label('rek_kd'), Rekening.nama.label('rek_nm'),
                Rekening.level_id, Rekening.defsign, subq1.c.urusan_kd, subq1.c.urusan_nm,
                subq1.c.unit_kd, subq1.c.unit_nm, subq1.c.tahun, subq1.c.perubahan, 
                func.sum(subq1.c.jml1).label('jumlah1'),func.sum(subq1.c.jml2).label('jumlah2'),
                func.sum(subq1.c.jml3).label('jumlah3'),func.sum(subq1.c.jml4).label('jumlah4'),
                func.sum(subq1.c.trw1).label('trw1'),func.sum(subq1.c.trw2).label('trw2'),
                func.sum(subq1.c.trw3).label('trw3'),func.sum(subq1.c.trw4).label('trw4'))\
                .filter(Rekening.kode==func.left(subq1.c.subrek_kd, func.length(Rekening.kode)))\
                .group_by(Rekening.kode, Rekening.nama,
                Rekening.level_id, Rekening.defsign, subq1.c.urusan_kd, subq1.c.urusan_nm,
                subq1.c.unit_kd, subq1.c.unit_nm, subq1.c.tahun, subq1.c.perubahan)\
                .order_by(Rekening.kode).all()                    

            generator = r401Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        elif url_dict['act']=='21' :
            subq1 = DBSession.query(Rekening.kode.label('subrek_kd'),Rekening.nama.label('subrek_nm'),
                (KegiatanItem.vol_1_1* KegiatanItem.vol_1_2*KegiatanItem.hsat_1).label('jml1'),
                (KegiatanItem.vol_2_1* KegiatanItem.vol_2_2*KegiatanItem.hsat_2).label('jml2'),
                (KegiatanItem.vol_3_1* KegiatanItem.vol_3_2*KegiatanItem.hsat_3).label('jml3'),
                (KegiatanItem.vol_4_1* KegiatanItem.vol_4_2*KegiatanItem.hsat_4).label('jml4'),
                (KegiatanItem.bln01+KegiatanItem.bln02+KegiatanItem.bln03).label('trw1'),
                (KegiatanItem.bln04+KegiatanItem.bln05+KegiatanItem.bln06).label('trw2'),
                (KegiatanItem.bln07+KegiatanItem.bln08+KegiatanItem.bln09).label('trw3'),
                (KegiatanItem.bln10+KegiatanItem.bln11+KegiatanItem.bln12).label('trw4'),
                Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'),
                Urusan.kode.label('urusan_kd'), Urusan.nama.label('urusan_nm'),
                KegiatanSub.perubahan, KegiatanSub.tahun_id.label('tahun'))\
                .filter(KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                        KegiatanItem.rekening_id==Rekening.id,
                        KegiatanSub.unit_id==Unit.id,
                        Unit.urusan_id==Urusan.id,
                        KegiatanSub.tahun_id==self.session['tahun'],
                        KegiatanSub.unit_id==self.unit_id,
                        KegiatanSub.kegiatan_id==3)\
                .subquery()

            query = DBSession.query(Rekening.kode.label('rek_kd'), Rekening.nama.label('rek_nm'),
                Rekening.level_id, Rekening.defsign, subq1.c.urusan_kd, subq1.c.urusan_nm,
                subq1.c.unit_kd, subq1.c.unit_nm, subq1.c.tahun, subq1.c.perubahan,
                func.sum(subq1.c.jml1).label('jumlah1'),func.sum(subq1.c.jml2).label('jumlah2'),
                func.sum(subq1.c.jml3).label('jumlah3'),func.sum(subq1.c.jml4).label('jumlah4'),
                func.sum(subq1.c.trw1).label('trw1'),func.sum(subq1.c.trw2).label('trw2'),
                func.sum(subq1.c.trw3).label('trw3'),func.sum(subq1.c.trw4).label('trw4'))\
                .filter(Rekening.kode==func.left(subq1.c.subrek_kd, func.length(Rekening.kode)))\
                .group_by(Rekening.kode, Rekening.nama,
                Rekening.level_id, Rekening.defsign, subq1.c.urusan_kd, subq1.c.urusan_nm,
                subq1.c.unit_kd, subq1.c.unit_nm, subq1.c.tahun, subq1.c.perubahan)\
                .order_by(Rekening.kode).all()                    

            generator = r402Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        elif url_dict['act']=='22' :
            query = DBSession.query(KegiatanSub.tahun_id.label('tahun'), Urusan.kode.label('urusan_kd'), Urusan.nama.label('urusan_nm'),
                  Unit.id.label('unit_id'), Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'),
                  Program.kode.label('program_kd'), Program.nama.label('program_nm'), 
                  Kegiatan.kode.label('kegiatan_kd'), Kegiatan.nama.label('kegiatan_nm'), 
                  KegiatanSub.lokasi.label('lokasi'), KegiatanSub.target.label('target'), 
        func.sum(KegiatanItem.vol_1_1*KegiatanItem.vol_1_2*KegiatanItem.hsat_1).label('jumlah1'), 
        func.sum(KegiatanItem.vol_2_1*KegiatanItem.vol_2_2*KegiatanItem.hsat_2).label('jumlah2'), 
        func.sum(KegiatanItem.vol_3_1*KegiatanItem.vol_3_2*KegiatanItem.hsat_3).label('jumlah3'), 
        func.sum(KegiatanItem.vol_4_1*KegiatanItem.vol_4_2*KegiatanItem.hsat_4).label('jumlah4'))\
                  .filter(KegiatanSub.id==KegiatanItem.kegiatan_sub_id,
          KegiatanSub.unit_id==Unit.id,
          Urusan.id==Unit.urusan_id,
          Kegiatan.id==KegiatanSub.kegiatan_id, 
          Program.id==Kegiatan.program_id,
                        KegiatanSub.unit_id==self.unit_id,
                        KegiatanSub.kegiatan_id>6)\
                  .group_by(KegiatanSub.tahun_id, Urusan.kode, Urusan.nama,
                  Unit.id, Unit.kode, Unit.nama,
                  Program.kode, Program.nama, 
                  Kegiatan.kode, Kegiatan.nama, 
                  KegiatanSub.lokasi, KegiatanSub.target)\
                  .order_by(Urusan.kode, Unit.kode, Program.kode, Kegiatan.kode).all()

            generator = r403Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        elif url_dict['act']=='221' :
            query = DBSession.query(KegiatanSub)\
                 .filter(KegiatanSub.tahun_id==self.session['tahun'],
                   KegiatanSub.unit_id==self.unit_id, 
                   KegiatanSub.id==self.request.params['id'])

            generator = r404Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        elif url_dict['act']=='3' :
            subq1 = DBSession.query(Rekening.kode.label('subrek_kd'),Rekening.nama.label('subrek_nm'),
                (KegiatanItem.vol_1_1* KegiatanItem.vol_1_2*KegiatanItem.hsat_1).label('jml1'),
                (KegiatanItem.vol_2_1* KegiatanItem.vol_2_2*KegiatanItem.hsat_2).label('jml2'),
                (KegiatanItem.vol_3_1* KegiatanItem.vol_3_2*KegiatanItem.hsat_3).label('jml3'),
                (KegiatanItem.vol_4_1* KegiatanItem.vol_4_2*KegiatanItem.hsat_4).label('jml4'),
                (KegiatanItem.bln01+KegiatanItem.bln02+KegiatanItem.bln03).label('trw1'),
                (KegiatanItem.bln04+KegiatanItem.bln05+KegiatanItem.bln06).label('trw2'),
                (KegiatanItem.bln07+KegiatanItem.bln08+KegiatanItem.bln09).label('trw3'),
                (KegiatanItem.bln10+KegiatanItem.bln11+KegiatanItem.bln12).label('trw4'),
                Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'),
                Urusan.kode.label('urusan_kd'), Urusan.nama.label('urusan_nm'),
                KegiatanSub.perubahan, KegiatanSub.tahun_id.label('tahun'))\
                .filter(KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                        KegiatanItem.rekening_id==Rekening.id,
                        KegiatanSub.unit_id==Unit.id,
                        Unit.urusan_id==Urusan.id,
                        KegiatanSub.tahun_id==self.session['tahun'],
                        KegiatanSub.unit_id==self.unit_id,
                        KegiatanSub.kegiatan_id.in_([4,5]))\
                .subquery()

            query = DBSession.query(Rekening.kode.label('rek_kd'), Rekening.nama.label('rek_nm'),
                Rekening.level_id, Rekening.defsign, subq1.c.urusan_kd, subq1.c.urusan_nm,
                subq1.c.unit_kd, subq1.c.unit_nm, subq1.c.tahun, subq1.c.perubahan, 
                func.sum(subq1.c.jml1).label('jumlah1'),func.sum(subq1.c.jml2).label('jumlah2'),
                func.sum(subq1.c.jml3).label('jumlah3'),func.sum(subq1.c.jml4).label('jumlah4'),
                func.sum(subq1.c.trw1).label('trw1'),func.sum(subq1.c.trw2).label('trw2'),
                func.sum(subq1.c.trw3).label('trw3'),func.sum(subq1.c.trw4).label('trw4'))\
                .filter(Rekening.kode==func.left(subq1.c.subrek_kd, func.length(Rekening.kode)))\
                .group_by(Rekening.kode, Rekening.nama,
                Rekening.level_id, Rekening.defsign, subq1.c.urusan_kd, subq1.c.urusan_nm,
                subq1.c.unit_kd, subq1.c.unit_nm, subq1.c.tahun, subq1.c.perubahan)\
                .order_by(Rekening.kode).all()                    

            generator = r405Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        elif url_dict['act']=='31' :
            subq1 = DBSession.query(Rekening.kode.label('subrek_kd'),Rekening.nama.label('subrek_nm'),
                (KegiatanItem.vol_1_1* KegiatanItem.vol_1_2*KegiatanItem.hsat_1).label('jml1'),
                (KegiatanItem.vol_2_1* KegiatanItem.vol_2_2*KegiatanItem.hsat_2).label('jml2'),
                (KegiatanItem.vol_3_1* KegiatanItem.vol_3_2*KegiatanItem.hsat_3).label('jml3'),
                (KegiatanItem.vol_4_1* KegiatanItem.vol_4_2*KegiatanItem.hsat_4).label('jml4'),
                (KegiatanItem.bln01+KegiatanItem.bln02+KegiatanItem.bln03).label('trw1'),
                (KegiatanItem.bln04+KegiatanItem.bln05+KegiatanItem.bln06).label('trw2'),
                (KegiatanItem.bln07+KegiatanItem.bln08+KegiatanItem.bln09).label('trw3'),
                (KegiatanItem.bln10+KegiatanItem.bln11+KegiatanItem.bln12).label('trw4'),
                Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'),
                Urusan.kode.label('urusan_kd'), Urusan.nama.label('urusan_nm'),
                KegiatanSub.perubahan, KegiatanSub.tahun_id.label('tahun'))\
                .filter(KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                        KegiatanItem.rekening_id==Rekening.id,
                        KegiatanSub.unit_id==Unit.id,
                        Unit.urusan_id==Urusan.id,
                        KegiatanSub.tahun_id==self.session['tahun'],
                        KegiatanSub.unit_id==self.unit_id,
                        KegiatanSub.kegiatan_id==4)\
                .subquery()

            query = DBSession.query(Rekening.kode.label('rek_kd'), Rekening.nama.label('rek_nm'),
                Rekening.level_id, Rekening.defsign, subq1.c.urusan_kd, subq1.c.urusan_nm,
                subq1.c.unit_kd, subq1.c.unit_nm, subq1.c.tahun, subq1.c.perubahan, 
                func.sum(subq1.c.jml1).label('jumlah1'),func.sum(subq1.c.jml2).label('jumlah2'),
                func.sum(subq1.c.jml3).label('jumlah3'),func.sum(subq1.c.jml4).label('jumlah4'),
                func.sum(subq1.c.trw1).label('trw1'),func.sum(subq1.c.trw2).label('trw2'),
                func.sum(subq1.c.trw3).label('trw3'),func.sum(subq1.c.trw4).label('trw4'))\
                .filter(Rekening.kode==func.left(subq1.c.subrek_kd, func.length(Rekening.kode)))\
                .group_by(Rekening.kode, Rekening.nama,
                Rekening.level_id, Rekening.defsign, subq1.c.urusan_kd, subq1.c.urusan_nm,
                subq1.c.unit_kd, subq1.c.unit_nm, subq1, subq1.c.tahun, subq1.c.perubahan)\
                .order_by(Rekening.kode).all()                    

            generator = r406Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

        elif url_dict['act']=='32' :
            subq1 = DBSession.query(Rekening.kode.label('subrek_kd'),Rekening.nama.label('subrek_nm'),
                (KegiatanItem.vol_1_1* KegiatanItem.vol_1_2*KegiatanItem.hsat_1).label('jml1'),
                (KegiatanItem.vol_2_1* KegiatanItem.vol_2_2*KegiatanItem.hsat_2).label('jml2'),
                (KegiatanItem.vol_3_1* KegiatanItem.vol_3_2*KegiatanItem.hsat_3).label('jml3'),
                (KegiatanItem.vol_4_1* KegiatanItem.vol_4_2*KegiatanItem.hsat_4).label('jml4'),
                (KegiatanItem.bln01+KegiatanItem.bln02+KegiatanItem.bln03).label('trw1'),
                (KegiatanItem.bln04+KegiatanItem.bln05+KegiatanItem.bln06).label('trw2'),
                (KegiatanItem.bln07+KegiatanItem.bln08+KegiatanItem.bln09).label('trw3'),
                (KegiatanItem.bln10+KegiatanItem.bln11+KegiatanItem.bln12).label('trw4'),
                Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'),
                Urusan.kode.label('urusan_kd'), Urusan.nama.label('urusan_nm'),
                KegiatanSub.perubahan, KegiatanSub.tahun_id.label('tahun'))\
                .filter(KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                        KegiatanItem.rekening_id==Rekening.id,
                        KegiatanSub.unit_id==Unit.id,
                        Unit.urusan_id==Urusan.id,
                        KegiatanSub.tahun_id==self.session['tahun'],
                        KegiatanSub.unit_id==self.unit_id,
                        KegiatanSub.kegiatan_id==5)\
                .subquery()

            query = DBSession.query(Rekening.kode.label('rek_kd'), Rekening.nama.label('rek_nm'),
                Rekening.level_id, Rekening.defsign, subq1.c.urusan_kd, subq1.c.urusan_nm,
                subq1.c.unit_kd, subq1.c.unit_nm, subq1.c.tahun, subq1.c.perubahan, 
                func.sum(subq1.c.jml1).label('jumlah1'),func.sum(subq1.c.jml2).label('jumlah2'),
                func.sum(subq1.c.jml3).label('jumlah3'),func.sum(subq1.c.jml4).label('jumlah4'),
                func.sum(subq1.c.trw1).label('trw1'),func.sum(subq1.c.trw2).label('trw2'),
                func.sum(subq1.c.trw3).label('trw3'),func.sum(subq1.c.trw4).label('trw4'))\
                .filter(Rekening.kode==func.left(subq1.c.subrek_kd, func.length(Rekening.kode)))\
                .group_by(Rekening.kode, Rekening.nama,
                Rekening.level_id, Rekening.defsign, subq1.c.urusan_kd, subq1.c.urusan_nm,
                subq1.c.unit_kd, subq1.c.unit_nm, subq1.c.tahun, subq1.c.perubahan)\
                .order_by(Rekening.kode).all()                    

            generator = r407Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
                 
if __name__ == '__main__':
        generator = r001Generator()

        generator.generate([('1','2')])
