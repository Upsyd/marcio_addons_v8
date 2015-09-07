# -*- coding: utf-8 -*-
##############################################################################
#
#    This module uses OpenERP, Open Source Management Solution Framework.
#    Copyright (C) 2014-Today BrowseInfo (<http://www.browseinfo.in>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################


{
    'name': 'Sale Mail Procurement',
    'version': '7.0',
    'description': """
    This Modules Contains functionality to Send Email Notification When Procurement Create,
    Contains feature for alert to warehouse manager when po confirmed,and receives copy of purchase order,
    wizard for Create Purchase Order from product form.

    """,
    "category": 'stock',
    'author': 'BrowseInfo',
    'website': 'www.browseinfo.in',
    'depends': ['stock','sale','procurement','purchase','mail'],
    'data': [
        'security/ir.model.access.csv',
        'send_mail_template.xml',
        'send_mail_custom.xml',
    ],
    'installable': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
