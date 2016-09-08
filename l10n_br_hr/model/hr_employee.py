# -*- encoding: utf-8 -*-
##############################################################################
#
#    Brazillian Human Resources Payroll module for OpenERP
#    Copyright (C) 2014 KMEE (http://www.kmee.com.br)
#    @author Rafael da Silva Lima <rafael.lima@kmee.com.br>
#            Matheus Felix <matheus.felix@kmee.com.br>
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
##############################################################################

from datetime import datetime

from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import odoo.addons.decimal_precision as dp
from odoo.exceptions import ValidationError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.multi
    def _get_dependents(self):
        for employee in self:
            dep_env = self.env['hr.employee.dependent']
            dep_ids = dep_env.search(
                [('employee_id', '=', employee.id),
                 ('dependent_verification', '=', True)])
            if dep_ids:
                employee.n_dependent = len(dep_ids)*179.71  #TODO Estranho multiplicar isto aqui
            else:
                employee.n_dependent = 0

    @api.one
    @api.constrains('pis_pasep')
    def _validate_pis_pasep(self):
        if not self.pis_pasep:
            return True

        digits = []
        for c in self.pis_pasep:
            if c == '.' or c == ' ' or c == '\t':
                continue

            if c == '-':
                if len(digits) != 10:
                    raise ValidationError(u"PIS/PASEP Inválido")
                continue

            if c.isdigit():
                digits.append(int(c))
                continue

            raise ValidationError(u"PIS/PASEP Inválido")
        if len(digits) != 11:
            raise ValidationError(u"PIS/PASEP Inválido")

        height = [int(x) for x in "3298765432"]

        total = 0

        for i in range(10):
            total += digits[i] * height[i]

        rest = total % 11
        if rest != 0:
            rest = 11 - rest
        if rest != digits[10]:
            raise ValidationError(u"PIS/PASEP Inválido")
    

    check_cpf = fields.Boolean('Check CPF', default=True)
    pis_pasep = fields.Char(u'PIS/PASEP', size=15)
    ctps = fields.Char('CTPS', help='Number of CTPS')
    ctps_series = fields.Char('Serie')
    ctps_date = fields.Date('Date of issue')
    creservist = fields.Char('Certificate of Reservist')
    crresv_categ = fields.Char('Category')
    cr_categ = fields.Selection([('estagiario', 'Trainee'),
                                 ('junior', 'Junior'),
                                 ('pleno', 'Full'),
                                 ('senior', 'Senior')],
                                string='Category', help="Choose work position")
    ginstru = fields.Selection(
        [('fundamental_incompleto', 'Basic Education incomplete'),
         ('fundamental', 'Basic Education complete'),
         ('medio_incompleto', 'High School incomplete'),
         ('medio', 'High School complete'),
         ('superior_incompleto', 'College Degree incomplete'),
         ('superior', 'College Degree complete'),
         ('mestrado', 'Master'),
         ('doutorado', 'PhD')],
        string='Schooling', help="Select Education")
    have_dependent = fields.Boolean("Associated")
    dependent_ids = fields.One2many('hr.employee.dependent',
                                    'employee_id', 'Employee')
    rg = fields.Char('RG', help='Number of RG')
    cpf = fields.Char(related='address_home_id.cnpj_cpf',
                      string='CPF', required=True)
    organ_exp = fields.Char("Organ Shipping")
    rg_emission = fields.Date('Date of issue')
    title_voter = fields.Char('Title', help='Number Voter')
    zone_voter = fields.Char('Zone')
    session_voter = fields.Char('Section')
    driver_license = fields.Char('Driver License',
                                 help='Driver License number')
    driver_categ = fields.Char('Category')
    father_name = fields.Char('Father name')
    mother_name = fields.Char('Mother name')
    validade = fields.Date('Expiration')
    sindicate = fields.Char('Sindicato', help="Sigla do Sindicato")
    n_dependent = fields.Float(string="Dependentes", compute=_get_dependents,
                               type="float",
                               digits_compute=dp.get_precision('Payroll'))

    #TODO Remover se não necessário
    def onchange_address_home_id(self):
        if address:
            address = self.pool.get('res.partner').browse(
                cr, uid, address, context=context)
            if address.cnpj_cpf:
                return {'value': {'check_cpf': True, 'cpf': address.cnpj_cpf}}
            else:
                return {'value': {'check_cpf': False, 'cpf': False}}
        return {'value': {}}

    #TODO Remover se não necessário
    def onchange_user(self):
        res = super(HrEmployee, self).onchange_user(
            cr, uid, ids, user_id, context)

        obj_partner = self.pool.get('res.partner')
        partner_id = obj_partner.search(
            cr, uid, [('user_ids', '=', user_id)])[0]
        partner = obj_partner.browse(cr, uid, partner_id)

        res['value'].update({'address_home_id': partner.id,
                             'cpf': partner.cnpj_cpf})
        return res


class HrEmployeeDependent(models.Model):
    _name = 'hr.employee.dependent'
    _description = 'Employee\'s Dependents'

    @api.one
    @api.constrains('dependent_age')
    def _check_birth(self, cr, uid, ids, context=None):
        dep_age = datetime.strptime(
            self.dependent_age, DEFAULT_SERVER_DATE_FORMAT)
        if dep_age.date() > datetime.now().date():
            raise ValidationError(u'Data de aniversário inválida')
        return True

    employee_id = fields.Many2one('hr.employee', 'Employee')
    dependent_name = fields.Char('Name', size=64, required=True,
                                 translate=True)
    dependent_age = fields.Date('Date of Birth', required=True)
    dependent_type = fields.Char('Type Associate', required=True)
    pension_benefits = fields.Float('Child Support')
    dependent_verification = fields.Boolean('Is dependent', required=False)
    health_verification = fields.Boolean('Health Plan', required=False)
