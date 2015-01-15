\COPY routes(kode,disabled,created,create_uid,nama,path,perm_name) FROM stdin
user-group	0	2014-12-24 03:04:42.837591	1	User Group	/user-group	view
user-group-add	0	2014-12-24 03:04:42.837591	1	Tambah User Group	/user-group/add	read
user-group-edit	0	2014-12-24 03:04:42.837591	1	Edit User Group	/user-group/{id}/edit	view
user-group-delete	0	2014-12-24 03:04:42.837591	1	Harus User Group	/user-group/{id}/delete	view
user-group-act	0	2014-12-24 03:04:42.837591	1	User Group Act	/user-group/act/{act}	read
user-group-csv	0	2014-12-24 03:04:42.837591	1	User Group Act	/user-group/csv/{csv}	read
