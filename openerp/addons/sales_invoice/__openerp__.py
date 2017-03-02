{
	'name': 'Minutes of Meeting',
	'version':'1.0',
	'description': """
		Minutes of Meeting
		- Meeting Agenda
		- Decisions
		- Notes
		- Issues
	""",
	'author': 'Suraj',
	'depends': ['base_setup','hr','mail','email_template', 'report','account','base'],
	'data': ['mom_report_new.xml', 'views/report_mom_new.xml','mom_report extra.xml', 'views/report_mom_extra.xml','mom_report.xml', 'views/report_mom.xml','views/header_layout.xml','invoice_report_new.xml','views/report_invoice_new.xml','invoice_report_extra.xml','views/report_invoice_extra.xml','invoice_report.xml','views/report_invoice.xml','wizard/print_invoice_view.xml','mom_view.xml'
	,'sale_order_report.xml','views/report_sale_order.xml','purchase_order_report.xml','views/report_purchase_order.xml','views/report_sale_quotation.xml','sale_quotation_report.xml'
	,'purchase_order_report_quotation.xml','views/report_purtchase_order_quotation.xml'],
	'installable': True,
	'auto_install': False,
}
