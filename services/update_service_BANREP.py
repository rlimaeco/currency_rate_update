# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2009 CamptoCamp. All rights reserved.
#    @author Rafael Lima
#
#    Abstract class to fetch rates from Yahoo Financial
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
"""
 Conventions:
    o_var: var type object
    s_var: var type string (char)
    i_var: var type integer
    f_var: var type float
"""
import logging
import xml.etree.ElementTree as ET
import suds
from datetime import datetime
from suds.client import Client
from .currency_getter_interface import Currency_getter_interface
_logger = logging.getLogger(__name__)


class BANREP_getter(Currency_getter_interface):
    """Implementation of Currency_getter_factory interface
    for Banco de la Republica Colombia
    """

    def _get_soap_trm(self):
        s_url = "http://obiee.banrep.gov.co/analytics/saw.dll?wsdl"
        o_client = Client(s_url, service="SAWSessionService")
        s_session_id = o_client.service.logon("publico", "publico")
        o_client.set_options(service="XmlViewService")
        s_reportPath = "/shared/Consulta Series Estadisticas desde Excel/1. " \
            "Tasa de Cambio Peso Colombiano/1.1 TRM - " \
            "Disponible desde el 27 de noviembre de 1991/" \
            "1.1.3 Serie historica para un rango de fechas dado"
        o_report = {
            "reportPath": s_reportPath,
            "reportXml": "null"
        }
        o_options = {
            "async": "false",
            "maxRowsPerPage": "100",
            "refresh": "true",
            "presentationInfo": "true"
        }
        try:
            o_result_query = o_client.service.executeXMLQuery(
                o_report, "SAWRowsetData", o_options, s_session_id)
            o_client.set_options(service="SAWSessionService")
            xml_data = ET.fromstring(o_result_query.rowset)

            rate_name = xml_data[0][1].text
            # Dolar currency get
            rate_value = float(xml_data[0][2].text)
        except suds.WebFault as detail:
            o_client.set_options(service="SAWSessionService")
            _logger.critical(
                "Error while working with BancoRep API: " + detail)

        o_client.service.logoff(s_session_id)
        return rate_name, rate_value

    def get_updated_currency(self, currency_array, main_currency,
                             max_delta_days):
        """implementation of abstract method of curreny_getter_interface"""
        self.validate_cur(main_currency)

        if main_currency in currency_array:
            currency_array.remove(main_currency)

        rate_name, trm = self._get_soap_trm()

        for curr in currency_array:
            self.validate_cur(curr)

            if curr == 'USD':
                self.updated_currency[curr] = trm

        return self.updated_currency, self.log_info
