# -*- coding: utf-8 -*-
#
#
#    Copyright (c) 2017 RLTI. All rights reserved.
#    @author Rafael Lima
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#

from openerp import models, fields, api, _


class ResCurrency(models.Model):
    """Override currency to add base attribute and company_id"""

    _inherit = "res.currency"

    # Base for exchange
    base = fields.Boolean(
        string=_('Base for Exchange'),
        company_dependent=True,
        help=_("This should be 1,00, while is the base for all calculations to exchange money"),
        default=False)

    company_id = fields.Many2one(
        comodel_name='res.company',
        company_dependent=True,
        string=_('Company'),
    )

    _defaults = {
        'company_id': lambda s, cr, uid, ctx=None: s.pool['res.users']._get_company(cr, uid, context=ctx)
    }

    @api.onchange('active', 'base')
    def check_change(self):
        if self.active:

            if not self.company_id:
                comp_id = self.env.user.company_id
                self.company_id = comp_id

            if self.base and self.company_id:

                bases = self.env['res.currency'].search(
                    [('base', '=', True), ('company_id.id', '=', self.company_id.id)])

                bases_list = [x for x in bases]

                service = self.env['currency.rate.update.service'].search(
                        [('company_id.id', '=', self.company_id.id)])

                # It's required to use CAD when using service CA_BOC_getter
                if service.service == 'CA_BOC_getter' and len(bases) > 0:

                    for curr in bases:
                        if curr.name != 'CAD':
                            if curr.name != self.name:
                                curr.write({'base': False})
                            else:
                                self.base = False

                            bases_list.pop(bases_list.index(curr))

                    if self.name != 'CAD':
                        self.base = False
                    if self.rate != 1.0:
                        self.rate = 1.0




                    # To ensure that is the only base currency in the company
                    if len(bases_list) > 1:
                        for curr in bases_list:

                            if curr.name != 'CAD':
                                if curr.name != self.name:
                                    curr.write({'base': False})
                                else:
                                    self.base = False
                                bases_list.pop(bases_list.index(curr))

                        while len(bases_list) > 1:
                            bases_list[0].base = False
                            bases_list.pop(0)

                elif service.service == 'CA_BOC_getter' and self.name != 'CAD':
                    self.base = False
                elif service.service == 'CA_BOC_getter' and self.name == 'CAD' and self.rate != 1.0:
                    self.rate = 1.0

        elif self.base:
            self.base = False


class ResCurrencyRate(models.Model):
    """Override currency rate to change company_id to a related field"""

    _inherit = "res.currency.rate"

    # Company_id to provide compatibility with 9.0
    company_id = fields.Many2one(
        related='currency_id.company_id',
        store=True)
