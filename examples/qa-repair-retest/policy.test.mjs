import { test } from 'node:test';
import assert from 'node:assert/strict';
import { quote, plans } from './policy.mjs';

test('selects the smallest sufficient plan, including exact boundaries', () => {
  assert.equal(quote(2, 4).plan, 'starter');
  assert.equal(quote(3, 4).plan, 'team');
  assert.equal(quote(10, 4).plan, 'team');
  assert.equal(quote(11, 4).plan, 'portfolio');
  assert.equal(quote(25, 4).plan, 'portfolio');
});

test('never recommends a plan below the requested sites or runs', () => {
  assert.equal(quote(26, 1), null);
  assert.equal(quote(10, 11), null);
  for (let sites = 1; sites <= 30; sites++) {
    for (const cadence of [1, 4, 8]) {
      const result = quote(sites, cadence);
      const eligible = plans.filter(p => p.sites >= sites && p.runs >= sites * cadence);
      assert.equal(result?.plan ?? null, eligible[0]?.id ?? null);
    }
  }
});

test('annual charge is calculated before rounding the monthly equivalent', () => {
  const result = quote(3, 4, true);
  assert.equal(result.displayedMonthly, 46);
  assert.equal(result.annualTotal, 550);
  assert.notEqual(result.annualTotal, result.displayedMonthly * 12);
});

test('invalid input cannot produce a plausible recommendation', () => {
  for (const input of [0, -1, 1.5, NaN, Infinity, '2', Number.MAX_SAFE_INTEGER + 1]) {
    assert.throws(() => quote(input, 1), RangeError);
    assert.throws(() => quote(1, input), RangeError);
  }
});
