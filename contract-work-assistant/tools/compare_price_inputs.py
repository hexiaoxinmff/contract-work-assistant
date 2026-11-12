#!/usr/bin/env python3
"""Compare supplied structured quotes from stdin; never extracts facts from contracts."""
import json
import sys
from decimal import Decimal, InvalidOperation, localcontext

FIELDS = ('scope', 'quantity', 'term', 'tax', 'extra_costs', 'currency')

def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    try:
        data = json.load(sys.stdin)
        quotes = data['quotes']
        if not isinstance(quotes, list) or len(quotes) < 2:
            raise ValueError('quotes must contain at least two entries')
        results = []
        labels = set()
        for q in quotes:
            if not isinstance(q, dict):
                raise ValueError('each quote must be an object')
            for key in ('label', 'source', 'amount', 'interval'):
                if not isinstance(q.get(key), str) or not q[key].strip():
                    raise ValueError(f'{key} must be a nonempty string')
            if q['label'] in labels:
                raise ValueError('quote labels must be unique')
            labels.add(q['label'])
            amount = Decimal(q['amount'])
            if not amount.is_finite() or amount < 0:
                raise ValueError('amount must be finite and nonnegative')
            if q['interval'] not in ('month', 'year', 'visit', 'sqm', 'once'):
                raise ValueError('interval must be month, year, visit, sqm or once')
            if q['interval'] in ('visit', 'sqm') and (not isinstance(q.get('unit_detail'), str) or not q['unit_detail'].strip()):
                raise ValueError('visit and sqm require unit_detail including any time basis')
            if 'calculation_quantity' in q and q['interval'] not in ('visit', 'sqm'):
                raise ValueError('calculation_quantity is supported only for visit or sqm')
            row = {'label': q['label'], 'source': q['source'], 'input_amount': q['amount'],
                   'interval': q['interval'], 'unit_detail': q.get('unit_detail'),
                   'conditions': {k: q.get(k) for k in FIELDS}}
            with localcontext() as ctx:
                ctx.prec = max(50, len(q['amount']) + 10)
                if q['interval'] in ('month', 'year'):
                    row['annual_rate'] = str(amount * (12 if q['interval'] == 'month' else 1))
                    row['formula'] = q['amount'] + (' �� 12' if q['interval'] == 'month' else ' �� 1')
                elif q['interval'] == 'once':
                    row['one_time_stated_fee'] = str(amount)
                elif 'calculation_quantity' in q:
                    raw_qty = q['calculation_quantity']
                    if not isinstance(raw_qty, str) or not isinstance(q.get('quantity_source'), str) or not q['quantity_source'].strip():
                        raise ValueError('calculation_quantity and quantity_source must both be nonempty strings')
                    quantity = Decimal(raw_qty)
                    if not quantity.is_finite() or quantity < 0:
                        raise ValueError('calculation_quantity must be finite and nonnegative')
                    ctx.prec = max(ctx.prec, len(q['amount']) + len(raw_qty) + 10)
                    row['partial_amount'] = str(amount * quantity)
                    row['formula'] = q['amount'] + ' �� ' + raw_qty
                    row['quantity_source'] = q['quantity_source']
                else:
                    row['calculation_note'] = 'Quantity not supplied; no partial amount calculated.'
            results.append(row)
        missing = {q['label']: [k for k in FIELDS if not isinstance(q.get(k), str) or not q[k].strip()] for q in quotes}
        different = [k for k in FIELDS if all(isinstance(q.get(k), str) and q[k].strip() for q in quotes)
                     and len({q[k].strip() for q in quotes}) > 1]
        units = {q['interval'] for q in quotes}
        basis_mismatch = (len(units) > 1 and not units.issubset({'month', 'year'})) or (
            bool(units & {'visit', 'sqm'}) and len({q.get('unit_detail') for q in quotes}) > 1)
        ready = not any(missing.values()) and not different and not basis_mismatch
        print(json.dumps({'quotes': results, 'missing_conditions': missing, 'different_conditions': different,
             'pricing_basis_mismatch': basis_mismatch, 'condition_texts_match': ready,
             'limitations': ['Annualized rate, partial amount and one-time fee are not contract total or final payable amount.',
               'Matching supplied condition text does not establish factual or semantic equivalence; verify source terms.',
               'Per-square-meter prices with a time unit require an additional time calculation and are not fully represented by sqm.',
               'No tax, discounts, extra charges, quantity or term is inferred; no recommendation is made.',
               'The caller must extract and check source facts and source locations before using this tool.']}, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, TypeError, KeyError, InvalidOperation, json.JSONDecodeError) as exc:
        print(f'Invalid input: {type(exc).__name__}: {exc}', file=sys.stderr)
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
