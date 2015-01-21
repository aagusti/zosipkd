import colander
from deform import widget
from datetime import datetime
kat_widget = widget.AutocompleteInputWidget(
        size=60,
        values = '/aset/kategori/headofnama/act',
        min_length=2)
katkode_widget = widget.AutocompleteInputWidget(
        size=60,
        values = '/aset/kategori/headofkode/act',
        min_length=2)
class KibSchema(colander.Schema):
    tahun           = colander.SchemaNode(
                          colander.Integer(),
                          default = datetime.now().year)
    unit_id         = colander.SchemaNode(
                          colander.Integer(),
                          widget = widget.HiddenWidget(),
                          oid = "unit_id")
    unit_kd         = colander.SchemaNode(
                          colander.String(),
                          #widget = katkode_widget,
                          oid = "unit_kd",
                          title = "SKPD")
    unit_nm         = colander.SchemaNode(
                          colander.String(),
                          #widget = katkode_widget,
                          oid = "unit_nm",
                          title = "")
    kategori_id  = colander.SchemaNode(
                    colander.Integer(),
                    widget = widget.HiddenWidget(),
                    oid = "kategori_id"
                    )
    kategori_kd = colander.SchemaNode(
                    colander.String(),
                    #widget = katkode_widget,
                    oid = "kategori_kd",
                    title = "Kategori"
                    )
    kategori_nm = colander.SchemaNode(
                    colander.String(),
                    #widget = kat_widget,
                    oid = "kategori_nm",
                    title = "Kategori"
                    )
    no_register     = colander.SchemaNode(
                          colander.Integer(),
                          missing = colander.drop,
                          oid = "no_register",)
    pemilik_id      = colander.SchemaNode(
                          colander.Integer(),
                          title="Pemilik")
                          
    uraian          = colander.SchemaNode(
                          colander.String())
    tgl_perolehan   = colander.SchemaNode(
                          colander.Date(),
                          title="Tanggal")
    cara_perolehan  = colander.SchemaNode(
                          colander.String(),
                          title="Cara")
    th_beli         = colander.SchemaNode(
                          colander.Integer(),
                          title="Thn. Beli")
    asal_usul       = colander.SchemaNode(
                          colander.String(),
                          title="Asal-usul")
    harga           = colander.SchemaNode(
                          colander.Integer())
    jumlah          = colander.SchemaNode(
                          colander.Integer())
    satuan          = colander.SchemaNode(
                          colander.String())
    kondisi         = colander.SchemaNode(
                          colander.String())
    keterangan      = colander.SchemaNode(
                          colander.String())



