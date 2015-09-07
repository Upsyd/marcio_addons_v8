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
from openerp.osv import fields, osv
from openerp.tools.translate import _

from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_round
from openerp import SUPERUSER_ID
from dateutil.relativedelta import relativedelta
from datetime import datetime
from psycopg2 import OperationalError
import openerp

class purchase_order(osv.osv):
    _inherit = 'purchase.order'

    def wkf_confirm_order(self, cr, uid, ids, context=None):
        order =  super(purchase_order, self).wkf_confirm_order(cr, uid, ids, context=context)
        groups = self.pool.get('res.groups').search(cr, uid, [('name','=','Manager'),('category_id.name','=', 'Warehouse')], context={})
        users = [x.id for x in self.pool.get('res.groups').browse(cr, uid, groups, context=context).users]
        template_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'purchase', 'email_template_edi_purchase_done')[1]
        email_template_obj = self.pool.get('email.template')
        if users:
            for user in self.pool.get('res.users').browse(cr,uid,users,context=context):
                if template_id:
                    values = email_template_obj.generate_email(cr, uid, template_id, ids[0], context=context)
                    values['email_to'] = user.email
                    values['res_id'] = False
                    mail_mail_obj = self.pool.get('mail.mail')
                    msg_id = mail_mail_obj.create(cr, SUPERUSER_ID, values, context=context)
                    if msg_id:
                        mail_mail_obj.send(cr, SUPERUSER_ID, [msg_id], context=context)
        return True


class custome_purchase(osv.osv_memory):
    _name = 'custom.purchase'
    _description = 'Select product for po'
    _columns = {
        'supplier': fields.many2one('res.partner', 'Supplier'),
        'option': fields.selection([('existing', 'Add Products in Draft Purchase Order'),('new', 'Create New Purchase Order')], 'Option'),
        'po_id': fields.many2one('purchase.order','Purchase Order'),
    }

    _defaults = {
        'option':'new',
    }

    def purchase_create(self, cr, uid, ids, context=None):
        record_id = context and context.get('active_ids', False)
        purchase_pool = self.pool.get('purchase.order')
        product_pool = self.pool.get('product.product')
        line_pool = self.pool.get('purchase.order.line')
        wizard_obj = self.browse(cr, uid, ids, context=context)
        if wizard_obj.option == 'new':
            res = purchase_pool.onchange_partner_id(cr, uid, [],
                                                    wizard_obj.supplier.id,
                                                    context=context)
            resdict = res['value']
            resdict.update({'partner_id': wizard_obj.supplier.id})
            locate = purchase_pool._get_picking_in(cr, uid, context=context)
            onchange_picking = purchase_pool.onchange_picking_type_id(cr, uid, ids, locate,
                                                          context=context)
            po_dict = onchange_picking['value']
            polinelist = []
            for o in product_pool.browse(cr,uid,record_id,context=context):
                product_id = o and o.id or False
                uom_id = o.product_tmpl_id.uom_po_id and o.product_tmpl_id.uom_po_id.id or False
                qty=o.qty_available or 0.0
                poline_dict = line_pool.onchange_product_id(cr, uid, [],
                                                      res['value']['pricelist_id'],
                                                      product_id,
                                                      qty,
                                                      uom_id,
                                                      partner_id=wizard_obj.supplier.id,
                                                      date_order=False,
                                                      fiscal_position_id=False,
                                                      date_planned=False,
                                                      name=False,
                                                      price_unit=False,
                                                      state='draft', context=context)
                polineval = poline_dict['value']
                polineval.update({'product_id':product_id})
                polinelist.append((0, 0, polineval))
                vals = {'partner_id': resdict['partner_id'],
                        'pricelist_id': resdict['pricelist_id'],
                        'order_line': polinelist,
                        'location_id': po_dict['location_id'], }
            po_id = purchase_pool.create(cr, uid, vals, context)
        elif wizard_obj.option == 'existing':
            res = purchase_pool.onchange_partner_id(cr, uid, [],
                                                    wizard_obj.po_id.partner_id.id,
                                                    context=context)
            resdict = res['value']
            resdict.update({'partner_id': wizard_obj.po_id.partner_id.id})
            locate = purchase_pool._get_picking_in(cr, uid, context=context)
            onchange_picking = purchase_pool.onchange_picking_type_id(cr, uid, ids, locate,
                                                          context=context)
            po_dict = onchange_picking['value']
            polinelist = []
            for o in product_pool.browse(cr,uid,record_id,context=context):
                product_id = o and o.id or False
                uom_id = o.product_tmpl_id.uom_po_id and o.product_tmpl_id.uom_po_id.id or False
                qty=o.qty_available or 0.0
                poline_dict = line_pool.onchange_product_id(cr, uid, [],
                                                      res['value']['pricelist_id'],
                                                      product_id,
                                                      qty,
                                                      uom_id,
                                                      partner_id=wizard_obj.po_id.partner_id.id,
                                                      date_order=False,
                                                      fiscal_position_id=False,
                                                      date_planned=False,
                                                      name=False,
                                                      price_unit=False,
                                                      state='draft', context=context)
                polineval = poline_dict['value']
                polineval.update({'product_id':product_id,'order_id':wizard_obj.po_id.id})
                poline = line_pool.create(cr, uid, polineval,context)
        else:
            pass
        return True



class procurement_order(osv.osv):
    _inherit = 'procurement.order'

    def _procure_orderpoint_confirm(self, cr, uid, use_new_cursor=False, company_id = False, context=None):
        if context is None:
            context = {}
        if use_new_cursor:
            cr = openerp.registry(cr.dbname).cursor()
        orderpoint_obj = self.pool.get('stock.warehouse.orderpoint')
        procurement_obj = self.pool.get('procurement.order')
        dom = company_id and [('company_id', '=', company_id)] or []
        orderpoint_ids = orderpoint_obj.search(cr, uid, dom)
        prev_ids = []
        while orderpoint_ids:
            ids = orderpoint_ids[:100]
            del orderpoint_ids[:100]
            for op in orderpoint_obj.browse(cr, uid, ids, context=context):
                try:
                    prods = self._product_virtual_get(cr, uid, op)
                    if prods is None:
                        continue
                    if float_compare(prods, op.product_min_qty, precision_rounding=op.product_uom.rounding) < 0:
                        qty = max(op.product_min_qty, op.product_max_qty) - prods
                        reste = op.qty_multiple > 0 and qty % op.qty_multiple or 0.0
                        if float_compare(reste, 0.0, precision_rounding=op.product_uom.rounding) > 0:
                            qty += op.qty_multiple - reste

                        if float_compare(qty, 0.0, precision_rounding=op.product_uom.rounding) <= 0:
                            continue

                        qty -= orderpoint_obj.subtract_procurements(cr, uid, op, context=context)
                        qty_rounded = float_round(qty, precision_rounding=op.product_uom.rounding)
                        if qty_rounded > 0:
                            proc_id = procurement_obj.create(cr, uid,
                                                             self._prepare_orderpoint_procurement(cr, uid, op, qty_rounded, context=context),
                                                             context=context)
                            self.check(cr, uid, [proc_id])
                            self.run(cr, uid, [proc_id])
                            #category_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'stock', 'group_stock_manager')[1]
                            #groups = self.pool.get('res.groups').search(cr, uid, [('name','=','Manager'),('category_id','=', category_id)], context={})
                            template_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'send_mail_procurement', 'email_template_procurement')[1]
                            groups = self.pool.get('res.groups').search(cr, uid, [('name','=','Manager'),('category_id.name','=', 'Warehouse')], context={})
                            users = [x.id for x in self.pool.get('res.groups').browse(cr, uid, groups, context=context).users]
                            email_template_obj = self.pool.get('email.template')
                            if users:
                                for user in self.pool.get('res.users').browse(cr,uid,users,context=context):
                                    if template_id:
                                        values = email_template_obj.generate_email(cr, uid, template_id, proc_id, context=context)
                                        values['email_to'] = user.email
                                        values['res_id'] = False
                                        mail_mail_obj = self.pool.get('mail.mail')
                                        msg_id = mail_mail_obj.create(cr, SUPERUSER_ID, values, context=context)
                                        if msg_id:
                                            mail_mail_obj.send(cr, SUPERUSER_ID, [msg_id], context=context)
                            #print "proc_idddddddddd\n\n", proc_id
                            #print "category_iddddddddd\n\n", category_id,groups
                            #print "template_iddddddddddd\n\n", template_id
                            #procure_obj = self.pool.get('procurement.order').browse(cr, uid, proc_id, context=context)
                            #self.pool.get('email.template').send_mail(cr, uid, template_id, procure_obj.id,force_send=False, context=context)
                    if use_new_cursor:
                        cr.commit()
                except OperationalError:
                    if use_new_cursor:
                        orderpoint_ids.append(op.id)
                        cr.rollback()
                        continue
                    else:
                        raise
            if use_new_cursor:
                cr.commit()
            if prev_ids == ids:
                break
            else:
                prev_ids = ids

        if use_new_cursor:
            cr.commit()
            cr.close()
        return {}
