from odoo import models, fields, api
from datetime import date
from datetime import datetime,timedelta
from collections import defaultdict




class CollectionSaleReportPdf(models.AbstractModel):
    _name = 'report.new_pdf_report.report_statement_pdf'

    def _get_report_values(self, docids, data=None):

        partner_id = self.env['res.partner'].browse(data['partner_id'])
        company_id = self.env.company

        partner_details = {
            'name': partner_id.name,
            'street': partner_id.street,
            'street2': partner_id.street2,
            'city': partner_id.city,
            'state': partner_id.state_id.name,
            'country': partner_id.country_id.name,
            'zip': partner_id.zip,
            'contact1': partner_id.phone,
            'contact2': partner_id.mobile,
        }

        statements_of_customer_template = {
            'get_pdc_details': self._get_pdc_details(data),
            'get_grand_total_amount': self._grand_total_amount(data),
            # 'vendor_bills': self._get_vendor_bill_details(data),
            # 'check_journal_entries': self._get_journal_entries_details(data),
            'data': data,
            'partner_details': partner_details,
            'company': company_id,
            # 'grand_total': self._get_total(data),
            # 'entry_total': self._get_entry_total(data),
            # 'check_status': self._get_status(data),
            # 'check_entries_ret': self._get_entries_ret(data),
            # 'get_cash_details': self._get_cash_details(data),
            # 'invoice_balance':self._invoice_balance(data),
            'combined_data_set':self._get_invoice_details_amt(data),
            'previous_total':self._previous_total_balance(data),

        }
        return statements_of_customer_template

    def _get_pdc_details(self, data):
        pdc_tots=[]
        rec_data = self.env['account.move'].search(
            [('company_id', '=', self.env.company.id),
             ('partner_id', '=', data['partner_id']),
             ('move_type', 'in', ['out_invoice', 'out_refund']),
             # ('pdc_payment_ids.payment_date', '<=', data['end_date']),
             # ('pdc_payment_ids.payment_date', '>=', data['start_date']),
             ('state', '=', 'posted'),
            ],
            order="invoice_date asc")

        vendor_data = self.env['account.move'].search(
            [('company_id', '=', self.env.company.id),
             ('partner_id', '=', data['partner_id']),
             ('move_type', 'in', ['out_invoice', 'out_refund']),
             ('invoice_date', '<=', data['end_date']),
             ('invoice_date','>=', data['start_date']),
             ('state', '=', 'posted'),
             ('payment_state', 'in', ['not_paid', 'partial'])],
            order="invoice_date asc")

        pdc_data= self.env['pdc.wizard'].search(
            [('company_id', '=', self.env.company.id),
             ('partner_id', '=', data['partner_id']),
             ('payment_date', '<=', data['end_date']),
             ('payment_date', '>=', data['start_date']),
             ('state', 'in',['done']),
             ],
            )

        data_dict = {}
        if rec_data :
            for rec in rec_data:
                pdc_ids = rec.pdc_payment_ids.filtered(
                    lambda x: x.state in ['done']and
                              x.payment_date >= datetime.strptime(data['start_date'], "%Y-%m-%d").date() and
                              x.payment_date <= datetime.strptime(data['end_date'], "%Y-%m-%d").date() )


                for pdc in pdc_ids:

                    key = pdc.id
                    inv_numbres = ''

                    for inv in pdc.invoice_ids:

                        inv_numbres += inv.name
                        inv_numbres += ','

                    if key in data_dict:
                        data_dict[key].append({
                            'name': pdc.name,
                            'reference': pdc.reference,
                            'date': pdc.payment_date.strftime('%d/%m/%Y'),
                            'amount': pdc.payment_amount,
                            'invoice_number': inv_numbres,
                            'due_date': pdc.due_date.strftime('%d/%m/%Y'),



                        })

                    else:
                        data_dict[key] = [({
                            'name': pdc.name,
                            'reference': pdc.reference,
                            'date': pdc.payment_date.strftime('%d/%m/%Y'),
                            'amount': pdc.payment_amount,
                            'invoice_number': inv_numbres,
                            'due_date': pdc.due_date.strftime('%d/%m/%Y'),
                        })]

        vend_dict = {}
        if vendor_data:
            for rec in vendor_data:
                pdc_ids = rec.pdc_payment_ids.filtered(
                    lambda x: x.state in ['draft','registered', 'deposited','done'])
                for pdc in pdc_ids:
                    key = pdc.id
                    inv_numbres = ''

                    for inv in pdc.invoice_ids:
                        inv_numbres += inv.name
                        inv_numbres += ','

                    if key in data_dict:
                        data_dict[key].append({
                            'name': pdc.name,
                            'reference': pdc.reference,
                            'date': pdc.payment_date.strftime('%d/%m/%Y'),
                            'amount': pdc.payment_amount,
                            'invoice_number': inv_numbres,
                            'due_date': pdc.due_date.strftime('%d/%m/%Y'),

                        })

                    else:
                        data_dict[key] = [({
                            'name': pdc.name,
                            'reference': pdc.reference,
                            'date': pdc.payment_date.strftime('%d/%m/%Y'),
                            'amount': pdc.payment_amount,
                            'invoice_number': inv_numbres,
                            'due_date': pdc.due_date.strftime('%d/%m/%Y'),

                        })]

        # pdc_dict = {}
        # if pdc_data:
        #     for data in pdc_data:
        #         for rec in data.rec_data:
        #             key = data.id
        #             inv_numbres = ''
        #             inv_numbres += rec.move_name
        #             if key in pdc_dict:
        #                 pdc_dict[key].append({
        #                     'move_name': rec.name,
        #                     'amount': data.payment_amount,
        #                     'date': rec.date.strftime('%d/%m/%Y'),
        #                     'reference': data.reference,
        #                     'invoice_number': rec.move_name,
        #                 })
        #             else:
        #                 pdc_dict[key] = [({
        #                     'move_name': rec.name,
        #                     'amount': data.payment_amount,
        #                     'reference': data.reference,
        #                     'invoice_number': rec.move_name,
        #                     'date': rec.date.strftime('%d/%m/%Y'),
        #                 })]

        new_data_dict = []
        for new_rec in data_dict:
            new_data_dict.append(data_dict[new_rec][0])
        # if pdc_data:
        #     for pdc_rec in pdc_dict:
        #         new_data_dict.append(pdc_dict[pdc_rec][0])
        #         print(new_data_dict,'new_data_dict')

        return new_data_dict


    def _get_invoice_details_amt(self, data):
        fst_totlas=0
        pls_lst=[]
        mns_lst=[]
        rec_data = self.env['account.move'].search(
            [('company_id', '=', self.env.company.id),
             ('partner_id', '=', data['partner_id']),
             ('move_type', 'in', ['out_invoice', 'out_refund']),
             ('invoice_date', '<=', data['end_date']),
             ('invoice_date', '>=', data['start_date']),
             ('state', '=', 'posted'),
             ],
            order="invoice_date asc")

        data_dict = {}
        length = 1
        for rec in rec_data:
            # edited
            ppch_ids = rec.env['account.payment'].search(
                [('partner_id', '=', rec.partner_id.id),
                 ('date', '<=', data['end_date']),
                 ('date', '>=', data['start_date']),
                 ],
                order="date asc"
            )


            for ppch in ppch_ids:
                if length > len(ppch_ids):
                    break
                length += 1
                key = ppch.date.strftime('%d/%m/%Y')
                if key in data_dict:

                    data_dict[key].append({
                        'name': ppch.name,
                        'date': ppch.date.strftime('%d/%m/%Y'),
                        'amount': ppch.amount,
                        'invoice_number': ppch.name,
                        'cash_payment':'CSH',
                        'lpo_no': ppch.lpo_number,
                        'do_no': ppch.ref,
                        'site_name': ppch.job_no,
                        # 'due_date': rec.invoice_date_due.strftime('%d/%m/%Y'),
                        'due_date': '0/0/0',

                    })

                else:

                    data_dict[key] = [({
                        'name': ppch.name,
                        'date': ppch.date.strftime('%d/%m/%Y'),
                        'amount': ppch.amount,
                        'invoice_number': ppch.name,
                        'cash_payment': 'CSH',
                        'lpo_no': ppch.lpo_number,
                        'do_no': ppch.ref,
                        'site_name': ppch.job_no,
                        # 'due_date': rec.invoice_date_due.strftime('%d/%m/%Y'),
                        'due_date': '0/0/0',
                    })]




        parms = data
        rec_data = self.env['account.move'].search([('company_id', '=', self.env.company.id),
                                                    ('partner_id', '=', data['partner_id']),
                                                    ('move_type', 'in', ['out_invoice', 'out_refund']),
                                                    ('invoice_date', '<=', data['end_date']),
                                                    ('invoice_date', '>=', data['start_date']),
                                                    ('state', '=', 'posted'),
                                                    ],
                                                   order="invoice_date asc")


        data_dicts = {}
        val = 0
        # records = self._invoice_balance(data)
        # itm = 0
        for rec in rec_data:
            # if rec.move_type == "out_refund":
            #     credit_note = 'neg'
            # else:
            #     credit_note = 'pos'
            # inital_blnc = float(format(records[itm], ".2f"))
            # itm += 1
            # if rec.show_del_order == False:
            #     del_num = rec.delivery_order
            # elif rec.show_del_order == True:
            #     del_num = rec.related_del_id.name
            pdc_ids = rec.pdc_payment_ids.filtered(lambda x: x.state in ['registered', 'deposited'])
            if not pdc_ids:
                key = rec.invoice_date.strftime('%d/%m/%Y')
                if key in data_dicts:

                    data_dicts[key].append({
                        'name': rec.name,
                            'date': rec.invoice_date.strftime('%d/%m/%Y'),
                            'amount': rec.amount_total_signed,
                            'order_no': rec.name ,
                            # 'due_date': rec.invoice_date_due.strftime('%d/%m/%Y'),
                         'due_date': '30/30/30',
                            'due_amount': rec.amount_residual_signed,
                            'cash_payment': 'INV',
                            'total':rec.amount_total,
                        'lpo_no': rec.lpo_number,
                        'do_no': rec.ref,
                        'site_name': rec.job_no,
                    })


                else:
                    data_dicts[key] = [
                        {
                            'name': rec.name,
                            'date': rec.invoice_date.strftime('%d/%m/%Y'),
                            'amount': rec.amount_total_signed,
                            'order_no': rec.name ,
                            # 'do_no': del_num,
                            # 'due_date': rec.invoice_date_due.strftime('%d/%m/%Y'),
                            'due_date': '30/30/30',
                            'due_amount': rec.amount_residual_signed,
                            'cash_payment': 'INV',
                            'total': rec.amount_total,
                            'lpo_no': rec.lpo_number,
                            'do_no': rec.ref,
                            'site_name': rec.job_no,
                            # 'credit_note':credit_note,
                            # 'invoice_amt': inital_blnc

                        }
                    ]


            else:
                key =  rec.invoice_date.strftime('%d/%m/%Y')
                if key in data_dicts:
                    data_dicts[key].append({
                        'name': rec.name,
                            'date': rec.invoice_date.strftime('%d/%m/%Y'),
                            'amount': rec.amount_total_signed,
                            'order_no': rec.name,
                            # 'do_no': del_num,
                            # 'due_date': rec.invoice_date_due.strftime('%d/%m/%Y'),
                        'due_date': '12/12/12',
                            'due_amount': rec.amount_residual_signed,
                            'cash_payment': 'INV',
                        # 'credit_note': credit_note,
                        'total': rec.amount_total,
                        'lpo_no': rec.lpo_number,
                        'do_no': rec.ref,
                        'site_name': rec.job_no,
                            # 'invoice_amt': inital_blnc
                    })

                else:
                    data_dicts[key] = [
                        {
                            'name': rec.name,
                            'date': rec.invoice_date.strftime('%d/%m/%Y'),
                            'amount': rec.amount_total_signed,
                            'order_no': rec.name,
                            # 'do_no': del_num,
                            # 'due_date': rec.invoice_date_due.strftime('%d/%m/%Y'),
                            'due_amount': rec.amount_residual_signed,
                            'due_date': '12/12/12',
                            'cash_payment': 'INV',
                            # 'credit_note': credit_note,
                            'total': rec.amount_total,
                            'lpo_no': rec.lpo_number,
                            'do_no': rec.ref,
                            'site_name': rec.job_no,
                            # 'invoice_amt': inital_blnc

                        }
                    ]



        #first staring
        record_datas = self.env['account.move.line'].search(
            [('partner_id', '=', data['partner_id']),
             ('move_id.move_type', '=', 'entry'),
             ('move_id.journal_id.type', 'in', ['general', 'sale']),
             ('date', '<=', data['end_date']),
             ('date', '>=', data['start_date']),
             ])
        total_value = 0
        # for rd in record_datas:
        #         # record_datas.move_id.print_initial = True
        #         if rd.account_id.account_type == 'asset_receivable':
        #             amount=0
        #             if rd.credit:
        #                 total_value += rd.credit
        #                 initial_amt='0'
        #                 amount=rd.credit
        #
        #             elif rd.debit:
        #                 total_value += rd.debit
        #                 initial_amt='INV'
        #                 amount=rd.debit
        #             key = rd.move_id.date.strftime('%d/%m/%Y')
        #             if key in data_dict:
        #
        #                 data_dict[key].append({
        #                     'name':rd.move_id.name,
        #                     'date':rd.move_id.date.strftime('%d/%m/%Y'),
        #                     'amount': amount,
        #                     'cash_payment':initial_amt,
        #                     'lpo_no': rd.lpo_number,
        #                     'do_no': rd.ref,
        #                     'site_name': rd.job_no,
        #                     # 'due_date': rd.invoice_payment_term_id.strftime('%d/%m/%Y'),
        #                     'due_date': '15/12/12',
        #                 })
        #             else:
        #
        #                 data_dict[key] = [
        #                     {
        #                         'name':rd.move_id.name,
        #                         'date':rd.move_id.date.strftime('%d/%m/%Y'),
        #                         'amount': amount,
        #                         'cash_payment': initial_amt,
        #                         'lpo_no': rd.lpo_number,
        #                         'do_no': rd.ref,
        #                         'site_name': rd.job_no,
        #                         # 'due_date': rd.invoice_payment_term_id.strftime('%d/%m/%Y'),
        #                         'due_date': '15/12/12',
        #                         # 'due_amount': rcrd.amount_residual_signed,
        #                     }
        #                 ]

        #last starting


        for date, records in data_dicts.items():
            date_obj = datetime.strptime(date, '%d/%m/%Y')
            key = date_obj.strftime('%d/%m/%Y')
            for record in records:
                if key in data_dict:
                    data_dict[key].append({
                                'name': record['name'],
                                'date':date_obj.strftime('%d/%m/%Y'),
                                'amount': record['amount'],
                                'cash_payment':record['cash_payment'],
                                'lpo_no': record['lpo_no'],
                                'do_no': record['do_no'],
                                'site_name': record['site_name'],
                                'due_date': record['due_date'],
                            })
                else:
                    data_dict[key] = [
                        {
                            'name': record['name'],
                            'date': date_obj.strftime('%d/%m/%Y'),
                            'amount': record['amount'],
                            'cash_payment': record['cash_payment'],
                            'lpo_no': record['lpo_no'],
                            'do_no': record['do_no'],
                            'site_name': record['site_name'],
                            'due_date': record['due_date'],
                        }
                    ]

        sorted_data = {k: sorted(v, key=lambda x: datetime.strptime(x['date'], '%d/%m/%Y')) for k, v in data_dict.items()}

        # Sort the main dictionary based on dates
        sorted_data = dict(sorted(sorted_data.items(), key=lambda x: datetime.strptime(x[0], '%d/%m/%Y')))
        for record in sorted_data.items():
            for rec in record[1]:

                print('srrrrrr',rec)

        return sorted_data

    def _previous_total_balance(self,data):
        previous_date = (datetime.strptime(data['start_date'], '%Y-%m-%d') - timedelta(days=1)).date()
        rec_data = self.env['account.move'].search(
            [('company_id', '=', self.env.company.id),
             ('partner_id', '=', data['partner_id']),
             ('move_type', 'in', ['out_invoice', 'out_refund']),
             ('invoice_date', '<=', previous_date),
             ('state', '=', 'posted'),
             ],
            order="invoice_date asc")


        sum_of_inv = 0
        sum_of_other = 0
        length = 1
        for rec in rec_data:
            ppch_ids = rec.env['account.payment'].search(
                [('partner_id', '=', rec.partner_id.id),
                 ('date', '<=', previous_date),
                 ],
                order="date asc"
            )

            for ppch in ppch_ids:
                if length > len(ppch_ids):
                    break
                length += 1
                sum_of_other += ppch.amount

        rec_data = self.env['account.move'].search([('company_id', '=', self.env.company.id),
                                                    ('partner_id', '=', data['partner_id']),
                                                    ('move_type', 'in', ['out_invoice', 'out_refund']),
                                                    ('invoice_date', '<=', previous_date),
                                                    ('state', '=', 'posted'),
                                                    ],
                                                   order="invoice_date asc")

        for rec in rec_data:
            sum_of_inv+=rec.amount_total_signed


        record_datas = self.env['account.move.line'].search(
            [('partner_id', '=', data['partner_id']),
             ('move_id.move_type', '=', 'entry'),
             ('move_id.journal_id.type', 'in', ['general', 'sale']),
             ('date', '<=', previous_date),
             ])
        for rd in record_datas:
            if rd.credit:
                sum_of_other+=rd.credit
            elif rd.debit:
                sum_of_inv+=rd.debit


        # rec_data = self.env['account.move'].search(
        #     [('company_id', '=', self.env.company.id),
        #      ('partner_id', '=', data['partner_id']),
        #      ('move_type', 'in', ['out_invoice', 'out_refund']),
        #      ('state', '=', 'posted'),
        #      ],
        #     order="invoice_date asc")
        #
        # if rec_data:
        #     for rec in rec_data:
        #         pdc_ids = rec.pdc_payment_ids.filtered(
        #             lambda x: x.state in ['done'] and
        #                       x.payment_date <= previous_date)
        #         for pdc in pdc_ids:
        #             for inv in pdc.invoice_ids:
        #                 sum_of_other+=pdc.payment_amount
        #start
        rec_data = self.env['account.move'].search(
            [('company_id', '=', self.env.company.id),
             ('partner_id', '=', data['partner_id']),
             ('move_type', 'in', ['out_invoice', 'out_refund']),
             # ('pdc_payment_ids.payment_date', '<=', data['end_date']),
             # ('pdc_payment_ids.payment_date', '>=', data['start_date']),
             ('state', '=', 'posted'),
             ],
            order="invoice_date asc")

        vendor_data = self.env['account.move'].search(
            [('company_id', '=', self.env.company.id),
             ('partner_id', '=', data['partner_id']),
             ('move_type', 'in', ['out_invoice', 'out_refund']),
             ('invoice_date', '<=', previous_date),
             ('state', '=', 'posted'),
             ('payment_state', 'in', ['not_paid', 'partial'])],
            order="invoice_date asc")

        pdc_data = self.env['pdc.wizard'].search(
            [('company_id', '=', self.env.company.id),
             ('partner_id', '=', data['partner_id']),
             ('payment_date', '<=', previous_date),
             ('state', 'in', ['done']),
             ],
        )

        data_dict = {}
        if rec_data:
            for rec in rec_data:
                pdc_ids = rec.pdc_payment_ids.filtered(
                    lambda x: x.state in ['done'] and
                              x.payment_date <= previous_date)

                for pdc in pdc_ids:

                    key = pdc.id
                    inv_numbres = ''

                    for inv in pdc.invoice_ids:
                        inv_numbres += inv.name
                        inv_numbres += ','

                    if key in data_dict:
                        data_dict[key].append({
                            'name': pdc.name,
                            'reference': pdc.reference,
                            'date': pdc.payment_date.strftime('%d/%m/%Y'),
                            'amount': pdc.payment_amount,
                            'invoice_number': pdc.name,
                            'due_date': pdc.due_date.strftime('%d/%m/%Y'),
                        })

                    else:
                        data_dict[key] = [({
                            'name': pdc.name,
                            'reference': pdc.reference,
                            'date': pdc.payment_date.strftime('%d/%m/%Y'),
                            'amount': pdc.payment_amount,
                            'invoice_number': pdc.name,
                            'due_date': pdc.due_date.strftime('%d/%m/%Y'),
                        })]

        vend_dict = {}
        if vendor_data:
            for rec in vendor_data:
                pdc_ids = rec.pdc_payment_ids.filtered(
                    lambda x: x.state in ['draft', 'registered', 'deposited', 'done'])
                for pdc in pdc_ids:
                    key = pdc.id
                    inv_numbres = ''

                    for inv in pdc.invoice_ids:
                        inv_numbres += inv.name
                        inv_numbres += ','

                    if key in data_dict:
                        data_dict[key].append({
                            'name': pdc.name,
                            'reference': pdc.reference,
                            'date': pdc.payment_date.strftime('%d/%m/%Y'),
                            'amount': pdc.payment_amount,
                            'invoice_number': inv_numbres,
                            'due_date': pdc.due_date.strftime('%d/%m/%Y'),

                        })

                    else:
                        data_dict[key] = [({
                            'name': pdc.name,
                            'reference': pdc.reference,
                            'date': pdc.payment_date.strftime('%d/%m/%Y'),
                            'amount': pdc.payment_amount,
                            'invoice_number': inv_numbres,
                            'due_date': pdc.due_date.strftime('%d/%m/%Y'),

                        })]


        new_data_dict = []
        for new_rec in data_dict:
            new_data_dict.append(data_dict[new_rec][0])
        for ddd in new_data_dict:
            sum_of_other += ddd['amount']

        #end

        return  sum_of_inv - sum_of_other


    def _grand_total_amount(self,data):
        invoice_dbt_amt=[]
        invoice_crdt_amt=[]
        pdc_total=[]
        inv_amounts=self._get_invoice_details_amt(data)
        pdc_amounts=self._get_pdc_details(data)
        opening_blnc=self._previous_total_balance(data)
        if opening_blnc:
            invoice_dbt_amt.append(opening_blnc)
        for record in inv_amounts.items():
            for rec in record[1]:
                if rec['cash_payment'] == 'CSH':
                    invoice_crdt_amt.append(abs(rec['amount']))
                elif rec['amount'] < 0:
                    invoice_crdt_amt.append(abs(rec['amount']))
                else:
                    invoice_dbt_amt.append(rec['amount'])


        for pdc in pdc_amounts:
            if pdc:
                pdc_total.append(pdc['amount'])

        invoice_debit_amount_sum = sum(invoice_dbt_amt)
        invoice_credit_amount_sum = sum(invoice_crdt_amt)
        pdc_amount_sum = sum(pdc_total)
        inv_last_amount=abs(invoice_debit_amount_sum)-abs(invoice_credit_amount_sum)

        return  inv_last_amount - abs(pdc_amount_sum)