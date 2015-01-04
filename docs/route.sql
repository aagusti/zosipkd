\COPY routes(kode,disabled,created,create_uid,nama,path,perm_name) FROM stdin
ag-item	0	2014-12-24 03:04:42.837591	1	Item Kegiatan	/ag-item/{sub_keg_id}	view
ag-item-add	0	2014-12-24 03:04:42.837591	1	Tambah Item Kegiatan	/ag-item/{sub_keg_id}/add	add
ag-item-edit	0	2014-12-24 03:04:42.837591	1	Edit Item Kegiatan	/ag-item/{sub_keg_id}/{id}/edit	edit
ag-item-delete	0	2014-12-24 03:04:42.837591	1	Hapus Item Kegiatan	/ag-item/{sub_keg_id}/{id}/delete	delete
ag-item-act	0	2014-12-24 03:04:42.837591	1	Item Kegiatan Act	/ag-item/{sub_keg_id}/act/{act}	read
ag-item-csv	0	2014-12-24 03:04:42.837591	1	Item Kegiatan Act	/ag-item/{sub_keg_id}/csv/{csv}	read
